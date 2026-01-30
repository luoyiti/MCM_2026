#!/usr/bin/env python3
"""Fetch remaining Season 34 celebrities."""

import time
import pandas as pd
from serpapi import GoogleSearch

API_KEY = "721cc04e1a2b9b6130648ab991c8197fb8525ef497324f5bf505cfb85f4b5462"
OUTPUT_PATH = "/Users/luoyiti/Project/MCM_2026/data/serpapi/google_trends_results.csv"

# Remaining celebrities
REMAINING = ["Jen Affleck", "Whitney Leavitt", "Dylan Efron"]
START_DATE = "2025-09-17"
END_DATE = "2025-11-25"

def fetch_and_save(name):
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
        
        rows = []
        for point in timeline_data:
            date_str = point.get("date", "")
            values = point.get("values", [])
            trend_value = values[0].get("extracted_value", 0) if values else 0
            rows.append({
                "celebrity_name": name,
                "season": 34,
                "date": date_str,
                "trend_value": trend_value,
                "error": None
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(OUTPUT_PATH, mode='a', header=False, index=False)
        print(f"  Saved {len(rows)} data points")
        
    except Exception as e:
        print(f"  Error: {e}")

for name in REMAINING:
    fetch_and_save(name)
    time.sleep(2)

print("Done!")
