#!/usr/bin/env python3
"""
Fetch additional Google Trends data for Season 32 celebrities.
Period: 2023-11-22 to 2023-12-05 (missing data after original end date)
"""

import time
import pandas as pd
from serpapi import GoogleSearch

API_KEY = "721cc04e1a2b9b6130648ab991c8197fb8525ef497324f5bf505cfb85f4b5462"
OUTPUT_PATH = "/Users/luoyiti/Project/MCM_2026/data/serpapi/google_trends_results.csv"

# Season 32 celebrities
SEASON_32_CELEBRITIES = [
    "Jamie Lynn Spears",
    "Mira Sorvino",
    "Barry Williams",
    "Alyson Hannigan",
    "Xochitl Gomez",
    "Adrian Peterson",
    "Matt Walsh",
    "Tyson Beckford",
    "Jason Mraz",
    "Lele Pons",
    "Harry Jowsey",
    "Mauricio Umansky",
    "Charity Lawson",
    "Ariana Madix"
]

# Missing date range
START_DATE = "2023-11-22"
END_DATE = "2023-12-05"

def fetch_and_save(name, season=32):
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
            return
        
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
        
    except Exception as e:
        print(f"  Error: {e}")

print("=" * 60)
print("Fetching Season 32 additional data")
print(f"Date range: {START_DATE} to {END_DATE}")
print("=" * 60)

for idx, name in enumerate(SEASON_32_CELEBRITIES):
    print(f"\n[{idx+1}/{len(SEASON_32_CELEBRITIES)}]", end=" ")
    fetch_and_save(name)
    if idx < len(SEASON_32_CELEBRITIES) - 1:
        time.sleep(1)

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
