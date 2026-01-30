#!/usr/bin/env python3
"""Fetch last remaining Season 32 celebrity."""

import pandas as pd
from serpapi import GoogleSearch

API_KEY = "721cc04e1a2b9b6130648ab991c8197fb8525ef497324f5bf505cfb85f4b5462"
OUTPUT_PATH = "/Users/luoyiti/Project/MCM_2026/data/serpapi/google_trends_results.csv"

print("Fetching: Ariana Madix")
params = {
    "engine": "google_trends",
    "q": "Ariana Madix",
    "data_type": "TIMESERIES",
    "date": "2023-11-22 2023-12-05",
    "geo": "US",
    "api_key": API_KEY
}

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
        "celebrity_name": "Ariana Madix",
        "season": 32,
        "date": date_str,
        "trend_value": trend_value,
        "error": None
    })

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_PATH, mode='a', header=False, index=False)
print(f"Saved {len(rows)} data points")
print("Done!")
