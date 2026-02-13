import json

with open('src/lib/teams.json') as f:
    teams_data = json.load(f)

formatted_teams = []
for t in teams_data:
    formatted_teams.append({
        'id': t.get('number'),
        'number': t.get('number'),
        'name': t.get('name'),
        'organization': t.get('organization'),
        'grade': t.get('grade'),
        'region': t.get('region'),
        'country': t.get('country'),
        'stats': {
            'rank': t.get('skills', {}).get('rank'),
            'total_matches': 0
        },
        'skills': {
            'driver_score': t.get('skills', {}).get('driver'),
            'programming_score': t.get('skills', {}).get('programming'),
            'combined_score': t.get('skills', {}).get('combined_score'),
            'rank': t.get('skills', {}).get('rank')
        }
    })

print(json.dumps(formatted_teams[:20], indent=4))
