#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse


def ingest_csv(input_path: str, out_dir: str = "data/metrics"):
    df = pd.read_csv(input_path)
    df.columns = [c.strip() for c in df.columns]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out = out_dir / f"ingest_{ts}.parquet"
    df.to_parquet(out, index=False)
    print(out)
    return str(out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("input", help="CSV or Parquet file to ingest")
    p.add_argument("--out", default="data/metrics")
    args = p.parse_args()
    ingest_csv(args.input, args.out)
