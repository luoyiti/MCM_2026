#!/usr/bin/env python3
import os

import pandas as pd


def pick_mode(series: pd.Series) -> str:
    vals = series.dropna().astype(str)
    vals = vals[vals.str.strip() != ""]
    if vals.empty:
        return "QID_NOT_FOUND"
    return vals.mode().iat[0]


def main() -> None:
    results_path = os.path.join("wikiPageview", "results_awards_pre_t0.csv")
    if not os.path.exists(results_path):
        raise FileNotFoundError(results_path)

    df = pd.read_csv(results_path)
    if "name" not in df.columns or "t0" not in df.columns:
        raise ValueError("Missing required columns: name or t0")

    # Ensure t0 is comparable and pick latest per person
    df["t0"] = pd.to_datetime(df["t0"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df[df["t0"].notna()].copy()

    # Fill qid by mode per name, mark remaining missing
    qid_map = df.groupby("name")["qid"].apply(pick_mode)
    df = df.merge(qid_map.rename("qid_fixed"), on="name", how="left")
    df["qid"] = df["qid_fixed"]
    df = df.drop(columns=["qid_fixed"])

    # Select the latest t0 row per name (latest participation)
    df = df.sort_values(["name", "t0"])
    latest = df.groupby("name", as_index=False).tail(1).copy()

    # Recompute coverage to avoid any inconsistencies
    latest.loc[:, "award_date_coverage"] = latest.apply(
        lambda r: (r["awards_dated"] / r["awards_total"]) if r["awards_total"] else 0.0,
        axis=1,
    )

    # Ensure no missing values in output (qid already handled)
    for col in ["awards_total", "awards_dated", "awards_pre_t0", "award_date_coverage"]:
        latest.loc[:, col] = latest[col].fillna(0)

    # Keep columns in the original order
    latest = latest[
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

    latest.to_csv(results_path, index=False)
    print("Saved unique-name results to:", results_path)
    print("Rows:", len(latest), "Unique names:", latest["name"].nunique())
    print("Missing values:\n", latest.isna().sum().to_string())


if __name__ == "__main__":
    main()
