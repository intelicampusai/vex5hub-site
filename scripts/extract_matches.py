import json
import sys

def extract_matches(sku):
    with open('/Users/jj/vex5hub-site/collected_matches.json', 'r') as f:
        data = json.load(f)
    
    matches = data.get('matches', {})
    event_matches = []
    for m_id, m_data in matches.items():
        if m_data.get('event', {}).get('code') == sku:
            event_matches.append(m_data)
    
    # Sort matches by scheduled time or started time
    event_matches.sort(key=lambda x: x.get('started') or x.get('scheduled') or '')
    
    with open(f'matches_{sku}.json', 'w') as f:
        json.dump(event_matches, f, indent=2)
    
    print(f"Extracted {len(event_matches)} matches for {sku}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        extract_matches(sys.argv[1])
    else:
        print("Usage: python extract_matches.py <SKU>")
