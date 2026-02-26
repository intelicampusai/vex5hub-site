import boto3
from boto3.dynamodb.conditions import Key

def cleanup_stale_v2(table_name, profile):
    session = boto3.Session(profile_name=profile, region_name='ca-central-1')
    table = session.resource('dynamodb').Table(table_name)
    
    print(f"Scanning {table_name} for stale match items...")
    
    deleted_count = 0
    
    # We'll scan for all matches (this is a small table, so it's okay)
    # Actually, let's just scan for anything starting with MATCH#
    response = table.scan(
        FilterExpression="begins_with(SK, :m)",
        ExpressionAttributeValues={":m": "MATCH#"}
    )
    
    while True:
        items = response.get('Items', [])
        for item in items:
            pk = item['PK']
            sk = item['SK']
            
            # Pattern check:
            # Old: MATCH#SKU#DIV#NUM (4 parts)
            # New: MATCH#SKU#DIV#ROUND#INST#NUM (6 parts)
            # Also Event matches:
            # Old: MATCH#DIV#NUM (3 parts)
            # New: MATCH#DIV#ROUND#INST#NUM (5 parts)
            
            parts = sk.split('#')
            is_stale = False
            
            if pk.startswith('TEAM#'):
                if len(parts) == 4:
                    is_stale = True
            elif pk.startswith('EVENT#'):
                if len(parts) == 3:
                    is_stale = True
            
            # Extra check for division 100 which was mis-assigned by the old script
            if not is_stale and '#100#' in sk:
                # We already did this, but let's be safe. 
                # Actually, some signature events USE 100 for finals, so we should be careful.
                # Only delete if it's from a non-signature event or we know it's wrong.
                # For now, let's stick to the segment count which is a much safer indicator of "old format".
                pass

            if is_stale:
                print(f"  Deleting stale item: PK={pk}, SK={sk}")
                table.delete_item(Key={'PK': pk, 'SK': sk})
                deleted_count += 1
                
        if 'LastEvaluatedKey' not in response:
            break
        response = table.scan(
            FilterExpression="begins_with(SK, :m)",
            ExpressionAttributeValues={":m": "MATCH#"},
            ExclusiveStartKey=response['LastEvaluatedKey']
        )

    print(f"Cleanup complete. Deleted {deleted_count} stale items.")

if __name__ == "__main__":
    cleanup_stale_v2("vex5hub-data", "rdp")
