"""
Deduplication + Video URL Merge Script

This script:
1. Scans ALL TEAM# MATCH# records in DynamoDB
2. Groups them by (PK, sku, match_num, round, instance) to find duplicates
3. For duplicates: merges video_url into the canonical (content-updater) record,
   deletes the timestamp-based duplicate
4. Deletes any legacy NESTED records (malformed SKs without sku)
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
from collections import defaultdict
import time

TABLE_NAME = 'vex5hub-data'
DRY_RUN = False  # Set to True to preview changes without modifying DB

def run():
    session = boto3.Session(profile_name='rdp', region_name='ca-central-1')
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)

    # Scan all MATCH records
    print("Scanning all MATCH records...")
    all_items = []
    scan_kwargs = {
        'FilterExpression': Attr('SK').begins_with('MATCH#')
    }
    
    while True:
        resp = table.scan(**scan_kwargs)
        all_items.extend(resp.get('Items', []))
        if 'LastEvaluatedKey' not in resp:
            break
        scan_kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']
    
    print(f"Total MATCH records found: {len(all_items)}")

    # Classify records
    canonical = []    # Content-updater style: SK like MATCH#SKU#div#round#inst#num
    timestamp_based = []  # upload_matches.py style: SK like MATCH#2026-...#id
    legacy_nested = []     # Malformed: SK like MATCH#1#2#01#...

    for item in all_items:
        sk = item.get('SK', '')
        pk = item.get('PK', '')
        
        if not pk.startswith('TEAM#'):
            continue
            
        if '#RE-V5RC-' in sk:
            canonical.append(item)
        elif sk.startswith('MATCH#2026-') or sk.startswith('MATCH#2025-'):
            timestamp_based.append(item)
        else:
            legacy_nested.append(item)

    print(f"Canonical (content-updater): {len(canonical)}")
    print(f"Timestamp-based (upload_matches): {len(timestamp_based)}")
    print(f"Legacy/malformed: {len(legacy_nested)}")

    # Build lookup from canonical records: (PK, sku, round, instance, match_num) -> item
    canonical_lookup = {}
    for item in canonical:
        pk = item['PK']
        sku = item.get('sku', '')
        rnd = item.get('round', '')
        inst = str(item.get('instance', '1'))
        mnum = str(item.get('match_num', ''))
        key = (pk, sku, rnd, inst, mnum)
        canonical_lookup[key] = item

    # Normalize round values from timestamp-based records
    ROUND_MAP = {
        '2': 'Qualification',
        '1': 'Practice', 
        '3': 'Quarterfinal',
        '4': 'Semifinal',
        '5': 'Final',
        '6': 'Round of 16'
    }

    updates = 0
    deletes = 0
    orphans = 0

    # Process timestamp-based records
    for item in timestamp_based:
        pk = item['PK']
        sk = item['SK']
        sku = item.get('sku', '')
        raw_round = str(item.get('round', ''))
        normalized_round = ROUND_MAP.get(raw_round, raw_round)
        inst = str(item.get('instance', '1'))
        mnum = str(item.get('match_num') or item.get('matchnum', ''))
        video_url = item.get('video_url', '')

        key = (pk, sku, normalized_round, inst, mnum)
        canonical_item = canonical_lookup.get(key)

        if canonical_item:
            # Merge video_url into canonical record if it doesn't have one
            if video_url and not canonical_item.get('video_url'):
                if not DRY_RUN:
                    table.update_item(
                        Key={'PK': canonical_item['PK'], 'SK': canonical_item['SK']},
                        UpdateExpression='SET video_url = :v',
                        ExpressionAttributeValues={':v': video_url}
                    )
                updates += 1

            # Delete the timestamp-based duplicate
            if not DRY_RUN:
                table.delete_item(Key={'PK': pk, 'SK': sk})
            deletes += 1
        else:
            # No canonical match found — this is an orphan (only exists in our upload)
            # Keep it but fix the round name if numeric
            if raw_round in ROUND_MAP and not DRY_RUN:
                table.update_item(
                    Key={'PK': pk, 'SK': sk},
                    UpdateExpression='SET #r = :r',
                    ExpressionAttributeNames={'#r': 'round'},
                    ExpressionAttributeValues={':r': normalized_round}
                )
            orphans += 1

    # Delete legacy nested records
    legacy_deletes = 0
    for item in legacy_nested:
        pk = item['PK']
        sk = item['SK']
        if not DRY_RUN:
            table.delete_item(Key={'PK': pk, 'SK': sk})
        legacy_deletes += 1

    print(f"\n--- Results ---")
    print(f"Video URLs merged into canonical records: {updates}")
    print(f"Timestamp-based duplicates deleted: {deletes}")
    print(f"Orphan records kept (no canonical match): {orphans}")
    print(f"Legacy/malformed records deleted: {legacy_deletes}")
    print(f"DRY_RUN: {DRY_RUN}")

if __name__ == "__main__":
    run()
