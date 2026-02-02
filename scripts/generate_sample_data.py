#!/usr/bin/env python3
"""
Generate realistic sample loan data for testing and development.

Usage:
    python scripts/generate_sample_data.py --num-loans 500 --output data/raw/loans.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import argparse
import sys
from pathlib import Path


def generate_loan_data(
    num_loans: int = 100,
    start_date: str = "2024-01-01",
    end_date: str = "2026-01-31",
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate realistic loan data for testing.
    
    Creates a portfolio with realistic distributions:
    - Loan amounts: Log-normal distribution ($10K-$500K, centered around $50K-$100K)
    - Interest rates: Normal distribution (28%-45%, centered around 36%)
    - Status: 70% active, 20% delinquent, 5% defaulted, 5% closed
    - DPD: Correlated with status
    
    Args:
        num_loans: Number of loans to generate
        start_date: Start date for disbursements (YYYY-MM-DD)
        end_date: End date for disbursements (YYYY-MM-DD)
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with loan data
    """
    np.random.seed(seed)
    random.seed(seed)
    
    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = (end - start).days
    
    if date_range <= 0:
        raise ValueError("End date must be after start date")
    
    # Generate loan data
    loans = []
    for i in range(num_loans):
        # Random disbursement date
        days_offset = random.randint(0, date_range)
        disbursement = start + timedelta(days=days_offset)
        
        # Loan term (6-24 months, with preference for 12/18)
        term_months = random.choices(
            [6, 12, 18, 24],
            weights=[0.1, 0.4, 0.4, 0.1]
        )[0]
        maturity = disbursement + timedelta(days=term_months * 30)
        
        # Loan amount ($10K-$500K, log-normal distribution)
        # mean=11, sigma=0.5 gives good distribution around $50K-$100K
        amount = np.random.lognormal(mean=11, sigma=0.5)
        amount = max(10000, min(500000, amount))
        
        # Interest rate (28%-45%, normal distribution around 36%)
        interest_rate = np.random.normal(loc=36, scale=4)
        interest_rate = max(28, min(45, interest_rate))
        
        # Status distribution (realistic portfolio)
        status_weights = {
            'active': 0.70,      # 70% performing
            'delinquent': 0.20,  # 20% delinquent
            'defaulted': 0.05,   # 5% defaulted
            'closed': 0.05       # 5% closed/repaid
        }
        status = random.choices(
            list(status_weights.keys()),
            weights=list(status_weights.values())
        )[0]
        
        # Days past due based on status
        if status == 'active' or status == 'closed':
            dpd = 0
        elif status == 'delinquent':
            # Delinquent: 1-90 days
            dpd = random.randint(1, 90)
        else:  # defaulted
            # Defaulted: 91-365 days
            dpd = random.randint(91, 365)
        
        # Outstanding balance and total paid
        if status == 'closed':
            outstanding_balance = 0
            total_paid = amount
        else:
            # Outstanding: 20%-95% of original amount
            outstanding_balance = amount * random.uniform(0.2, 0.95)
            # Total paid: remaining amount
            total_paid = amount - outstanding_balance
        
        # Create loan record
        loan = {
            'loan_id': f'LOAN-{disbursement.year}-{i+1:04d}',
            'borrower_id': f'BRRW-{random.randint(1, num_loans//3):04d}',  # Some repeat borrowers
            'amount': round(amount, 2),
            'disbursement_date': disbursement.strftime('%Y-%m-%d'),
            'maturity_date': maturity.strftime('%Y-%m-%d'),
            'interest_rate': round(interest_rate, 2),
            'status': status,
            'days_past_due': dpd,
            'term_months': term_months,
            'outstanding_balance': round(outstanding_balance, 2),
            'total_paid': round(total_paid, 2),
            'organization_id': 'ORG-001'
        }
        loans.append(loan)
    
    df = pd.DataFrame(loans)
    return df


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate realistic sample loan data',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--num-loans',
        type=int,
        default=100,
        help='Number of loans to generate'
    )
    parser.add_argument(
        '--start-date',
        default='2024-01-01',
        help='Start date for disbursements (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        default='2026-01-31',
        help='End date for disbursements (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--output',
        default='data/raw/generated_loans.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.num_loans <= 0:
        print("Error: num-loans must be positive", file=sys.stderr)
        sys.exit(1)
    
    # Generate data
    print(f"Generating {args.num_loans} loans...")
    try:
        df = generate_loan_data(
            num_loans=args.num_loans,
            start_date=args.start_date,
            end_date=args.end_date,
            seed=args.seed
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(args.output, index=False)
    
    # Print summary
    print(f"\n✅ Generated {len(df)} loans")
    print(f"   Saved to: {args.output}")
    print(f"\nSummary:")
    print(f"  - Date range: {df['disbursement_date'].min()} to {df['disbursement_date'].max()}")
    print(f"  - Total amount: ${df['amount'].sum():,.2f}")
    print(f"  - Average loan: ${df['amount'].mean():,.2f}")
    print(f"  - Unique borrowers: {df['borrower_id'].nunique()}")
    print(f"\nStatus distribution:")
    for status, count in df['status'].value_counts().items():
        pct = count / len(df) * 100
        print(f"  - {status}: {count} ({pct:.1f}%)")
    print(f"\nTerm distribution:")
    for term, count in df['term_months'].value_counts().sort_index().items():
        pct = count / len(df) * 100
        print(f"  - {term} months: {count} ({pct:.1f}%)")
    
    # Print sample records
    print(f"\nSample records (first 3):")
    print(df.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
