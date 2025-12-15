#!/usr/bin/env python3
"""
Cascade Debt Data Ingestion Script

This script downloads data from Cascade Debt platform and processes it using
the CascadeIngestion class for the Abaco portfolio.

Usage:
    python scripts/ingest_cascade.py [--loan-tape] [--financials] [--all]
    
Options:
    --loan-tape     Download and process loan tape export
    --financials    Download and process financial statements
    --all           Download all available data sources
    --output-dir    Output directory for processed data (default: data/cascade)
    
Environment Variables:
    CASCADE_USERNAME    Cascade Debt username
    CASCADE_PASSWORD    Cascade Debt password
    CASCADE_PID         Portfolio ID (default: abaco)

For manual downloads, use the URLs documented in CASCADE_DATA_SOURCES.md
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.ingestion import CascadeIngestion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Cascade URLs
CASCADE_BASE_URL = "https://app.cascadedebt.com"
CASCADE_LOAN_TAPE_URL = f"{CASCADE_BASE_URL}/data/exports/loan-tape"
CASCADE_PL_URL = f"{CASCADE_BASE_URL}/analytics/financials/statements"
CASCADE_BALANCE_SHEET_URL = f"{CASCADE_BASE_URL}/analytics/financials/statements"


def get_cascade_credentials() -> tuple[Optional[str], Optional[str], str]:
    """
    Get Cascade credentials from environment variables.
    
    Returns:
        Tuple of (username, password, portfolio_id)
    """
    username = os.getenv("CASCADE_USERNAME")
    password = os.getenv("CASCADE_PASSWORD")
    pid = os.getenv("CASCADE_PID", "abaco")
    
    if not username or not password:
        logger.warning(
            "CASCADE_USERNAME and CASCADE_PASSWORD not set. "
            "Manual download required."
        )
    
    return username, password, pid


def download_loan_tape(pid: str, output_dir: Path) -> Optional[Path]:
    """
    Download loan tape export from Cascade.
    
    Note: This function requires manual download or API integration.
    For now, it provides instructions for manual download.
    
    Args:
        pid: Portfolio ID
        output_dir: Directory to save the file
        
    Returns:
        Path to downloaded file, or None if manual download required
    """
    logger.info("Loan tape download requires manual process")
    logger.info(f"Please download from: {CASC ADE_LOAN_TAPE_URL}?pid={pid}")
    logger.info(f"Save file to: {output_dir}/loan_tape_{datetime.now().strftime('%Y%m%d')}.csv")
    
    # Check if file exists
    expected_file = output_dir / f"loan_tape_{datetime.now().strftime('%Y%m%d')}.csv"
    if expected_file.exists():
        logger.info(f"Found existing loan tape file: {expected_file}")
        return expected_file
    
    return None


def process_loan_tape(file_path: Path, output_dir: Path) -> pd.DataFrame:
    """
    Process loan tape using CascadeIngestion.
    
    Args:
        file_path: Path to loan tape CSV
        output_dir: Directory for processed output
        
    Returns:
        Processed DataFrame
    """
    logger.info(f"Processing loan tape: {file_path}")
    
    # Initialize ingestion
    ingestion = CascadeIngestion(
        data_dir=str(file_path.parent),
        strict_validation=False
    )
    
    # Set context
    ingestion.set_context(
        source="cascade_debt",
        portfolio="abaco",
        data_type="loan_tape"
    )
    
    # Ingest CSV
    df = ingestion.ingest_csv(file_path.name)
    
    if df.empty:
        logger.error("Failed to ingest loan tape")
        logger.error(f"Errors: {ingestion.errors}")
        return df
    
    logger.info(f"Ingested {len(df)} loan records")
    
    # Validate
    df = ingestion.validate_loans(df)
    
    # Check validation results
    if "_validation_passed" in df.columns:
        passed = df["_validation_passed"].sum()
        failed = len(df) - passed
        logger.info(f"Validation: {passed} passed, {failed} failed")
    
    # Save summary
    summary = ingestion.get_ingest_summary()
    summary_file = output_dir / f"loan_tape_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    import json
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved ingestion summary to: {summary_file}")
    
    # Save processed data
    output_file = output_dir / f"loan_tape_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    df.to_parquet(output_file, index=False)
    logger.info(f"Saved processed data to: {output_file}")
    
    return df


def process_financials(data_type: str, file_path: Path, output_dir: Path) -> pd.DataFrame:
    """
    Process financial statements (P&L or Balance Sheet).
    
    Args:
        data_type: Type of financial data ("profit_loss" or "balance_sheet")
        file_path: Path to financial data CSV
        output_dir: Directory for processed output
        
    Returns:
        Processed DataFrame
    """
    logger.info(f"Processing {data_type}: {file_path}")
    
    # For financial data, we might need different processing
    # For now, use basic CSV ingestion
    df = pd.read_csv(file_path)
    
    logger.info(f"Loaded {len(df)} financial records")
    
    # Save processed data
    output_file = output_dir / f"{data_type}_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    df.to_parquet(output_file, index=False)
    logger.info(f"Saved processed data to: {output_file}")
    
    return df


def main():
    """
    Main entry point for Cascade data ingestion.
    """
    parser = argparse.ArgumentParser(
        description="Ingest data from Cascade Debt platform"
    )
    parser.add_argument(
        "--loan-tape",
        action="store_true",
        help="Process loan tape export"
    )
    parser.add_argument(
        "--financials",
        action="store_true",
        help="Process financial statements"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all data sources"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/cascade",
        help="Output directory for processed data"
    )
    parser.add_argument(
        "--input-file",
        type=str,
        help="Input CSV file to process (skips download)"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Output directory: {output_dir}")
    
    # Get credentials
    username, password, pid = get_cascade_credentials()
    
    # Determine what to process
    process_all = args.all or (not args.loan_tape and not args.financials)
    
    if args.input_file:
        # Process provided file
        input_path = Path(args.input_file)
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            sys.exit(1)
        
        logger.info(f"Processing input file: {input_path}")
        
        # Determine type based on filename
        if "loan_tape" in input_path.name.lower():
            df = process_loan_tape(input_path, output_dir)
        else:
            df = process_financials("financial_data", input_path, output_dir)
        
        logger.info("Processing complete")
        sys.exit(0)
    
    if args.loan_tape or process_all:
        logger.info("=== Processing Loan Tape ===")
        logger.info("")
        logger.info("To download loan tape data:")
        logger.info(f"1. Navigate to: {CASCADE_LOAN_TAPE_URL}?pid={pid}")
        logger.info("2. Click Export button and select CSV format")
        logger.info(f"3. Save to: {output_dir}/loan_tape_YYYYMMDD.csv")
        logger.info(f"4. Run: python scripts/ingest_cascade.py --loan-tape --input-file {output_dir}/loan_tape_YYYYMMDD.csv")
        logger.info("")
    
    if args.financials or process_all:
        logger.info("=== Processing Financial Statements ===")
        logger.info("")
        logger.info("To download financial data:")
        logger.info(f"1. P&L: {CASCADE_PL_URL}?pid={pid}&tab=profit-%26-loss")
        logger.info(f"2. Balance Sheet: {CASCADE_BALANCE_SHEET_URL}?pid={pid}&tab=balance-sheet")
        logger.info("3. Click Export button and select CSV format")
        logger.info(f"4. Save to: {output_dir}/")
        logger.info("")
    
    logger.info("For automated ingestion, see CASCADE_DATA_SOURCES.md for API integration")


if __name__ == "__main__":
    main()
