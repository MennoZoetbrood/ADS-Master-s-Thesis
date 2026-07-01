#!/usr/bin/env python3
"""
Harvest the last 10 years of EUVD vulnerabilities into a CSV file,
preserving all original fields from the API response.

API docs:  https://euvd.enisa.europa.eu/apidoc
Endpoint:  https://euvdservices.enisa.europa.eu/api/search

Notes on storage:
  * One row per vulnerability.
  * Nested fields (enisaIdVendor, enisaIdProduct) are stored as JSON
    strings so no information is lost. Recover them with:
        df["enisaIdProduct"].apply(json.loads)
  * Multi-valued string fields (aliases, references) are kept as-is
    with the API's native '\\n' separator.
  * Dates are stored raw ("Apr 15, 2025, 8:30:58 PM"). Parse on load:
        pd.to_datetime(df["datePublished"])
"""

from __future__ import annotations

import csv
import json
import time
from datetime import date
from pathlib import Path

import requests

# --- Configuration ------------------------------------------------------------
BASE_URL = "https://euvdservices.enisa.europa.eu/api/search"
PAGE_SIZE = 100                          # API maximum
REQUEST_DELAY = 1.0                      # seconds between successful requests
MAX_RETRIES = 5
RETRY_BACKOFF = 2.0                      # seconds; doubles each retry

TODAY = date.today()
FROM_DATE = TODAY.replace(year=TODAY.year - 10)   # 10-year window
OUT_PATH = Path(__file__).parent / "10_years_euvd.csv"

# Output columns in the order requested.
CSV_COLUMNS = [
    "id",
    "description",
    "datePublished",
    "dateUpdated",
    "baseScoreVersion",
    "exploitedSince",
    "baseScoreVector",
    "epss",
    "assigner",
    "aliases",
    "enisaIdVendor",
    "references",
    "enisaIdProduct",
    "baseScore",
    "enisaUuid",
]

# Fields that arrive as lists/dicts and should be JSON-encoded for CSV.
JSON_FIELDS = {"enisaIdVendor", "enisaIdProduct"}


# --- Row construction ---------------------------------------------------------
def row_from_item(item: dict) -> dict:
    """Map one EUVD JSON object to a flat dict matching CSV_COLUMNS."""
    row: dict[str, object] = {}
    for col in CSV_COLUMNS:
        value = item.get(col, "")
        if col in JSON_FIELDS:
            # Preserve full nested structure as a JSON string.
            # Default to [] when the field is missing or null.
            row[col] = json.dumps(value if value else [], ensure_ascii=False)
        elif isinstance(value, str):
            # Strip stray \r so csv.writer doesn't get confused.
            row[col] = value.replace("\r", " ")
        else:
            row[col] = value
    return row


# --- HTTP ---------------------------------------------------------------------
def fetch_page(session: requests.Session, page: int) -> dict:
    """Fetch one page; retry on transient errors."""
    params = {
        "fromDate": FROM_DATE.isoformat(),
        "toDate": TODAY.isoformat(),
        "page": page,
        "size": PAGE_SIZE,
    }
    delay = RETRY_BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.get(BASE_URL, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                print(f"  page {page}: HTTP {r.status_code}; "
                      f"retrying in {delay:.0f}s ({attempt}/{MAX_RETRIES})")
                time.sleep(delay)
                delay *= 2
                continue
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"  page {page}: {e!r}; "
                  f"retrying in {delay:.0f}s ({attempt}/{MAX_RETRIES})")
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Gave up on page {page} after {MAX_RETRIES} attempts")


# --- Main loop ----------------------------------------------------------------
def harvest() -> None:
    session = requests.Session()
    session.headers.update({"accept": "application/json"})

    print(f"Querying EUVD from {FROM_DATE} to {TODAY}...")
    first = fetch_page(session, 0)
    total = first.get("total", 0)
    pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    est_minutes = pages * REQUEST_DELAY / 60
    print(f"  total matching records: {total:,}")
    print(f"  pages to fetch:         {pages:,}")
    print(f"  estimated runtime:      ~{est_minutes:.1f} minutes")
    print(f"  output file:            {OUT_PATH.resolve()}")
    print()

    written = 0
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()

        for item in first.get("items", []):
            writer.writerow(row_from_item(item))
            written += 1

        for p in range(1, pages):
            time.sleep(REQUEST_DELAY)
            data = fetch_page(session, p)
            for item in data.get("items", []):
                writer.writerow(row_from_item(item))
                written += 1
            if p % 10 == 0 or p == pages - 1:
                pct = 100 * (p + 1) / pages
                print(f"  page {p:>5}/{pages - 1}  "
                      f"({written:>7,} records, {pct:5.1f}%)")

    print()
    print(f"Done. Wrote {written:,} records to {OUT_PATH.resolve()}")


if __name__ == "__main__":
    harvest()
