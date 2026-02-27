
import json
import urllib.request
import ssl
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

ssl._create_default_https_context = ssl._create_unverified_context

# Config
API_KEY = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIzIiwianRpIjoiNWYzZGYyMTMwNmU2MDMwNThhZTg5MjYwYzZlMzYzZGFlZjU4MGQ0Njg5YzBkNjEyOTZiN2U3ZWU4MmY4NzQ0Mzk5YmFjZDkwNzA5YTdhNTciLCJpYXQiOjE3NzA4Mzg4MDUuNjI3MTkwMSwibmJmIjoxNzcwODM4ODA1LjYyNzE5MiwiZXhwIjoyNzE3NTIzNjA1LjYxNzk4MTksInN1YiI6IjExNzI1NSIsInNjb3BlcyI6W119.Z82UT9B8JCg-q75ar1nBVaXAFcQNfv5RdMjy47swGVdixePU77FZ8cb12hZifDefj4e49ontpY9lRmPo5nytB8EI1NDkEa4TEo1Lml-1FR0P73gq-IZIwxU3Ela-Gx8JUdMNFyAc4ZgdFKnCDxqHHyzzBvZupfdOtZV78KtyCERLmETgMGTNQcRhiT3E19Yvj2dkciLVOxSm1J_fFBdg4sbuRNLfsiizo1hRNwu-_OwePpJPP_nHjThou1Nd9kLsAj9R_aOnbvww_aDdOdYehmZkKGb_BTr_-oGPTUsRuEObY64G0EUTEY9l5pvm7sYPJCkX8rGRkQXW95C-OJL56hBAtfmJaiEuWi1zbZG44HjzV3MwYTKf2vU-ypKW9vVZJCODRZU1PDUeJnIbOsh3HjdVQC4oFhSDEhSBCwtA-ma8hfViwWhiY9qnhOjzrwEmbdAYjTrN_7_-aF_07500eIkwbYJ9KRZ5HFgN_4vXZCyeMft4jW6oOyJf9X9-9nTIrkPJHIXUQEKCSAofTYcR4KotFgZZrm0NfovHkyZop7zKGlxE78I4mAn1vAxIolOvNVlqi4kFl8S8R7-4F1DcM5YQbAmglq67wzlanerbmCckBQJ_NHGXrPnkPoNxQCaHkfsyVvTulip5r92GMvyesnqKt_vmJnCVrL_ycSps-kE'
WORLDS_SKUS = ["RE-V5RC-26-4025", "RE-V5RC-26-4026"]
TABLE_NAME = 'vex5hub-data'

# AWS
session = boto3.Session(profile_name='rdp', region_name='ca-central-1')
table = session.resource('dynamodb').Table(TABLE_NAME)

def api_request(url):
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {API_KEY}',
        'Accept': 'application/json',
        'User-Agent': 'Vex5Hub/1.0'
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_actual_worlds_teams():
    print("Fetching actual Worlds teams...")
    actual_teams = set()
    for sku in WORLDS_SKUS:
        # Get event ID first
        evt_data = api_request(f'https://www.robotevents.com/api/v2/events?sku[]={sku}')
        if not evt_data or not evt_data.get('data'):
            print(f"Warning: SKU {sku} not found.")
            continue
        
        evt_id = evt_data['data'][0]['id']
        page = 1
        last_page = 1
        while page <= last_page:
            teams_data = api_request(f'https://www.robotevents.com/api/v2/events/{evt_id}/teams?page={page}')
            if not teams_data or 'data' not in teams_data:
                break
            for team in teams_data['data']:
                actual_teams.add(team.get('number'))
            last_page = teams_data.get('meta', {}).get('last_page', 1)
            page += 1
    
    print(f"Found {len(actual_teams)} actual Worlds teams.")
    return actual_teams

def cleanup():
    actual_teams = get_actual_worlds_teams()
    
    print("Scanning DynamoDB for teams marked as Worlds Qualified...")
    # Scan for teams with worlds_qualified = true
    # Note: We use METADATA SK to find team items
    response = table.scan(
        FilterExpression=Attr('worlds_qualified').eq(True) & Attr('SK').eq('METADATA')
    )
    
    items = response.get('Items', [])
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression=Attr('worlds_qualified').eq(True) & Attr('SK').eq('METADATA'),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items.extend(response.get('Items', []))

    print(f"Found {len(items)} items in DB marked as qualified.")
    
    cleared_count = 0
    kept_count = 0
    
    for item in items:
        team_num = item.get('number')
        if team_num not in actual_teams:
            print(f"Correcting {team_num}: removing worlds_qualified flag.")
            try:
                table.update_item(
                    Key={'PK': f'TEAM#{team_num}', 'SK': 'METADATA'},
                    UpdateExpression="SET worlds_qualified = :val",
                    ExpressionAttributeValues={':val': False}
                )
                cleared_count += 1
            except Exception as e:
                print(f"Error updating {team_num}: {e}")
        else:
            kept_count += 1
            
    print(f"Cleanup complete. Cleared: {cleared_count}, Kept: {kept_count}")

if __name__ == "__main__":
    cleanup()
