import polars as pl
import sys
import logging
from python.config import settings

logger = logging.getLogger(__name__)

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

# Ingestion Schema (Used for Data Contracts and FastAPI validation)
INGESTION_SCHEMA = LOAN_SCHEMA

def validate_ingestion_contract(df: pl.DataFrame) -> bool:
    """
    Validates the loan data against defined business contracts using Polars.
    Returns True if valid, raises ValueError or returns False otherwise.
    """
    # 1. Schema Check
    for col, dtype in INGESTION_SCHEMA.items():
        if col not in df.columns:
            raise ValueError(f"Contract Violation: Missing column {col}")

    # 2. Value Range / Integrity Checks
    # Loan Amount must be positive
    if "loan_amount" in df.columns:
        if df.filter(pl.col("loan_amount") <= 0).height > 0:
            logger.warning("Data Quality Issue: Found loans with non-positive amounts")

    # Interest Rate should be between 0.0 and 1.0 (as decimal)
    if "interest_rate" in df.columns:
        if df.filter((pl.col("interest_rate") < 0) | (pl.col("interest_rate") > 1.0)).height > 0:
            logger.warning("Interest rate out of typical 0.0-1.0 range")

    # 3. Monotonicity Checks (Ensure measurement dates are not regressing)
    if "measurement_date" in df.columns:
        # Sort and check if dates are non-decreasing
        dates = df.select("measurement_date").sort("measurement_date")
        if not df.select("measurement_date").equals(dates):
            logger.warning("Data Continuity Issue: measurement_date is not monotonically increasing")

    # 4. Outlier / Threshold Detection
    if "loan_amount" in df.columns:
        max_loan = 1_000_000 # Example business threshold
        if df.filter(pl.col("loan_amount") > max_loan).height > 0:
            logger.warning(f"Threshold Violation: Loans found exceeding {max_loan}")

    # 5. Completeness
    null_counts = df.null_count()
    for col in df.columns:
        null_val = null_counts.get_column(col)[0]
        if null_val > 0:
            logger.info(f"Column {col} has {null_val} null values.")

    return True

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
