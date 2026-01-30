#!/usr/bin/env python3
"""
Fetch Google Trends data for DWTS celebrities using SerpAPI.

This script fetches Google Trends interest data for the first 220 celebrities
from the DWTS dataset during their respective season dates.
"""

import os
import time
import pandas as pd
from serpapi import GoogleSearch
from datetime import datetime

# Configuration
API_KEY = "721cc04e1a2b9b6130648ab991c8197fb8525ef497324f5bf505cfb85f4b5462"
DELAY_BETWEEN_REQUESTS = 2  # seconds between API calls to avoid rate limiting
SKIP_FIRST = 220  # Skip first 220 celebrities (already processed)

# File paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(SCRIPT_DIR)
CELEBRITY_DATA_PATH = os.path.join(DATA_DIR, "2026_MCM_Problem_C_Data.csv")
SEASON_DATES_PATH = os.path.join(DATA_DIR, "DWTS_season_dates.csv")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "google_trends_results.csv")
PROGRESS_PATH = os.path.join(SCRIPT_DIR, "progress.csv")


def load_data():
    """Load celebrity data and season dates."""
    # Load all celebrity data, skip first 220 (already processed)
    celebrities_df = pd.read_csv(CELEBRITY_DATA_PATH, skiprows=range(1, SKIP_FIRST + 1))
    celebrities_df = celebrities_df[["celebrity_name", "season"]].copy()
    
    # Load season dates
    season_dates_df = pd.read_csv(SEASON_DATES_PATH)
    
    # Merge to get date ranges for each celebrity
    merged_df = celebrities_df.merge(season_dates_df, on="season", how="left")
    
    print(f"Loaded {len(merged_df)} celebrities with season dates")
    return merged_df


def fetch_google_trends(celebrity_name: str, start_date: str, end_date: str) -> dict:
    """
    Fetch Google Trends data for a celebrity during a specific date range.
    
    Args:
        celebrity_name: Name of the celebrity to search
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Dictionary with trend data or error information
    """
    # Format date range for SerpAPI (YYYY-MM-DD YYYY-MM-DD)
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
    """
    Extract timeline data from SerpAPI response.
    
    Args:
        results: Raw API response dictionary
        celebrity_name: Name of the celebrity
        season: DWTS season number
    
    Returns:
        List of dictionaries with extracted trend data
    """
    extracted = []
    
    if "error" in results:
        return [{
            "celebrity_name": celebrity_name,
            "season": season,
            "date": None,
            "trend_value": None,
            "error": results["error"]
        }]
    
    # Extract interest over time data
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
        
        # Get the first value (for single query)
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


def load_progress() -> set:
    """Load already processed celebrities from progress file."""
    if os.path.exists(PROGRESS_PATH):
        progress_df = pd.read_csv(PROGRESS_PATH)
        return set(progress_df["celebrity_name"].unique())
    return set()


def save_progress(celebrity_name: str):
    """Save progress for a celebrity."""
    progress_entry = pd.DataFrame([{"celebrity_name": celebrity_name, "timestamp": datetime.now().isoformat()}])
    
    if os.path.exists(PROGRESS_PATH):
        progress_entry.to_csv(PROGRESS_PATH, mode='a', header=False, index=False)
    else:
        progress_entry.to_csv(PROGRESS_PATH, index=False)


def main():
    """Main execution function."""
    print("=" * 60)
    print("Google Trends Data Fetcher for DWTS Celebrities")
    print("=" * 60)
    
    # Load data
    data_df = load_data()
    
    # Load progress (for resume capability)
    processed = load_progress()
    print(f"Already processed: {len(processed)} celebrities")
    
    # Initialize results list
    all_results = []
    
    # Load existing results if any
    if os.path.exists(OUTPUT_PATH):
        existing_df = pd.read_csv(OUTPUT_PATH)
        all_results = existing_df.to_dict('records')
        print(f"Loaded {len(existing_df)} existing result rows")
    
    # Process each celebrity
    total = len(data_df)
    for idx, row in data_df.iterrows():
        celebrity_name = row["celebrity_name"]
        season = row["season"]
        start_date = row["start_date"]
        end_date = row["end_date"]
        
        # Skip if already processed
        if celebrity_name in processed:
            print(f"[{idx+1}/{total}] Skipping {celebrity_name} (already processed)")
            continue
        
        print(f"[{idx+1}/{total}] Fetching trends for: {celebrity_name} (Season {season})")
        print(f"         Date range: {start_date} to {end_date}")
        
        # Fetch Google Trends data
        results = fetch_google_trends(celebrity_name, start_date, end_date)
        
        # Extract timeline data
        extracted = extract_timeline_data(results, celebrity_name, season)
        all_results.extend(extracted)
        
        # Save progress
        save_progress(celebrity_name)
        
        # Log result
        if extracted and extracted[0].get("error"):
            print(f"         Error: {extracted[0]['error']}")
        else:
            print(f"         Got {len(extracted)} data points")
        
        # Save intermediate results every 10 celebrities
        if (idx + 1) % 10 == 0:
            results_df = pd.DataFrame(all_results)
            results_df.to_csv(OUTPUT_PATH, index=False)
            print(f"         [Saved intermediate results: {len(results_df)} rows]")
        
        # Rate limiting delay
        time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Save final results
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(OUTPUT_PATH, index=False)
    
    print("\n" + "=" * 60)
    print("COMPLETED!")
    print(f"Total celebrities processed: {len(data_df)}")
    print(f"Total data rows: {len(results_df)}")
    print(f"Results saved to: {OUTPUT_PATH}")
    print("=" * 60)
    
    # Display summary statistics
    if not results_df.empty:
        errors = results_df[results_df["error"].notna()]
        success = results_df[results_df["error"].isna()]
        print(f"\nSummary:")
        print(f"  - Successful data points: {len(success)}")
        print(f"  - Errors: {len(errors)}")
        
        if len(success) > 0:
            print(f"  - Average trend value: {success['trend_value'].mean():.2f}")
            print(f"  - Max trend value: {success['trend_value'].max()}")


if __name__ == "__main__":
    main()
