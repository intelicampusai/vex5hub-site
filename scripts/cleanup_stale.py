import boto3
from boto3.dynamodb.conditions import Key

def cleanup_stale_matches(table_name, profile):
    session = boto3.Session(profile_name=profile, region_name='ca-central-1')
    table = session.resource('dynamodb').Table(table_name)
    
    # 1. Cleanup EVENT matches with div 100
    print("Cleaning up EVENT matches with div 100...")
    # This is slightly harder because we don't have a GSI on division_id for events usually
    # But we can query by PK=EVENT#sku and filter or scan
    # For now, let's just scan for anything with SK containing #100#
    
    count = 0
    # Scan for matches with #100# in SK
    # This is inefficient but safe for a one-time cleanup of a small table
    response = table.scan(
        FilterExpression="contains(SK, :s)",
        ExpressionAttributeValues={":s": "#100#"}
    )
    
    items = response.get('Items', [])
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression="contains(SK, :s)",
            ExpressionAttributeValues={":s": "#100#"},
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items.extend(response.get('Items', []))
        
    print(f"Found {len(items)} stale items to delete.")
    
    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})
            count += 1
            if count % 100 == 0:
                print(f"  Deleted {count} items...")
                
    print(f"Cleanup complete. Deleted {count} items.")

if __name__ == "__main__":
    cleanup_stale_matches("vex5hub-data", "rdp")
