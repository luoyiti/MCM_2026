#!/usr/bin/env python3
import os

import pandas as pd


def compute_t0(df: pd.DataFrame) -> pd.Series:
    if "t0" in df.columns:
        raw = df["t0"]
    elif "week_start" in df.columns:
        raw = df["week_start"]
    else:
        raise ValueError("Missing t0 and week_start columns in processed file")
    return pd.to_datetime(raw, errors="coerce").dt.strftime("%Y-%m-%d")


def main() -> None:
    processed_path = os.path.join("data", "processed_with_trends.csv")
    progress_path = os.path.join("wikiPageview", "results_awards_pre_t0_progress.csv")
    results_path = os.path.join("wikiPageview", "results_awards_pre_t0.csv")

    if not os.path.exists(processed_path):
        raise FileNotFoundError(processed_path)
    if not os.path.exists(progress_path):
        raise FileNotFoundError(progress_path)

    processed = pd.read_csv(processed_path)
    processed = processed.reset_index().rename(columns={"index": "row_idx"})
    processed["t0"] = compute_t0(processed)

    progress = pd.read_csv(progress_path)
    if "row_idx" not in progress.columns:
        raise ValueError("Missing row_idx in progress file")

    merged = progress.merge(
        processed[["row_idx", "t0", "week_exists"]],
        on="row_idx",
        how="left",
        suffixes=("", "_proc"),
    )
    merged["t0"] = merged["t0_proc"]
    merged = merged.drop(columns=["t0_proc"])

    missing_t0 = merged["t0"].isna()
    merged.loc[missing_t0, [
        "awards_total",
        "awards_dated",
        "awards_pre_t0",
        "award_date_coverage",
    ]] = pd.NA

    # Clean results: remove rows with missing t0 (these are week_exists == False).
    cleaned = merged[~missing_t0].copy()
    cleaned = cleaned[
        [
            "name",
            "t0",
            "qid",
            "awards_total",
            "awards_dated",
            "awards_pre_t0",
            "award_date_coverage",
        ]
    ]
    cleaned.to_csv(results_path, index=False)

    # Merge awards into processed file (keep all rows).
    awards_cols = [
        "qid",
        "awards_total",
        "awards_dated",
        "awards_pre_t0",
        "award_date_coverage",
    ]
    awards = merged[["row_idx"] + awards_cols].copy()

    # Drop existing columns to avoid duplication, then merge.
    drop_cols = [c for c in awards_cols if c in processed.columns]
    processed_out = processed.drop(columns=drop_cols)
    processed_out = processed_out.merge(awards, on="row_idx", how="left")
    processed_out = processed_out.drop(columns=["row_idx"])
    processed_out.to_csv(processed_path, index=False)

    print("Fixed results saved to:", results_path)
    print("Updated processed file saved to:", processed_path)
    print("Rows in cleaned results:", len(cleaned))
    print("Rows in processed:", len(processed_out))
    print("Missing t0 rows (kept in processed, removed in results):", int(missing_t0.sum()))


if __name__ == "__main__":
    main()
