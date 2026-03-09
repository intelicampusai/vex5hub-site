
import json
import boto3
import urllib.request
import ssl
import os

API_BASE_URL = "https://www.robotevents.com/api/v2"

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

def fetch_matches(api_key, sku):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print(f"Fetching Event ID for {sku}...")
    url = f"{API_BASE_URL}/events?sku[]={sku}"
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
        'User-Agent': 'Vex5Hub/1.0'
    })
    
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            if not data['data']: return []
            event_id = data['data'][0]['id']
            divisions = data['data'][0].get('divisions', [])
    except Exception as e:
        print(f"Error: {e}")
        return []

    print(f"Fetching matches for event {event_id} ({sku})...")
    all_matches = []
    
    for div in divisions:
        div_id = div['id']
        page = 1
        while True:
            url = f"{API_BASE_URL}/events/{event_id}/divisions/{div_id}/matches?page={page}&per_page=250"
            req = urllib.request.Request(url, headers={
                'Authorization': f'Bearer {api_key}',
                'Accept': 'application/json',
                'User-Agent': 'Vex5Hub/1.0'
            })
            try:
                with urllib.request.urlopen(req, context=ctx) as resp:
                    data = json.loads(resp.read().decode())
                    if not data['data']: break
                    all_matches.extend(data['data'])
                    if data['meta']['current_page'] >= data['meta']['last_page']: break
                    page += 1
            except Exception as e:
                print(f"Error: {e}")
                break
    return all_matches

def update_collected(skus):
    api_key = get_api_key()
    if not api_key: return

    file_path = 'collected_matches.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
    else:
        data = {"matches": {}}

    modified = False
    for sku in skus:
        matches = fetch_matches(api_key, sku)
        print(f"Fetched {len(matches)} matches for {sku}")
        for m in matches:
            m_id = str(m['id'])
            if m_id not in data['matches']:
                data['matches'][m_id] = m
                modified = True
    
    if modified:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Updated {file_path}")
    else:
        print("No new matches found.")

if __name__ == "__main__":
    import sys
    skus = sys.argv[1:] if len(sys.argv) > 1 else ["RE-V5RC-25-0011", "RE-V5RC-25-0010"]
    update_collected(skus)
