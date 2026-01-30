#!/usr/bin/env python3
"""Fetch remaining Season 26 celebrities."""

import time
import pandas as pd
from serpapi import GoogleSearch

API_KEY = "721cc04e1a2b9b6130648ab991c8197fb8525ef497324f5bf505cfb85f4b5462"
OUTPUT_PATH = "/Users/luoyiti/Project/MCM_2026/data/serpapi/google_trends_results.csv"

REMAINING = ["Mirai Nagasu", "Tonya Harding", "Josh Norman", "Adam Rippon"]
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

for idx, name in enumerate(REMAINING):
    print(f"[{idx+1}/{len(REMAINING)}]", end=" ")
    fetch_and_save(name)
    if idx < len(REMAINING) - 1:
        time.sleep(2)

print("\nDone!")
