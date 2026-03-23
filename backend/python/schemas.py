import logging
import sys
import polars as pl
logger = logging.getLogger(__name__)
LOAN_SCHEMA = pl.Schema([('loan_id', pl.String), ('loan_amount', pl.Int64), ('appraised_value', pl.Int64), ('borrower_income', pl.Int64), ('monthly_debt', pl.Int64), ('principal_balance', pl.Int64), ('interest_rate', pl.Int64), ('loan_status', pl.String), ('measurement_date', pl.String)])
INGESTION_SCHEMA = LOAN_SCHEMA

def validate_ingestion_contract(df: pl.DataFrame) -> bool:
    monetary_fields = ['loan_amount', 'appraised_value', 'borrower_income', 'monthly_debt', 'principal_balance']
    rate_fields = ['interest_rate']
    for col in monetary_fields:
        if col not in df.columns:
            raise ValueError(f'Contract Violation: Missing monetary column {col}')
        if df[col].dtype != pl.Int64:
            raise ValueError(f'Financial Precision Violation: {col} must be Int64 (cents), found {df[col].dtype}. Use financial_precision.dollars_to_cents() to convert from dollars.')
    for col in rate_fields:
        if col not in df.columns:
            raise ValueError(f'Contract Violation: Missing rate column {col}')
        if df[col].dtype != pl.Int64:
            raise ValueError(f'Financial Precision Violation: {col} must be Int64 (basis points), found {df[col].dtype}. Use financial_precision.interest_rate_to_basis_points() to convert from decimal rates.')
    for col in monetary_fields:
        if col in df.columns:
            invalid = df.filter(pl.col(col) <= 0).height
            if invalid > 0:
                logger.warning(f'Data Quality: {col} has {invalid} non-positive values')
            if df.filter(pl.col(col) > 10000000000).height > 0:
                logger.warning(f'Data Quality: {col} exceeds $100M maximum')
    if 'interest_rate' in df.columns:
        invalid = df.filter((pl.col('interest_rate') < 0) | (pl.col('interest_rate') > 20000000)).height
        if invalid > 0:
            logger.warning(f'Data Quality: interest_rate has {invalid} out-of-range values')
    if 'measurement_date' in df.columns:
        dates = df.select('measurement_date').sort('measurement_date')
        if not df.select('measurement_date').equals(dates):
            logger.warning('Data Continuity Issue: measurement_date is not monotonically increasing')
    null_counts = df.null_count()
    for col in df.columns:
        null_val = null_counts.get_column(col)[0]
        if null_val > 0:
            logger.info('Column %s has %d null values.', col, null_val)
    return True

def assert_healthy(df: pl.DataFrame):
    monetary_cols = ['loan_amount', 'appraised_value', 'borrower_income', 'monthly_debt', 'principal_balance']
    rate_cols = ['interest_rate']
    for col in monetary_cols:
        if col in df.columns:
            neg_count = df.filter(pl.col(col) < 0).height
            if neg_count > 0:
                print(f"❌ CRITICAL: Monetary column '{col}' contains {neg_count} negative values.")
                print('   Negative monetary amounts violate financial invariants.')
                sys.exit(1)
    for col in rate_cols:
        if col in df.columns:
            out_of_range = df.filter((pl.col(col) < 0) | (pl.col(col) > 20000000)).height
            if out_of_range > 0:
                print(f"❌ CRITICAL: Rate column '{col}' has {out_of_range} out-of-range values.")
                print('   Interest rates must be 0-20000000 basis points (0-2000%).')
                sys.exit(1)
    print('✅ Financial precision health checks passed.')
    print(f"   ✓ Monetary columns use Int64 (cents): {', '.join(monetary_cols)}")
    print(f"   ✓ Rate columns use Int64 (basis points): {', '.join(rate_cols)}")
    print('   ✓ No negative monetary amounts')
    print('   ✓ All interest rates within 0-2000% range')
