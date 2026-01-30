#!/usr/bin/env python3
"""
Fix Season 26 data: Remove old data and fetch new trends for corrected dates.
Season 26 should be 2018-04-30 to 2018-05-21
"""

import time
import pandas as pd
from serpapi import GoogleSearch

API_KEY = "721cc04e1a2b9b6130648ab991c8197fb8525ef497324f5bf505cfb85f4b5462"
OUTPUT_PATH = "/Users/luoyiti/Project/MCM_2026/data/serpapi/google_trends_results.csv"

# Season 26 celebrities
SEASON_26_CELEBRITIES = [
    "Jamie Anderson",
    "Johnny Damon",
    "Kareem Abdul-Jabbar",
    "Arike Ogunbowale",
    "Jennie Finch Daigle",
    "Chris Mazdzer",
    "Mirai Nagasu",
    "Tonya Harding",
    "Josh Norman",
    "Adam Rippon"
]

# Correct date range
START_DATE = "2018-04-30"
END_DATE = "2018-05-21"

def fetch_and_save(name, season=26):
    print(f"Fetching: {name}")
    params = {
        "engine": "google_trends",
        "q": name,
        "data_type": "TIMESERIES",
        "date": f"{START_DATE} {END_DATE}",
        "geo": "US",
        "api_key": API_KEY
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        interest_data = results.get("interest_over_time", {})
        timeline_data = interest_data.get("timeline_data", [])
        
        if not timeline_data:
            print(f"  No data available")
            return 0
        
        rows = []
        for point in timeline_data:
            date_str = point.get("date", "")
            values = point.get("values", [])
            trend_value = values[0].get("extracted_value", 0) if values else 0
            rows.append({
                "celebrity_name": name,
                "season": season,
                "date": date_str,
                "trend_value": trend_value,
                "error": None
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(OUTPUT_PATH, mode='a', header=False, index=False)
        print(f"  Saved {len(rows)} data points")
        return len(rows)
        
    except Exception as e:
        print(f"  Error: {e}")
        return 0

def main():
    print("=" * 60)
    print("Fixing Season 26 Data")
    print(f"New date range: {START_DATE} to {END_DATE}")
    print("=" * 60)
    
    # Step 1: Remove old Season 26 data
    print("\n[Step 1] Removing old Season 26 data...")
    df = pd.read_csv(OUTPUT_PATH)
    original_count = len(df)
    df = df[df["season"] != 26]
    removed_count = original_count - len(df)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"  Removed {removed_count} rows")
    
    # Step 2: Fetch new data
    print(f"\n[Step 2] Fetching new data for {len(SEASON_26_CELEBRITIES)} celebrities...")
    total_rows = 0
    
    for idx, name in enumerate(SEASON_26_CELEBRITIES):
        print(f"\n[{idx+1}/{len(SEASON_26_CELEBRITIES)}]", end=" ")
        rows = fetch_and_save(name)
        total_rows += rows
        if idx < len(SEASON_26_CELEBRITIES) - 1:
            time.sleep(1)
    
    print(f"\n{'=' * 60}")
    print("COMPLETED!")
    print(f"  Total new rows added: {total_rows}")
    print("=" * 60)

if __name__ == "__main__":
    main()
