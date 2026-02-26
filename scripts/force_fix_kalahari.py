import json
import boto3
from decimal import Decimal

def final_fix(table_name, profile):
    session = boto3.Session(profile_name=profile, region_name='ca-central-1')
    table = session.resource('dynamodb').Table(table_name)
    
    with open("match_links.json", "r") as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} match links from JSON.")
    
    # Metadata for Kalahari (since the sync might be unreliable)
    # 0166 = HS, 0165 = MS
    META = {
        "RE-V5RC-25-0166": {
            "start": "2026-01-23T00:00:00-05:00",
            "end": "2026-01-24T00:00:00-05:00",
            "loc": "Sandusky, Ohio, United States"
        },
        "RE-V5RC-25-0165": {
            "start": "2026-01-21T00:00:00-05:00",
            "end": "2026-01-22T00:00:00-05:00",
            "loc": "Sandusky, Ohio, United States"
        }
    }
    
    round_map = {1: 'Practice', 2: 'Qualification', 3: 'Quarterfinal', 4: 'Semifinal', 5: 'Final', 6: 'Round of 16'}

    count = 0
    for match_id, m in data.items():
        sku = m['event']['sku']
        div_id = m['division_id']
        round_num = m['round']
        instance = m['instance']
        match_num = m['matchnum']
        
        round_name = round_map.get(round_num, f'Round {round_num}')
        video_url = m['video_url']
        
        meta = META.get(sku, {})
        
        # Determine all teams involved
        teams = []
        for alliance in m['alliances']:
            for t_obj in alliance['teams']:
                teams.append(t_obj['team']['name'])
        
        # Try several possible division IDs for this match
        possible_divs = [div_id, 1, 100, 2, 3, 4]
        for d in possible_divs:
            sk = f"MATCH#{sku}#{d}#{round_num}#{instance:02d}#{match_num:04d}"
            
            # Try to update even without condition if necessary, but keep it for safety first
            try:
                table.update_item(
                    Key={'PK': f"TEAM#{t}", 'SK': sk},
                    UpdateExpression="SET video_url = :v, event_start = :s, event_end = :e, event_location = :l",
                    ExpressionAttributeValues={
                        ':v': video_url,
                        ':s': meta.get('start'),
                        ':e': meta.get('end'),
                        ':l': meta.get('loc')
                    },
                    ConditionExpression="attribute_exists(PK)"
                )
                print(f"  [OK] Updated TEAM#{t} {sk}")
                count += 1
            except Exception as e:
                # print(f"  [SKIP] {t} {sk}: {e}")
                pass
        
        # 2. Update Event Item
        event_sk = f"MATCH#{div_id}#{round_num}#{instance:02d}#{match_num:04d}"
        try:
            table.update_item(
                Key={'PK': f"EVENT#{sku}", 'SK': event_sk},
                UpdateExpression="SET video_url = :v",
                ExpressionAttributeValues={':v': video_url},
                ConditionExpression="attribute_exists(PK)"
            )
        except:
            pass
            
        if count % 100 == 0 and count > 0:
            print(f"  Processed {count} team updates...")

    print(f"Final fix complete. Updated {count} team match records.")

if __name__ == "__main__":
    final_fix("vex5hub-data", "rdp")
