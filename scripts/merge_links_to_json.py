import json
import csv
import os

def merge_links():
    links_file = '/Users/jj/vex5hub-site/match_links.json'
    csv_file = '/Users/jj/vex5hub-site/multi_event_links.csv'
    matches_file = '/Users/jj/vex5hub-site/collected_matches.json'
    
    # Load existing links
    try:
        if os.path.exists(links_file):
            with open(links_file, 'r') as f:
                links = json.load(f)
        else:
            links = {}
    except Exception as e:
        print(f"Error loading {links_file}: {e}")
        links = {}
    
    # Load all matches
    with open(matches_file, 'r') as f:
        data = json.load(f)
        all_matches = data.get('matches', {})
    
    # Pre-index matches for faster lookup: (sku, div_id, normalized_name) -> match_id
    match_lookup = {}
    for m_id, m in all_matches.items():
        sku = m.get('event', {}).get('code')
        div = m.get('division', {}).get('id')
        name = m.get('name')
        if sku and name:
            # We need to normalize name like the generation script did
            norm_name = name.replace('Qualifier #', 'Q')
            norm_name = norm_name.replace('Round of 16 #', 'R16')
            norm_name = norm_name.replace('Quarterfinal #', 'QF')
            norm_name = norm_name.replace('Semifinal #', 'SF')
            norm_name = norm_name.replace('Final #', 'F')
            norm_name = norm_name.replace(' #', '')
            match_lookup[(sku, div, norm_name)] = m_id
            
    # Load CSV and merge
    merged_count = 0
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row['sku']
            name = row['match_name']
            div = int(row['division_id'])
            v_id = row['youtube_id']
            ts = int(row['timestamp_seconds'])
            
            m_id = match_lookup.get((sku, div, name))
            if m_id:
                match_data = all_matches[m_id]
                links[m_id] = {
                    "match_id": int(m_id),
                    "match_name": match_data.get('name'),
                    "video_url": f"https://www.youtube.com/watch?v={v_id}&t={ts}s",
                    "timestamp": ts,
                    "alliances": match_data.get('alliances'),
                    "round": match_data.get('round'),
                    "instance": match_data.get('instance'),
                    "matchnum": match_data.get('matchnum'),
                    "division_id": div,
                    "started": match_data.get('started'),
                    "scheduled": match_data.get('scheduled'),
                    "field": match_data.get('field'),
                    "event": match_data.get('event')
                }
                merged_count += 1
            else:
                # Silently skip if match_id not found in current local data (it might be in RobotEvents but not here)
                pass

    # Save merged links
    with open(links_file, 'w') as f:
        json.dump(links, f, indent=2)
    
    print(f"Successfully merged {merged_count} links into {links_file}")

if __name__ == "__main__":
    merge_links()
