#!/usr/bin/env python3
"""
Fix Season 34 data: Remove old data and fetch new trends for corrected dates.
Season 34 should be 2025-09-17 to 2025-11-25 (not 2025-03-04 to 2025-05-20)
"""

import os
import time
import pandas as pd
from serpapi import GoogleSearch
from datetime import datetime

# Configuration
API_KEY = "721cc04e1a2b9b6130648ab991c8197fb8525ef497324f5bf505cfb85f4b5462"
DELAY_BETWEEN_REQUESTS = 1

# Corrected Season 34 dates
SEASON_34_START = "2025-09-17"
SEASON_34_END = "2025-11-25"

# File paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(SCRIPT_DIR)
CELEBRITY_DATA_PATH = os.path.join(DATA_DIR, "2026_MCM_Problem_C_Data.csv")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "google_trends_results.csv")


def fetch_google_trends(celebrity_name: str, start_date: str, end_date: str) -> dict:
    """Fetch Google Trends data for a celebrity during a specific date range."""
    date_range = f"{start_date} {end_date}"
    
    params = {
        "engine": "google_trends",
        "q": celebrity_name,
        "data_type": "TIMESERIES",
        "date": date_range,
        "geo": "US",
        "api_key": API_KEY
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        return results
    except Exception as e:
        return {"error": str(e)}


def extract_timeline_data(results: dict, celebrity_name: str, season: int) -> list:
    """Extract timeline data from SerpAPI response."""
    extracted = []
    
    if "error" in results:
        return [{
            "celebrity_name": celebrity_name,
            "season": season,
            "date": None,
            "trend_value": None,
            "error": results["error"]
        }]
    
    interest_data = results.get("interest_over_time", {})
    timeline_data = interest_data.get("timeline_data", [])
    
    if not timeline_data:
        return [{
            "celebrity_name": celebrity_name,
            "season": season,
            "date": None,
            "trend_value": None,
            "error": "No timeline data available"
        }]
    
    for point in timeline_data:
        date_str = point.get("date", "")
        values = point.get("values", [])
        
        trend_value = None
        if values:
            trend_value = values[0].get("extracted_value", values[0].get("value", None))
        
        extracted.append({
            "celebrity_name": celebrity_name,
            "season": season,
            "date": date_str,
            "trend_value": trend_value,
            "error": None
        })
    
    return extracted


def main():
    print("=" * 60)
    print("Fixing Season 34 Data")
    print("=" * 60)
    
    # Step 1: Load existing results and remove Season 34 data
    print("\n[Step 1] Loading existing data and removing old Season 34 entries...")
    results_df = pd.read_csv(OUTPUT_PATH)
    original_count = len(results_df)
    
    # Remove Season 34 data
    results_df = results_df[results_df["season"] != 34]
    removed_count = original_count - len(results_df)
    print(f"  Removed {removed_count} rows of old Season 34 data")
    
    # Save immediately after removing old data
    results_df.to_csv(OUTPUT_PATH, index=False)
    print(f"  Saved cleaned data (removed old Season 34)")
    
    # Step 2: Get Season 34 celebrities from original data
    print("\n[Step 2] Getting Season 34 celebrities...")
    celebrity_df = pd.read_csv(CELEBRITY_DATA_PATH)
    season34_celebrities = celebrity_df[celebrity_df["season"] == 34]["celebrity_name"].tolist()
    print(f"  Found {len(season34_celebrities)} celebrities for Season 34:")
    for name in season34_celebrities:
        print(f"    - {name}")
    
    # Step 3: Fetch new trends for correct date range
    print(f"\n[Step 3] Fetching Google Trends for {SEASON_34_START} to {SEASON_34_END}...")
    
    for idx, celebrity_name in enumerate(season34_celebrities):
        print(f"\n  [{idx+1}/{len(season34_celebrities)}] Fetching: {celebrity_name}")
        
        results = fetch_google_trends(celebrity_name, SEASON_34_START, SEASON_34_END)
        extracted = extract_timeline_data(results, celebrity_name, 34)
        
        if extracted and extracted[0].get("error"):
            print(f"    Error: {extracted[0]['error']}")
        else:
            print(f"    Got {len(extracted)} data points")
        
        # Save immediately after each celebrity
        new_df = pd.DataFrame(extracted)
        new_df.to_csv(OUTPUT_PATH, mode='a', header=False, index=False)
        print(f"    Saved to file")
        
        # Rate limiting
        if idx < len(season34_celebrities) - 1:
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Final count
    final_df = pd.read_csv(OUTPUT_PATH)
    print(f"\n{'=' * 60}")
    print("COMPLETED!")
    print(f"  Final total rows: {len(final_df)}")
    print(f"  Results saved to: {OUTPUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
