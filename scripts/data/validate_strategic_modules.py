"""Full validation of strategic_modules.py against real Abaco data."""
import sys, warnings, json
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')
import pandas as pd, numpy as np
from datetime import datetime, timezone
from pathlib import Path

loan = pd.read_csv('data/raw/loan_data.csv', low_memory=False)
real = pd.read_csv('data/raw/real_payment.csv', low_memory=False)
loan.columns = [c.strip().lower().replace(' ','_') for c in loan.columns]
real.columns = [c.strip().lower().replace(' ','_') for c in real.columns]
for c in ['disbursement_date']:
    if c in loan.columns: loan[c] = pd.to_datetime(loan[c], errors='coerce')
for c in ['true_payment_date']:
    if c in real.columns: real[c] = pd.to_datetime(real[c], errors='coerce')
for nc in ['outstanding_loan_value','disbursement_amount','tpv','interest_rate_apr','term','days_in_default']:
    if nc in loan.columns: loan[nc] = pd.to_numeric(loan[nc], errors='coerce').fillna(0)
for nc in ['true_total_payment']:
    if nc in real.columns: real[nc] = pd.to_numeric(real[nc], errors='coerce').fillna(0)

from backend.python.kpis.strategic_modules import (
    predict_kpis, build_compliance_dashboard, build_next_steps_plan,
    detect_exposure_weighted_outliers, build_pd_model,
)

print("=" * 70)
print("3.1 OUTLIER DETECTION (exposure-weighted Z-score)")
outliers = detect_exposure_weighted_outliers(loan)
for var, s in outliers['summary'].items():
    print(f"  {var:16s}: weighted_mean={s['mean_w']:.4f}  outliers={s['outlier_count']:4d}  bal=${s['outlier_balance_usd']:>12,.2f}")
print(f"  TOTAL flagged: {outliers['total_flagged']} loans  ${outliers['total_flagged_balance_usd']:,.2f}")

print()
print("=" * 70)
print("3.2 PD MODEL (logistic regression, k-fold AUC)")
pd_result = build_pd_model(loan)
print(f"  Status:  {pd_result['status']}")
if pd_result['status'] == 'ok':
    print(f"  AUC:     {pd_result['auc_mean']:.3f} +/- {pd_result['auc_std']:.3f}")
    print(f"  Folds:   {pd_result['auc_by_fold']}")
    print(f"  Features:{pd_result['features_used']}")
    print(f"  Imp:     {pd_result['feature_importance']}")
    print(f"  n_def={pd_result['n_defaults']}  n_nondef={pd_result['n_non_defaults']}  dr={pd_result['default_rate_actual']}%")
    high_risk = sum(1 for r in pd_result['pd_scores'] if r['pd_score'] >= 0.5)
    print(f"  PD>=50% loans: {high_risk}")
else:
    print(f"  {pd_result.get('message','')}")

print()
print("=" * 70)
print("7.0 PREDICTIVE KPIs (linear trend, +/-1.5 sigma)")
forecast = predict_kpis(loan, real, horizon_months=6)
print(f"  AUM forecast months: {len(forecast['aum_forecast'])} (training: {forecast['training_months']['aum']})")
print(f"  Revenue forecast months: {len(forecast['revenue_forecast'])} (training: {forecast['training_months']['revenue']})")
print(f"  PAR30 forecast months: {len(forecast['par30_forecast'])} (training: {forecast['training_months']['par30']})")
print()
print("  Revenue forecast (6m):")
for r in forecast['revenue_forecast']:
    print(f"    {r['month']}  ${r['value']:>12,.0f}  [{r['lower']:>12,.0f} - {r['upper']:>12,.0f}]")
print()
print("  AUM (disbursement) forecast (6m):")
for r in forecast['aum_forecast']:
    print(f"    {r['month']}  ${r['value']:>12,.0f}  [{r['lower']:>12,.0f} - {r['upper']:>12,.0f}]")
print()
print("  Data notes:")
for k, v in forecast.get('data_notes', {}).items():
    print(f"    {k}: {v}")

print()
print("=" * 70)
print("7.1 COMPLIANCE DASHBOARD (target vs actual)")
compliance = build_compliance_dashboard(loan, real)
par_source = compliance.get('data_sources', {}).get('par', 'NO_DATA')
print(f"  DPD source resolved: {par_source}")
print(f"  Summary: ok={compliance['summary'].get('ok',0)}  warning={compliance['summary'].get('warning',0)}  breach={compliance['summary'].get('breach',0)}  no_data={compliance['summary'].get('no_data',0)}")
print()
print(f"  {'Metric':30s}  {'Actual':>10}  {'Target':>8}  {'Variance':>10}  {'Status':10}  Owner")
print("  " + "-"*85)
for row in compliance['metrics']:
    actual_str = f"{row['actual']:.1f}" if isinstance(row['actual'], float) else str(row['actual'])
    var_str    = f"{row['variance']:+.2f}" if row['variance'] is not None else "—"
    print(f"  {row['metric']:30s}  {actual_str:>10}  {row['target']:>8.1f}  {var_str:>10}  {row['status']:10}  {row['owner']}")
print()
print("  Data sources:")
for k, v in compliance.get('data_sources', {}).items():
    print(f"    {k:14s}: {v}")
print()
print("  Variance decomposition:")
for metric, vd in compliance.get('variance_decomposition', {}).items():
    print(f"    {metric}: driver='{vd['driver']}' magnitude={vd['magnitude']:+.1f}")

print()
print("=" * 70)
print("7.2 NEXT-STEPS PLAN")
plan = build_next_steps_plan(forecast, compliance, outliers['alerts'], pd_result)
print(f"  Actions: {plan['action_count']}  Sources: {plan['sources_used']}")
for a in plan['actions']:
    print(f"  [{a['priority']}] [{a['impact'].upper():6}|{a['effort']:6}] {a['area']:22} {a['action'][:68]}")

print()
print("=" * 70)
print("GAPS SUMMARY")
gaps = []
# PAR forecast
if forecast['training_months']['par30'] < 3:
    gaps.append("PAR forecast: insufficient time-series history — single DPD snapshot, no historical PAR archives")
# Utilization
util_val = compliance['actuals'].get('utilization_pct')
if util_val is None:
    gaps.append("Utilization: NO_DATA — loan_data.csv has no porcentaje_utilizado or lineacredito column")
# DSCR
gaps.append("DSCR: NO_DATA — requires net income / debt service data, not in loan tape")
# PD AUC
if pd_result.get('status') == 'ok' and pd_result.get('auc_mean', 0) < 0.65:
    gaps.append(f"PD Model AUC={pd_result['auc_mean']:.3f} < 0.65 target — add Equifax score + payment cadence features")
# INTERMEDIA data
gaps.append("INTERMEDIA snapshot: file not available locally — concentration/DPD from INTERMEDIA not computed")
# customer.csv
gaps.append("customer.csv: file not available locally — customer-level features (age, industry) excluded from PD model")
# CE 6M
ce = compliance['actuals'].get('ce_6m_pct')
if ce is not None:
    gaps.append(f"CE 6M: proxy calculation (collected/disbursed_{'{6m}'}={ce:.1f}%) — no total_scheduled column; use ValorAprobado join for exact value")

for i, g in enumerate(gaps, 1):
    print(f"  GAP {i}: {g}")
