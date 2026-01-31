#!/usr/bin/env python3
import os
import time
from typing import Dict, Optional, Tuple

import pandas as pd
import requests

try:
    from tqdm import tqdm  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    tqdm = None


WDQS_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "MCM_2026_DataTeam/1.0 (MCM_2026 project)"


def load_participants(input_csv: str) -> pd.DataFrame:
    df = pd.read_csv(input_csv)
    if "celebrity_name" not in df.columns:
        raise ValueError("Missing required column: celebrity_name")

    if "t0" in df.columns:
        t0_col = "t0"
    elif "week_start" in df.columns:
        t0_col = "week_start"
    else:
        raise ValueError("Missing required date column: t0 or week_start")

    df["t0"] = pd.to_datetime(df[t0_col], errors="coerce").dt.strftime("%Y-%m-%d")
    if "qid" not in df.columns:
        df["qid"] = pd.NA
    return df


def request_with_retries(
    session: requests.Session,
    method: str,
    url: str,
    *,
    params: Optional[Dict] = None,
    data: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: int = 60,
    max_retries: int = 5,
) -> requests.Response:
    backoff = 1
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.request(
                method,
                url,
                params=params,
                data=data,
                headers=headers,
                timeout=timeout,
            )
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                retry_after = resp.headers.get("Retry-After")
                sleep_s = backoff
                if retry_after:
                    try:
                        sleep_s = max(sleep_s, int(retry_after))
                    except ValueError:
                        pass
                time.sleep(sleep_s)
                backoff *= 2
                continue
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(backoff)
            backoff *= 2
    raise RuntimeError(f"Request failed after {max_retries} attempts: {last_exc}")


def resolve_qid_if_needed(
    df: pd.DataFrame, cache_path: str, session: requests.Session
) -> pd.DataFrame:
    cache: Dict[str, str] = {}
    if os.path.exists(cache_path):
        cache_df = pd.read_csv(cache_path)
        if "celebrity_name" in cache_df.columns and "qid" in cache_df.columns:
            for _, row in cache_df.iterrows():
                name = str(row["celebrity_name"]).strip()
                qid = str(row["qid"]).strip()
                if name and qid:
                    cache[name] = qid

    updated = False
    for idx, row in df.iterrows():
        current_qid = str(row["qid"]).strip() if pd.notna(row["qid"]) else ""
        if current_qid:
            continue
        name = str(row["celebrity_name"]).strip()
        if not name:
            continue
        if name in cache:
            df.at[idx, "qid"] = cache[name]
            continue

        params = {
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "limit": 1,
            "format": "json",
        }
        resp = request_with_retries(session, "GET", WIKIDATA_API, params=params)
        data = resp.json()
        qid = ""
        if data.get("search"):
            qid = data["search"][0].get("id", "")
        if qid:
            cache[name] = qid
            df.at[idx, "qid"] = qid
            updated = True
        else:
            df.at[idx, "qid"] = ""
            updated = True

    if updated:
        cache_items = sorted(cache.items(), key=lambda x: x[0])
        cache_df = pd.DataFrame(cache_items, columns=["celebrity_name", "qid"])
        cache_df.to_csv(cache_path, index=False)
    return df


def build_sparql(qid: str, t0_datetime: str) -> str:
    return f"""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT
  (COUNT(?stmt) AS ?awards_total)
  (SUM(IF(BOUND(?date), 1, 0)) AS ?awards_dated)
  (SUM(IF(BOUND(?date) && ?date < ?t0, 1, 0)) AS ?awards_pre_t0)
WHERE {{
  BIND(wd:{qid} AS ?person)
  BIND("{t0_datetime}"^^xsd:dateTime AS ?t0)
  ?person p:P166 ?stmt .
  ?stmt ps:P166 ?award .
  OPTIONAL {{ ?stmt pq:P585 ?date . }}
}}
""".strip()


def query_awards_counts(
    session: requests.Session, qid: str, t0_datetime: str
) -> Tuple[int, int, int]:
    sparql = build_sparql(qid, t0_datetime)
    params = {"format": "json", "query": sparql}
    resp = request_with_retries(session, "GET", WDQS_ENDPOINT, params=params)
    data = resp.json()
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return 0, 0, 0

    row = bindings[0]
    def _to_int(key: str) -> int:
        val = row.get(key, {}).get("value", "0")
        try:
            return int(float(val))
        except ValueError:
            return 0

    return _to_int("awards_total"), _to_int("awards_dated"), _to_int("awards_pre_t0")


def main() -> None:
    input_csv = os.path.join("data", "processed_with_trends.csv")
    output_dir = "wikiPageview"
    os.makedirs(output_dir, exist_ok=True)
    cache_path = os.path.join(output_dir, "qid_cache.csv")
    progress_path = os.path.join(output_dir, "results_awards_pre_t0_progress.csv")
    output_path = os.path.join(output_dir, "results_awards_pre_t0.csv")

    df = load_participants(input_csv)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    df = resolve_qid_if_needed(df, cache_path, session)

    df = df.reset_index().rename(columns={"index": "row_idx"})

    processed_rows = set()
    if os.path.exists(progress_path):
        progress_df = pd.read_csv(progress_path)
        if "row_idx" in progress_df.columns:
            processed_rows = set(
                progress_df["row_idx"].dropna().astype(int).tolist()
            )

    results = []
    award_cache: Dict[Tuple[str, str], Tuple[int, int, int]] = {}

    save_every = 20
    if tqdm is not None:
        pbar = tqdm(
            total=len(df),
            initial=len(processed_rows),
            desc="Querying awards",
        )
    else:
        pbar = None

    for row in df.itertuples(index=False):
        row_idx = int(row.row_idx)
        if row_idx in processed_rows:
            continue

        name = str(row.celebrity_name).strip()
        qid = str(row.qid).strip() if pd.notna(row.qid) else ""
        t0_date = str(row.t0).strip() if pd.notna(row.t0) else ""

        if not t0_date or t0_date == "NaT":
            awards_total = awards_dated = awards_pre_t0 = 0
            coverage = 0.0
        elif not qid:
            awards_total = awards_dated = awards_pre_t0 = 0
            coverage = 0.0
        else:
            t0_datetime = f"{t0_date}T00:00:00Z"
            key = (qid, t0_datetime)
            if key in award_cache:
                awards_total, awards_dated, awards_pre_t0 = award_cache[key]
            else:
                awards_total, awards_dated, awards_pre_t0 = query_awards_counts(
                    session, qid, t0_datetime
                )
                award_cache[key] = (awards_total, awards_dated, awards_pre_t0)
            coverage = (awards_dated / awards_total) if awards_total else 0.0

        results.append(
            {
                "row_idx": row_idx,
                "name": name,
                "t0": t0_date,
                "qid": qid,
                "awards_total": awards_total,
                "awards_dated": awards_dated,
                "awards_pre_t0": awards_pre_t0,
                "award_date_coverage": coverage,
            }
        )
        if pbar is not None:
            pbar.update(1)

        if len(results) >= save_every:
            pd.DataFrame(results).to_csv(
                progress_path,
                index=False,
                mode="a",
                header=not os.path.exists(progress_path),
            )
            results = []

    if results:
        pd.DataFrame(results).to_csv(
            progress_path,
            index=False,
            mode="a",
            header=not os.path.exists(progress_path),
        )

    if pbar is not None:
        pbar.close()

    final_df = pd.read_csv(progress_path)
    if "row_idx" in final_df.columns:
        final_df["row_idx"] = final_df["row_idx"].astype(int)
        final_df = final_df.drop_duplicates("row_idx", keep="last")
        final_df = final_df.sort_values("row_idx")
        final_df = final_df.drop(columns=["row_idx"])

    final_df.to_csv(output_path, index=False)
    print(final_df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
