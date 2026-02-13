"""
VEX V5 Hub API Handler Lambda Function

Serves data from DynamoDB via API Gateway HTTP API.
Routes:
  GET /api/teams?region=<region_id>    → team rankings by region
  GET /api/competitions                → competition/season data
  GET /api/events                      → upcoming events
  GET /api/robots                      → trending robot designs

Every response includes source_url fields linking to official RobotEvents pages.
"""

import json
import os
import logging
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)


class DecimalEncoder(json.JSONEncoder):
    """Handle DynamoDB Decimal types in JSON serialization."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            n = int(obj) if obj == int(obj) else float(obj)
            return n
        return super().default(obj)


def handler(event: dict, context: Any) -> dict:
    """Main Lambda handler for API Gateway v2 (HTTP API) or Function URL."""
    # Try routeKey first (API Gateway specific routes)
    route_key = event.get('routeKey', '')
    
    # Fallback to rawPath for Function URL or $default route
    if not route_key or route_key == '$default':
        path = event.get('rawPath', '')
        method = event.get('requestContext', {}).get('http', {}).get('method', '')
        route_key = f"{method} {path}"

    query = event.get('queryStringParameters') or {}
    logger.info(f"API request: {route_key} params={query}")

    try:
        if route_key == 'GET /api/teams':
            body = get_teams(query.get('region'))
        elif route_key == 'GET /api/competitions':
            body = get_competitions()
        elif route_key == 'GET /api/events':
            body = get_events()
        elif route_key == 'GET /api/robots':
            body = get_robots()
        else:
            return response(404, {"error": "Not found"})

        return response(200, body)

    except Exception as e:
        logger.error(f"API error: {str(e)}", exc_info=True)
        return response(500, {"error": "Internal server error"})


# ===================================
# Data Access Functions
# ===================================

def get_teams(region_id: str = None) -> dict:
    """
    Get teams data grouped by region.
    If region_id is specified, return only that region's teams.
    """
    if region_id:
        # Query specific region
        result = table.query(
            KeyConditionExpression=Key('PK').eq(f'REGION#{region_id}') & Key('SK').begins_with('TEAM#')
        )
        teams = [clean_item(item) for item in result.get('Items', [])]
        teams.sort(key=lambda t: t.get('rank', 999))

        # Get region metadata
        meta = table.get_item(Key={'PK': f'REGION#{region_id}', 'SK': 'META'})
        region_meta = clean_item(meta.get('Item', {}))

        return {
            "region": {
                "id": region_id,
                "name": region_meta.get('name', region_id),
                "country": region_meta.get('country', ''),
            },
            "teams": teams,
            "source_url": f"https://www.robotevents.com/robot-competitions/vex-robotics-competition"
        }
    else:
        # Return all regions with their teams
        result = table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq('REGION')
        )
        regions_meta = {clean_item(i)['id']: clean_item(i) for i in result.get('Items', [])}

        regions = []
        for region_id, meta in regions_meta.items():
            team_result = table.query(
                KeyConditionExpression=Key('PK').eq(f'REGION#{region_id}') & Key('SK').begins_with('TEAM#')
            )
            teams = [clean_item(item) for item in team_result.get('Items', [])]
            teams.sort(key=lambda t: t.get('rank', 999))
            regions.append({
                "id": region_id,
                "name": meta.get('name', region_id),
                "country": meta.get('country', ''),
                "teams": teams
            })

        return {
            "regions": regions,
            "source_url": "https://www.robotevents.com/robot-competitions/vex-robotics-competition"
        }


def get_competitions() -> list:
    """Get all competitions."""
    result = table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq('COMPETITION')
    )
    items = [clean_item(item) for item in result.get('Items', [])]
    return items


def get_events() -> list:
    """Get all events."""
    result = table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq('EVENT')
    )
    items = [clean_item(item) for item in result.get('Items', [])]
    return items


def get_robots() -> dict:
    """Get robots and tech breakdowns."""
    viral_result = table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq('ROBOT')
    )
    tech_result = table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq('TECH')
    )
    return {
        "viral": [clean_item(i) for i in viral_result.get('Items', [])],
        "techBreakdowns": [clean_item(i) for i in tech_result.get('Items', [])]
    }


# ===================================
# Helpers
# ===================================

def clean_item(item: dict) -> dict:
    """Remove DynamoDB key attributes from item for API response."""
    cleaned = {k: v for k, v in item.items() if k not in ('PK', 'SK', 'GSI1PK', 'GSI1SK')}
    return cleaned


def response(status_code: int, body: Any) -> dict:
    """Build API Gateway v2 response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "max-age=300"  # 5 min browser cache
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }
