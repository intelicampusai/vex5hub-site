
import json
import os
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional, List, Dict

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
secrets_client = boto3.client('secretsmanager')

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME')
PROJECT_NAME = os.environ.get('PROJECT_NAME', 'vex5hub')
SEASON_ID = int(os.environ.get('SEASON_ID', 190)) # Default to 2024-25, override as needed

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
        # 1. Update Events
        update_events(api_key)
        results["updates"].append("events")
        
        # 2. Fetch Worlds Teams
        worlds_teams = fetch_worlds_teams(api_key, SEASON_ID)
        
        # 3. Update Top Teams (e.g. from Skills)
        update_top_teams(api_key, worlds_teams)
        results["updates"].append("teams")
        
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

def update_events(api_key: str):
    """Fetch events for the current season and store in DynamoDB."""
    # Fetch events for the next 30 days and current ones
    url = f"{RE_API_BASE}/events?season[]={SEASON_ID}&start={datetime.now(timezone.utc).strftime('%Y-%m-%d')}&per_page=50"
    data = api_request(url, api_key)
    if not data or 'data' not in data: return

    for evt in data['data']:
        sku = evt.get('sku')
        start_date = evt.get('start', '')
        
        item = {
            'PK': f'SEASON#{SEASON_ID}',
            'SK': f'EVENT#{start_date}#{sku}',
            'sku': sku,
            'name': evt.get('name'),
            'start': start_date,
            'end': evt.get('end'),
            'location': {
                'venue': evt.get('location', {}).get('venue'),
                'city': evt.get('location', {}).get('city'),
                'region': evt.get('location', {}).get('region'),
                'country': evt.get('location', {}).get('country')
            },
            'status': 'future', # Will update based on date logic or real status
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Simple status logic
        now = datetime.now(timezone.utc).isoformat()
        if start_date <= now <= evt.get('end', ''):
            item['status'] = 'active'
        elif evt.get('end', '') < now:
            item['status'] = 'past'
            
        table.put_item(Item=item)

def fetch_worlds_teams(api_key: str, season_id: int) -> set:
    """Fetch the set of team numbers registered for the World Championship."""
    qualified_teams = set()
    
    # First, find the Worlds event(s)
    events_url = f"{RE_API_BASE}/events?season[]={season_id}&per_page=100"
    events_data = api_request(events_url, api_key)
    if not events_data or 'data' not in events_data:
        return qualified_teams
        
    worlds_events = []
    for evt in events_data['data']:
        name = evt.get('name', '')
        if "World Championship" in name and ("V5RC" in name or "VRC" in name):
            worlds_events.append(evt)
            
    if not worlds_events:
        logger.warning("No World Championship events found for this season.")
        return qualified_teams
        
    # Then fetch teams for each
    for evt in worlds_events:
        evt_id = evt.get('id')
        if not evt_id: continue
        
        logger.info(f"Fetching teams for Worlds event: {evt.get('name')} ({evt_id})")
        
        page = 1
        last_page = 1
        
        while page <= last_page and page <= 50: # Safety limit
            teams_url = f"{RE_API_BASE}/events/{evt_id}/teams?page={page}"
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
                
                # Process top 50 for each grade to save capacity
                for entry in data[:50]:
                    team_info = entry.get('team', {})
                    scores = entry.get('scores', {})
                    
                    team_num = team_info.get('team')
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
                        'GSI1SK': f'RANK#{rank:04d}#TEAM#{team_num}', # This mixes ranks (e.g. two Rank 1s), handled by frontend filtering
                        'number': team_num,
                        'name': team_info.get('teamName'),
                        'organization': team_info.get('organization'),
                        'region': team_info.get('region'),
                        'country': team_info.get('country'),
                        'grade': team_info.get('gradeLevel'), # e.g. "Middle School" or "High School"
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

def api_request(url: str, api_key: str) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers={
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'User-Agent': 'Vex5Hub/1.0 (internal-tool)'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.error(f"API Error ({url}): {e}")
        return None
