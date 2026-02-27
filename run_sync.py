import sys
import boto3
import json
import os

# add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from sync_event import sync_event_matches

def get_api():
    session = boto3.Session(profile_name='rdp', region_name='ca-central-1')
    return json.loads(session.client('secretsmanager').get_secret_value(SecretId='vex5hub/robotevents-api-key')['SecretString'])['api_key']

api = get_api()
skus = ['RE-V5RC-25-0147', 'RE-V5RC-25-0011', 'RE-V5RC-25-0254']

for sku in skus:
    print(f"Syncing {sku}...")
    sync_event_matches(sku, api, 'vex5hub-data', 'rdp')

print("Uploading multi_event_links.csv to DynamoDB...")
os.system("python3 scripts/upload_match_videos.py multi_event_links.csv")
print("Done.")
