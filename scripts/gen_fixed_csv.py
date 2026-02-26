import json
import csv
import re

def convert_json_to_csv(json_path, csv_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    rows = []
    for match_id, m in data.items():
        sku = m['event']['sku']
        
        # Normalize match name
        # Qualifier #1 -> Q1
        # Final #1 -> F1
        # Semifinals #2 -> SF2
        # Round of 16 #5-2 -> R16-5-2
        name = m['match_name']
        match_type = ""
        if "Qualifier" in name: match_type = "Q"
        elif "Final" in name: match_type = "F"
        elif "Semifinal" in name: match_type = "SF"
        elif "Quarterfinal" in name: match_type = "QF"
        elif "Round of 16" in name: match_type = "R16"
        
        # Extract numbers
        nums = re.findall(r'\d+', name)
        match_str = match_type + "-".join(nums)
        
        yt_url = m['video_url']
        # Extract youtube ID: https://www.youtube.com/watch?v=ID&...
        yt_id = ""
        if 'v=' in yt_url:
            yt_id = yt_url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in yt_url:
             yt_id = yt_url.split('youtu.be/')[1].split('?')[0]
             
        ts = m['timestamp']
        div_id = m.get('division_id', 1)
        
        rows.append([sku, match_str, yt_id, ts, div_id])
        
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['sku', 'match_name', 'youtube_id', 'timestamp_seconds', 'division_id'])
        writer.writerows(rows)
    
    print(f"Generated {csv_path} with {len(rows)} rows.")

if __name__ == "__main__":
    convert_json_to_csv("match_links.json", "match_videos_fixed.csv")
