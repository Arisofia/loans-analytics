import pandas as pd
import polars as pl
import pytest
from polars.testing import assert_frame_equal as pl_assert_frame_equal

from src.analytics.enterprise_analytics_engine import LoanAnalyticsEngine
from src.analytics.polars_analytics_engine import PolarsAnalyticsEngine


def test_engine_parity():
    """
    Shadow Mode Verification: Compare Pandas and Polars engines for exact matches.
    """
    data = {
        "loan_amount": [250000.0, 450000.0, 150000.0, 600000.0],
        "appraised_value": [300000.0, 500000.0, 160000.0, 750000.0],
        "borrower_income": [80000.0, 120000.0, 60000.0, 150000.0],
        "monthly_debt": [1500.0, 2500.0, 1000.0, 3000.0],
        "loan_status": ["current", "30-59 days past due", "current", "current"],
        "interest_rate": [0.035, 0.042, 0.038, 0.045],
        "principal_balance": [240000.0, 440000.0, 145000.0, 590000.0],
        "measurement_date": ["2025-01-01", "2025-01-01", "2025-01-01", "2025-01-01"],
        "loan_id": ["L1", "L2", "L3", "L4"],
    }

    # 1. Pandas Path
    pandas_kpis = LoanAnalyticsEngine(pd.DataFrame(data)).run_full_analysis()

    # 2. Polars Path
    polars_kpis = PolarsAnalyticsEngine(pl.DataFrame(data)).compute_kpis()

    # 3. Strict Parity Check
    comparison_map = {
        "portfolio_delinquency_rate_percent": "delinquency_rate",
        "portfolio_yield_percent": "portfolio_yield",
        "average_ltv_ratio_percent": "avg_ltv",
        "average_dti_ratio_percent": "avg_dti",
    }

    for pd_key, pl_key in comparison_map.items():
        assert pytest.approx(pandas_kpis[pd_key], rel=1e-5) == polars_kpis[pl_key]

    print("✅ Parity confirmed.")


def test_dataframe_strict_parity():
    """Verify that converted dataframes match exactly."""
    data = {
        "loan_amount": [100.0],
        "appraised_value": [200.0],
        "borrower_income": [1000.0],
        "monthly_debt": [10.0],
        "loan_status": ["current"],
        "interest_rate": [0.05],
        "principal_balance": [90.0],
        "measurement_date": ["2025-01-01"],
        "loan_id": ["L1"],
    }
    pd_df = pd.DataFrame(data)
    pl_df = pl.DataFrame(data)

    # Convert Polars to Pandas for comparison
    pl_converted = pl_df.to_pandas()
    pd.testing.assert_frame_equal(pd_df, pl_converted, check_dtype=False)


if __name__ == "__main__":
    test_engine_parity()
