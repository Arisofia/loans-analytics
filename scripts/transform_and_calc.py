#!/usr/bin/env python3
import pandas as pd
import sys
from python.data_validation import validate_df_basic
from python.kpis.collection_rate import calculate_collection_rate, calculate_par_90


def transform_and_report(path):
    df = pd.read_parquet(path) if path.endswith(".parquet") else pd.read_csv(path)
    validate_df_basic(df)
    df['segment'] = df['segment'].astype(str).str.strip().str.title()
    return {
        "par90_all": float(calculate_par_90(df)),
        "collection_rate_all": float(calculate_collection_rate(df))
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: transform_and_calc.py <data-file>")
        sys.exit(2)
    print(transform_and_report(sys.argv[1]))
