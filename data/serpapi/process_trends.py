#!/usr/bin/env python3
"""
Process Google Trends data:
1. Retry fetching data for celebrities with errors
2. Extract core features for each celebrity
3. Create a summary CSV with one row per celebrity
"""

import os
import time
import pandas as pd
import numpy as np
from serpapi import GoogleSearch
from datetime import datetime

# Configuration
API_KEY = "7da2c11917154c8d2572e1f8909cf2e0c6f0b9f4f92b77612b104b8810340f13"
DELAY_BETWEEN_REQUESTS = 2

# File paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(SCRIPT_DIR)
CELEBRITY_DATA_PATH = os.path.join(DATA_DIR, "2026_MCM_Problem_C_Data.csv")
SEASON_DATES_PATH = os.path.join(DATA_DIR, "DWTS_season_dates.csv")
RESULTS_PATH = os.path.join(SCRIPT_DIR, "google_trends_results.csv")
SUMMARY_PATH = os.path.join(SCRIPT_DIR, "celebrity_trends_summary.csv")
MANUAL_FETCH_PATH = os.path.join(SCRIPT_DIR, "manual_fetch_required.csv")


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


def retry_failed_celebrities(df: pd.DataFrame) -> pd.DataFrame:
    """Retry fetching data for celebrities with errors."""
    print("\n" + "=" * 60)
    print("STEP 1: Retry Failed Celebrities")
    print("=" * 60)
    
    # Find celebrities with errors
    error_celebs = df[df['error'].notna()]['celebrity_name'].unique()
    print(f"Found {len(error_celebs)} celebrities with errors")
    
    if len(error_celebs) == 0:
        return df
    
    # Load season dates
    season_dates = pd.read_csv(SEASON_DATES_PATH)
    celebrity_data = pd.read_csv(CELEBRITY_DATA_PATH)
    
    # Get season info for error celebrities
    celeb_seasons = celebrity_data[celebrity_data['celebrity_name'].isin(error_celebs)][['celebrity_name', 'season']]
    celeb_seasons = celeb_seasons.merge(season_dates, on='season', how='left')
    
    manual_fetch_list = []
    new_data = []
    
    for idx, row in celeb_seasons.iterrows():
        celeb_name = row['celebrity_name']
        season = row['season']
        start_date = row['start_date']
        end_date = row['end_date']
        
        print(f"\nRetrying: {celeb_name} (Season {season})")
        print(f"  Date range: {start_date} to {end_date}")
        
        # Try different query variations
        query_variations = [
            celeb_name,
            celeb_name.replace("'", ""),  # Remove apostrophe
            celeb_name.replace(".", ""),  # Remove periods
            celeb_name.strip(),  # Remove extra spaces
            " ".join(celeb_name.split()),  # Normalize spaces
            celeb_name.split()[0] + " " + celeb_name.split()[-1] if len(celeb_name.split()) > 1 else celeb_name,  # First + Last name
            celeb_name.replace(" Jr.", "").replace(" Jr", ""),  # Remove Jr
            celeb_name.replace(".", "").replace("'", "").strip(),  # Remove all punctuation
        ]
        
        # For specific problematic names, try alternative spellings
        name_alternatives = {
            "Floyd Mayweather Jr. ": ["Floyd Mayweather", "Floyd Mayweather Jr"],
            "Lil' Kim": ["Lil Kim", "Lilkim"],
            "Ashley Hamiliton": ["Ashley Hamilton"],
            "D. L. Hughley": ["DL Hughley", "D L Hughley"],
            "Calvin Johnson Jr.": ["Calvin Johnson", "Megatron"],
            "Jennie Finch Daigle": ["Jennie Finch"],
            "Sherri Sheperd": ["Sherri Shepherd"],
            "Chris Mazdzer": ["Chris Mazdzer luge", "Mazdzer", "Chris Mazdzer Olympics", "Chris Mazdzer athlete"],
            "Scott Hoying": ["Scott Hoying Pentatonix", "Pentatonix Scott", "Scott Hoying singer"],
        }
        
        if celeb_name in name_alternatives:
            query_variations.extend(name_alternatives[celeb_name])
        
        success = False
        for query in query_variations:
            if success:
                break
                
            results = fetch_google_trends(query, start_date, end_date)
            extracted = extract_timeline_data(results, celeb_name, season)
            
            if extracted and extracted[0].get("error") is None:
                print(f"  ✓ Success with query: '{query}' - Got {len(extracted)} data points")
                new_data.extend(extracted)
                success = True
            else:
                print(f"  ✗ Failed with query: '{query}'")
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        if not success:
            print(f"  ⚠ All attempts failed for {celeb_name}")
            manual_fetch_list.append({
                "celebrity_name": celeb_name,
                "season": season,
                "start_date": start_date,
                "end_date": end_date,
                "suggested_queries": ", ".join(query_variations[:3])
            })
    
    # Remove old error rows and add new successful data
    if new_data:
        successful_names = list(set([d['celebrity_name'] for d in new_data if d['error'] is None]))
        df = df[~((df['celebrity_name'].isin(successful_names)) & (df['error'].notna()))]
        new_df = pd.DataFrame(new_data)
        df = pd.concat([df, new_df], ignore_index=True)
        print(f"\nSuccessfully re-fetched data for {len(successful_names)} celebrities")
    
    # Save manual fetch list
    if manual_fetch_list:
        manual_df = pd.DataFrame(manual_fetch_list)
        manual_df.to_csv(MANUAL_FETCH_PATH, index=False)
        print(f"\n⚠ {len(manual_fetch_list)} celebrities require manual fetching")
        print(f"  Saved to: {MANUAL_FETCH_PATH}")
        print("\nCelebrities requiring manual fetch:")
        for item in manual_fetch_list:
            print(f"  - {item['celebrity_name']} (Season {item['season']})")
    
    return df


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract core Google Trends features for each celebrity."""
    print("\n" + "=" * 60)
    print("STEP 2: Extract Core Features")
    print("=" * 60)
    
    # Remove error rows for feature extraction
    valid_df = df[df['error'].isna()].copy()
    
    # Convert trend_value to numeric
    valid_df['trend_value'] = pd.to_numeric(valid_df['trend_value'], errors='coerce')
    
    # Group by celebrity and extract features
    features = []
    
    for celeb_name, group in valid_df.groupby('celebrity_name'):
        season = group['season'].iloc[0]
        values = group['trend_value'].dropna().values
        
        if len(values) == 0:
            features.append({
                'celebrity_name': celeb_name,
                'season': season,
                'trend_mean': np.nan,
                'trend_max': np.nan,
                'trend_min': np.nan,
                'trend_std': np.nan,
                'trend_median': np.nan,
                'trend_sum': np.nan,
                'trend_range': np.nan,
                'trend_peak_count': np.nan,
                'trend_above_50_days': np.nan,
                'trend_above_25_days': np.nan,
                'trend_zero_days': np.nan,
                'total_days': 0,
                'data_quality': 'no_data',
                # Additional features
                'trend_q25': np.nan,
                'trend_q75': np.nan,
                'trend_iqr': np.nan,
                'trend_skewness': np.nan,
                'trend_kurtosis': np.nan,
                'trend_cv': np.nan,
                'trend_first_week_mean': np.nan,
                'trend_last_week_mean': np.nan,
                'trend_growth_rate': np.nan,
                'trend_volatility': np.nan,
                'trend_peak_position': np.nan,
                'trend_above_mean_ratio': np.nan,
                'trend_momentum': np.nan,
                'trend_entropy': np.nan,
                'trend_vector': ''
            })
            continue
        
        # Basic statistics
        mean_val = np.mean(values)
        max_val = np.max(values)
        min_val = np.min(values)
        std_val = np.std(values)
        median_val = np.median(values)
        sum_val = np.sum(values)
        range_val = max_val - min_val
        
        # Quartiles and IQR
        q25 = np.percentile(values, 25)
        q75 = np.percentile(values, 75)
        iqr = q75 - q25
        
        # Peak analysis (values above 75th percentile)
        threshold_75 = np.percentile(values, 75)
        peak_count = np.sum(values >= threshold_75)
        
        # Days above certain thresholds
        above_50 = np.sum(values >= 50)
        above_25 = np.sum(values >= 25)
        zero_days = np.sum(values == 0)
        
        # Advanced statistics
        # Skewness (asymmetry of distribution)
        if std_val > 0:
            skewness = np.mean(((values - mean_val) / std_val) ** 3)
        else:
            skewness = 0
        
        # Kurtosis (tail heaviness)
        if std_val > 0:
            kurtosis = np.mean(((values - mean_val) / std_val) ** 4) - 3
        else:
            kurtosis = 0
        
        # Coefficient of Variation
        cv = (std_val / mean_val * 100) if mean_val > 0 else 0
        
        # Temporal features
        first_week_mean = np.mean(values[:7]) if len(values) >= 7 else np.mean(values)
        last_week_mean = np.mean(values[-7:]) if len(values) >= 7 else np.mean(values)
        growth_rate = ((last_week_mean - first_week_mean) / first_week_mean * 100) if first_week_mean > 0 else 0
        
        # Volatility (standard deviation of daily changes)
        if len(values) > 1:
            daily_changes = np.diff(values)
            volatility = np.std(daily_changes)
        else:
            volatility = 0
        
        # Peak position (relative position of max value, 0-1)
        peak_position = np.argmax(values) / len(values) if len(values) > 0 else 0
        
        # Ratio of days above mean
        above_mean_ratio = np.sum(values > mean_val) / len(values) if len(values) > 0 else 0
        
        # Momentum (difference between second half and first half means)
        mid = len(values) // 2
        if mid > 0:
            first_half_mean = np.mean(values[:mid])
            second_half_mean = np.mean(values[mid:])
            momentum = second_half_mean - first_half_mean
        else:
            momentum = 0
        
        # Entropy (information content / randomness)
        if sum_val > 0:
            probs = values / sum_val
            probs = probs[probs > 0]  # Avoid log(0)
            entropy = -np.sum(probs * np.log2(probs + 1e-10))
        else:
            entropy = 0
        
        # Data quality assessment
        if max_val == 0:
            quality = 'all_zero'
        elif std_val == 0:
            quality = 'constant'
        elif len(values) < 30:
            quality = 'sparse'
        else:
            quality = 'good'
        
        # Convert values array to string vector
        trend_vector = ','.join([str(int(v)) for v in values])
        
        features.append({
            'celebrity_name': celeb_name,
            'season': season,
            'trend_mean': round(mean_val, 2),
            'trend_max': max_val,
            'trend_min': min_val,
            'trend_std': round(std_val, 2),
            'trend_median': median_val,
            'trend_sum': sum_val,
            'trend_range': range_val,
            'trend_peak_count': peak_count,
            'trend_above_50_days': above_50,
            'trend_above_25_days': above_25,
            'trend_zero_days': zero_days,
            'total_days': len(values),
            'data_quality': quality,
            # Additional features
            'trend_q25': round(q25, 2),
            'trend_q75': round(q75, 2),
            'trend_iqr': round(iqr, 2),
            'trend_skewness': round(skewness, 2),
            'trend_kurtosis': round(kurtosis, 2),
            'trend_cv': round(cv, 2),
            'trend_first_week_mean': round(first_week_mean, 2),
            'trend_last_week_mean': round(last_week_mean, 2),
            'trend_growth_rate': round(growth_rate, 2),
            'trend_volatility': round(volatility, 2),
            'trend_peak_position': round(peak_position, 2),
            'trend_above_mean_ratio': round(above_mean_ratio, 2),
            'trend_momentum': round(momentum, 2),
            'trend_entropy': round(entropy, 2),
            'trend_vector': trend_vector
        })
    
    features_df = pd.DataFrame(features)
    
    print(f"Extracted features for {len(features_df)} celebrities")
    print(f"\nData quality summary:")
    print(features_df['data_quality'].value_counts())
    
    return features_df


def main():
    """Main execution function."""
    print("=" * 60)
    print("Google Trends Data Processing")
    print("=" * 60)
    
    # Load results
    print(f"\nLoading results from: {RESULTS_PATH}")
    df = pd.read_csv(RESULTS_PATH)
    print(f"Loaded {len(df)} rows for {df['celebrity_name'].nunique()} celebrities")
    
    # Step 1: Retry failed celebrities
    df = retry_failed_celebrities(df)
    
    # Save updated results
    df.to_csv(RESULTS_PATH, index=False)
    print(f"\nUpdated results saved to: {RESULTS_PATH}")
    
    # Step 2: Extract features
    features_df = extract_features(df)
    
    # Save summary
    features_df.to_csv(SUMMARY_PATH, index=False)
    print(f"\nSummary saved to: {SUMMARY_PATH}")
    
    # Print summary statistics
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Total celebrities: {len(features_df)}")
    print(f"Average trend mean: {features_df['trend_mean'].mean():.2f}")
    print(f"Max trend value across all: {features_df['trend_max'].max()}")
    
    # Show top 10 celebrities by trend
    print("\nTop 10 celebrities by average trend:")
    top10 = features_df.nlargest(10, 'trend_mean')[['celebrity_name', 'season', 'trend_mean', 'trend_max']]
    print(top10.to_string(index=False))
    
    return features_df


if __name__ == "__main__":
    main()
