#!/usr/bin/env python3
"""
Demonstration script for the FinancialAnalyzer class.
This script generates sample loan data and applies segmentation,
DPD bucketing, and weighted statistic calculations.
"""

import sys
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.financial_analysis import FinancialAnalyzer

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    print("--- ABACO Financial Analysis Demo ---\n")
    
    # 1. Create Sample Data
    today = datetime.now().date()
    data = {
        'loan_id': [101, 102, 103, 104, 105],
        'customer_id': ['C1', 'C2', 'C1', 'C3', 'C2'],
        'outstanding_balance': [5000.0, 15000.0, 200.0, 50000.0, 12000.0],
        'line_amount': [10000.0, 20000.0, 5000.0, 50000.0, 15000.0],
        'days_past_due': [0, 45, 5, 120, 0],
        'apr': [0.12, 0.15, 0.18, 0.10, 0.14],
        'loan_count': [2, 5, 2, 1, 5],
        'last_active_date': [today, today, today, today - timedelta(days=100), today]
    }
    df = pd.DataFrame(data)
    print(f"Loaded {len(df)} loans.")

    analyzer = FinancialAnalyzer()

    # 2. Enrich Data (Buckets, Segments, Utilization)
    print("\n[1] Enriching Master Dataframe...")
    enriched_df = analyzer.enrich_master_dataframe(df)
    
    cols_to_show = ['loan_id', 'dpd_bucket', 'exposure_segment', 'line_utilization', 'client_type']
    print(enriched_df[cols_to_show].to_string(index=False))

    # 3. Calculate Weighted Stats
    print("\n[2] Calculating Weighted APR by Balance...")
    weighted_stats = analyzer.calculate_weighted_stats(enriched_df, metrics=['apr'])
    print(weighted_stats.to_string(index=False))

    # 4. Calculate Concentration Risk (HHI)
    print("\n[3] Calculating Portfolio Concentration (HHI)...")
    hhi = analyzer.calculate_hhi(enriched_df, 'customer_id')
    print(f"HHI Score: {hhi:.2f} (Scale 0-10,000)")

if __name__ == "__main__":
    main()