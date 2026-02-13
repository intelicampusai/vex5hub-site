import json
import random

def enrich_teams():
    with open('data/teams.json', 'r') as f:
        data = json.load(f)

    for region in data['regions']:
        for i, team in enumerate(region['teams']):
            # Add division (mostly HS for top teams)
            team['division'] = "High School" if random.random() > 0.1 else "Middle School"
            
            # Add skills rank (using rank + world offset for realism)
            team['skills_rank'] = (i + 1) * random.randint(5, 15)
            
            # Add worlds qualification status
            # Top 2 in each region usually qualify by this time (Feb 10th)
            team['worlds_qualified'] = True if i < 2 or "World" in " ".join(team.get('awards', [])) else False
            
            # Ensure rankings are competition rankings
            # team['rank'] is already used as competition rank in JS

    with open('data/teams.json', 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    enrich_teams()
