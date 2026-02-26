import os
import json
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
import boto3

import ssl

RE_API_BASE = "https://www.robotevents.com/api/v2"

def api_request(url, api_key):
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
        'User-Agent': 'Vex5Hub/1.0'
    })
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode())

def sync_event_matches(sku, api_key, table_name, profile):
    session = boto3.Session(profile_name=profile, region_name='ca-central-1')
    table = session.resource('dynamodb').Table(table_name)
    
    # Get event details to get internal ID
    event_data = api_request(f"{RE_API_BASE}/events?sku[]={sku}", api_key)
    if not event_data['data']:
        print(f"Event {sku} not found")
        return
    
    event = event_data['data'][0]
    evt_id = event['id']
    evt_name = event['name']
    
    print(f"Syncing matches for {evt_name} ({sku})...")
    
    # Divisions are usually in the event payload
    divs = event.get('divisions', [])
    if not divs:
        # Fallback to fetching if not in payload
        divs_url = f"{RE_API_BASE}/events/{evt_id}/divisions"
        try:
            divs_data = api_request(divs_url, api_key)
            divs = divs_data.get('data', [])
        except:
            print("Could not fetch divisions, defaulting to division 1")
            divs = [{'id': 1, 'name': 'Division 1'}]
    
    for div in divs:
        div_id = div['id']
        div_name = div['name']
        print(f"  Division: {div_name} ({div_id})")
        
        matches_url = f"{RE_API_BASE}/events/{evt_id}/divisions/{div_id}/matches?per_page=250"
        matches_data = api_request(matches_url, api_key)
        
        for m in matches_data['data']:
            match_num = m.get('matchnum', 0)
            round_num = m.get('round', 0)
            instance = m.get('instance', 0)
            
            round_names = {1: 'Practice', 2: 'Qualification', 3: 'Quarterfinal', 4: 'Semifinal', 5: 'Final', 6: 'Round of 16'}
            round_name = round_names.get(round_num, f'Round {round_num}')

            alliances = m.get('alliances', [])
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
                'field': m.get('field', ''),
                'scheduled': m.get('scheduled', ''),
                'started': m.get('started', ''),
                'red_teams': red_teams,
                'blue_teams': blue_teams,
                'red_score': Decimal(str(red_score)) if red_score is not None else None,
                'blue_score': Decimal(str(blue_score)) if blue_score is not None else None,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            item = {k: v for k, v in item.items() if v is not None}
            table.put_item(Item=item)
            
            # Team records
            for tnum in red_teams + blue_teams:
                alliance_color = 'red' if tnum in red_teams else 'blue'
                my_score = red_score if alliance_color == 'red' else blue_score
                opp_score = blue_score if alliance_color == 'red' else red_score
                partner_teams = red_teams if alliance_color == 'red' else blue_teams
                opponent_teams = blue_teams if alliance_color == 'red' else red_teams
                won = (my_score is not None and opp_score is not None and int(my_score) > int(opp_score))

                team_match_sk = f"MATCH#{sku}#{div_id}#{round_num}#{instance:02d}#{match_num:04d}"
                
                loc = event.get('location', {})
                loc_str = ", ".join(filter(None, [loc.get('city'), loc.get('region'), loc.get('country')]))
                
                team_item = {
                    'PK': f'TEAM#{tnum}',
                    'SK': team_match_sk,
                    'sku': sku,
                    'event_name': evt_name,
                    'alliance': alliance_color,
                    'my_score': Decimal(str(my_score)) if my_score is not None else None,
                    'opp_score': Decimal(str(opp_score)) if opp_score is not None else None,
                    'partner_teams': [p for p in partner_teams if p != tnum],
                    'opponent_teams': opponent_teams,
                    'won': won,
                    'round': round_name,
                    'match_num': Decimal(str(match_num)),
                    'event_start': event.get('start'),
                    'event_end': event.get('end'),
                    'event_location': loc_str,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                team_item = {k: v for k, v in team_item.items() if v is not None}
                table.put_item(Item=team_item)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 sync_event.py <sku> <api_key>")
        sys.exit(1)
    sync_event_matches(sys.argv[1], sys.argv[2], "vex5hub-data", "rdp")
