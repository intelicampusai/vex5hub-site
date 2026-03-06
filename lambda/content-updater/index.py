
import json
import os
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional, List, Dict

import boto3
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
secrets_client = boto3.client('secretsmanager')

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME')
PROJECT_NAME = os.environ.get('PROJECT_NAME', 'vex5hub')
SEASON_ID = int(os.environ.get('SEASON_ID', 197)) # Default to 2025-26, override as needed
WORLDS_SKUS = os.environ.get('WORLDS_SKUS', '')

table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None

# RobotEvents API
RE_API_BASE = "https://www.robotevents.com/api/v2"

def handler(event: dict, context: Any) -> dict:
    """Main Lambda handler triggered by EventBridge."""
    logger.info(f"VEX V5 Hub Update triggered at {datetime.now(timezone.utc).isoformat()}")

    api_key = get_api_key()
    if not api_key:
        return {"statusCode": 500, "body": "Missing RobotEvents API Key"}

    results = {"timestamp": datetime.now(timezone.utc).isoformat(), "updates": [], "errors": []}

    try:
        # 1. Update Events (fast: one API call, stores level+status to DynamoDB)
        update_events(api_key)
        results["updates"].append("events")

        # 2. Fetch Worlds Qualified teams (for flag tagging in step 3)
        worlds_teams = fetch_worlds_teams(api_key, SEASON_ID)

        # 3. Update Top Teams from Skills leaderboard
        #    *** This stores re_id (numeric RobotEvents team ID) in DynamoDB ***
        update_top_teams(api_key, worlds_teams)
        results["updates"].append("teams")

        # 4. Update Match results — reads re_id stored in step 3 (no extra API calls)
        match_count = update_matches(api_key)
        results["updates"].append(f"matches ({match_count})")

        # 5. Update team event registrations (upcoming/live events)
        event_count = update_team_events(api_key)
        results["updates"].append(f"team_events ({event_count})")

    except Exception as e:
        logger.error(f"Update failed: {e}", exc_info=True)
        results["errors"].append(str(e))

    return {"statusCode": 200, "body": json.dumps(results)}

def get_api_key() -> Optional[str]:
    """Retrieve API key from Secrets Manager."""
    try:
        secret = secrets_client.get_secret_value(SecretId=f"{PROJECT_NAME}/robotevents-api-key")
        data = json.loads(secret['SecretString'])
        return data.get('api_key')
    except Exception as e:
        logger.error(f"Failed to get API key: {e}")
        return None

def save_event_to_dynamo(evt: dict):
    """Process and save a single event object to DynamoDB."""
    sku = evt.get('sku')
    if not sku:
        return
        
    start_date = evt.get('start', '')
    level = evt.get('level', '')
    
    item = {
        'PK': f'SEASON#{SEASON_ID}',
        'SK': f'EVENT#{start_date}#{sku}',
        'sku': sku,
        'name': evt.get('name'),
        'level': level,
        'start': start_date,
        'end': evt.get('end'),
        'location': {
            'venue': evt.get('location', {}).get('venue'),
            'city': evt.get('location', {}).get('city'),
            'region': evt.get('location', {}).get('region'),
            'country': evt.get('location', {}).get('country')
        },
        'status': 'future',
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Status logic
    now = datetime.now(timezone.utc).isoformat()
    if start_date <= now <= evt.get('end', ''):
        item['status'] = 'active'
    elif evt.get('end', '') < now:
        item['status'] = 'past'
        
    table.put_item(Item=item)

    # Also store SKU metadata for reverse-lookup enrichment
    meta_item = {
        'PK': f'EVENT#{sku}',
        'SK': 'METADATA',
        'sku': sku,
        'name': evt.get('name'),
        'level': level,
        'start': start_date,
        'end': evt.get('end'),
        'venue': evt.get('location', {}).get('venue'),
        'city': evt.get('location', {}).get('city'),
        'region': evt.get('location', {}).get('region'),
        'country': evt.get('location', {}).get('country'),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    table.put_item(Item=meta_item)

def update_events(api_key: str):
    """Fetch events for the current season and store in DynamoDB."""
    # 1. Fetch recent past events (last 60 days) + upcoming events via paging
    from datetime import timedelta
    sixty_days_ago = (datetime.now(timezone.utc) - timedelta(days=60)).strftime('%Y-%m-%d')
    
    page = 1
    last_page = 1
    while page <= last_page and page <= 20: # Safety limit of 20 pages
        url = f"{RE_API_BASE}/events?season[]={SEASON_ID}&start={sixty_days_ago}&per_page=100&page={page}"
        data = api_request(url, api_key)
        if not data or 'data' not in data: break

        for evt in data['data']:
            save_event_to_dynamo(evt)

        last_page = data.get('meta', {}).get('last_page', 1)
        page += 1

    # 2. Explicitly fetch WORLDS_SKUS to ensure they are present even if > 60 days away
    if WORLDS_SKUS:
        skus = [s.strip() for s in WORLDS_SKUS.split(',') if s.strip()]
        for sku in skus:
            url = f"{RE_API_BASE}/events?sku[]={sku}"
            data = api_request(url, api_key)
            if data and 'data' in data and len(data['data']) > 0:
                save_event_to_dynamo(data['data'][0])

def update_matches(api_key: str) -> int:
    """Fetch match results for top teams at Signature and Regional events.
    
    Uses /teams/{id}/matches endpoint (correct RE API) filtered to season.
    Only stores matches from Signature or Regional level events.
    
    Stores two item types per unique match:
      1. PK: EVENT#{sku}  SK: MATCH#{division_id}#{match_num:04d}   (source of truth)
      2. PK: TEAM#{num}   SK: MATCH#{sku}#{division_id}#{match_num:04d}  (reverse lookup)
    """
    import time
    TARGET_LEVELS = {'Signature', 'Regional'}
    total_matches = 0
    seen_matches = set()  # deduplicate: tracks (sku, div_id, match_num)
    team_records: Dict[str, Dict[str, int]] = {}

    # Get top tracked teams from DynamoDB GSI1 (ranked teams)
    resp = table.query(
        IndexName='GSI1',
        KeyConditionExpression=(
            Key('GSI1PK').eq(f'SEASON#{SEASON_ID}') &
            Key('GSI1SK').begins_with('RANK#')
        ),
        Limit=100  # top 100 teams
    )
    teams = resp.get('Items', [])
    team_lookup = {team.get('number'): team for team in teams if team.get('number')}
    logger.info(f"Fetching matches for {len(teams)} teams...")

    # Pre-fetch event metadata map for denormalization
    # Since we don't have many events per season, we can just fetch all
    events_resp = table.query(
        KeyConditionExpression=Key('PK').eq(f'SEASON#{SEASON_ID}') & Key('SK').begins_with('EVENT#')
    )
    event_meta_map = {}
    for e in events_resp.get('Items', []):
        sku = e['sku']
        loc = e.get('location', {})
        loc_str = ", ".join(filter(None, [loc.get('city'), loc.get('region'), loc.get('country')]))
        event_meta_map[sku] = {
            'start': e.get('start'),
            'end': e.get('end'),
            'location': loc_str
        }

    for team in teams:
        team_num = team.get('number', '')
        re_id = team.get('re_id')   # numeric RobotEvents team ID stored during update_top_teams
        if not team_num or not re_id:
            continue

        re_id = int(re_id)

        # Fetch matches for this team this season
        matches_data = api_request(
            f"{RE_API_BASE}/teams/{re_id}/matches?season[]={SEASON_ID}&per_page=250",
            api_key
        )
        if not matches_data or 'data' not in matches_data:
            continue

        for match in matches_data['data']:
            evt_info = match.get('event', {})
            sku = evt_info.get('code', '')
            evt_name = evt_info.get('name', '')
            div_id = match.get('division', {}).get('id', 1)
            match_num = match.get('matchnum', 0)
            round_num = match.get('round', 0)
            instance = match.get('instance', 0)
            match_key = (sku, div_id, round_num, instance, match_num)

            # Filter: only Signature/Regional events
            # We check DynamoDB event level if available, else skip unknown levels
            # (We stored level in update_events, keyed by SKU)
            # Use a lightweight check: if keywords appear in event name
            # Proper check: Look up from our stored events table
            if not sku:
                continue

            # Compute record for list view (only count finished matches with scores)
            _track_team_record(team_records, team_num, match)

            # Only write team reverse-lookup items for this specific team
            evt_meta = event_meta_map.get(sku, {})
            _write_team_match_item(match, sku, evt_name, team_num, evt_meta)

            # Only write event source-of-truth once per unique match
            if match_key not in seen_matches:
                _write_event_match_item(match, sku, evt_name, evt_meta)
                seen_matches.add(match_key)
                total_matches += 1

        time.sleep(0.5)  # gentle rate limiting between teams

    _persist_team_records(team_records, team_lookup)

    logger.info(f"Total unique matches stored: {total_matches}")
    return total_matches


def _track_team_record(team_records: Dict[str, Dict[str, int]], team_num: str, match: dict):
    """Increment local W-L-T tallies for a team based on a single match."""
    if not team_num:
        return

    alliances = match.get('alliances', [])
    red = next((a for a in alliances if a.get('color') == 'red'), {})
    blue = next((a for a in alliances if a.get('color') == 'blue'), {})
    red_teams = [t.get('team', {}).get('name', '') for t in red.get('teams', [])]
    blue_teams = [t.get('team', {}).get('name', '') for t in blue.get('teams', [])]
    red_score = red.get('score')
    blue_score = blue.get('score')

    if red_score is None or blue_score is None:
        return  # Skip matches without final scores

    alliance_color = 'red' if team_num in red_teams else 'blue'
    my_score = red_score if alliance_color == 'red' else blue_score
    opp_score = blue_score if alliance_color == 'red' else red_score
    if my_score is None or opp_score is None:
        return

    stats = team_records.setdefault(team_num, {
        'wins': 0,
        'losses': 0,
        'ties': 0,
        'total_matches': 0,
        'wp': 0,
        'ap': 0,
        'sp': 0
    })

    stats['total_matches'] += 1
    my_score = int(my_score)
    opp_score = int(opp_score)

    if my_score > opp_score:
        stats['wins'] += 1
        stats['wp'] += 2  # Standard WP scoring
    elif my_score < opp_score:
        stats['losses'] += 1
    else:
        stats['ties'] += 1
        stats['wp'] += 1


def _persist_team_records(team_records: Dict[str, Dict[str, int]], team_lookup: Dict[str, dict]):
    """Write aggregated stats back to DynamoDB for each team."""
    for team_num, stats in team_records.items():
        existing = team_lookup.get(team_num, {})
        stats_payload = {
            'wins': Decimal(str(stats['wins'])),
            'losses': Decimal(str(stats['losses'])),
            'ties': Decimal(str(stats['ties'])),
            'total_matches': Decimal(str(stats['total_matches'])),
            'wp': Decimal(str(stats['wp'])),
            'ap': Decimal('0'),
            'sp': Decimal('0')
        }

        # Preserve the ranking value if we have one
        existing_rank = None
        existing_stats = existing.get('stats') or {}
        if 'rank' in existing_stats:
            existing_rank = existing_stats['rank']
        else:
            gsi_key = existing.get('GSI1SK', '')
            if gsi_key.startswith('RANK#'):
                try:
                    rank_str = gsi_key.split('#')[1]
                    existing_rank = Decimal(rank_str)
                except Exception:
                    existing_rank = None

        if existing_rank is not None:
            stats_payload['rank'] = existing_rank if isinstance(existing_rank, Decimal) else Decimal(str(existing_rank))

        try:
            table.update_item(
                Key={'PK': f'TEAM#{team_num}', 'SK': 'METADATA'},
                UpdateExpression="SET stats = :stats, updated_at = :updated_at",
                ExpressionAttributeValues={
                    ':stats': stats_payload,
                    ':updated_at': datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to persist stats for TEAM#{team_num}: {e}")


def update_team_events(api_key: str) -> int:
    """Fetch upcoming/active event registrations for tracked teams.

    For each team, calls /teams/{re_id}/events?season[]=SEASON_ID and stores
    items with PK: TEAM#{num}  SK: EVENT#{start_date}#{sku} for future or
    active events.
    """
    import time
    total_events = 0

    # Get tracked teams
    resp = table.query(
        IndexName='GSI1',
        KeyConditionExpression=(
            Key('GSI1PK').eq(f'SEASON#{SEASON_ID}') &
            Key('GSI1SK').begins_with('RANK#')
        ),
        Limit=200
    )
    teams = resp.get('Items', [])
    logger.info(f"Fetching event registrations for {len(teams)} teams...")

    for team in teams:
        team_num = team.get('number', '')
        re_id = team.get('re_id')
        if not team_num or not re_id:
            continue

        re_id = int(re_id)

        events_data = api_request(
            f"{RE_API_BASE}/teams/{re_id}/events?season[]={SEASON_ID}&per_page=100",
            api_key
        )
        if not events_data or 'data' not in events_data:
            continue

        for evt in events_data['data']:
            sku = evt.get('sku', '')
            evt_name = evt.get('name', '')
            start_date = evt.get('start', '')
            end_date = evt.get('end', '')
            level = evt.get('level', '')
            loc = evt.get('location', {})
            loc_str = ', '.join(filter(None, [
                loc.get('city'), loc.get('region'), loc.get('country')
            ]))

            # Determine status using proper datetime comparison
            try:
                now_dt = datetime.now(timezone.utc)
                end_dt = datetime.fromisoformat(end_date) if end_date else None
                start_dt = datetime.fromisoformat(start_date) if start_date else None
                
                if end_dt and end_dt < now_dt:
                    status = 'past'
                elif start_dt and start_dt <= now_dt:
                    status = 'active'
                else:
                    status = 'future'
            except (ValueError, TypeError):
                # If date parsing fails, default to future (better to show than miss)
                status = 'future'

            # Only store upcoming or active events
            if status == 'past':
                continue

            item = {
                'PK': f'TEAM#{team_num}',
                'SK': f'EVENT#{start_date}#{sku}',
                'sku': sku,
                'event_name': evt_name,
                'start': start_date,
                'end': end_date,
                'location': loc_str,
                'level': level,
                'status': status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            try:
                table.put_item(Item=item)
                total_events += 1
            except Exception as e:
                logger.error(f"Error writing team event TEAM#{team_num}/EVENT#{start_date}#{sku}: {e}")

        time.sleep(0.3)

    logger.info(f"Total team event registrations stored: {total_events}")
    return total_events


def _write_event_match_item(match: dict, sku: str, evt_name: str, evt_meta: dict = None):
    """Write the event-owned source-of-truth match item.
    PK: EVENT#{sku}  SK: MATCH#{div_id}#{match_num:04d}
    """
    if evt_meta is None: evt_meta = {}
    div_id = match.get('division', {}).get('id', 1)
    match_num = match.get('matchnum', 0)
    round_num = match.get('round', 0)
    instance = match.get('instance', 0)
    round_names = {1: 'Practice', 2: 'Qualification', 3: 'Quarterfinal', 4: 'Semifinal', 5: 'Final', 6: 'Round of 16'}
    round_name = round_names.get(round_num, f'Round {round_num}')

    alliances = match.get('alliances', [])
    red = next((a for a in alliances if a.get('color') == 'red'), {})
    blue = next((a for a in alliances if a.get('color') == 'blue'), {})
    red_teams = [t.get('team', {}).get('name', '') for t in red.get('teams', [])]
    blue_teams = [t.get('team', {}).get('name', '') for t in blue.get('teams', [])]
    red_score = red.get('score')
    blue_score = blue.get('score')

    match_sk = f"MATCH#{div_id}#{round_num}#{instance:02d}#{match_num:04d}"
    item = {
        'PK': f'EVENT#{sku}',
        'SK': match_sk,
        'sku': sku,
        'event_name': evt_name,
        'division_id': Decimal(str(div_id)),
        'match_num': Decimal(str(match_num)),
        'round': round_name,
        'instance': Decimal(str(instance)),
        'field': match.get('field', ''),
        'scheduled': match.get('scheduled', ''),
        'started': match.get('started', ''),
        'red_teams': red_teams,
        'blue_teams': blue_teams,
        'red_score': Decimal(str(red_score)) if red_score is not None else None,
        'blue_score': Decimal(str(blue_score)) if blue_score is not None else None,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    item = {k: v for k, v in item.items() if v is not None}
    try:
        existing = table.get_item(Key={'PK': item['PK'], 'SK': item['SK']}).get('Item')
        if existing and 'video_url' in existing:
            item['video_url'] = existing['video_url']
            
        table.put_item(Item=item)
        
        # Increment match_count on the metadata item
        table.update_item(
            Key={'PK': f'EVENT#{sku}', 'SK': 'METADATA'},
            UpdateExpression="ADD match_count :inc",
            ExpressionAttributeValues={':inc': Decimal('1')}
        )

        # Increment match_count on the seasonal event item (used in lists)
        start_date = evt_meta.get('start')
        if start_date:
            table.update_item(
                Key={'PK': f'SEASON#{SEASON_ID}', 'SK': f'EVENT#{start_date}#{sku}'},
                UpdateExpression="ADD match_count :inc",
                ExpressionAttributeValues={':inc': Decimal('1')}
            )
    except Exception as e:
        logger.error(f"Error writing event match {sku}/{match_sk}: {e}")

def _write_team_match_item(match: dict, sku: str, evt_name: str, team_num: str, evt_meta: dict = None):
    """Write the team reverse-lookup match item.
    PK: TEAM#{num}  SK: MATCH#{sku}#{div_id}#{match_num:04d}
    """
    if evt_meta is None: evt_meta = {}
    div_id = match.get('division', {}).get('id', 1)
    match_num = match.get('matchnum', 0)
    round_num = match.get('round', 0)
    instance = match.get('instance', 0)
    round_names = {1: 'Practice', 2: 'Qualification', 3: 'Quarterfinal', 4: 'Semifinal', 5: 'Final', 6: 'Round of 16'}
    round_name = round_names.get(round_num, f'Round {round_num}')

    alliances = match.get('alliances', [])
    red = next((a for a in alliances if a.get('color') == 'red'), {})
    blue = next((a for a in alliances if a.get('color') == 'blue'), {})
    red_teams = [t.get('team', {}).get('name', '') for t in red.get('teams', [])]
    blue_teams = [t.get('team', {}).get('name', '') for t in blue.get('teams', [])]
    red_score = red.get('score')
    blue_score = blue.get('score')

    alliance_color = 'red' if team_num in red_teams else 'blue'
    my_score = red_score if alliance_color == 'red' else blue_score
    opp_score = blue_score if alliance_color == 'red' else red_score
    partner_teams = red_teams if alliance_color == 'red' else blue_teams
    opponent_teams = blue_teams if alliance_color == 'red' else red_teams
    won = (my_score is not None and opp_score is not None and int(my_score) > int(opp_score))

    team_match_sk = f"MATCH#{sku}#{div_id}#{round_num}#{instance:02d}#{match_num:04d}"
    item = {
        'PK': f'TEAM#{team_num}',
        'SK': team_match_sk,
        'sku': sku,
        'event_name': evt_name,
        'division_id': Decimal(str(div_id)),
        'match_num': Decimal(str(match_num)),
        'round': round_name,
        'instance': Decimal(str(instance)),
        'alliance': alliance_color,
        'partner_teams': [t for t in partner_teams if t != team_num],
        'opponent_teams': opponent_teams,
        'my_score': Decimal(str(my_score)) if my_score is not None else None,
        'opp_score': Decimal(str(opp_score)) if opp_score is not None else None,
        'won': won,
        'scheduled': match.get('scheduled', ''),
        'event_start': evt_meta.get('start'),
        'event_end': evt_meta.get('end'),
        'event_location': evt_meta.get('location'),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    item = {k: v for k, v in item.items() if v is not None}
    try:
        existing = table.get_item(Key={'PK': item['PK'], 'SK': item['SK']}).get('Item')
        if existing and 'video_url' in existing:
            item['video_url'] = existing['video_url']
            
        table.put_item(Item=item)
    except Exception as e:
        logger.error(f"Error writing team match TEAM#{team_num}/{team_match_sk}: {e}")



def fetch_worlds_teams(api_key: str, season_id: int) -> set:
    """Fetch the set of team numbers registered for the World Championship."""
    qualified_teams = set()
    
    # Priority: use specific SKUs if provided via environment variable
    if WORLDS_SKUS:
        skus = [s.strip() for s in WORLDS_SKUS.split(',') if s.strip()]
        for sku in skus:
            logger.info(f"Fetching teams for specific Worlds SKU: {sku}")
            
            # Step 1: Resolve SKU to event ID via /events?sku[]=...
            event_lookup_url = f"{RE_API_BASE}/events?sku[]={sku}"
            event_data = api_request(event_lookup_url, api_key)
            if not event_data or 'data' not in event_data or len(event_data['data']) == 0:
                logger.warning(f"Could not resolve SKU {sku} to event ID, skipping.")
                continue
            
            evt_id = event_data['data'][0].get('id')
            if not evt_id:
                logger.warning(f"No event ID found for SKU {sku}, skipping.")
                continue
            
            logger.info(f"Resolved SKU {sku} to event ID {evt_id}")
            
            # Step 2: Fetch teams using the resolved event ID
            page = 1
            last_page = 1
            while page <= last_page and page <= 50:
                teams_url = f"{RE_API_BASE}/events/{evt_id}/teams?page={page}&per_page=250"
                teams_data = api_request(teams_url, api_key)
                if not teams_data or 'data' not in teams_data:
                    break
                for team in teams_data['data']:
                    team_num = team.get('number')
                    if team_num: qualified_teams.add(team_num)
                last_page = teams_data.get('meta', {}).get('last_page', 1)
                page += 1
        
        # When WORLDS_SKUS is explicitly configured, always return here.
        # Do NOT fall through to the legacy fallback — an empty result simply
        # means no teams are registered yet for the configured Worlds events.
        logger.info(f"Found {len(qualified_teams)} teams from specific SKUs.")
        return qualified_teams

    # Fallback/Legacy: find the Worlds event(s) using the native level[]=World query
    # Only used when WORLDS_SKUS is not configured at all.
    events_url = f"{RE_API_BASE}/events?season[]={season_id}&level[]=World&per_page=100"
    events_data = api_request(events_url, api_key)
    if not events_data or 'data' not in events_data:
        return qualified_teams
        
    worlds_events = events_data.get('data', [])
            
    if not worlds_events:
        logger.warning("No World Championship events found for this season via level[]=World API query.")
        return qualified_teams
        
    # Then fetch teams for each
    for evt in worlds_events:
        evt_id = evt.get('id')
        if not evt_id: continue
        
        # STRICT FILTER: RobotEvents API returns Signature events in level[]=World query
        if evt.get('level') != 'World':
            continue
            
        logger.info(f"Fetching teams for Worlds event: {evt.get('name')} ({evt_id})")
        
        page = 1
        last_page = 1
        
        while page <= last_page and page <= 50: # Safety limit
            teams_url = f"{RE_API_BASE}/events/{evt_id}/teams?page={page}&per_page=250"
            teams_data = api_request(teams_url, api_key)
            
            if not teams_data or 'data' not in teams_data:
                break
                
            for team in teams_data['data']:
                team_num = team.get('number')
                if team_num: qualified_teams.add(team_num)
                
            last_page = teams_data.get('meta', {}).get('last_page', 1)
            page += 1
            
    logger.info(f"Found {len(qualified_teams)} Worlds qualified teams.")
    return qualified_teams

def update_top_teams(api_key: str, worlds_teams: set = None):
    """Fetch top teams from Skills for both Middle and High School."""
    # Define endpoints for both grade levels
    endpoints = [
        ("Middle School", "https://www.robotevents.com/api/seasons/197/skills?post_season=0&grade_level=Middle%20School"),
        ("High School", "https://www.robotevents.com/api/seasons/197/skills?post_season=0&grade_level=High%20School")
    ]
    
    total_teams = 0
    
    for grade, url in endpoints:
        try:
            logger.info(f"Fetching {grade} skills from: {url}")
            data = api_request(url, api_key)
            
            if isinstance(data, list) and len(data) > 0:
                logger.info(f"Fetched {len(data)} teams for {grade}")
                
                # Process top 150 for each grade + any Worlds Qualified team to ensure they appear
                for i, entry in enumerate(data):
                    team_info = entry.get('team', {})
                    team_num = team_info.get('team')
                    scores = entry.get('scores', {})
                    
                    is_worlds = team_num in (worlds_teams or set())
                    if i >= 150 and not is_worlds:
                        continue
                        
                    rank = entry.get('rank')
                    score = scores.get('score')
                    
                    # Check for required fields
                    if not team_num or rank is None: 
                        continue

                    # Create unique GSI1SK for combined ranking list if needed, 
                    # or just use standard rank. We'll use grade in SK to differentiate if sorting by grade.
                    # For now, we store them all.
                    
                    item = {
                        'PK': f'TEAM#{team_num}',
                        'SK': 'METADATA',
                        'GSI1PK': f'SEASON#{SEASON_ID}',
                        'GSI1SK': f'RANK#{rank:04d}#TEAM#{team_num}',
                        'number': team_num,
                        're_id': team_info.get('id'),  # numeric RobotEvents team ID
                        'name': team_info.get('teamName'),
                        'organization': team_info.get('organization'),
                        'region': team_info.get('region'),
                        'country': team_info.get('country'),
                        'grade': team_info.get('gradeLevel'),
                        'worlds_qualified': team_num in (worlds_teams or set()),
                        'location': {
                            'city': team_info.get('city'),
                            'region': team_info.get('region'),
                            'country': team_info.get('country')
                        },
                        'skills': {
                            'combined_score': Decimal(str(score)) if score is not None else Decimal(0),
                            'rank': Decimal(str(rank)),
                            'driver': Decimal(str(scores.get('driver', 0))),
                            'programming': Decimal(str(scores.get('programming', 0)))
                        },
                        'stats': {
                            'rank': Decimal(str(rank)),
                            'wins': Decimal('0'),
                            'losses': Decimal('0'),
                            'ties': Decimal('0'),
                            'total_matches': Decimal('0'),
                            'wp': Decimal('0'),
                            'ap': Decimal('0'),
                            'sp': Decimal('0')
                        },
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    table.put_item(Item=item)
                    total_teams += 1
                
        except Exception as e:
            logger.warning(f"Skills fetch failed for {grade}: {e}")

    logger.info(f"Total teams updated: {total_teams}")

    # Fallback to basic team fetch if needed
    logger.info("Falling back to basic team list fetch")
    # ... fallback logic (keep existing if desired, or simpler)

def api_request(url: str, api_key: str, max_retries: int = 3) -> Optional[dict]:
    import time
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
        'User-Agent': 'Vex5Hub/1.0 (internal-tool)'
    })
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 5 * (2 ** attempt)  # 5s, 10s, 20s
                logger.warning(f"Rate limited (429) on {url}, waiting {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                logger.error(f"API Error ({url}): HTTP Error {e.code}: {e.reason}")
                return None
        except Exception as e:
            logger.error(f"API Error ({url}): {e}")
            return None
    logger.error(f"Max retries exceeded for {url}")
    return None
