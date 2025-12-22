#!/usr/bin/env python3
"""
Production Cascade ingestion script.

Usage: python3 scripts/cascade_ingest.py --export-url "https://app.cascadedebt.com/analytics/..." \
    --output-prefix data/raw/cascade/loan_tapes/$(date +%Y%m)/loan_tape_full

Secrets required (GH Actions set in repo secrets):
- CASCADE_SESSION_COOKIE (string)   # secure, read-only user session cookie
- CASCADE_USER_AGENT (optional)     # recommended user-agent string
"""

import argparse
import hashlib
import io
import json
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from python.ingest.cascade_client import CascadeClient
from python.ingest.transform import canonicalize_loan_tape

LOG = logging.getLogger("cascade_ingest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

RUN_ID = uuid.uuid4().hex
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds
AUDIT_DIR = Path("data/audit/runs")
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()



def make_output_paths(prefix: str) -> Tuple[Path, Path]:
    folder = Path(prefix).parent
    folder.mkdir(parents=True, exist_ok=True)
    csv_path = Path(f"{prefix}.csv")
    parquet_path = Path(f"{prefix}.parquet")
    return csv_path, parquet_path


def save_and_validate(df: pd.DataFrame, csv_path: Path, parquet_path: Path):
    required_cols = ["loan_id", "origination_date", "balance", "days_past_due"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise RuntimeError(f"Missing required columns in ingestion output: {missing}")

    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    LOG.info("Saved %d rows to %s and %s", len(df), csv_path, parquet_path)


def write_run_manifest(
    export_url: str,
    output_prefix: str,
    parquet_path: Path,
    csv_path: Path,
    secrets_hash: str,
):
    manifest = {
        "run_id": RUN_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "export_url": export_url,
        "output_prefix": output_prefix,
        "csv_path": str(csv_path),
        "parquet_path": str(parquet_path),
        "secrets_hash": secrets_hash,
    }
    manifest_path = AUDIT_DIR / f"cascade_ingest_run_{RUN_ID}.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    LOG.info("Wrote audit manifest %s", manifest_path)


def run_cascade_ingest(export_url: str, cookie: str, output_prefix: str, user_agent: Optional[str]):
    csv_path, parquet_path = make_output_paths(output_prefix)
    LOG.info("Starting Cascade ingest run_id=%s", RUN_ID)

    client = CascadeClient(session_cookie=cookie, user_agent=user_agent)
    csv_text = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            LOG.info("Attempt %d to fetch Cascade export", attempt)
            csv_text = client.fetch_csv(export_url)
            if csv_text and len(csv_text) > 100:
                break
        except Exception as exc:
            LOG.warning("Attempt %d failed: %s", attempt, exc)
        time.sleep(RETRY_BACKOFF * attempt)

    if not csv_text:
        raise RuntimeError("Failed to extract CSV from Cascade after retries")

    try:
        df = pd.read_csv(io.StringIO(csv_text))
    except Exception:
        import re

        matcher = re.search(r"(<pre[^>]*>)(.*?)(</pre>)", csv_text, flags=re.S | re.I)
        if matcher:
            df = pd.read_csv(io.StringIO(matcher.group(2)))
        else:
            raise

    df = canonicalize_loan_tape(df)
    save_and_validate(df, csv_path, parquet_path)
    write_run_manifest(export_url, output_prefix, parquet_path, csv_path, _hash_secret(cookie))
    LOG.info("Cascade ingest completed run_id=%s", RUN_ID)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-url", required=True)
    parser.add_argument("--output-prefix", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    session_cookie = os.getenv("CASCADE_SESSION_COOKIE")
    if not session_cookie:
        raise RuntimeError("CASCADE_SESSION_COOKIE secret missing")

    user_agent = os.getenv("CASCADE_USER_AGENT")
    run_cascade_ingest(args.export_url, session_cookie, args.output_prefix, user_agent)


if __name__ == "__main__":
    main()
