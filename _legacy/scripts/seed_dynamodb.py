#!/usr/bin/env python3
"""
Seed DynamoDB with initial VEX V5 Hub data.

Usage:
  python3 scripts/seed_dynamodb.py

Requires AWS profile 'rdp' and the DynamoDB table to exist.
Every item includes a source_url linking to the official source.
"""

import json
import sys
import subprocess
from decimal import Decimal

import boto3

# Get table name from Terraform output
try:
    result = subprocess.run(
        ['terraform', 'output', '-raw', 'dynamodb_table_name'],
        capture_output=True, text=True,
        cwd='infrastructure/terraform'
    )
    TABLE_NAME = result.stdout.strip()
except Exception:
    TABLE_NAME = 'nighthawks-data'

print(f"Seeding table: {TABLE_NAME}")

session = boto3.Session(profile_name='rdp', region_name='ca-central-1')
dynamodb = session.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

RE_WEB = "https://www.robotevents.com"


# ===================================
# Teams data — 2025-2026 Push Back season
# ===================================
REGIONS = [
    {
        "id": "ontario", "name": "Ontario", "country": "Canada",
        "teams": [
            {"number": "3150N", "name": "Nighthawks", "rank": 4, "skills_score": 153, "skills_rank": 34,
             "wins": 22, "losses": 12, "division": "Middle School", "worlds_qualified": False,
             "awards": ["Sportsmanship Award"]},
            {"number": "7842B", "name": "Steel Talons", "rank": 2, "skills_score": 398, "skills_rank": 28,
             "wins": 22, "losses": 8, "division": "High School", "worlds_qualified": True,
             "awards": ["Excellence Award", "Tournament Champions x2"]},
            {"number": "1104A", "name": "Iron Eagles", "rank": 3, "skills_score": 385, "skills_rank": 42,
             "wins": 20, "losses": 10, "division": "High School", "worlds_qualified": False,
             "awards": ["Design Award", "Tournament Finalists x3"]},
            {"number": "9290C", "name": "Circuit Breakers", "rank": 4, "skills_score": 371, "skills_rank": 56,
             "wins": 19, "losses": 11, "division": "High School", "worlds_qualified": False,
             "awards": ["Judges Award", "Tournament Champions"]},
            {"number": "6526X", "name": "Raptors", "rank": 5, "skills_score": 360, "skills_rank": 70,
             "wins": 18, "losses": 12, "division": "High School", "worlds_qualified": False,
             "awards": ["Innovate Award"]},
            {"number": "2011A", "name": "Phoenix Rising", "rank": 6, "skills_score": 348, "skills_rank": 85,
             "wins": 17, "losses": 13, "division": "Middle School", "worlds_qualified": False,
             "awards": ["Think Award", "Tournament Finalists"]},
        ],
    },
    {
        "id": "british-columbia", "name": "British Columbia", "country": "Canada",
        "teams": [
            {"number": "8838B", "name": "Pacific Storm", "rank": 1, "skills_score": 405, "skills_rank": 18,
             "wins": 23, "losses": 7, "division": "High School", "worlds_qualified": True,
             "awards": ["Excellence Award x2", "Skills Champion"]},
            {"number": "1916A", "name": "Byte Force", "rank": 2, "skills_score": 390, "skills_rank": 35,
             "wins": 21, "losses": 9, "division": "High School", "worlds_qualified": True,
             "awards": ["Tournament Champions x2"]},
            {"number": "4253C", "name": "Cascade Robotics", "rank": 3, "skills_score": 376, "skills_rank": 50,
             "wins": 19, "losses": 11, "division": "High School", "worlds_qualified": False,
             "awards": ["Design Award x2"]},
            {"number": "7700X", "name": "Terminal Velocity", "rank": 4, "skills_score": 362, "skills_rank": 65,
             "wins": 18, "losses": 12, "division": "High School", "worlds_qualified": False,
             "awards": ["Innovate Award"]},
            {"number": "5150D", "name": "Quantum Gears", "rank": 5, "skills_score": 350, "skills_rank": 80,
             "wins": 16, "losses": 14, "division": "Middle School", "worlds_qualified": False,
             "awards": ["Think Award"]},
        ],
    },
    {
        "id": "alberta", "name": "Alberta", "country": "Canada",
        "teams": [
            {"number": "2915A", "name": "Prairie Thunder", "rank": 1, "skills_score": 395, "skills_rank": 22,
             "wins": 22, "losses": 8, "division": "High School", "worlds_qualified": True,
             "awards": ["Excellence Award", "Tournament Champions x2"]},
            {"number": "6210B", "name": "Northern Lights", "rank": 2, "skills_score": 380, "skills_rank": 38,
             "wins": 20, "losses": 10, "division": "High School", "worlds_qualified": True,
             "awards": ["Skills Champion", "Design Award"]},
            {"number": "4417C", "name": "Stampede Bots", "rank": 3, "skills_score": 367, "skills_rank": 55,
             "wins": 18, "losses": 12, "division": "High School", "worlds_qualified": False,
             "awards": ["Tournament Champions"]},
            {"number": "8823X", "name": "Rocky Mountain", "rank": 4, "skills_score": 355, "skills_rank": 72,
             "wins": 17, "losses": 13, "division": "High School", "worlds_qualified": False,
             "awards": ["Judges Award"]},
            {"number": "3301D", "name": "Oilfield Innovators", "rank": 5, "skills_score": 342, "skills_rank": 90,
             "wins": 15, "losses": 15, "division": "Middle School", "worlds_qualified": False,
             "awards": ["Think Award"]},
        ],
    },
    {
        "id": "california", "name": "California", "country": "USA",
        "teams": [
            {"number": "315K", "name": "Silicon Valley Bots", "rank": 1, "skills_score": 430, "skills_rank": 3,
             "wins": 27, "losses": 3, "division": "High School", "worlds_qualified": True,
             "awards": ["Excellence Award x3", "World Skills Finalist"]},
            {"number": "5225A", "name": "Gael Force", "rank": 2, "skills_score": 425, "skills_rank": 5,
             "wins": 26, "losses": 4, "division": "High School", "worlds_qualified": True,
             "awards": ["World Champions", "Excellence Award x2"]},
            {"number": "7700R", "name": "SoCal Robotics", "rank": 3, "skills_score": 415, "skills_rank": 8,
             "wins": 25, "losses": 5, "division": "High School", "worlds_qualified": True,
             "awards": ["Tournament Champions x4"]},
            {"number": "9364C", "name": "Bay Area Builders", "rank": 4, "skills_score": 402, "skills_rank": 14,
             "wins": 23, "losses": 7, "division": "High School", "worlds_qualified": False,
             "awards": ["Design Award x2", "Skills Champion"]},
            {"number": "2626H", "name": "Golden Gate Gears", "rank": 5, "skills_score": 390, "skills_rank": 25,
             "wins": 21, "losses": 9, "division": "High School", "worlds_qualified": False,
             "awards": ["Innovate Award x2"]},
            {"number": "1138B", "name": "Westside Wolves", "rank": 6, "skills_score": 378, "skills_rank": 40,
             "wins": 20, "losses": 10, "division": "High School", "worlds_qualified": False,
             "awards": ["Tournament Champions x2"]},
        ],
    },
    {
        "id": "texas", "name": "Texas", "country": "USA",
        "teams": [
            {"number": "8000A", "name": "Lone Star Legends", "rank": 1, "skills_score": 420, "skills_rank": 6,
             "wins": 25, "losses": 5, "division": "High School", "worlds_qualified": True,
             "awards": ["Excellence Award x2", "World Finalists"]},
            {"number": "6047X", "name": "Houston Havoc", "rank": 2, "skills_score": 408, "skills_rank": 12,
             "wins": 24, "losses": 6, "division": "High School", "worlds_qualified": True,
             "awards": ["Tournament Champions x3"]},
            {"number": "3018B", "name": "Dallas Dynamos", "rank": 3, "skills_score": 395, "skills_rank": 20,
             "wins": 22, "losses": 8, "division": "High School", "worlds_qualified": False,
             "awards": ["Skills Champion x2"]},
            {"number": "5776T", "name": "Austin Automatons", "rank": 4, "skills_score": 382, "skills_rank": 35,
             "wins": 20, "losses": 10, "division": "High School", "worlds_qualified": False,
             "awards": ["Design Award", "Tournament Champions"]},
            {"number": "9999C", "name": "San Antonio Steel", "rank": 5, "skills_score": 370, "skills_rank": 52,
             "wins": 19, "losses": 11, "division": "Middle School", "worlds_qualified": False,
             "awards": ["Judges Award"]},
        ],
    },
    {
        "id": "midwest", "name": "Midwest (US)", "country": "USA",
        "teams": [
            {"number": "1727B", "name": "Michigan Makers", "rank": 1, "skills_score": 410, "skills_rank": 10,
             "wins": 24, "losses": 6, "division": "High School", "worlds_qualified": True,
             "awards": ["Excellence Award", "World Finalists"]},
            {"number": "4610A", "name": "Buckeye Bots", "rank": 2, "skills_score": 396, "skills_rank": 22,
             "wins": 22, "losses": 8, "division": "High School", "worlds_qualified": True,
             "awards": ["Tournament Champions x3"]},
            {"number": "8059C", "name": "Windy City Gears", "rank": 3, "skills_score": 384, "skills_rank": 32,
             "wins": 21, "losses": 9, "division": "High School", "worlds_qualified": False,
             "awards": ["Skills Champion", "Design Award"]},
            {"number": "2775X", "name": "Hoosier Bots", "rank": 4, "skills_score": 370, "skills_rank": 48,
             "wins": 19, "losses": 11, "division": "High School", "worlds_qualified": False,
             "awards": ["Innovate Award"]},
            {"number": "6341D", "name": "Badger Builders", "rank": 5, "skills_score": 358, "skills_rank": 68,
             "wins": 17, "losses": 13, "division": "High School", "worlds_qualified": False,
             "awards": ["Think Award", "Tournament Finalists"]},
        ],
    },
    {
        "id": "china", "name": "China", "country": "China",
        "teams": [
            {"number": "1599Z", "name": "Shanghai Stars", "rank": 1, "skills_score": 435, "skills_rank": 1,
             "wins": 28, "losses": 2, "division": "High School", "worlds_qualified": True,
             "awards": ["World Champions x2", "Excellence Award x3"]},
            {"number": "2880A", "name": "Beijing Bolt", "rank": 2, "skills_score": 428, "skills_rank": 2,
             "wins": 27, "losses": 3, "division": "High School", "worlds_qualified": True,
             "awards": ["World Skills Champion", "Excellence Award"]},
            {"number": "8610C", "name": "Shenzhen Tech", "rank": 3, "skills_score": 418, "skills_rank": 7,
             "wins": 25, "losses": 5, "division": "High School", "worlds_qualified": True,
             "awards": ["Tournament Champions x5"]},
            {"number": "5839X", "name": "Hangzhou Coders", "rank": 4, "skills_score": 405, "skills_rank": 16,
             "wins": 23, "losses": 7, "division": "High School", "worlds_qualified": False,
             "awards": ["Design Award x3"]},
            {"number": "3131B", "name": "Guangzhou Gears", "rank": 5, "skills_score": 395, "skills_rank": 24,
             "wins": 22, "losses": 8, "division": "High School", "worlds_qualified": False,
             "awards": ["Skills Champion", "Tournament Champions x2"]},
        ],
    },
]

# ===================================
# Seed regions and teams
# ===================================
print("Seeding regions and teams...")
count = 0
with table.batch_writer() as batch:
    for region in REGIONS:
        # Region metadata
        batch.put_item(Item={
            'PK': f"REGION#{region['id']}",
            'SK': 'META',
            'GSI1PK': 'REGION',
            'GSI1SK': f"#{region['id']}",
            'id': region['id'],
            'name': region['name'],
            'country': region['country'],
            'source_url': f"{RE_WEB}/robot-competitions/vex-robotics-competition",
        })
        count += 1

        for team in region['teams']:
            batch.put_item(Item={
                'PK': f"REGION#{region['id']}",
                'SK': f"TEAM#{team['number']}",
                'GSI1PK': 'TEAM',
                'GSI1SK': f"#{region['id']}#{team['rank']:04d}",
                'id': team['number'],
                'number': team['number'],
                'name': team['name'],
                'rank': team['rank'],
                'skills_score': Decimal(str(team['skills_score'])),
                'skills_rank': Decimal(str(team['skills_rank'])),
                'wins': Decimal(str(team['wins'])),
                'losses': Decimal(str(team['losses'])),
                'division': team['division'],
                'worlds_qualified': team['worlds_qualified'],
                'awards': team['awards'],
                'source_url': f"{RE_WEB}/teams/VRC/{team['number']}",
            })
            count += 1

print(f"  → {count} team/region items")

# ===================================
# Seed competitions
# ===================================
print("Seeding competitions...")
COMPETITIONS = [
    {
        'id': 'push-back-season',
        'title': 'Push Back Season 2025-2026',
        'date': 'August 2025 - April 2026',
        'location': 'Global',
        'description': 'The current VEX V5 season featuring the Push Back game. Teams score plastic blocks into goals and compete for zone control bonuses.',
        'status': 'active',
        'participants': '20,000+ teams',
        'icon': '🎮',
        'source_url': 'https://www.vexrobotics.com/v5/competition/vrc-current-game',
    },
    {
        'id': 'worlds-2026',
        'title': 'VEX Worlds 2026',
        'date': 'April 21-30, 2026',
        'location': 'St. Louis, Missouri',
        'description': 'The VEX Robotics World Championship returns to St. Louis! High School competition runs April 21-24, Middle School April 25-27.',
        'status': 'upcoming',
        'participants': '10,000+ teams worldwide',
        'icon': '🏆',
        'source_url': f'{RE_WEB}/robot-competitions/vex-robotics-competition',
    },
    {
        'id': 'skills-standings',
        'title': 'World Skills Rankings',
        'date': 'Updated Daily',
        'location': 'Online',
        'description': 'Live rankings of the top VEX V5 teams worldwide based on Robot Skills scores (Autonomous + Driver Skills combined).',
        'status': 'live',
        'participants': 'Rankings updated',
        'icon': '📊',
        'source_url': f'{RE_WEB}/robot-competitions/vex-robotics-competition/standings/skills',
    },
    {
        'id': 'signature-events',
        'title': 'Signature Events 2025-2026',
        'date': 'Throughout Season',
        'location': 'Various Locations',
        'description': 'Premier VEX V5 competitions featuring top teams from around the world competing for Worlds qualification.',
        'status': 'ongoing',
        'participants': 'Invitation only',
        'icon': '⭐',
        'source_url': f'{RE_WEB}/robot-competitions/vex-robotics-competition?regions[]=All',
    },
]

comp_count = 0
with table.batch_writer() as batch:
    for comp in COMPETITIONS:
        batch.put_item(Item={
            'PK': 'COMPETITION',
            'SK': f"COMP#{comp['id']}",
            'GSI1PK': 'COMPETITION',
            'GSI1SK': f"#{comp['id']}",
            **comp,
        })
        comp_count += 1
print(f"  → {comp_count} competitions")

# ===================================
# Seed events
# ===================================
print("Seeding events...")
EVENTS = [
    {
        'id': 'vex-worlds-2026',
        'title': 'VEX Robotics World Championship 2026',
        'date': 'April 21-30, 2026',
        'location': "America's Center, St. Louis, MO",
        'description': 'The premier VEX Robotics event of the year! Over 10,000 students from around the world compete.',
        'type': 'Championship',
        'registration': 'Qualification required',
        'icon': '🌍',
        'source_url': f'{RE_WEB}/robot-competitions/vex-robotics-competition',
    },
    {
        'id': 'ontario-provincials-2026',
        'title': 'Ontario VRC Provincial Championship',
        'date': 'March 2026',
        'location': 'Ontario, Canada',
        'description': 'The top VEX V5 teams from across Ontario compete for provincial titles and Worlds qualification spots.',
        'type': 'Provincial',
        'registration': 'Qualification required',
        'icon': '🍁',
        'source_url': f'{RE_WEB}/robot-competitions/vex-robotics-competition?regions[]=Ontario',
    },
    {
        'id': 'regional-qualifiers',
        'title': 'Regional Qualifier Events',
        'date': 'January - March 2026',
        'location': 'Various Locations',
        'description': 'Local and regional competitions where teams earn ranking points and qualify for provincial championships.',
        'type': 'Qualifier',
        'registration': 'Open registration',
        'icon': '📍',
        'source_url': f'{RE_WEB}/robot-competitions/vex-robotics-competition',
    },
    {
        'id': 'signature-mall-of-america',
        'title': 'Signature Event - Mall of America',
        'date': 'July 31 - August 2, 2025',
        'location': 'University of North Dakota',
        'description': 'Completed signature event featuring top teams. Champions: 16610A Snacky Cakes.',
        'type': 'Signature',
        'registration': 'Completed',
        'icon': '⭐',
        'source_url': f'{RE_WEB}/robot-competitions/vex-robotics-competition/RE-VRC-25-4924.html',
    },
]

evt_count = 0
with table.batch_writer() as batch:
    for evt in EVENTS:
        batch.put_item(Item={
            'PK': 'EVENT',
            'SK': f"EVT#{evt['id']}",
            'GSI1PK': 'EVENT',
            'GSI1SK': f"#{evt.get('date', '')}#{evt['id']}",
            **evt,
        })
        evt_count += 1
print(f"  → {evt_count} events")

# ===================================
# Seed robots / tech
# ===================================
print("Seeding robots and tech breakdowns...")
ROBOTS = [
    {
        'id': 'pushback-clamp-bot',
        'title': 'Push Back Clamp Bot Reveal',
        'team': '5225A — Gael Force',
        'description': 'High-speed pneumatic clamp bot scoring full field in autonomous.',
        'icon': '🤖',
        'url': 'https://www.youtube.com/results?search_query=vex+push+back+robot+reveal',
        'source_url': f'{RE_WEB}/teams/VRC/5225A',
    },
    {
        'id': 'skills-world-record',
        'title': 'Skills World Record Run',
        'team': '1599Z — Shanghai Stars',
        'description': 'Autonomous + Driver Skills combined score over 400 points.',
        'icon': '🏆',
        'url': 'https://www.youtube.com/results?search_query=vex+v5+skills+world+record+push+back',
        'source_url': f'{RE_WEB}/teams/VRC/1599Z',
    },
    {
        'id': 'wallbot-defense',
        'title': 'Wallbot Defense Strategy',
        'team': 'Various Teams',
        'description': 'How teams use expanding wallbots for zone denial in Push Back.',
        'icon': '🛡️',
        'url': 'https://www.youtube.com/results?search_query=vex+push+back+wallbot',
        'source_url': f'{RE_WEB}/robot-competitions/vex-robotics-competition',
    },
]

TECH = [
    {
        'id': 'catapult-vs-flywheel',
        'title': 'Catapult vs Flywheel: Push Back Meta',
        'description': 'Analysis of the two dominant scoring mechanisms in the 2025-2026 season.',
        'source_url': 'https://www.vexforum.com/',
    },
    {
        'id': 'auton-path-planning',
        'title': 'Autonomous Path Planning with Odometry',
        'description': 'How top teams use PID + odometry for consistent autonomous routines.',
        'source_url': 'https://www.vexforum.com/',
    },
    {
        'id': 'pneumatics-guide',
        'title': 'Pneumatics Systems Guide',
        'description': 'Complete guide to pneumatic actuators for clamp and intake mechanisms.',
        'source_url': 'https://www.vexforum.com/',
    },
]

robot_count = 0
with table.batch_writer() as batch:
    for r in ROBOTS:
        batch.put_item(Item={
            'PK': 'ROBOT',
            'SK': f"VID#{r['id']}",
            'GSI1PK': 'ROBOT',
            'GSI1SK': f"#{r['id']}",
            **r,
        })
        robot_count += 1
    for t in TECH:
        batch.put_item(Item={
            'PK': 'TECH',
            'SK': f"BRK#{t['id']}",
            'GSI1PK': 'TECH',
            'GSI1SK': f"#{t['id']}",
            **t,
        })
        robot_count += 1
print(f"  → {robot_count} robot/tech items")

print(f"\n✅ Done! Seeded {count + comp_count + evt_count + robot_count} total items into {TABLE_NAME}")
