import sys
from pathlib import Path
import pandas as pd
import json
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from backend.python.models.woe_iv_engine import WoEIVEngine
from backend.python.features.feature_store import FeatureStore

def main():
    loan_path = REPO_ROOT / 'data' / 'raw' / 'loan_data.csv'
    cust_path = REPO_ROOT / 'data' / 'raw' / 'customer_data.csv'
    if not loan_path.exists() or not cust_path.exists():
        print('Error: Data files not found.')
        return
    loans = pd.read_csv(loan_path, low_memory=False)
    cust = pd.read_csv(cust_path, low_memory=False)
    cust_cols = ['Loan ID', 'Equifax Score', 'Industry', 'Client Type']
    cust_subset = cust[cust_cols].drop_duplicates(subset=['Loan ID'])
    df = pd.merge(loans, cust_subset, on='Loan ID', how='left')
    col_map = {'Disbursement Amount': 'principal_amount', 'Interest Rate APR': 'interest_rate', 'Term': 'term_months', 'Outstanding Loan Value': 'outstanding_balance', 'TPV': 'tpv', 'Equifax Score': 'equifax_score'}
    df = df.rename(columns=col_map)
    for col in ['collateral_value', 'last_payment_amount', 'total_scheduled', 'origination_fee', 'days_past_due']:
        if col not in df.columns:
            df[col] = 0.0
    fs = FeatureStore()
    features_df = fs.compute_features(df)
    status_col = 'Loan Status'
    features_df['is_default'] = (df[status_col].str.strip().str.lower() == 'default').astype(int)
    engine = WoEIVEngine(target_col='is_default')
    feature_cols = [c for c in features_df.columns if c not in ['is_default', 'loan_id', 'days_past_due', 'outstanding_balance']]
    iv_ranking = engine.analyze_all(features_df, feature_cols)
    print('\n' + '=' * 50)
    print('  RANKING DE PODER PREDICTIVO (INFORMATION VALUE)')
    print('=' * 50)
    print(f"{'Variable':<25} | {'IV':<10} | {'Interpretación'}")
    print('-' * 50)
    for feat, iv in iv_ranking.items():
        interpretation = engine.interpret_iv(iv)
        print(f'{feat:<25} | {iv:<10.4f} | {interpretation}')
    output_dir = REPO_ROOT / 'models' / 'risk'
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / 'iv_ranking.json', 'w') as f:
        json.dump(iv_ranking, f, indent=2)
if __name__ == '__main__':
    main()
