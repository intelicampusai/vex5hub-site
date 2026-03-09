
import json
import boto3
from decimal import Decimal
from datetime import datetime, timezone
import time

TABLE_NAME = 'vex5hub-data'

def load_matches():
    with open('match_links.json', 'r') as f:
        return json.load(f)

def clean_item(obj):
    """Recursively convert floats to Decimal for DynamoDB"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: clean_item(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_item(v) for v in obj]
    return obj

def get_iso_timestamp(iso_str):
    # Normalize to UTC string for sorting
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    except (ValueError, TypeError):
        return iso_str

def upload_matches():
    matches = load_matches()
    print(f"Loaded {len(matches)} matches to upload.")
    
    session = boto3.Session(profile_name='rdp', region_name='ca-central-1')
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    
    count = 0
    with table.batch_writer() as batch:
        for match_id, match_data in matches.items():
            # Calculate Sort Key timestamp
            started_iso = match_data.get('started')
            if not started_iso:
                print(f"Skipping match {match_id}: No started time")
                continue
            
            utc_started = get_iso_timestamp(started_iso)
            
            # Identify teams and normalize alliances
            teams = []
            alliances_list = match_data.get('alliances', [])
            alliances_obj = {'red': {'score': 0, 'teams': []}, 'blue': {'score': 0, 'teams': []}}

            # Handle list of alliances (RobotEvents v2 style)
            if isinstance(alliances_list, list):
                for alliance in alliances_list:
                    color = alliance.get('color', 'red') # default to red if missing? unlikely
                    alliances_obj[color] = alliance
                    
                    for team_entry in alliance.get('teams', []):
                         team = team_entry.get('team')
                         if team and 'name' in team:
                             teams.append(team['name'])
            # Handle dict of alliances (if any legacy format)
            elif isinstance(alliances_list, dict):
                alliances_obj = alliances_list # Assuming it's already correct object
                for color in ['red', 'blue']:
                    alliance = alliances_list.get(color, {})
                    for team_entry in alliance.get('teams', []):
                        team = team_entry.get('team')
                        if team and 'name' in team:
                            teams.append(team['name'])
            
            # Prepare flattened fields for frontend compatibility
            alliances = match_data.get('alliances', [])
            sku = match_data.get('event', {}).get('code')
            event_name = match_data.get('event', {}).get('name')
            
            # Write for each team
            for team_number in teams:
                # Determine "partner" teams and "opponent" teams for this specific team
                partner_teams = []
                opponent_teams = []
                my_score = None
                opp_score = None
                won = None
                my_color = None

                for alliance in alliances:
                    alliance_teams = [t.get('team', {}).get('name') for t in alliance.get('teams', [])]
                    if team_number in alliance_teams:
                        my_color = alliance.get('color')
                        partner_teams = [t for t in alliance_teams if t != team_number]
                        my_score = alliance.get('score')
                    else:
                        opponent_teams.extend(alliance_teams)
                        opp_score = alliance.get('score')

                if my_score is not None and opp_score is not None:
                    won = my_score > opp_score
                
                item = {
                    'PK': f'TEAM#{team_number}',
                    'SK': f'MATCH#{utc_started}#{match_id}',
                    'id': match_data['match_id'],
                    'name': match_data['match_name'],
                    'video_url': match_data['video_url'],
                    'sku': sku,
                    'event_name': event_name,
                    'round': match_data.get('round'),
                    'instance': match_data.get('instance'),
                    'match_num': match_data.get('matchnum'),
                    'alliance': my_color,
                    'partner_teams': partner_teams,
                    'opponent_teams': opponent_teams,
                    'my_score': my_score,
                    'opp_score': opp_score,
                    'won': won,
                    'started': started_iso,
                    'scheduled': match_data.get('scheduled'),
                    'field': match_data.get('field'),
                    'division_id': match_data.get('division_id'),
                    'updated_at': datetime.now().isoformat()
                }
                
                item = clean_item(item)
                
                try:
                    batch.put_item(Item=item)
                    count += 1
                except Exception as e:
                    print(f"Error uploading for team {team_number}: {e}")

    print(f"Successfully uploaded {count} match records.")

if __name__ == "__main__":
    upload_matches()
