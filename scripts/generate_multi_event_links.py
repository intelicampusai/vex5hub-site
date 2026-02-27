import json
import csv
from datetime import datetime

# --- Configuration ---
# Keys are SKU, values are lists of stream configs for that event
STREAMS = {
    "RE-V5RC-25-0147": [ # Ignite the Northwest
        {
            "video_id": "NaLgd1bmHy4", # Day 1 Volcanic
            "ref_match_name": "Qualifier #26",
            "ref_timestamp": 4779, # 1:19:39
            "div_id": 1
        },
        {
            "video_id": "T3iBuIt4M-0", # Day 2 Volcanic
            "ref_match_name": "Qualifier #40",
            "ref_timestamp": 8428, # 2:20:28
            "div_id": 1
        }
    ],
    "RE-V5RC-25-0011": [ # Rumble In the Rockies
        {
            "video_id": "dqiXLjV04TY", # Wasatch HS Day 1
            "ref_match_name": "Qualifier #38",
            "ref_timestamp": 12132, # 3:22:12
            "div_id": 1
        }
    ],
    "RE-V5RC-25-0254": [ # NorCal SV MS
        {
            "video_id": "PM0oZwGOi7E", # MS Division 1
            "ref_match_name": "Qualifier #57",
            "ref_timestamp": 7691, # 2:08:11
            "div_id": 1
        },
        {
            "video_id": "PM0oZwGOi7E", # MS Division 1 After gap
            "ref_match_name": "Qualifier #110",
            "ref_timestamp": 15020, # 4:10:20
            "div_id": 1
        }
    ],
    "RE-V5RC-24-5556": [ # Sugar Rush (Last Season)
        {
            "video_id": "4zax7Yvnr20",
            "ref_match_name": "Qualifier #3",
            "ref_timestamp": 4256,
            "div_id": 1
        },
        {
            "video_id": "bZbPGEhARNY",
            "ref_match_name": "Qualifier #112",
            "ref_timestamp": 3516,
            "div_id": 1
        }
    ],
    "RE-V5RC-24-5730": [ # NorCal SV (Last Season)
        {
            "video_id": "xrCy_MCgMMk",
            "ref_match_name": "Qualifier #1",
            "ref_timestamp": 3114,
            "div_id": 1
        }
    ]
}

def load_matches(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_links():
    data = load_matches('collected_matches.json')
    matches = list(data.get('matches', {}).values())
    print(f"Total collected matches loaded: {len(matches)}")
    
    # Pre-calculate video start timestamps
    video_starts = {} # format: { SKU: { video_id: start_timestamp } }
    
    for match in matches:
        if not match.get('started'): continue
        
        sku = match.get('event', {}).get('code')
        if sku not in STREAMS: continue
        
        match_name = match.get('name')
        div_id = match.get('division', {}).get('id')
        
        for cfg in STREAMS[sku]:
            if match_name == cfg['ref_match_name'] and div_id == cfg['div_id']:
                ref_start_dt = datetime.fromisoformat(match['started'].replace('Z', '+00:00'))
                
                if sku not in video_starts:
                    video_starts[sku] = {}
                
                start_ts = ref_start_dt.timestamp() - cfg['ref_timestamp']
                cfg['v_start'] = start_ts
                print(f"Calculated Video Start for {sku} ({cfg['video_id']}) using {match_name}: {start_ts}")

    
    links = []
    
    for match in matches:
        if not match.get('started'): continue
        
        sku = match.get('event', {}).get('code')
        if sku not in STREAMS or sku not in video_starts: continue
        
        div_id = match.get('division', {}).get('id')
        
        match_start_dt = datetime.fromisoformat(match['started'].replace('Z', '+00:00'))
        
        # Determine which stream config applies by finding the closest past stream
        # This assumes videos don't overlap much, or we pick the one where match_start > stream_start
        # If there are multiple days, we can match by the date
        
        best_cfg = None
        min_offset = float('inf')
        
        for cfg in STREAMS[sku]:
            if div_id != cfg['div_id'] or 'v_start' not in cfg: continue
            
            offset = match_start_dt.timestamp() - cfg['v_start']
            
            if 0 <= offset < min_offset and offset < 43200:
                min_offset = offset
                best_cfg = cfg
                
        if not best_cfg:
            continue
            
        timestamp = int(match_start_dt.timestamp() - best_cfg['v_start'])
        
        if match_name.startswith('Qualifier #'):
            clean_name = match_name.replace('Qualifier #', 'Q')
        else:
            clean_name = match_name.replace(' #', '')

        try:
            if sku == 'RE-V5RC-25-0254' and clean_name.startswith('Q'):
                qnum = int(clean_name[1:])
                if 84 <= qnum <= 109:
                    continue # Skip lost matches during stream crash
        except:
            pass
            
        links.append({
            'sku': sku,
            'match_name': clean_name,
            'youtube_id': best_cfg['video_id'],
            'timestamp_seconds': timestamp,
            'division_id': div_id
        })

    print(f"Generated links for {len(links)} matches.")
    
    # Save to CSV
    csv_file = 'multi_event_links.csv'
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sku', 'match_name', 'youtube_id', 'timestamp_seconds', 'division_id'])
        writer.writeheader()
        writer.writerows(links)
    print(f"Saved to {csv_file}")

if __name__ == "__main__":
    generate_links()
