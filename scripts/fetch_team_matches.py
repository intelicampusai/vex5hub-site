import json
import boto3
import urllib.request
import ssl
import os
import time
from datetime import datetime

# --- Configuration ---
TEAMS_FILE = "/Users/binjiang/vex5hub-site/top_100_teams.json"
API_BASE_URL = "https://www.robotevents.com/api/v2"
SEASON_ID = 197  # V5RC 2025-2026 Push Back

def get_api_key():
    print("Fetching API Key from Secrets Manager...")
    try:
        session = boto3.Session(profile_name='rdp')
        client = session.client('secretsmanager', region_name='ca-central-1')
        secret = client.get_secret_value(SecretId='vex5hub/robotevents-api-key')
        return json.loads(secret['SecretString'])['api_key']
    except Exception as e:
        print(f"Error fetching API key: {e}")
        return None

def fetch_team_matches(api_key, team_number):
    print(f"Fetching matches for team {team_number}...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # 1. Get Team ID
    url = f"{API_BASE_URL}/teams?number[]={team_number}"
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
        'User-Agent': 'Vex5Hub/1.0'
    })
    
    try:
        time.sleep(0.2) # Rate limiting
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            if not data['data']:
                print(f"Team {team_number} not found!")
                return []
            team_id = data['data'][0]['id']
    except Exception as e:
        print(f"Error fetching team {team_number}: {e}")
        return []

    # 2. Get Matches for Team
    matches = []
    page = 1
    while True:
        url = f"{API_BASE_URL}/teams/{team_id}/matches?season[]={SEASON_ID}&page={page}&per_page=250"
        req = urllib.request.Request(url, headers={
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'User-Agent': 'Vex5Hub/1.0'
        })
        try:
            time.sleep(0.2) # Rate limiting
            with urllib.request.urlopen(req, context=ctx) as resp:
                data = json.loads(resp.read().decode())
                if not data['data']: break
                matches.extend(data['data'])
                if data['meta']['current_page'] >= data['meta']['last_page']: break
                page += 1
        except Exception as e:
            print(f"Error fetching matches for team {team_number}: {e}")
            break
            
    return matches

def main():
    api_key = get_api_key()
    if not api_key: return

    with open(TEAMS_FILE, "r") as f:
        teams = json.load(f)

    all_matches = {}
    event_skus = set()

    for team in teams:
        matches = fetch_team_matches(api_key, team)
        print(f"  Found {len(matches)} matches for {team}")
        for m in matches:
            match_id = m['id']
            if match_id not in all_matches:
                all_matches[match_id] = m
                sku = m.get('event', {}).get('code') # Use 'code' for SKU
                if sku:
                    event_skus.add(sku)

    print(f"\nTotal unique matches: {len(all_matches)}")
    print(f"Total unique events: {len(event_skus)}")

    # Save results
    output = {
        "matches": all_matches,
        "event_skus": list(event_skus)
    }
    with open("/Users/binjiang/vex5hub-site/collected_matches.json", "w") as f:
        json.dump(output, f, indent=2)
    print("Saved to collected_matches.json")

    # Also summary of events for easier picking
    event_counts = {}
    for m in all_matches.values():
        sku = m.get('event', {}).get('code')
        if sku:
            event_counts[sku] = event_counts.get(sku, 0) + 1
    
    sorted_events = sorted(event_counts.items(), key=lambda x: x[1], reverse=True)
    with open("/Users/binjiang/vex5hub-site/event_summary.json", "w") as f:
        json.dump(sorted_events, f, indent=2)
    print("Saved to event_summary.json")

if __name__ == "__main__":
    main()
