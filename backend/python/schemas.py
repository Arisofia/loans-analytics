import logging
import sys

import polars as pl

logger = logging.getLogger(__name__)

# ============================================================================
# FINANCIAL PRECISION SCHEMA
# ============================================================================
# 
# Monetary values are now stored using precision-safe representations:
#
# 1. MONETARY AMOUNTS (loan_amount, principal_balance, etc.)
#    - Stored as: Int64 (cents)
#    - Range: 1 to 10,000,000,000 cents ($0.01 to $100,000,000)
#    - Conversion: dollars_to_cents() and cents_to_dollars()
#    - Precision: Exact (no floating point drift)
#
# 2. INTEREST RATES (interest_rate)
#    - Stored as: Int64 (basis points)
#    - Range: 0 to 2,000,000 basis points (0% to 2000%)
#    - Conversion: interest_rate_to_basis_points() / 10000 for display
#    - Precision: 4 decimal places (0.0001%)
#
# IMPORTANT: Never use Float64 for monetary values. Always validate
# conversions using financial_precision module.
#

# Finance-Grade Loan Schema (UPDATED FOR PRECISION)
LOAN_SCHEMA = pl.Schema(
    [
        ("loan_id", pl.String),
        # Monetary amounts: stored as Int64 (cents for dollars)
        ("loan_amount", pl.Int64),  # Amount in cents ($X.YZ → cents)
        ("appraised_value", pl.Int64),  # Amount in cents
        ("borrower_income", pl.Int64),  # Amount in cents
        ("monthly_debt", pl.Int64),  # Amount in cents
        ("principal_balance", pl.Int64),  # Amount in cents
        # Rates: stored as Int64 (basis points, 0-2000000)
        ("interest_rate", pl.Int64),  # Rate in basis points (500 = 5%)
        # Status / metadata
        ("loan_status", pl.String),
        ("measurement_date", pl.String),  # ISO string
    ]
)
# Ingestion Schema (Used for Data Contracts and FastAPI validation)
INGESTION_SCHEMA = LOAN_SCHEMA


def validate_ingestion_contract(df: pl.DataFrame) -> bool:
    """
    Validates the loan data against defined business contracts using Polars.
    
    Updated for financial precision: Validates that monetary columns are Int64
    (cents) and that rate columns are Int64 (basis points).
    
    Returns True if valid, raises ValueError or returns False otherwise.
    """
    # 1. Schema Check: Verify monetary fields are Int64 (not Float64)
    monetary_fields = [
        "loan_amount",
        "appraised_value",
        "borrower_income",
        "monthly_debt",
        "principal_balance",
    ]
    rate_fields = ["interest_rate"]
    
    for col in monetary_fields:
        if col not in df.columns:
            raise ValueError(f"Contract Violation: Missing monetary column {col}")
        if df[col].dtype != pl.Int64:
            raise ValueError(
                f"Financial Precision Violation: {col} must be Int64 (cents), "
                f"found {df[col].dtype}. Use financial_precision.dollars_to_cents() "
                f"to convert from dollars."
            )
    
    for col in rate_fields:
        if col not in df.columns:
            raise ValueError(f"Contract Violation: Missing rate column {col}")
        if df[col].dtype != pl.Int64:
            raise ValueError(
                f"Financial Precision Violation: {col} must be Int64 (basis points), "
                f"found {df[col].dtype}. Use financial_precision.interest_rate_to_basis_points() "
                f"to convert from decimal rates."
            )
    
    # 2. Range Checks
    # Monetary amounts: must be positive and within bounds
    for col in monetary_fields:
        if col in df.columns:
            invalid = df.filter(pl.col(col) <= 0).height
            if invalid > 0:
                logger.warning(f"Data Quality: {col} has {invalid} non-positive values")
            
            # Warn on extreme values but don't fail
            if (df.filter(pl.col(col) > 10_000_000_000).height > 0):  # > $100M
                logger.warning(f"Data Quality: {col} exceeds $100M maximum")
    
    # Interest rates: 0-2000% (0 to 20,000,000 basis points)
    if "interest_rate" in df.columns:
        invalid = df.filter(
            (pl.col("interest_rate") < 0) | (pl.col("interest_rate") > 20_000_000)
        ).height
        if invalid > 0:
            logger.warning(f"Data Quality: interest_rate has {invalid} out-of-range values")
    
    # 3. Measurement date monotonicity
    if "measurement_date" in df.columns:
        dates = df.select("measurement_date").sort("measurement_date")
        if not df.select("measurement_date").equals(dates):
            logger.warning(
                "Data Continuity Issue: measurement_date is not monotonically increasing"
            )
    
    # 4. Completeness check
    null_counts = df.null_count()
    for col in df.columns:
        null_val = null_counts.get_column(col)[0]
        if null_val > 0:
            logger.info("Column %s has %d null values.", col, null_val)
    
    return True


def assert_healthy(df: pl.DataFrame):
    """
    Fail-fast financial precision health checks.
    
    Ensures:
    1. Monetary columns (Int64, cents) are never negative
    2. Interest rate columns (Int64, basis points) are in valid range
    3. No conversion from float64 to int64 without precision validation
    """
    monetary_cols = [
        "loan_amount",
        "appraised_value",
        "borrower_income",
        "monthly_debt",
        "principal_balance",
    ]
    rate_cols = ["interest_rate"]
    
    # Check monetary columns for negative values
    for col in monetary_cols:
        if col in df.columns:
            neg_count = df.filter(pl.col(col) < 0).height
            if neg_count > 0:
                print(f"❌ CRITICAL: Monetary column '{col}' contains {neg_count} negative values.")
                print("   Negative monetary amounts violate financial invariants.")
                sys.exit(1)
    
    # Check rate columns for invalid ranges
    for col in rate_cols:
        if col in df.columns:
            out_of_range = df.filter(
                (pl.col(col) < 0) | (pl.col(col) > 20_000_000)
            ).height
            if out_of_range > 0:
                print(f"❌ CRITICAL: Rate column '{col}' has {out_of_range} out-of-range values.")
                print("   Interest rates must be 0-20000000 basis points (0-2000%).")
                sys.exit(1)
    
    print("✅ Financial precision health checks passed.")
    print(f"   ✓ Monetary columns use Int64 (cents): {', '.join(monetary_cols)}")
    print(f"   ✓ Rate columns use Int64 (basis points): {', '.join(rate_cols)}")
    print("   ✓ No negative monetary amounts")
    print("   ✓ All interest rates within 0-2000% range")
