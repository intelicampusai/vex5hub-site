"""
VEX V5 Hub Content Updater Lambda Function

Fetches live data from the RobotEvents API and stores it in DynamoDB.
Triggered by EventBridge every 4 hours.

Data sources:
  - RobotEvents API v2: https://www.robotevents.com/api/v2
  - All items include source_url linking to official pages

DynamoDB single-table design:
  PK / SK patterns:
    REGION#{id} / META               → region metadata
    REGION#{id} / TEAM#{number}      → team record
    COMPETITION / COMP#{id}          → competition info
    EVENT / EVT#{id}                 → event info
    ROBOT / VID#{id}                 → viral robot video
    TECH / BRK#{id}                  → tech breakdown

  GSI1 (GSI1PK / GSI1SK):
    REGION / #{id}                   → list all regions
    COMPETITION / #{sort_key}        → list competitions
    EVENT / #{date}                  → list events by date
    ROBOT / #{id}                    → list robots
    TECH / #{id}                     → list tech breakdowns

Maintained by Team 3150N Nighthawks.
"""

import json
import os
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
cloudfront_client = boto3.client('cloudfront')
secrets_client = boto3.client('secretsmanager')

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME')
DATA_BUCKET = os.environ.get('DATA_BUCKET_NAME')
CLOUDFRONT_DIST_ID = os.environ.get('CLOUDFRONT_DIST_ID')
PROJECT_NAME = os.environ.get('PROJECT_NAME', 'nighthawks')

table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None

# RobotEvents API
RE_API_BASE = "https://www.robotevents.com/api/v2"
RE_WEB_BASE = "https://www.robotevents.com"
# Default to 190 but allow override via env var. User must verify this ID.
SEASON_ID = int(os.environ.get('SEASON_ID', 190))
PROGRAM_ID = 1   # VRC (V5 Robotics Competition)

# Regions to track (region name → RobotEvents region string)
TRACKED_REGIONS = {
    "ontario":          {"name": "Ontario",          "country": "Canada",  "re_region": "Ontario"},
    "british-columbia": {"name": "British Columbia", "country": "Canada",  "re_region": "British Columbia"},
    "alberta":          {"name": "Alberta",          "country": "Canada",  "re_region": "Alberta"},
    "california":       {"name": "California",       "country": "USA",     "re_region": "California"},
    "texas":            {"name": "Texas",            "country": "USA",     "re_region": "Texas"},
    "midwest":          {"name": "Midwest (US)",     "country": "USA",     "re_region": "Illinois,Michigan,Ohio,Indiana,Wisconsin"},
    "china":            {"name": "China",            "country": "China",   "re_region": "China"},
}


def handler(event: dict, context: Any) -> dict:
    """Main Lambda handler triggered by EventBridge every 4 hours."""
    logger.info(f"Content update triggered at {datetime.now(timezone.utc).isoformat()}")

    api_key = get_api_key()
    results = {"timestamp": datetime.now(timezone.utc).isoformat(), "updates": [], "errors": []}

    # --- Update Teams ---
    try:
        update_teams(api_key)
        results["updates"].append("teams")
    except Exception as e:
        logger.error(f"Teams update failed: {e}", exc_info=True)
        results["errors"].append(f"teams: {str(e)}")

    # --- Update Competitions ---
    try:
        update_competitions(api_key)
        results["updates"].append("competitions")
    except Exception as e:
        logger.error(f"Competitions update failed: {e}", exc_info=True)
        results["errors"].append(f"competitions: {str(e)}")

    # --- Update Events ---
    try:
        update_events(api_key)
        results["updates"].append("events")
    except Exception as e:
        logger.error(f"Events update failed: {e}", exc_info=True)
        results["errors"].append(f"events: {str(e)}")

    # --- Update Robots ---
    try:
        update_robots()
        results["updates"].append("robots")
    except Exception as e:
        logger.error(f"Robots update failed: {e}", exc_info=True)
        results["errors"].append(f"robots: {str(e)}")

    # Invalidate CloudFront API cache
    try:
        invalidate_cache(["/api/*"])
    except Exception as e:
        logger.warning(f"Cache invalidation failed: {e}")

    logger.info(f"Content update completed: {json.dumps(results)}")
    return {"statusCode": 200, "body": json.dumps(results)}


# ===================================
# API Key Management
# ===================================

def get_api_key() -> Optional[str]:
    """Retrieve RobotEvents API key from Secrets Manager."""
    try:
        secret = secrets_client.get_secret_value(
            SecretId=f"{PROJECT_NAME}/robotevents-api-key"
        )
        data = json.loads(secret['SecretString'])
        return data.get('api_key')
    except Exception as e:
        logger.warning(f"Could not retrieve API key: {e}. Using seed data only.")
        return None


# ===================================
# Teams
# ===================================

def update_teams(api_key: Optional[str]):
    """Fetch team rankings from RobotEvents API and store in DynamoDB."""

    for region_id, info in TRACKED_REGIONS.items():
        # Write region metadata
        table.put_item(Item={
            'PK': f'REGION#{region_id}',
            'SK': 'META',
            'GSI1PK': 'REGION',
            'GSI1SK': f'#{region_id}',
            'id': region_id,
            'name': info['name'],
            'country': info['country'],
            'source_url': f"{RE_WEB_BASE}/robot-competitions/vex-robotics-competition",
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })

        if not api_key:
            logger.info(f"No API key — skipping live fetch for {region_id}")
            continue

        # Fetch top teams in region from skills rankings (HS and MS)
        hs_teams = fetch_region_teams(api_key, info['re_region'], 'High School')
        ms_teams = fetch_region_teams(api_key, info['re_region'], 'Middle School')
        
        # Combine and sort by skills score
        all_teams = hs_teams + ms_teams
        all_teams.sort(key=lambda t: t.get('skills_score', 0), reverse=True)
        
        # Store top 20 total
        for rank, team in enumerate(all_teams[:20], 1):
            team_number = team.get('number', 'N/A')
            team_name = team.get('team_name', '')
            team_id = team.get('id', '')

            item = {
                'PK': f'REGION#{region_id}',
                'SK': f'TEAM#{team_number}',
                'GSI1PK': 'TEAM',
                'GSI1SK': f'#{region_id}#{rank:04d}',
                'id': team_number,
                'number': team_number,
                'name': team_name,
                'rank': rank,
                'skills_score': Decimal(str(team.get('skills_score', 0))),
                'skills_rank': Decimal(str(team.get('skills_rank', 0))),
                'wins': Decimal(str(team.get('wins', 0))),
                'losses': Decimal(str(team.get('losses', 0))),
                'division': team.get('grade', 'High School'),
                'worlds_qualified': team.get('worlds_qualified', False),
                'awards': team.get('awards', []),
                'source_url': f"{RE_WEB_BASE}/teams/VRC/{team_number}",
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }

            # Preserve manually-added fields and calculate rank change
            rank_change = 0
            try:
                existing = table.get_item(Key={'PK': item['PK'], 'SK': item['SK']}).get('Item', {})
                
                # Calculate rank change (positive = improved, e.g. 5 -> 1 is +4)
                if 'rank' in existing:
                    prev_rank = int(existing['rank'])
                    rank_change = prev_rank - rank
                
                if 'match_videos' in existing:
                    item['match_videos'] = existing['match_videos']
            except Exception as e:
                logger.warning(f"Failed to read existing record for {team_number}: {e}")

            item['rank_change'] = rank_change
            table.put_item(Item=item)

    logger.info("Teams update complete")


def fetch_region_teams(api_key: str, region_filter: str, grade: str) -> list:
    """
    Fetch teams from a region via the RobotEvents Skills Rankings API.
    Returns list of team dicts sorted by skills score descending.
    """
    teams = []

    # Get skills rankings for the region this season
    url = (
        f"{RE_API_BASE}/seasons/{SEASON_ID}/skills"
        f"?region={urllib.request.quote(region_filter)}"
        f"&grade_level={urllib.request.quote(grade)}"
        f"&per_page=20"
    )
    data = api_request(url, api_key)
    if not data:
        return teams

    for entry in data.get('data', []):
        team_data = entry.get('team', {})
        teams.append({
            'id': team_data.get('id', ''),
            'number': team_data.get('name', ''),
            'team_name': team_data.get('team_name', ''),
            'grade': grade,
            'skills_score': entry.get('score', 0),
            'skills_rank': entry.get('rank', 0),
            'wins': 0,  # Populated separately from event results
            'losses': 0,
            'worlds_qualified': False,
            'awards': [],
        })

    return teams


# ===================================
# Competitions
# ===================================

def update_competitions(api_key: Optional[str]):
    """Store competition / season information in DynamoDB."""
    competitions = [
        {
            'id': 'push-back-season',
            'title': 'Push Back Season 2025-2026',
            'date': 'August 2025 - April 2026',
            'location': 'Global',
            'description': 'The current VEX V5 season featuring the Push Back game. Teams score plastic blocks into goals and compete for zone control bonuses.',
            'status': 'active',
            'participants': '20,000+ teams',
            'icon': '🎮',
            'source_url': 'https://www.vexrobotics.com/v5/competition/vrc-current-game',
        },
        {
            'id': 'worlds-2026',
            'title': 'VEX Worlds 2026',
            'date': 'April 21-30, 2026',
            'location': 'St. Louis, Missouri',
            'description': 'The VEX Robotics World Championship returns to St. Louis!',
            'status': 'upcoming',
            'participants': '10,000+ teams worldwide',
            'icon': '🏆',
            'source_url': 'https://www.robotevents.com/robot-competitions/vex-robotics-competition',
        },
        {
            'id': 'skills-standings',
            'title': 'World Skills Rankings',
            'date': 'Updated Daily',
            'location': 'Online',
            'description': 'Live rankings of the top VEX V5 teams worldwide based on Robot Skills scores.',
            'status': 'live',
            'participants': 'Rankings updated',
            'icon': '📊',
            'source_url': 'https://www.robotevents.com/robot-competitions/vex-robotics-competition/standings/skills',
        },
        {
            'id': 'signature-events',
            'title': 'Signature Events 2025-2026',
            'date': 'Throughout Season',
            'location': 'Various Locations',
            'description': 'Premier VEX V5 competitions featuring top teams from around the world.',
            'status': 'ongoing',
            'participants': 'Invitation only',
            'icon': '⭐',
            'source_url': 'https://www.robotevents.com/robot-competitions/vex-robotics-competition?regions[]=All',
        },
    ]

    if api_key:
        live = fetch_live_competitions(api_key)
        if live:
            competitions.extend(live)

    for comp in competitions:
        table.put_item(Item={
            'PK': 'COMPETITION',
            'SK': f"COMP#{comp['id']}",
            'GSI1PK': 'COMPETITION',
            'GSI1SK': f"#{comp['id']}",
            **{k: v for k, v in comp.items()},
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })

    logger.info(f"Stored {len(competitions)} competitions")


def fetch_live_competitions(api_key: str) -> list:
    """Fetch recently completed events from RobotEvents API."""
    url = (
        f"{RE_API_BASE}/events"
        f"?season[]={SEASON_ID}"
        f"&end=2026-02-10"
        f"&per_page=5"
        f"&order=desc"
    )
    data = api_request(url, api_key)
    if not data:
        return []

    results = []
    for evt in data.get('data', []):
        sku = evt.get('sku', '')
        results.append({
            'id': f"live-{sku}",
            'title': evt.get('name', ''),
            'date': evt.get('start', ''),
            'location': f"{evt.get('location', {}).get('city', '')}, {evt.get('location', {}).get('region', '')}",
            'description': f"VRC event ({sku})",
            'status': 'completed',
            'participants': '',
            'icon': '🏁',
            'source_url': f"{RE_WEB_BASE}/robot-competitions/vex-robotics-competition/{sku}.html",
        })
    return results


# ===================================
# Events
# ===================================

def update_events(api_key: Optional[str]):
    """Store upcoming events in DynamoDB."""
    events = [
        {
            'id': 'vex-worlds-2026',
            'title': 'VEX Robotics World Championship 2026',
            'date': 'April 21-30, 2026',
            'location': "America's Center, St. Louis, MO",
            'description': 'The premier VEX Robotics event of the year!',
            'type': 'Championship',
            'registration': 'Qualification required',
            'icon': '🌍',
            'source_url': 'https://www.robotevents.com/robot-competitions/vex-robotics-competition',
        },
        {
            'id': 'ontario-provincials-2026',
            'title': 'Ontario VRC Provincial Championship',
            'date': 'March 2026',
            'location': 'Ontario, Canada',
            'description': 'Top Ontario VEX V5 teams compete for provincial titles and Worlds spots.',
            'type': 'Provincial',
            'registration': 'Qualification required',
            'icon': '🍁',
            'source_url': 'https://www.robotevents.com/robot-competitions/vex-robotics-competition?regions[]=Ontario',
        },
    ]

    if api_key:
        live = fetch_upcoming_events(api_key)
        if live:
            events.extend(live)

    for evt in events:
        table.put_item(Item={
            'PK': 'EVENT',
            'SK': f"EVT#{evt['id']}",
            'GSI1PK': 'EVENT',
            'GSI1SK': f"#{evt.get('date', '')}#{evt['id']}",
            **{k: v for k, v in evt.items()},
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })

    logger.info(f"Stored {len(events)} events")


def fetch_upcoming_events(api_key: str) -> list:
    """Fetch upcoming events from RobotEvents API."""
    url = (
        f"{RE_API_BASE}/events"
        f"?season[]={SEASON_ID}"
        f"&start=2026-02-10"
        f"&per_page=10"
        f"&order=asc"
    )
    data = api_request(url, api_key)
    if not data:
        return []

    results = []
    for evt in data.get('data', []):
        sku = evt.get('sku', '')
        loc = evt.get('location', {})
        results.append({
            'id': f"upcoming-{sku}",
            'title': evt.get('name', ''),
            'date': evt.get('start', ''),
            'location': f"{loc.get('city', '')}, {loc.get('region', '')}",
            'description': f"VRC event ({sku})",
            'type': 'Qualifier',
            'registration': 'Open',
            'icon': '📍',
            'source_url': f"{RE_WEB_BASE}/robot-competitions/vex-robotics-competition/{sku}.html",
        })
    return results


# ===================================
# Robots / Viral Content
# ===================================

def update_robots():
    """Store robot design and tech breakdown content."""
    viral = [
        {
            'id': 'pushback-clamp-bot',
            'title': 'Push Back Clamp Bot Reveal',
            'team': '5225A — Gael Force',
            'description': 'High-speed pneumatic clamp bot scoring full field in autonomous.',
            'icon': '🤖',
            'url': 'https://www.youtube.com/results?search_query=vex+push+back+robot+reveal',
            'source_url': 'https://www.robotevents.com/teams/VRC/5225A',
        },
        {
            'id': 'skills-world-record',
            'title': 'Skills World Record Run',
            'team': '1599Z — Shanghai Stars',
            'description': 'Autonomous + Driver Skills combined score over 400 points.',
            'icon': '🏆',
            'url': 'https://www.youtube.com/results?search_query=vex+v5+skills+world+record+push+back',
            'source_url': 'https://www.robotevents.com/teams/VRC/1599Z',
        },
    ]

    tech = [
        {
            'id': 'catapult-vs-flywheel',
            'title': 'Catapult vs Flywheel: Push Back Meta',
            'description': 'Analysis of the two dominant scoring mechanisms in the 2025-2026 season.',
            'source_url': 'https://www.vexforum.com/',
        },
        {
            'id': 'auton-path-planning',
            'title': 'Autonomous Path Planning with Odometry',
            'description': 'How top teams use PID + odometry for consistent autonomous routines.',
            'source_url': 'https://www.vexforum.com/',
        },
    ]

    for v in viral:
        table.put_item(Item={
            'PK': 'ROBOT',
            'SK': f"VID#{v['id']}",
            'GSI1PK': 'ROBOT',
            'GSI1SK': f"#{v['id']}",
            **v,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })

    for t in tech:
        table.put_item(Item={
            'PK': 'TECH',
            'SK': f"BRK#{t['id']}",
            'GSI1PK': 'TECH',
            'GSI1SK': f"#{t['id']}",
            **t,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })

    logger.info(f"Stored {len(viral)} robots, {len(tech)} tech breakdowns")


# ===================================
# RobotEvents API Helper
# ===================================

def api_request(url: str, api_key: str) -> Optional[dict]:
    """Make authenticated GET request to RobotEvents API v2."""
    try:
        req = urllib.request.Request(url, headers={
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        logger.error(f"RobotEvents API HTTP {e.code}: {e.read().decode()[:200]}")
        return None
    except Exception as e:
        logger.error(f"RobotEvents API error: {e}")
        return None


# ===================================
# Cache Invalidation
# ===================================

def invalidate_cache(paths: list) -> None:
    """Invalidate CloudFront cache for specified paths."""
    if not CLOUDFRONT_DIST_ID:
        return
    try:
        cloudfront_client.create_invalidation(
            DistributionId=CLOUDFRONT_DIST_ID,
            InvalidationBatch={
                "Paths": {"Quantity": len(paths), "Items": paths},
                "CallerReference": f"{PROJECT_NAME}-{datetime.now(timezone.utc).timestamp()}"
            }
        )
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
