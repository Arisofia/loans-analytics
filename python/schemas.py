import polars as pl
import sys

# Finance-Grade Loan Schema
LOAN_SCHEMA = pl.Schema([
    ("loan_id", pl.String),
    ("loan_amount", pl.Float64),
    ("appraised_value", pl.Float64),
    ("borrower_income", pl.Float64),
    ("monthly_debt", pl.Float64),
    ("loan_status", pl.String),
    ("interest_rate", pl.Float64),
    ("principal_balance", pl.Float64),
    ("measurement_date", pl.String), # ISO string
])

def assert_healthy(df: pl.DataFrame):
    """Fail-fast health checks."""
    numeric_cols = ["loan_amount", "principal_balance", "interest_rate"]
    for col in numeric_cols:
        if col in df.columns:
            # Explicitly fail if negative values found in financial columns
            neg_count = df.filter(pl.col(col) < 0).height
            if neg_count > 0:
                print(f"❌ CRITICAL: Column '{col}' contains {neg_count} negative values.")
                sys.exit(1)

    print("✅ Polars health checks passed.")
