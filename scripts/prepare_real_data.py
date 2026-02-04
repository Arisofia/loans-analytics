#!/usr/bin/env python3
"""
Prepare Real Abaco Data for Pipeline Processing
Merges relational tables into single pipeline-ready dataset.
"""

import pandas as pd
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# File mappings
FILES = {
    'loan_data': 'Abaco - Loan Tape_Loan Data_Table (3).csv',
    'customer': 'Abaco - Loan Tape_Customer Data_Table (3).csv',
    'collateral': 'Abaco - Loan Tape_Collateral_Table (3).csv',
    'payment_schedule': 'Abaco - Loan Tape_Payment Schedule_Table (3).csv',
    'historic_payments': 'Abaco - Loan Tape_Historic Real Payment_Table (3).csv'
}

def load_table(data_dir: Path, table_name: str) -> pd.DataFrame:
    """Load and inspect a table."""
    filepath = data_dir / FILES[table_name]
    logger.info(f"📄 Loading {table_name}: {filepath.name}")

    df = pd.read_csv(filepath)
    logger.info(f"   ✅ Loaded {len(df):,} rows, {len(df.columns)} columns")
    logger.info(f"   📋 Columns: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")

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

    # Real Abaco column mappings
    column_mapping = {
        # Loan identifiers
        'Loan ID': 'loan_id',
        'Customer ID': 'borrower_id',
        'Cliente': 'borrower_name',
        'Pagador': 'payor_name',

        # Loan amounts and terms
        'Disbursement Amount': 'principal_amount',
        'Interest Rate APR': 'interest_rate',
        'Term': 'term_months',
        'Term Unit': 'term_unit',
        'Disbursement Date': 'origination_date',

        # Status and performance
        'Loan Status': 'current_status',
        'Days in Default': 'days_past_due',
        'Outstanding Loan Value': 'outstanding_balance',

        # Additional context
        'Product Type': 'product_type',
        'Payment Frequency': 'payment_frequency',
        'Loan Currency': 'currency',
        'TPV': 'tpv',

        # Fees and charges
        'Origination Fee': 'origination_fee',
        'Origination Fee Taxes': 'origination_fee_taxes',

        # Customer info
        'Sales Channel': 'sales_channel',
        'Location City': 'city',
        'Location State Province': 'state',
        'Location Country': 'country',
        'Internal Credit Score': 'credit_score',
        'Client Type': 'client_type',
        'Industry': 'industry',

        # Collateral
        'Collateral Type': 'collateral_type',
        'Collateral Current': 'collateral_value',

        # Payment tracking
        'True Payment Date': 'last_payment_date',
        'True Total Payment': 'last_payment_amount',
        'True Outstanding Loan Value': 'current_balance',
    }

    # Apply mapping
    logger.info(f"   📋 Original columns: {len(merged_df.columns)}")
    mapped_df = merged_df.rename(columns=column_mapping)

    # Log what was mapped
    mapped_cols = [col for col in column_mapping.values() if col in mapped_df.columns]
    logger.info(f"   ✅ Mapped {len(mapped_cols)} columns")
    logger.info(f"   📋 New columns: {', '.join(mapped_cols[:10])}{'...' if len(mapped_cols) > 10 else ''}")

    # Add computed fields if missing
    if 'amount' not in mapped_df.columns:
        if 'principal_amount' in mapped_df.columns:
            mapped_df['amount'] = mapped_df['principal_amount']
        else:
            mapped_df['amount'] = 0
            logger.info("   ⚠️  Added 'amount' with default value 0")

    if 'status' not in mapped_df.columns:
        if 'current_status' in mapped_df.columns:
            mapped_df['status'] = mapped_df['current_status']
        else:
            mapped_df['status'] = 'Unknown'
            logger.info("   ⚠️  Added 'status' with default value 'Unknown'")

    # Convert interest rate to decimal if it's percentage
    if 'interest_rate' in mapped_df.columns:
        # Check if values are > 1 (likely percentage format like 34.5)
        sample_rate = mapped_df['interest_rate'].dropna().iloc[0] if not mapped_df['interest_rate'].dropna().empty else 0
        if sample_rate > 1:
            mapped_df['interest_rate'] = mapped_df['interest_rate'] / 100
            logger.info("   🔄 Converted interest_rate from percentage to decimal")

    # Convert term to months if in different unit
    if 'term_unit' in mapped_df.columns and 'term_months' in mapped_df.columns:
        # Handle 'Days', 'Weeks', 'Months', 'Years'
        def convert_to_months(row):
            term = row.get('term_months', 0)
            unit = str(row.get('term_unit', 'months')).lower()
            if 'day' in unit:
                return term / 30
            elif 'week' in unit:
                return term / 4
            elif 'year' in unit:
                return term * 12
            else:  # months
                return term

        mapped_df['term_months'] = mapped_df.apply(convert_to_months, axis=1)
        logger.info("   🔄 Normalized term_months from various units")

    # Calculate maturity_date if missing (origination_date + term_months)
    if 'maturity_date' not in mapped_df.columns:
        if 'origination_date' in mapped_df.columns and 'term_months' in mapped_df.columns:
            try:
                mapped_df['origination_date'] = pd.to_datetime(mapped_df['origination_date'], errors='coerce')
                mapped_df['maturity_date'] = mapped_df.apply(
                    lambda row: row['origination_date'] + pd.DateOffset(months=int(row['term_months'])) 
                    if pd.notna(row['origination_date']) and pd.notna(row['term_months']) 
                    else pd.NaT,
                    axis=1
                )
                logger.info("   ✅ Calculated maturity_date from origination_date + term_months")
            except Exception as e:
                logger.warning(f"   ⚠️  Could not calculate maturity_date: {e}")
                mapped_df['maturity_date'] = pd.NaT
        else:
            mapped_df['maturity_date'] = pd.NaT
            logger.info("   ⚠️  Added 'maturity_date' with null values")

    # Ensure outstanding_balance uses current balance if available
    if 'current_balance' in mapped_df.columns and mapped_df['outstanding_balance'].isna().sum() > 0:
        mapped_df['outstanding_balance'] = mapped_df['outstanding_balance'].fillna(mapped_df['current_balance'])
        logger.info("   🔄 Filled missing outstanding_balance with current_balance")

    # Add other required columns with defaults if missing
    required_columns = {
        'loan_id': 'UNKNOWN',
        'borrower_id': 'UNKNOWN',
        'borrower_name': 'Unknown',
        'principal_amount': 0.0,
        'interest_rate': 0.0,
        'term_months': 0,
        'origination_date': pd.NaT,
        'current_status': 'Unknown',
        'days_past_due': 0,
        'outstanding_balance': 0.0
    }

    for col, default_val in required_columns.items():
        if col not in mapped_df.columns:
            mapped_df[col] = default_val
            logger.info(f"   ⚠️  Added required column '{col}' with default value")

    return mapped_df

def main():
    """Main data preparation pipeline."""
    logger.info("=" * 60)
    logger.info("🚀 Preparing Real Abaco Data for Pipeline")
    logger.info("=" * 60)

    # Use Downloads folder as source
    downloads_dir = Path.home() / 'Downloads'
    data_dir = Path(__file__).parent.parent / 'data' / 'raw'
    output_file = data_dir / f'abaco_real_data_{datetime.now():%Y%m%d}.csv'

    # Updated file mappings with actual filenames
    files_in_downloads = {
        'loan_data': downloads_dir / 'Abaco - Loan Tape_Loan Data_Table (3).csv',
        'customer': downloads_dir / 'Abaco - Loan Tape_Customer Data_Table (3).csv',
        'collateral': downloads_dir / 'Abaco - Loan Tape_Collateral_Table (3).csv',
        'payment_schedule': downloads_dir / 'Abaco - Loan Tape_Payment Schedule_Table (3).csv',
        'historic_payments': downloads_dir / 'Abaco - Loan Tape_Historic Real Payment_Table (3).csv'
    }

    # Load all tables
    logger.info(f"\n📂 Loading tables from {downloads_dir}/...")
    tables = {}
    for table_name, filepath in files_in_downloads.items():
        try:
            df = pd.read_csv(filepath)
            tables[table_name] = df
            logger.info(f"   ✅ {table_name}: {len(df):,} rows, {len(df.columns)} columns")
        except FileNotFoundError:
            logger.error(f"   ❌ File not found: {filepath}")
            return
        except Exception as e:
            logger.error(f"   ❌ Error loading {table_name}: {e}")
            return

    # Merge tables
    logger.info("\n🔗 Merging tables on 'Loan ID'...")

    # Start with loan data as base
    merged = tables['loan_data'].copy()
    logger.info(f"   📊 Base: loan_data ({len(merged):,} loans)")

    # Merge customer data (left join to preserve all loans)
    if 'customer' in tables:
        # Select customer columns not already in loan_data
        customer_cols = ['Customer ID', 'Loan ID', 'Sales Channel', 'Location City', 
                        'Location State Province', 'Location Country', 'Internal Credit Score',
                        'Client Type', 'Industry', 'Equifax Score']
        customer_df = tables['customer'][customer_cols].drop_duplicates(subset=['Loan ID'])
        merged = merged.merge(customer_df, on='Loan ID', how='left', suffixes=('', '_cust'))
        logger.info(f"   🔗 + customer data ({len(customer_df):,} unique loans)")

    # Merge collateral (left join, aggregate if multiple per loan)
    if 'collateral' in tables:
        collateral_cols = ['Loan ID', 'Collateral Type', 'Collateral Current']
        collateral_agg = tables['collateral'][collateral_cols].groupby('Loan ID').agg({
            'Collateral Type': 'first',      # Use first type if multiple; assumes consistency per loan
            'Collateral Current': 'sum',     # Total collateral value per loan
        }).reset_index()
        merged = merged.merge(collateral_agg, on='Loan ID', how='left', suffixes=('', '_coll'))
        logger.info(f"   🔗 + collateral data (aggregated, {len(collateral_agg):,} loans)")

    # Aggregate payment schedule (scheduled payments)
    if 'payment_schedule' in tables:
        payment_agg = tables['payment_schedule'].groupby('Loan ID').agg({
            'Payment Date': 'max',  # Last scheduled payment date
            'Total Payment': 'sum',  # Total scheduled payments
        }).reset_index()
        payment_agg.columns = ['Loan ID', 'last_scheduled_date', 'total_scheduled']
        merged = merged.merge(payment_agg, on='Loan ID', how='left')
        logger.info(f"   🔗 + payment schedule (aggregated, {len(payment_agg):,} loans)")

    # Aggregate historic payments (actual payments made)
    if 'historic_payments' in tables:
        historic_agg = tables['historic_payments'].groupby('Loan ID').agg({
            'True Payment Date': 'max',  # Last payment date
            'True Total Payment': 'sum',  # Total amount paid
            'True Outstanding Loan Value': 'last',  # Current balance
        }).reset_index()
        historic_agg.columns = ['Loan ID', 'True Payment Date', 'True Total Payment', 
                               'True Outstanding Loan Value']
        merged = merged.merge(historic_agg, on='Loan ID', how='left')
        logger.info(f"   🔗 + historic payments (aggregated, {len(historic_agg):,} loans)")

    logger.info(f"\n   ✅ Merged dataset: {len(merged):,} rows, {len(merged.columns)} columns")

    # Map to pipeline schema
    final_df = map_to_pipeline_schema(merged)

    # Save
    logger.info(f"\n💾 Saving to: {output_file.name}")
    final_df.to_csv(output_file, index=False)
    logger.info(f"   ✅ Saved {len(final_df):,} loans to {output_file}")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ Data Preparation Complete!")
    logger.info("=" * 60)
    logger.info(f"📄 Output file: {output_file}")
    logger.info(f"📊 Total loans: {len(final_df):,}")
    logger.info(f"📋 Columns: {len(final_df.columns)}")

    # Show key statistics
    if 'principal_amount' in final_df.columns:
        total_disbursed = final_df['principal_amount'].sum()
        logger.info(f"💰 Total disbursed: ${total_disbursed:,.2f}")

    if 'outstanding_balance' in final_df.columns:
        total_outstanding = final_df['outstanding_balance'].sum()
        logger.info(f"📊 Total outstanding: ${total_outstanding:,.2f}")

    if 'current_status' in final_df.columns:
        status_counts = final_df['current_status'].value_counts()
        logger.info("\n📈 Loan status distribution:")
        for status, count in status_counts.head(5).items():
            pct = (count / len(final_df)) * 100
            logger.info(f"   {status}: {count:,} ({pct:.1f}%)")

    logger.info("\n🚀 Next steps:")
    logger.info(f"  1. Inspect: head {output_file}")
    logger.info(f"  2. Run pipeline: .venv/bin/python scripts/run_data_pipeline.py --input {output_file} --verbose")

if __name__ == '__main__':
    main()
