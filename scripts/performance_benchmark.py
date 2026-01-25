import time

import numpy as np
import pandas as pd
import polars as pl

from src.kpis.engine import KPIEngineV2
from src.kpis.polars_engine import PolarsKPIEngine


def generate_large_dataset(n_rows: int = 1_000_000):
    print(f"Generating synthetic dataset with {n_rows:,} rows...")
    data = {
        "loan_id": [f"L_{i}" for i in range(n_rows)],
        "dpd_30_60_usd": np.random.uniform(0, 1000, n_rows),
        "dpd_60_90_usd": np.random.uniform(0, 500, n_rows),
        "dpd_90_plus_usd": np.random.uniform(0, 250, n_rows),
        "total_receivable_usd": np.random.uniform(10000, 100000, n_rows),
    }
    return pd.DataFrame(data)


def benchmark():
    n_rows = 1_000_000
    df_pandas = generate_large_dataset(n_rows)
    df_polars = pl.from_pandas(df_pandas)

    print("\n--- Performance Benchmark (1M Rows) ---")

    # Pandas Benchmark
    start_pd = time.perf_counter()
    engine_v1 = KPIEngineV2(df_pandas)
    _ = engine_v1.calculate_all()
    end_pd = time.perf_counter()
    duration_pd = end_pd - start_pd
    print(f"Pandas (Legacy) Engine: {duration_pd:.4f} seconds")

    # Polars Benchmark
    start_pl = time.perf_counter()
    engine_v2 = PolarsKPIEngine(df_polars)
    _ = engine_v2.calculate_all()
    end_pl = time.perf_counter()
    duration_pl = end_pl - start_pl
    print(f"Polars (v2.0) Engine: {duration_pl:.4f} seconds")

    if duration_pl > 0:
        print(f"Speedup: {duration_pd / duration_pl:.2f}x")


if __name__ == "__main__":
    benchmark()
