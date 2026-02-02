#!/usr/bin/env python3
"""
Prepare Real Abaco Data for Pipeline Processing
Merges relational tables into single pipeline-ready dataset.
"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# String constants
LOAN_ID = "Loan ID"
CUSTOMER_ID = "Customer ID"
UNKNOWN_STR = "Unknown"
UNKNOWN_ID = "UNKNOWN"

# Table names
TABLE_LOAN_DATA = "loan_data"
TABLE_CUSTOMER = "customer"
TABLE_COLLATERAL = "collateral"
TABLE_PAYMENT_SCHEDULE = "payment_schedule"
TABLE_HISTORIC_PAYMENTS = "historic_payments"

# File mappings
FILES = {
    TABLE_LOAN_DATA: "Abaco - Loan Tape_Loan Data_Table (3).csv",
    TABLE_CUSTOMER: "Abaco - Loan Tape_Customer Data_Table (3).csv",
    TABLE_COLLATERAL: "Abaco - Loan Tape_Collateral_Table (3).csv",
    TABLE_PAYMENT_SCHEDULE: "Abaco - Loan Tape_Payment Schedule_Table (3).csv",
    TABLE_HISTORIC_PAYMENTS: "Abaco - Loan Tape_Historic Real Payment_Table (3).csv",
}


def load_table(data_dir: Path, table_name: str) -> pd.DataFrame:
    """Load and inspect a table."""
    filepath = data_dir / FILES[table_name]
    logger.info(f"📄 Loading {table_name}: {filepath.name}")

    df = pd.read_csv(filepath)
    logger.info(f"   ✅ Loaded {len(df):,} rows, {len(df.columns)} columns")
    logger.info(f"   📋 Columns: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")

    return df


def _apply_column_rename(df: pd.DataFrame) -> pd.DataFrame:
    """Apply column name mappings."""
    column_mapping = {
        # Loan identifiers
        "Loan ID": "loan_id",
        "Customer ID": "borrower_id",
        "Cliente": "borrower_name",
        "Pagador": "payor_name",
        # Loan amounts and terms
        "Disbursement Amount": "principal_amount",
        "Interest Rate APR": "interest_rate",
        "Term": "term_months",
        "Term Unit": "term_unit",
        "Disbursement Date": "origination_date",
        # Status and performance
        "Loan Status": "current_status",
        "Days in Default": "days_past_due",
        "Outstanding Loan Value": "outstanding_balance",
        # Additional context
        "Product Type": "product_type",
        "Payment Frequency": "payment_frequency",
        "Loan Currency": "currency",
        "TPV": "tpv",
        # Fees and charges
        "Origination Fee": "origination_fee",
        "Origination Fee Taxes": "origination_fee_taxes",
        # Customer info
        "Sales Channel": "sales_channel",
        "Location City": "city",
        "Location State Province": "state",
        "Location Country": "country",
        "Internal Credit Score": "credit_score",
        "Client Type": "client_type",
        "Industry": "industry",
        # Collateral
        "Collateral Type": "collateral_type",
        "Collateral Current": "collateral_value",
        # Payment tracking
        "True Payment Date": "last_payment_date",
        "True Total Payment": "last_payment_amount",
        "True Outstanding Loan Value": "current_balance",
    }

    logger.info(f"   📋 Original columns: {len(df.columns)}")
    renamed_df = df.rename(columns=column_mapping)

    mapped_cols = [col for col in column_mapping.values() if col in renamed_df.columns]
    logger.info(f"   ✅ Mapped {len(mapped_cols)} columns")
    logger.info(
        f"   📋 New columns: {', '.join(mapped_cols[:10])}{'...' if len(mapped_cols) > 10 else ''}"
    )

    return renamed_df


def _add_computed_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add computed fields like amount and status."""
    # Add amount if missing
    if "amount" not in df.columns:
        if "principal_amount" in df.columns:
            df["amount"] = df["principal_amount"]
        else:
            df["amount"] = 0
            logger.info("   ⚠️  Added 'amount' with default value 0")

    # Add status if missing
    if "status" not in df.columns:
        if "current_status" in df.columns:
            df["status"] = df["current_status"]
        else:
            df["status"] = UNKNOWN_STR
            logger.info(f"   ⚠️  Added 'status' with default value '{UNKNOWN_STR}'")

    return df


def _normalize_interest_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Convert interest rate to decimal if it's percentage."""
    if "interest_rate" not in df.columns:
        return df

    sample_rate = (
        df["interest_rate"].dropna().iloc[0]
        if not df["interest_rate"].dropna().empty
        else 0
    )

    if sample_rate > 1:
        df["interest_rate"] = df["interest_rate"] / 100
        logger.info("   🔄 Converted interest_rate from percentage to decimal")

    return df


def _convert_term_to_months(row: pd.Series) -> float:
    """Convert term duration to months based on unit."""
    term = row.get("term_months", 0)
    unit = str(row.get("term_unit", "months")).lower()

    if "day" in unit:
        return term / 30
    elif "week" in unit:
        return term / 4
    elif "year" in unit:
        return term * 12
    else:  # months
        return term


def _normalize_term_months(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize term_months from various units."""
    if "term_unit" not in df.columns or "term_months" not in df.columns:
        return df

    df["term_months"] = df.apply(_convert_term_to_months, axis=1)
    logger.info("   🔄 Normalized term_months from various units")

    return df


def _calculate_maturity_date(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate maturity_date from origination_date + term_months."""
    if "maturity_date" in df.columns:
        return df

    if "origination_date" not in df.columns or "term_months" not in df.columns:
        df["maturity_date"] = pd.NaT
        logger.info("   ⚠️  Added 'maturity_date' with null values")
        return df

    try:
        df["origination_date"] = pd.to_datetime(df["origination_date"], errors="coerce")
        df["maturity_date"] = df.apply(
            lambda row: (
                row["origination_date"] + pd.DateOffset(months=int(row["term_months"]))
                if pd.notna(row["origination_date"]) and pd.notna(row["term_months"])
                else pd.NaT
            ),
            axis=1,
        )
        logger.info("   ✅ Calculated maturity_date from origination_date + term_months")
    except Exception as e:
        logger.warning(f"   ⚠️  Could not calculate maturity_date: {e}")
        df["maturity_date"] = pd.NaT

    return df


def _fill_outstanding_balance(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing outstanding_balance with current_balance."""
    if "current_balance" not in df.columns:
        return df

    if "outstanding_balance" not in df.columns or df["outstanding_balance"].isna().sum() == 0:
        return df

    df["outstanding_balance"] = df["outstanding_balance"].fillna(df["current_balance"])
    logger.info("   🔄 Filled missing outstanding_balance with current_balance")

    return df


def _add_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add required columns with default values if missing."""
    required_columns = {
        "loan_id": UNKNOWN_ID,
        "borrower_id": UNKNOWN_ID,
        "borrower_name": UNKNOWN_STR,
        "principal_amount": 0.0,
        "interest_rate": 0.0,
        "term_months": 0,
        "origination_date": pd.NaT,
        "current_status": UNKNOWN_STR,
        "days_past_due": 0,
        "outstanding_balance": 0.0,
    }

    for col, default_val in required_columns.items():
        if col not in df.columns:
            df[col] = default_val
            logger.info(f"   ⚠️  Added required column '{col}' with default value")

    return df


def map_to_pipeline_schema(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Map real Abaco columns to pipeline schema.

    Expected pipeline columns (from validation.py):
    - loan_id, borrower_id, borrower_name, principal_amount,
    - interest_rate, term_months, origination_date, maturity_date,
    - current_status, days_past_due, outstanding_balance, etc.
    """
    logger.info("\n🔄 Mapping to pipeline schema...")

    # Apply transformations in sequence
    df = _apply_column_rename(merged_df)
    df = _add_computed_fields(df)
    df = _normalize_interest_rate(df)
    df = _normalize_term_months(df)
    df = _calculate_maturity_date(df)
    df = _fill_outstanding_balance(df)
    df = _add_required_columns(df)

    return df


def _load_all_tables(files_in_downloads: dict) -> dict | None:
    """Load all required tables from CSV files."""
    logger.info(f"\n📂 Loading tables from {files_in_downloads[TABLE_LOAN_DATA].parent}/...")
    tables = {}

    for table_name, filepath in files_in_downloads.items():
        try:
            df = pd.read_csv(filepath)
            tables[table_name] = df
            logger.info(f"   ✅ {table_name}: {len(df):,} rows, {len(df.columns)} columns")
        except FileNotFoundError:
            logger.error(f"   ❌ File not found: {filepath}")
            return None
        except Exception as e:
            logger.error(f"   ❌ Error loading {table_name}: {e}")
            return None

    return tables


def _merge_tables(tables: dict) -> pd.DataFrame:
    """Merge all tables on Loan ID."""
    logger.info(f"\n🔗 Merging tables on '{LOAN_ID}'...")

    # Start with loan data as base
    merged = tables[TABLE_LOAN_DATA].copy()
    logger.info(f"   📊 Base: {TABLE_LOAN_DATA} ({len(merged):,} loans)")

    # Merge customer data (left join to preserve all loans)
    if TABLE_CUSTOMER in tables:
        customer_cols = [
            CUSTOMER_ID,
            LOAN_ID,
            "Sales Channel",
            "Location City",
            "Location State Province",
            "Location Country",
            "Internal Credit Score",
            "Client Type",
            "Industry",
            "Equifax Score",
        ]
        customer_df = tables[TABLE_CUSTOMER][customer_cols].drop_duplicates(subset=[LOAN_ID])
        merged = merged.merge(customer_df, on=LOAN_ID, how="left", suffixes=("", "_cust"))
        logger.info(f"   🔗 + {TABLE_CUSTOMER} data ({len(customer_df):,} unique loans)")

    # Merge collateral (left join, aggregate if multiple per loan)
    if TABLE_COLLATERAL in tables:
        collateral_cols = [LOAN_ID, "Collateral Type", "Collateral Current"]
        collateral_df = tables[TABLE_COLLATERAL][collateral_cols].drop_duplicates(subset=[LOAN_ID])
        merged = merged.merge(collateral_df, on=LOAN_ID, how="left", suffixes=("", "_coll"))
        logger.info(f"   🔗 + {TABLE_COLLATERAL} data ({len(collateral_df):,} unique loans)")

    # Aggregate payment schedule (scheduled payments)
    if TABLE_PAYMENT_SCHEDULE in tables:
        payment_agg = (
            tables[TABLE_PAYMENT_SCHEDULE]
            .groupby(LOAN_ID)
            .agg(
                {
                    "Payment Date": "max",  # Last scheduled payment date
                    "Total Payment": "sum",  # Total scheduled payments
                }
            )
            .reset_index()
        )
        payment_agg.columns = [LOAN_ID, "last_scheduled_date", "total_scheduled"]
        merged = merged.merge(payment_agg, on=LOAN_ID, how="left")
        logger.info(f"   🔗 + {TABLE_PAYMENT_SCHEDULE} (aggregated, {len(payment_agg):,} loans)")

    # Aggregate historic payments (actual payments made)
    if TABLE_HISTORIC_PAYMENTS in tables:
        historic_agg = (
            tables[TABLE_HISTORIC_PAYMENTS]
            .groupby(LOAN_ID)
            .agg(
                {
                    "True Payment Date": "max",  # Last payment date
                    "True Total Payment": "sum",  # Total amount paid
                    "True Outstanding Loan Value": "last",  # Current balance
                }
            )
            .reset_index()
        )
        historic_agg.columns = [
            LOAN_ID,
            "True Payment Date",
            "True Total Payment",
            "True Outstanding Loan Value",
        ]
        merged = merged.merge(historic_agg, on=LOAN_ID, how="left")
        logger.info(f"   🔗 + {TABLE_HISTORIC_PAYMENTS} (aggregated, {len(historic_agg):,} loans)")

    logger.info(f"\n   ✅ Merged dataset: {len(merged):,} rows, {len(merged.columns)} columns")
    return merged


def _save_output(df: pd.DataFrame, output_file: Path) -> None:
    """Save processed data to CSV."""
    logger.info(f"\n💾 Saving to: {output_file.name}")
    df.to_csv(output_file, index=False)
    logger.info(f"   ✅ Saved {len(df):,} loans to {output_file}")


def _log_summary_statistics(df: pd.DataFrame, output_file: Path) -> None:
    """Log summary statistics about the processed dataset."""
    logger.info("\n" + "=" * 60)
    logger.info("✅ Data Preparation Complete!")
    logger.info("=" * 60)
    logger.info("📄 Output file: %s", output_file)
    logger.info("📊 Total loans: %d", len(df))
    logger.info("📋 Columns: %d", len(df.columns))

    if "principal_amount" in df.columns:
        total_disbursed = df["principal_amount"].sum()
        logger.info(f"💰 Total disbursed: ${total_disbursed:,.2f}")

    if "outstanding_balance" in df.columns:
        total_outstanding = df["outstanding_balance"].sum()
        logger.info(f"📊 Total outstanding: ${total_outstanding:,.2f}")

    if "current_status" in df.columns:
        status_counts = df["current_status"].value_counts()
        logger.info("\\n\ud83d\udcc8 Loan status distribution:")
        for status, count in status_counts.head(5).items():
            pct = (count / len(df)) * 100
            logger.info("   %s: %s (%.1f%%)", status, f"{count:,}", pct)

    logger.info("\n🚀 Next steps:")
    logger.info("  1. Inspect: head %s", output_file)
    logger.info(
        "  2. Run pipeline: .venv/bin/python scripts/run_data_pipeline.py --input %s --verbose",
        output_file,
    )


def main():
    """Main data preparation pipeline."""
    logger.info("=" * 60)
    logger.info("🚀 Preparing Real Abaco Data for Pipeline")
    logger.info("=" * 60)

    # Use Downloads folder as source
    downloads_dir = Path.home() / "Downloads"
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    output_file = data_dir / f"abaco_real_data_{datetime.now():%Y%m%d}.csv"

    # Updated file mappings with actual filenames
    files_in_downloads = {
        TABLE_LOAN_DATA: downloads_dir / "Abaco - Loan Tape_Loan Data_Table (3).csv",
        TABLE_CUSTOMER: downloads_dir / "Abaco - Loan Tape_Customer Data_Table (3).csv",
        TABLE_COLLATERAL: downloads_dir / "Abaco - Loan Tape_Collateral_Table (3).csv",
        TABLE_PAYMENT_SCHEDULE: downloads_dir / "Abaco - Loan Tape_Payment Schedule_Table (3).csv",
        TABLE_HISTORIC_PAYMENTS: downloads_dir
        / "Abaco - Loan Tape_Historic Real Payment_Table (3).csv",
    }

    # Load all tables
    tables = _load_all_tables(files_in_downloads)
    if tables is None:
        return

    # Merge tables
    merged = _merge_tables(tables)

    # Map to pipeline schema
    final_df = map_to_pipeline_schema(merged)

    # Save and summarize
    _save_output(final_df, output_file)
    _log_summary_statistics(final_df, output_file)


if __name__ == "__main__":
    main()
