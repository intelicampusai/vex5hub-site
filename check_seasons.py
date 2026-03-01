import urllib.request
import json
import ssl
import sys
import boto3

def get_api():
    session = boto3.Session(profile_name='rdp', region_name='ca-central-1')
    return json.loads(session.client('secretsmanager').get_secret_value(SecretId='vex5hub/robotevents-api-key')['SecretString'])['api_key']

api = get_api()
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://www.robotevents.com/api/v2/seasons', headers={'Authorization': 'Bearer ' + api, 'Accept': 'application/json', 'User-Agent': 'Vex5Hub'})
with urllib.request.urlopen(req, context=ctx) as r:
    data = json.loads(r.read())['data']
    for s in data:
        print(f"ID: {s['id']}, Name: {s['name']}")
