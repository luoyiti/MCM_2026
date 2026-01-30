#!/usr/bin/env python3
"""Compute 5-year Wikipedia pageview features for DWTS celebrities by season."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import time
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import numpy as np
import requests
from urllib.parse import quote


WIKI_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
PAGEVIEWS_URL = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "{project}/{access}/{agent}/{article}/{granularity}/{start}/{end}"
)

DEFAULT_SEARCH_LIMIT = 5
SLEEP_RANGE = (0.1, 0.2)
EARLIEST_PAGEVIEWS_DATE = datetime(2015, 7, 1).date()


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def polite_sleep() -> None:
    time.sleep(random.uniform(*SLEEP_RANGE))


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logging.warning("Failed to load cache %s: %s", path, exc)
        return None


def save_json(path: str, data: Dict[str, Any]) -> None:
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True)
    os.replace(tmp_path, path)


def hash_key(parts: Iterable[str]) -> str:
    raw = "|".join(parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def request_json(
    session: requests.Session,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    cache_path: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
    if cache_path and os.path.exists(cache_path):
        cached = load_json(cache_path)
        if cached is not None:
            return cached, cached.get("_status_code")

    try:
        resp = session.get(url, params=params, timeout=20)
    except Exception as exc:
        logging.error("Request failed: %s params=%s error=%s", url, params, exc)
        return None, None

    status_code = resp.status_code
    try:
        payload = resp.json()
    except Exception:
        payload = {"_error": "invalid_json"}

    payload["_status_code"] = status_code

    if cache_path and status_code in (200, 404):
        ensure_dir(os.path.dirname(cache_path))
        save_json(cache_path, payload)

    polite_sleep()
    return payload, status_code


def find_date_column(columns: List[str]) -> str:
    lower = {c.lower(): c for c in columns}
    for key in ("premiere_date", "premiere", "start_date", "start"):
        if key in lower:
            return lower[key]
    for c in columns:
        if "premiere" in c.lower():
            return c
    for c in columns:
        if "start" in c.lower():
            return c
    raise ValueError("No premiere/start date column found in season dates file")


def find_celebrity_column(columns: List[str]) -> str:
    lower = {c.lower(): c for c in columns}
    if "celebrity_name" in lower:
        return lower["celebrity_name"]
    for c in columns:
        lc = c.lower()
        if "celebrity" in lc and "name" in lc:
            return c
    for c in columns:
        if "name" in c.lower():
            return c
    raise ValueError("No celebrity name column found in DWTS data file")


def normalize_article_title(title: str) -> str:
    return title.replace(" ", "_")


def resolve_wikipedia_title(
    session: requests.Session,
    name: str,
    title_cache: Dict[str, Dict[str, Any]],
    search_limit: int,
    cache_path: str,
) -> Tuple[Optional[str], str]:
    if name in title_cache:
        cached = title_cache[name]
        return cached.get("article"), cached.get("status", "unknown")

    params = {
        "action": "query",
        "list": "search",
        "srsearch": name,
        "srlimit": search_limit,
        "format": "json",
        "utf8": 1,
    }

    search_payload, status_code = request_json(session, WIKI_SEARCH_URL, params=params)
    if not search_payload or status_code != 200:
        logging.error("Search failed for %s (status=%s)", name, status_code)
        return None, "title_error"

    results = search_payload.get("query", {}).get("search", [])
    if not results:
        title_cache[name] = {"article": None, "status": "no_page"}
        save_json(cache_path, title_cache)
        return None, "no_page"

    disambig_only = True
    for item in results:
        title = item.get("title")
        if not title:
            continue
        article = normalize_article_title(title)
        summary_url = WIKI_SUMMARY_URL.format(title=quote(article, safe=""))
        summary_payload, summary_status = request_json(session, summary_url)
        if summary_status != 200 or not summary_payload:
            continue
        page_type = summary_payload.get("type")
        if page_type == "disambiguation":
            continue
        disambig_only = False
        title_cache[name] = {"article": article, "status": "ok"}
        save_json(cache_path, title_cache)
        return article, "ok"

    status = "disambiguation_only" if disambig_only else "no_page"
    title_cache[name] = {"article": None, "status": status}
    save_json(cache_path, title_cache)
    return None, status


def fetch_pageviews(
    session: requests.Session,
    article: str,
    start: str,
    end: str,
    cache_dir: str,
    project: str = "en.wikipedia.org",
    access: str = "all-access",
    agent: str = "user",
    granularity: str = "daily",
) -> Tuple[Optional[Dict[str, Any]], str]:
    key = hash_key([project, access, agent, article, granularity, start, end])
    cache_path = os.path.join(cache_dir, "pageviews", f"{key}.json")

    url = PAGEVIEWS_URL.format(
        project=project,
        access=access,
        agent=agent,
        article=quote(article, safe=""),
        granularity=granularity,
        start=start,
        end=end,
    )

    payload, status_code = request_json(session, url, cache_path=cache_path)
    if payload is None:
        return None, "pageviews_error"
    if status_code == 404:
        return payload, "pageviews_404"
    if status_code != 200:
        return payload, "pageviews_error"
    items = payload.get("items")
    if not items:
        return payload, "pageviews_empty"
    return payload, "ok"


def compute_metrics(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    views = [int(item.get("views", 0)) for item in items]
    arr = np.array(views, dtype=float)
    metrics = {
        "wiki_mean_5y": float(np.mean(arr)) if arr.size else np.nan,
        "wiki_sum_5y": float(np.sum(arr)) if arr.size else np.nan,
        "wiki_median_5y": float(np.median(arr)) if arr.size else np.nan,
        "wiki_std_5y": float(np.std(arr)) if arr.size else np.nan,
        "wiki_p95_5y": float(np.percentile(arr, 95)) if arr.size else np.nan,
        "wiki_max_5y": float(np.max(arr)) if arr.size else np.nan,
        "wiki_nonzero_days_5y": int(np.sum(arr > 0)) if arr.size else np.nan,
        "wiki_days_5y": int(arr.size) if arr.size else np.nan,
    }
    return metrics


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "DWTS-WikiPageviews/1.0 (MCM 2026 research)",
            "Accept": "application/json",
        }
    )
    return session


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute 5-year Wikipedia pageview metrics for DWTS celebrities."
    )
    parser.add_argument(
        "--season-dates",
        default="data/DWTS_season_dates.csv",
        help="Path to DWTS season dates CSV",
    )
    parser.add_argument(
        "--dwts-data",
        default="data/2026_MCM_Problem_C_Data.csv",
        help="Path to DWTS data CSV",
    )
    parser.add_argument(
        "--output",
        default="wikiPageview/dwts_wiki_pageviews_5y.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--search-limit",
        type=int,
        default=DEFAULT_SEARCH_LIMIT,
        help="Number of Wikipedia search results to try",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    setup_logging(args.verbose)

    if not os.path.exists(args.season_dates):
        raise FileNotFoundError(args.season_dates)
    if not os.path.exists(args.dwts_data):
        raise FileNotFoundError(args.dwts_data)

    ensure_dir(os.path.dirname(args.output))
    cache_dir = os.path.join(os.path.dirname(args.output), "cache")
    ensure_dir(cache_dir)

    dates_df = pd.read_csv(args.season_dates)
    date_col = find_date_column(list(dates_df.columns))
    logging.info("Using season date column: %s", date_col)

    dates_df = dates_df[["season", date_col]].copy()
    dates_df[date_col] = pd.to_datetime(dates_df[date_col], errors="coerce")

    data_df = pd.read_csv(args.dwts_data)
    celeb_col = find_celebrity_column(list(data_df.columns))
    logging.info("Using celebrity name column: %s", celeb_col)

    merged = data_df.merge(dates_df, on="season", how="left")
    merged.rename(columns={celeb_col: "celebrity_name", date_col: "premiere_date"}, inplace=True)

    title_cache_path = os.path.join(cache_dir, "title_cache.json")
    title_cache = load_json(title_cache_path) or {}

    session = build_session()

    results = []
    result_cache: Dict[Tuple[str, Any], Dict[str, Any]] = {}

    for idx, row in merged.iterrows():
        name = row.get("celebrity_name")
        season = row.get("season")
        premiere = row.get("premiere_date")
        if pd.isna(name) or name is None:
            record = {
                "celebrity_name": name,
                "season": season,
                "premiere_date": premiere,
                "window_start": None,
                "window_end": None,
                "wiki_article": None,
                "wiki_status": "missing_name",
            }
            result_cache[(name, season)] = record
            results.append(record)
            continue

        name = str(name).strip()
        cache_key = (name, season)
        if cache_key in result_cache:
            results.append(result_cache[cache_key])
            continue

        record = {
            "celebrity_name": name,
            "season": season,
            "premiere_date": premiere,
            "window_start": None,
            "window_end": None,
            "wiki_article": None,
            "wiki_status": None,
        }

        if pd.isna(premiere) or premiere is None:
            record["wiki_status"] = "missing_premiere_date"
            result_cache[cache_key] = record
            results.append(record)
            continue
        premiere_date = pd.to_datetime(premiere).normalize()
        window_start = (premiere_date - pd.DateOffset(years=5)).date()
        window_end = (premiere_date - pd.Timedelta(days=1)).date()

        record["premiere_date"] = premiere_date.date().isoformat()
        record["window_start"] = window_start.isoformat()
        record["window_end"] = window_end.isoformat()

        if window_end < window_start:
            record["wiki_status"] = "invalid_window"
            result_cache[cache_key] = record
            results.append(record)
            continue

        article, title_status = resolve_wikipedia_title(
            session,
            name,
            title_cache,
            args.search_limit,
            title_cache_path,
        )
        record["wiki_article"] = article
        if title_status != "ok" or not article:
            record["wiki_status"] = title_status
            result_cache[cache_key] = record
            results.append(record)
            continue

        if window_end < EARLIEST_PAGEVIEWS_DATE:
            record["wiki_status"] = "pageviews_unavailable_pre20150701"
            result_cache[cache_key] = record
            results.append(record)
            continue

        if window_start < EARLIEST_PAGEVIEWS_DATE:
            record["wiki_status"] = "pageviews_partial_unavailable_pre20150701"
            result_cache[cache_key] = record
            results.append(record)
            continue

        start_str = window_start.strftime("%Y%m%d")
        end_str = window_end.strftime("%Y%m%d")

        payload, pv_status = fetch_pageviews(
            session,
            article,
            start_str,
            end_str,
            cache_dir,
        )

        if pv_status != "ok":
            record["wiki_status"] = pv_status
            result_cache[cache_key] = record
            results.append(record)
            continue

        items = payload.get("items", []) if payload else []
        metrics = compute_metrics(items)
        record.update(metrics)
        record["wiki_status"] = "ok"

        result_cache[cache_key] = record
        results.append(record)

        if (idx + 1) % 50 == 0:
            logging.info("Processed %s rows", idx + 1)

    out_df = pd.DataFrame(results)
    out_df.to_csv(args.output, index=False)

    logging.info("Saved output to %s", args.output)


if __name__ == "__main__":
    main()
