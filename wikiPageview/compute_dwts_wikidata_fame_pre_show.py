#!/usr/bin/env python3
"""Compute pre-show Wikidata structural fame metrics for DWTS celebrities by season."""

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

import numpy as np
import pandas as pd
import requests


WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
SPARQL_URL = "https://query.wikidata.org/sparql"
DEFAULT_SEARCH_LIMIT = 5
SLEEP_RANGE = (0.1, 0.2)
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 1.5
SPARQL_RETRY_ATTEMPTS = 2
SPARQL_TIMEOUT = 30


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
    headers: Optional[Dict[str, str]] = None,
    cache_path: Optional[str] = None,
    ok_statuses: Tuple[int, ...] = (200, 404),
    timeout: int = 25,
    retry_attempts: int = RETRY_ATTEMPTS,
    cache_on_error: bool = False,
) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
    if cache_path and os.path.exists(cache_path):
        cached = load_json(cache_path)
        if cached is not None:
            return cached, cached.get("_status_code")

    last_error: Optional[str] = None
    for attempt in range(1, retry_attempts + 1):
        try:
            resp = session.get(url, params=params, headers=headers, timeout=timeout)
            status_code = resp.status_code
            try:
                payload = resp.json()
            except Exception:
                payload = {"_error": "invalid_json"}
            payload["_status_code"] = status_code

            if cache_path and status_code in ok_statuses:
                ensure_dir(os.path.dirname(cache_path))
                save_json(cache_path, payload)

            polite_sleep()
            return payload, status_code
        except Exception as exc:
            last_error = str(exc)
            logging.warning("Request attempt %s failed: %s", attempt, exc)
            time.sleep(RETRY_BACKOFF ** (attempt - 1))

    logging.error("Request failed after retries: %s params=%s error=%s", url, params, last_error)
    if cache_path and cache_on_error:
        ensure_dir(os.path.dirname(cache_path))
        save_json(cache_path, {"_status_code": None, "_error": last_error})
    return None, None


def request_sparql(
    session: requests.Session,
    query: str,
    cache_path: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
    headers = {
        "Accept": "application/sparql-results+json",
    }
    params = {"query": query, "format": "json"}
    return request_json(
        session,
        SPARQL_URL,
        params=params,
        headers=headers,
        cache_path=cache_path,
        timeout=SPARQL_TIMEOUT,
        retry_attempts=SPARQL_RETRY_ATTEMPTS,
        cache_on_error=True,
    )


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


def find_industry_column(columns: List[str]) -> Optional[str]:
    lower = {c.lower(): c for c in columns}
    if "celebrity_industry" in lower:
        return lower["celebrity_industry"]
    if "industry" in lower:
        return lower["industry"]
    for c in columns:
        if "industry" in c.lower():
            return c
    return None


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "DWTS-Wikidata-Fame/1.0 (MCM 2026 research)",
            "Accept": "application/json",
        }
    )
    return session


def search_wikidata_candidates(
    session: requests.Session,
    name: str,
    search_limit: int,
    cache_dir: str,
) -> List[Dict[str, Any]]:
    key = hash_key(["search", name, str(search_limit)])
    cache_path = os.path.join(cache_dir, "title_cache.json")
    cache = load_json(cache_path) or {}
    if key in cache:
        return cache[key].get("results", [])

    params = {
        "action": "wbsearchentities",
        "search": name,
        "language": "en",
        "format": "json",
        "limit": search_limit,
    }
    payload, status = request_json(session, WIKIDATA_API_URL, params=params)
    results = payload.get("search", []) if payload and status == 200 else []
    cache[key] = {"results": results, "status": status}
    save_json(cache_path, cache)
    return results


def is_human_qid(
    session: requests.Session,
    qid: str,
    cache_dir: str,
) -> Tuple[Optional[bool], str]:
    cache_path = os.path.join(cache_dir, "qid_claims_cache.json")
    cache = load_json(cache_path) or {}
    if qid in cache:
        return cache[qid].get("is_human"), cache[qid].get("status", "cached")

    params = {
        "action": "wbgetentities",
        "ids": qid,
        "props": "claims",
        "format": "json",
    }
    payload, status = request_json(session, WIKIDATA_API_URL, params=params)
    if not payload or status != 200:
        cache[qid] = {"is_human": None, "status": "qid_error"}
        save_json(cache_path, cache)
        return None, "qid_error"

    entity = payload.get("entities", {}).get(qid, {})
    claims = entity.get("claims", {})
    p31_claims = claims.get("P31", [])

    is_human = False
    for claim in p31_claims:
        mainsnak = claim.get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})
        value = datavalue.get("value", {})
        if isinstance(value, dict) and value.get("id") == "Q5":
            is_human = True
            break

    cache[qid] = {"is_human": is_human, "status": "ok"}
    save_json(cache_path, cache)
    return is_human, "ok"


def resolve_qid(
    session: requests.Session,
    name: str,
    search_limit: int,
    cache_dir: str,
    qid_cache_path: str,
) -> Tuple[Optional[str], str]:
    qid_cache = load_json(qid_cache_path) or {}
    if name in qid_cache:
        cached = qid_cache[name]
        return cached.get("qid"), cached.get("status", "cached")

    candidates = search_wikidata_candidates(session, name, search_limit, cache_dir)
    if not candidates:
        qid_cache[name] = {"qid": None, "status": "no_qid"}
        save_json(qid_cache_path, qid_cache)
        return None, "no_qid"

    for cand in candidates:
        qid = cand.get("id")
        if not qid:
            continue
        is_human, human_status = is_human_qid(session, qid, cache_dir)
        if human_status != "ok":
            continue
        if is_human:
            qid_cache[name] = {"qid": qid, "status": "ok"}
            save_json(qid_cache_path, qid_cache)
            return qid, "ok"

    qid_cache[name] = {"qid": None, "status": "not_human"}
    save_json(qid_cache_path, qid_cache)
    return None, "not_human"


def build_sparql_query(qid: str, cutoff_date: str) -> str:
    return f"""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?sitelinks_count ?awards_total ?awards_pre_show ?awards_dated_count ?occupation_count ?birth_date WHERE {{
  BIND(wd:{qid} as ?person)
  OPTIONAL {{ ?person wikibase:sitelinks ?sitelinks_count. }}
  OPTIONAL {{ ?person wdt:P569 ?birth_date. }}
  OPTIONAL {{
    SELECT ?person (COUNT(DISTINCT ?occ) AS ?occupation_count) WHERE {{
      BIND(wd:{qid} as ?person)
      OPTIONAL {{ ?person wdt:P106 ?occ. }}
    }} GROUP BY ?person
  }}
  OPTIONAL {{
    SELECT ?person
      (COUNT(?awardStmt) AS ?awards_total)
      (SUM(IF(BOUND(?award_time), 1, 0)) AS ?awards_dated_count)
      (SUM(IF(BOUND(?awardStmt) && (!BOUND(?award_time) || xsd:date(?award_time) < ?cutoff), 1, 0)) AS ?awards_pre_show)
    WHERE {{
      BIND(wd:{qid} as ?person)
      OPTIONAL {{ ?person p:P166 ?awardStmt. }}
      OPTIONAL {{ ?awardStmt pq:P585 ?award_time. }}
      BIND(xsd:date(\"{cutoff_date}\") AS ?cutoff)
    }} GROUP BY ?person
  }}
}}
"""


def parse_sparql_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    bindings = payload.get("results", {}).get("bindings", []) if payload else []
    if not bindings:
        return {}

    row = bindings[0]
    def get_int(key: str) -> Optional[int]:
        val = row.get(key, {}).get("value")
        return int(val) if val is not None else None

    def get_str(key: str) -> Optional[str]:
        return row.get(key, {}).get("value")

    return {
        "sitelinks_count": get_int("sitelinks_count"),
        "awards_total": get_int("awards_total"),
        "awards_pre_show": get_int("awards_pre_show"),
        "awards_dated_count": get_int("awards_dated_count"),
        "occupation_count": get_int("occupation_count"),
        "birth_date": get_str("birth_date"),
    }


def fetch_wikidata_metrics(
    session: requests.Session,
    qid: str,
    premiere_date: datetime,
    cache_dir: str,
) -> Tuple[Dict[str, Any], str]:
    cutoff = premiere_date.date().isoformat()
    key = hash_key(["sparql", qid, cutoff])
    cache_path = os.path.join(cache_dir, "sparql", f"{key}.json")
    query = build_sparql_query(qid, cutoff)

    payload, status = request_sparql(session, query, cache_path=cache_path)
    if not payload or status != 200:
        return {}, "sparql_error"

    metrics = parse_sparql_metrics(payload)
    return metrics, "ok"


def compute_fame_raw(sitelinks_count: Optional[int], awards_pre_show: Optional[int]) -> float:
    s = sitelinks_count if sitelinks_count is not None else 0
    a = awards_pre_show if awards_pre_show is not None else 0
    return float(np.log1p(s) + 0.7 * np.log1p(a))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute pre-show Wikidata structural fame metrics for DWTS celebrities."
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
        default="/mnt/data/DWTS_wikidata_fame_pre_show.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--search-limit",
        type=int,
        default=DEFAULT_SEARCH_LIMIT,
        help="Number of Wikidata search results to try",
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

    output_dir = os.path.dirname(args.output) or "."
    ensure_dir(output_dir)

    cache_dir = os.path.join("wikiPageview", "cache")
    ensure_dir(cache_dir)

    dates_df = pd.read_csv(args.season_dates)
    date_col = find_date_column(list(dates_df.columns))
    logging.info("Using season date column: %s", date_col)

    dates_df = dates_df[["season", date_col]].copy()
    dates_df[date_col] = pd.to_datetime(dates_df[date_col], errors="coerce")

    data_df = pd.read_csv(args.dwts_data)
    celeb_col = find_celebrity_column(list(data_df.columns))
    industry_col = find_industry_column(list(data_df.columns))
    logging.info("Using celebrity name column: %s", celeb_col)
    if industry_col:
        logging.info("Using industry column: %s", industry_col)

    merged = data_df.merge(dates_df, on="season", how="left")
    merged.rename(columns={celeb_col: "celebrity_name", date_col: "premiere_date"}, inplace=True)

    session = build_session()

    qid_cache_path = os.path.join(cache_dir, "qid_cache.json")

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
                "qid": None,
                "sitelinks_count": None,
                "awards_total": None,
                "awards_pre_show": None,
                "awards_dated_count": None,
                "occupation_count": None,
                "birth_date": None,
                "fame_structural_raw": None,
                "status": "missing_name",
            }
            if industry_col:
                record["industry"] = row.get(industry_col)
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
            "premiere_date": None,
            "qid": None,
            "sitelinks_count": None,
            "awards_total": None,
            "awards_pre_show": None,
            "awards_dated_count": None,
            "occupation_count": None,
            "birth_date": None,
            "fame_structural_raw": None,
            "status": None,
        }
        if industry_col:
            record["industry"] = row.get(industry_col)

        if pd.isna(premiere) or premiere is None:
            record["status"] = "missing_premiere_date"
            result_cache[cache_key] = record
            results.append(record)
            continue

        premiere_date = pd.to_datetime(premiere)
        if pd.isna(premiere_date):
            record["status"] = "invalid_premiere_date"
            result_cache[cache_key] = record
            results.append(record)
            continue

        record["premiere_date"] = premiere_date.date().isoformat()

        qid, qid_status = resolve_qid(
            session,
            name,
            args.search_limit,
            cache_dir,
            qid_cache_path,
        )
        record["qid"] = qid
        if qid_status != "ok" or not qid:
            record["status"] = qid_status
            result_cache[cache_key] = record
            results.append(record)
            continue

        metrics, metric_status = fetch_wikidata_metrics(
            session,
            qid,
            premiere_date,
            cache_dir,
        )
        if metric_status != "ok":
            record["status"] = metric_status
            result_cache[cache_key] = record
            results.append(record)
            continue

        record.update(metrics)
        record["fame_structural_raw"] = compute_fame_raw(
            record.get("sitelinks_count"),
            record.get("awards_pre_show"),
        )
        record["status"] = "ok"

        result_cache[cache_key] = record
        results.append(record)

        if (idx + 1) % 50 == 0:
            logging.info("Processed %s rows", idx + 1)

    out_df = pd.DataFrame(results)

    if industry_col and "industry" in out_df.columns:
        out_df["fame_structural_z_by_industry"] = np.nan
        for industry, sub_df in out_df.groupby("industry"):
            if industry is None or (isinstance(industry, float) and np.isnan(industry)):
                continue
            vals = sub_df["fame_structural_raw"].astype(float)
            mean = vals.mean()
            std = vals.std(ddof=0)
            if std == 0 or np.isnan(std):
                continue
            z = (vals - mean) / std
            out_df.loc[sub_df.index, "fame_structural_z_by_industry"] = z

    out_df.to_csv(args.output, index=False)
    logging.info("Saved output to %s", args.output)


if __name__ == "__main__":
    main()
