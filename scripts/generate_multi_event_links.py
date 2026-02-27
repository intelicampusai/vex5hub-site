
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

def normalize_match_name(name):
    """
    Normalizes 'Qualifier #1' -> 'Q1', 'Round of 16 #4-1' -> 'R164-1', etc.
    Matches the expectations of parse_match_name in upload_match_videos.py
    """
    if not name: return name
    n = name.replace('Qualifier #', 'Q')
    n = n.replace('Round of 16 #', 'R16')
    n = n.replace('Quarterfinal #', 'QF')
    n = n.replace('Semifinal #', 'SF')
    n = n.replace('Final #', 'F')
    n = n.replace('Practice #', 'P')
    n = n.replace('Round of 32 #', 'R32')
    n = n.replace('Round of 64 #', 'R64')
    return n.replace(' #', '')

def generate_links():
    data = load_matches('collected_matches.json')
    matches = list(data.get('matches', {}).values())
    print(f"Total collected matches loaded: {len(matches)}")
    
    # Pre-calculate video start timestamps
    for sku in STREAMS:
        for cfg in STREAMS[sku]:
            # Find the reference match to anchor this stream segment
            ref_match = None
            for match in matches:
                if (match.get('event', {}).get('code') == sku and 
                    match.get('name') == cfg['ref_match_name'] and 
                    match.get('division', {}).get('id') == cfg['div_id']):
                    ref_match = match
                    break
            
            if ref_match and ref_match.get('started'):
                ref_start_dt = datetime.fromisoformat(ref_match['started'].replace('Z', '+00:00'))
                v_start = ref_start_dt.timestamp() - cfg['ref_timestamp']
                cfg['v_start'] = v_start
                print(f"Anchored {sku} ({cfg['video_id']}) using {cfg['ref_match_name']} -> v_start={v_start}")

    links = []
    
    for match in matches:
        if not match.get('started'): continue
        
        sku = match.get('event', {}).get('code')
        if sku not in STREAMS: continue
        
        div_id = match.get('division', {}).get('id')
        match_name = match.get('name')
        match_start_dt = datetime.fromisoformat(match['started'].replace('Z', '+00:00'))
        match_ts = match_start_dt.timestamp()
        
        # Select the best stream segment
        best_cfg = None
        min_abs_offset = float('inf')
        
        for cfg in STREAMS[sku]:
            if div_id != cfg['div_id'] or 'v_start' not in cfg: continue
            
            offset = match_ts - cfg['v_start']
            
            # A match belongs to a segment if it's reasonably close. 
            # If there's a huge gap (crash), the later segment will eventually be "closer" or have a smaller positive offset.
            # We prefer positive offsets (match starts AFTER segment start)
            if 0 <= offset < 43200: # Match is within 12 hours after segment start
                if offset < min_abs_offset:
                    min_abs_offset = offset
                    best_cfg = cfg
            elif best_cfg is None and -14400 < offset < 0:
                # Allow matches up to 4 hours BEFORE the anchor if no positive match found yet
                # This handles early morning matches before the reference match
                if abs(offset) < min_abs_offset:
                    min_abs_offset = abs(offset)
                    best_cfg = cfg
                
        if not best_cfg:
            continue
            
        timestamp = int(match_ts - best_cfg['v_start'])
        if timestamp < 0: timestamp = 0
        
        clean_name = normalize_match_name(match_name)

        # Event-specific filtering (NorCal Crash)
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
