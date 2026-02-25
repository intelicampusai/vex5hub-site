import urllib.request
import json
import boto3

secrets_client = boto3.client('secretsmanager', region_name='ca-central-1')
try:
    secret = secrets_client.get_secret_value(SecretId="vex5hub/robotevents-api-key")
    api_key = json.loads(secret['SecretString'])['api_key']
except Exception as e:
    print("Error getting secret:", e)
    exit(1)

url = "https://www.robotevents.com/api/v2/events?sku[]=RE-V5RC-26-4026"
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {api_key}', 'Accept': 'application/json'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print(json.dumps(data, indent=2))
except Exception as e:
    print("API Error:", e)
