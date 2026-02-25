
import json
import os
import logging
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('TABLE_NAME')
table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def handler(event: dict, context: Any) -> dict:
    # Handler deployed via Terraform
    path = event.get('rawPath', '/')
    method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    query_params = event.get('queryStringParameters', {})

    logger.info(f"API Request: {method} {path}")

    # Normalize path by removing /api prefix if present (from CloudFront)
    if path.startswith('/api/'):
        path = path[4:]
    elif path == '/api':
        path = '/'

    try:
        if path == '/teams' and method == 'GET':
            return get_teams(query_params)
        elif path.startswith('/teams/') and method == 'GET':
            parts = path.split('/')
            team_number = parts[2] if len(parts) > 2 else None
            sub = parts[3] if len(parts) > 3 else None
            if sub == 'matches':
                return get_team_matches(team_number)
            return get_team_detail(team_number)
        elif path == '/events' and method == 'GET':
            return get_events(query_params)
        elif path.startswith('/events/') and method == 'GET':
            parts = path.split('/')
            sku = parts[2] if len(parts) > 2 else None
            sub = parts[3] if len(parts) > 3 else None
            if sub == 'matches':
                return get_event_matches(sku)
            return response(404, {"error": "Not Found"})
        else:
            return response(404, {"error": "Not Found"})
    except Exception as e:
        logger.error(f"Internal Error: {e}", exc_info=True)
        return response(500, {"error": str(e)})

def get_teams(params: dict):
    season_id = params.get('season', os.environ.get('SEASON_ID', '197'))
    query = params.get('q', '').lower()
    
    # Use GSI1 to list teams by rank
    resp = table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq(f'SEASON#{season_id}') & Key('GSI1SK').begins_with('RANK#'),
        Limit=1000
    )
    
    teams = resp.get('Items', [])
    if query:
        teams = [t for t in teams if query in t['number'].lower() or query in t.get('name', '').lower()]
        
    return response(200, teams)

def get_team_detail(number: str):
    # Get metadata
    meta = table.get_item(Key={'PK': f'TEAM#{number}', 'SK': 'METADATA'})
    if 'Item' not in meta:
        return response(404, {"error": "Team not found"})
        
    # Get matches via reverse-lookup
    matches = table.query(
        KeyConditionExpression=Key('PK').eq(f'TEAM#{number}') & Key('SK').begins_with('MATCH#'),
        ScanIndexForward=False,
        Limit=50
    )
    
    data = meta['Item']
    data['matches'] = matches.get('Items', [])
    
    return response(200, data)

def get_team_matches(number: str):
    """Return all match reverse-lookup items for a team."""
    resp = table.query(
        KeyConditionExpression=Key('PK').eq(f'TEAM#{number}') & Key('SK').begins_with('MATCH#'),
        ScanIndexForward=False,
        Limit=200
    )
    return response(200, resp.get('Items', []))

def get_event_matches(sku: str):
    """Return all match source-of-truth items for an event."""
    resp = table.query(
        KeyConditionExpression=Key('PK').eq(f'EVENT#{sku}') & Key('SK').begins_with('MATCH#'),
        ScanIndexForward=True
    )
    return response(200, resp.get('Items', []))

def get_events(params: dict):
    season_id = params.get('season', '190')
    
    resp = table.query(
        KeyConditionExpression=Key('PK').eq(f'SEASON#{season_id}') & Key('SK').begins_with('EVENT#'),
        Limit=50
    )
    
    return response(200, resp.get('Items', []))

def response(status_code: int, body: Any) -> dict:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }
