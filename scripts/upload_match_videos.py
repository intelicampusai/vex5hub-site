import csv
import sys
import argparse
import boto3
from boto3.dynamodb.conditions import Key

def parse_match_name(name: str):
    """
    Parses a string like 'Q12' or 'SF1-2' into (round_name, instance, match_num)
    Returns: (round_name: str, instance: int, match_num: int)
    """
    name = name.upper().strip().replace(' ', '')
    
    if name.startswith('Q') and not name.startswith('QF'):
        return ('Qualification', 1, int(name[1:]))
    elif name.startswith('P'):
        return ('Practice', 1, int(name[1:]))
    elif name.startswith('QF'):
        return _parse_elim('Quarterfinal', name[2:])
    elif name.startswith('SF'):
        return _parse_elim('Semifinal', name[2:])
    elif name.startswith('F'):
        return _parse_elim('Final', name[1:])
    elif name.startswith('R16'):
        return _parse_elim('Round of 16', name[3:].lstrip('-'))
    elif name.startswith('R32'):
        return _parse_elim('Round of 32', name[3:].lstrip('-'))
    elif name.startswith('R64'):
        return _parse_elim('Round of 64', name[3:].lstrip('-'))
    
    raise ValueError(f"Unknown match notation: {name}")

def _parse_elim(round_name: str, s: str):
    if '-' in s:
        parts = s.split('-')
        return (round_name, int(parts[0]), int(parts[1]))
    else:
        # e.g. R16-4 or SF2 -> instance N, match 1
        # BUT F1, F2 -> instance 1, match N
        if round_name == 'Final':
            return (round_name, 1, int(s))
        else:
            return (round_name, int(s), 1)

def main():
    parser = argparse.ArgumentParser(description="Upload YouTube timestamp URLs to match items in DynamoDB")
    parser.add_argument("csv_file", help="Path to csv file. Format: sku,match_name,youtube_id,timestamp_seconds")
    parser.add_argument("--profile", default="rdp", help="AWS profile to use")
    parser.add_argument("--region", default="ca-central-1", help="AWS region")
    parser.add_argument("--table", default="vex5hub-data", help="DynamoDB table name")
    
    args = parser.parse_args()
    
    try:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        dynamodb = session.resource('dynamodb')
        table = dynamodb.Table(args.table)
    except Exception as e:
        print(f"Error initializing boto3 (check your AWS profile): {e}")
        return

    # Read CSV
    # sku, match_name, youtube_id, timestamp_seconds, [division_id]
    updates = []
    with open(args.csv_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header and header[0] != 'sku':
            # No header, seek back
            f.seek(0)
            reader = csv.reader(f)
            
        for row in reader:
            if not row or len(row) < 4:
                continue
            sku, match_name, yt_id, ts = [r.strip() for r in row[:4]]
            div_id = int(row[4].strip()) if len(row) > 4 and row[4].strip() else None
            
            try:
                round_name, instance, match_num = parse_match_name(match_name)
                ts = int(ts)
                updates.append({
                    'sku': sku,
                    'match_name': match_name,
                    'round': round_name,
                    'instance': instance,
                    'match_num': match_num,
                    'yt_id': yt_id,
                    'ts': ts,
                    'division_id': div_id
                })
            except Exception as e:
                print(f"Failed to parse row {row}: {e}")

    print(f"Loaded {len(updates)} matches to update from CSV.")
    
    # Process
    # To minimize reads, group updates by SKU
    sku_groups = {}
    for u in updates:
        skuGroups = sku_groups.setdefault(u['sku'], [])
        skuGroups.append(u)
        
    for sku, match_updates in sku_groups.items():
        print(f"\nProcessing SKU: {sku} ({len(match_updates)} matches)")
        
        # Query all matches for this event (Event source-of-truth items)
        resp = table.query(
            KeyConditionExpression=Key('PK').eq(f"EVENT#{sku}") & Key('SK').begins_with("MATCH#")
        )
        event_matches = resp.get('Items', [])
        
        for u in match_updates:
            # Find the corresponding event match item
            target_match = None
            for m in event_matches:
                # Basic match criteria
                is_match = (
                    m.get('round') == u['round'] and 
                    int(m.get('instance', 1)) == u['instance'] and 
                    int(m.get('match_num', 0)) == u['match_num']
                )
                
                # Refine with division_id if provided
                if is_match and u['division_id'] is not None:
                    if int(m.get('division_id', 0)) != u['division_id']:
                        is_match = False
                
                if is_match:
                    target_match = m
                    break
            
            if not target_match:
                div_str = f" div={u['division_id']}" if u['division_id'] is not None else ""
                print(f"  [WARN] Match {u['match_name']}{div_str} not found in DB for {sku}. Skipping.")
                continue
            
            video_url = f"https://youtu.be/{u['yt_id']}?t={u['ts']}s"
            
            # 1. Update the Event-owned item
            table.update_item(
                Key={'PK': target_match['PK'], 'SK': target_match['SK']},
                UpdateExpression="SET video_url = :v",
                ExpressionAttributeValues={':v': video_url}
            )
            print(f"  [OK] Updated Event match {u['match_name']} PK={target_match['PK']} -> {video_url}")
            
            # 2. Update the Team-owned reverse-lookup items
            # We need to find the specific team items. 
            # We know the Red API teams and Blue API teams from the event match item.
            teams = target_match.get('red_teams', []) + target_match.get('blue_teams', [])
            
            # Construct the SK for the team item
            # The new format is: MATCH#{sku}#{div_id}#{round_num}#{instance:02d}#{match_num:04d}
            # Instead of rebuilding it perfectly, it's safer to rebuild it precisely as the content-updater does
            round_order = {'Practice': 1, 'Qualification': 2, 'Quarterfinal': 3, 'Semifinal': 4, 'Final': 5, 'Round of 16': 6}
            round_num = round_order.get(u['round'], 0)
            instance = int(target_match.get('instance', 1))
            match_num = int(target_match.get('match_num', 0))
            div_id = int(target_match.get('division_id', 1))
            
            team_sk = f"MATCH#{sku}#{div_id}#{round_num}#{instance:02d}#{match_num:04d}"
            
            for t in teams:
                try:
                    table.update_item(
                        Key={'PK': f"TEAM#{t}", 'SK': team_sk},
                        UpdateExpression="SET video_url = :v",
                        ExpressionAttributeValues={':v': video_url},
                        ConditionExpression="attribute_exists(PK)" # Only update if it exists
                    )
                except Exception as e:
                    # Depending on top-team limits, the team item might not exist
                    pass

if __name__ == "__main__":
    main()
