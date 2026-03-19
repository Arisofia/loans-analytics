"""Audit real data fields for strategic_modules validation."""
import os
import warnings

import pandas as pd

warnings.filterwarnings("ignore")

loan = pd.read_csv('data/raw/loan_data.csv', low_memory=False)
real = pd.read_csv('data/raw/real_payment.csv', low_memory=False)
loan.columns = [c.strip().lower().replace(' ','_') for c in loan.columns]
real.columns = [c.strip().lower().replace(' ','_') for c in real.columns]
loan['disbursement_date'] = pd.to_datetime(loan['disbursement_date'], errors='coerce')
for c in ['outstanding_loan_value','disbursement_amount','tpv','interest_rate_apr','term','days_in_default']:
    if c in loan.columns:
        loan[c] = pd.to_numeric(loan[c], errors='coerce').fillna(0)
real['true_payment_date'] = pd.to_datetime(real['true_payment_date'], errors='coerce')
real['true_total_payment'] = pd.to_numeric(real['true_total_payment'], errors='coerce').fillna(0)

print("=== LOAN STATUS ===")
print(loan['loan_status'].value_counts().to_string())

print("\n=== TPV field ===")
print(loan['tpv'].describe().to_string())

print("\n=== TERM_UNIT ===")
print(loan['term_unit'].value_counts().to_string())

print("\n=== PAYMENT_FREQUENCY ===")
print(loan['payment_frequency'].value_counts().to_string())

print("\n=== PAR from days_in_default ===")
bal = loan['outstanding_loan_value']
dpd = loan['days_in_default']
total = bal.sum()
print(f"  PAR30 = {bal[dpd>=30].sum()/total*100:.2f}%")
print(f"  PAR60 = {bal[dpd>=60].sum()/total*100:.2f}%")
print(f"  PAR90 = {bal[dpd>=90].sum()/total*100:.2f}%")
print(f"  PAR180= {bal[dpd>=180].sum()/total*100:.2f}%")
print(f"  DPD>0 count: {(dpd>0).sum()}")

print("\n=== PAGADOR CONCENTRATION ===")
print(f"  Unique pagadores: {loan['pagador'].nunique()}")
top10 = loan.groupby('pagador')['outstanding_loan_value'].sum().sort_values(ascending=False).head(10)
for name, v in top10.items():
    print(f"  {str(name)[:40]:40s}: {v/total*100:.1f}%")
top1_pct = float(top10.iloc[0]/total*100)
top10_pct = float(top10.sum()/total*100)
print(f"  Top-1 concentration: {top1_pct:.1f}%")
print(f"  Top-10 concentration: {top10_pct:.1f}%")

print("\n=== ROTATION ===")
max_date = loan['disbursement_date'].max()
mask12 = loan['disbursement_date'] >= max_date - pd.DateOffset(months=12)
disb12 = float(loan.loc[mask12, 'disbursement_amount'].sum())
outstanding = float(loan['outstanding_loan_value'].sum())
print(f"  Disbursed in trailing 12m: {disb12:,.2f}")
print(f"  Total outstanding: {outstanding:,.2f}")
print(f"  Rotation = {disb12/outstanding:.2f}x" if outstanding else "  Rotation = N/A")

print("\n=== APR ===")
apr = loan['interest_rate_apr']
print(f"  mean={apr.mean():.4f}, median={apr.median():.4f}, min={apr.min():.4f}, max={apr.max():.4f}")
print(f"  Interpreted as monthly: annualized effective = {((1+apr.mean())**12-1)*100:.1f}%")
print("  Weighted annualized effective APR:")
w_apr = float((apr * bal).sum() / total)
print(f"    portfolio avg monthly rate: {w_apr:.4f} -> annual: {((1+w_apr)**12-1)*100:.1f}%")

print("\n=== REVENUE MONTHLY (real payments) ===")
real['month'] = real['true_payment_date'].dt.to_period('M')
monthly = real.groupby('month')['true_total_payment'].sum()
print(monthly.tail(12).to_string())

print("\n=== AUM MONTHLY (outstanding by disbursement month) ===")
loan['month'] = loan['disbursement_date'].dt.to_period('M')
aum = loan.groupby('month')['outstanding_loan_value'].sum()
print(aum.tail(12).to_string())

print("\n=== CE 6M: collected vs disbursed (proxy) ===")
recent_date = real['true_payment_date'].max()
mask6m = real['true_payment_date'] >= recent_date - pd.DateOffset(months=6)
collected6 = float(real.loc[mask6m, 'true_total_payment'].sum())
# Scheduled: sum of disbursement_amount for loans active in same period
mask6m_loan = loan['disbursement_date'] >= loan['disbursement_date'].max() - pd.DateOffset(months=6)
sched6 = float(loan.loc[mask6m_loan, 'disbursement_amount'].sum())
print(f"  Collected 6m: {collected6:,.2f}")
print(f"  Disbursed 6m (proxy for scheduled): {sched6:,.2f}")
print(f"  CE 6M proxy: {collected6/sched6*100:.1f}%" if sched6 else "  CE 6M: NO DATA (no scheduled column)")
print("  NOTE: no 'total_scheduled' column exists; using disbursement_amount as proxy")

print("\n=== PD model target (loan_status==Default) ===")
y_default = (loan['loan_status'].astype(str).str.lower() == 'default').astype(int)
print(f"  Defaults: {y_default.sum()}, Non-defaults: {(y_default==0).sum()}")

print("\n=== DATA FILES AVAILABLE ===")
for path in ['data/raw/loan_data.csv','data/raw/real_payment.csv','data/raw/customer.csv',
             'data/abaco/CONTROL_DE_MORA__VENTA_Y_RECUPERACION_-_INTERMEDIA.csv',
             'data/samples/abaco_sample_data_20260202.csv']:
    exists = os.path.exists(path)
    size = os.path.getsize(path)/1024 if exists else 0
    print(f"  {'OK' if exists else 'MISSING':6s} {path} ({size:.0f} KB)")
