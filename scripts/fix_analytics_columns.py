import pandas as pd
import sys

def add_missing_analytics_columns(input_path, output_path):
    df = pd.read_csv(input_path)
    required = [
        'loan_amount',
        'appraised_value',
        'borrower_income',
        'monthly_debt',
        'loan_status',
        'interest_rate',
        'principal_balance'
    ]
    # Add missing columns with default values (NaN or placeholder)
    for col in required:
        if col not in df.columns:
            if col == 'loan_status':
                df[col] = 'unknown'
            else:
                df[col] = float('nan')
    df.to_csv(output_path, index=False)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python scripts/fix_analytics_columns.py <input_csv> <output_csv>')
        sys.exit(1)
    add_missing_analytics_columns(sys.argv[1], sys.argv[2])
