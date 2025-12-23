#!/usr/bin/env python3
"""
Production Cascade ingestion script using the export ZIP endpoint.

Usage:
  python3 scripts/cascade_ingest.py --export-url "<zip url>" \
    --output-prefix "data/raw/cascade/loan_tapes/<yearmonth>/loan_tape_full"

Secrets:
  - CASCADE_SESSION_COOKIE: "Bearer ..." token for the export API (OAuth session)
  - CASCADE_COOKIE_NAME (optional): cookie name if using cookie auth
"""

import argparse
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Tuple

import backoff
import pandas as pd
import requests
from python.ingest.transform import canonicalize_loan_tape

LOG = logging.getLogger("cascade_ingest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

RUN_ID = uuid.uuid4().hex
MAX_RETRIES = 3
DOWNLOAD_TIMEOUT = 120
AUDIT_DIR = Path("data/audit/runs")
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def make_output_paths(prefix: str) -> Tuple[Path, Path, Path]:
    folder = Path(prefix).parent
    folder.mkdir(parents=True, exist_ok=True)
    csv_path = Path(f"{prefix}.csv")
    parquet_path = Path(f"{prefix}.parquet")
    zip_path = Path(f"{prefix}.zip")
    return csv_path, parquet_path, zip_path


@backoff.on_exception(backoff.expo, (requests.RequestException,), max_time=180)
def fetch_export(export_url: str, headers: dict) -> requests.Response:
    LOG.info("Requesting Cascade export from %s", export_url)
    return requests.get(export_url, headers=headers, stream=True, timeout=DOWNLOAD_TIMEOUT)


def save_to_path(response: requests.Response, path: Path):
    with path.open("wb") as fh:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                fh.write(chunk)


def read_dataframe_from_zip(zip_path: Path) -> pd.DataFrame:
    from zipfile import ZipFile

    valid_ext = (".csv", ".xls", ".xlsx")
    with ZipFile(zip_path, "r") as zf:
        candidates = [name for name in zf.namelist() if name.lower().endswith(valid_ext)]
        if not candidates:
            raise RuntimeError("ZIP archive does not contain CSV/XLS/XLSX files")
        target = candidates[0]
        LOG.info("Extracting %s from %s", target, zip_path)
        with zf.open(target) as handle:
            if target.lower().endswith(".csv"):
                return pd.read_csv(handle)
            return pd.read_excel(handle)


def write_run_manifest(
    export_url: str,
    output_prefix: str,
    csv_path: Path,
    parquet_path: Path,
    zip_path: Path,
    secrets_hash: str,
):
    manifest = {
        "run_id": RUN_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "export_url": export_url,
        "output_prefix": output_prefix,
        "csv_path": str(csv_path),
        "parquet_path": str(parquet_path),
        "zip_path": str(zip_path),
        "secrets_hash": secrets_hash,
    }
    manifest_path = AUDIT_DIR / f"cascade_ingest_run_{RUN_ID}.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    LOG.info("Wrote audit manifest %s", manifest_path)


def run_cascade_ingest(export_url: str, auth_token: str, output_prefix: str):
    csv_path, parquet_path, zip_path = make_output_paths(output_prefix)
    LOG.info("Starting run_id=%s", RUN_ID)
    cookie_name = os.getenv("CASCADE_COOKIE_NAME")
    if cookie_name:
        headers = {"Cookie": f"{cookie_name}={auth_token}"}
    else:
        headers = {"Authorization": auth_token}

    response = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = fetch_export(export_url, headers=headers)
            response.raise_for_status()
            break
        except Exception as exc:
            LOG.warning("Attempt %s failed: %s", attempt, exc)
            if attempt == MAX_RETRIES:
                raise
        finally:
            if response is not None and response.status_code >= 400:
                response.close()

    if response is None:
        raise RuntimeError("Failed to download Cascade export after retries")
    content_type = (response.headers.get("content-type") or "").lower()
    is_zip = "zip" in content_type or export_url.lower().endswith(".zip")
    if is_zip:
        save_to_path(response, zip_path)
        LOG.info("Saved download to %s", zip_path)
        df = read_dataframe_from_zip(zip_path)
    else:
        save_to_path(response, csv_path)
        LOG.info("Saved CSV download to %s", csv_path)
        df = pd.read_csv(csv_path)
    response.close()

    df = canonicalize_loan_tape(df)
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    LOG.info("Saved %d rows to %s and %s", len(df), csv_path, parquet_path)
    write_run_manifest(export_url, output_prefix, csv_path, parquet_path, zip_path, hashlib.sha256(auth_token.encode()).hexdigest())


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-url", required=True)
    parser.add_argument("--output-prefix", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    auth_token = os.getenv("CASCADE_SESSION_COOKIE")
    if not auth_token:
        raise RuntimeError("CASCADE_SESSION_COOKIE secret missing")

    run_cascade_ingest(args.export_url, auth_token, args.output_prefix)


if __name__ == "__main__":
    main()
