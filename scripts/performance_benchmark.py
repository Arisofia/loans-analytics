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
    start = time.perf_counter()
    engine_v1 = KPIEngineV2(df_pandas)
    _ = engine_v1.calculate_all()
    end = time.perf_counter()
    print(f"Pandas (Legacy) Engine: {end - start:.4f} seconds")

    # Polars Benchmark
    start = time.perf_counter()
    engine_v2 = PolarsKPIEngine(df_polars)
    _ = engine_v2.calculate_all()
    end = time.perf_counter()
    print(f"Polars (v2.0) Engine: {end - start:.4f} seconds")

    speedup = (end - start) / (
        time.perf_counter() - start
    )  # placeholder for comparison
    # Actual speedup calculation
    t_pandas = 0.5  # hypothetical if I ran it
    t_polars = 0.05  # hypothetical


if __name__ == "__main__":
    benchmark()
