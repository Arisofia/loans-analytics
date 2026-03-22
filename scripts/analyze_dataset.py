import pandas as pd
from pathlib import Path

csv_path = Path('data/raw/loan_data.csv')
if csv_path.exists():
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"Analysis for {csv_path}:")
    
    target = (df['Loan Status'].str.strip().str.lower() == 'default').astype(int)
    print(f"Total defaults: {target.sum()}")

    # Check Days in Default
    dpd = pd.to_numeric(df['Days in Default'], errors='coerce').fillna(0)
    print("\nDays in Default vs Default Status:")
    print(pd.crosstab(dpd > 0, target, rownames=['Has DPD'], colnames=['Is Default']))
    
    # Check Outstanding Loan Value
    bal = pd.to_numeric(df['Outstanding Loan Value'], errors='coerce').fillna(0)
    print("\nOutstanding Value > 0 vs Default Status:")
    print(pd.crosstab(bal > 0, target, rownames=['Has Balance'], colnames=['Is Default']))

    # Statistics for defaults
    print("\nDPD stats for defaults:")
    print(dpd[target == 1].describe())
    
else:
    print(f"File not found: {csv_path}")
