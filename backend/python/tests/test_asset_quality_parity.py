from __future__ import annotations
import pandas as pd
from backend.python.kpis.advanced_risk import calculate_advanced_risk_metrics
from backend.python.kpis.graph_analytics import npl_benchmarks
from backend.python.kpis.portfolio_analytics import credit_line_category_kpis
from backend.python.kpis.ssot_asset_quality import calculate_asset_quality_metrics
from backend.python.kpis.strategic_modules import build_compliance_dashboard

def _loans_snapshot() -> pd.DataFrame:
    return pd.DataFrame({'loan_id': ['L1', 'L2', 'L3', 'L4'], 'outstanding_loan_value': [100.0, 200.0, 300.0, 400.0], 'principal_balance': [100.0, 200.0, 300.0, 400.0], 'days_past_due': [10, 35, 95, 210], 'days_in_default': [10, 35, 95, 210], 'loan_status': ['current', 'current', 'delinquent', 'defaulted'], 'pagador': ['P1', 'P2', 'P2', 'P3'], 'categorialineacredito': ['A', 'A', 'A', 'A'], 'disbursement_amount': [120.0, 220.0, 320.0, 420.0], 'interest_rate_apr': [0.3, 0.32, 0.34, 0.36], 'term': [45, 55, 65, 75]})

def _intermedia_from_loans(loans: pd.DataFrame) -> pd.DataFrame:
    cutoff = pd.Timestamp('2026-03-13')
    due_dates = cutoff - pd.to_timedelta(pd.to_numeric(loans['days_past_due'], errors='coerce'), unit='D')
    return pd.DataFrame({'TotalSaldoVigente': pd.to_numeric(loans['outstanding_loan_value'], errors='coerce'), 'FechaPagoProgramado': due_dates.dt.strftime('%Y-%m-%d')})

def test_asset_quality_metrics_parity_across_consumers() -> None:
    loans = _loans_snapshot()
    balance = pd.to_numeric(loans['outstanding_loan_value'], errors='coerce')
    dpd = pd.to_numeric(loans['days_past_due'], errors='coerce')
    status = loans['loan_status'].astype(str)
    canonical = calculate_asset_quality_metrics(balance, dpd, actor='parity_test', metric_aliases=('par30', 'par60', 'par90', 'npl90', 'npl180'), status=status)
    advanced = calculate_advanced_risk_metrics(loans)
    assert advanced['par30'] == round(canonical['par30'], 2)
    assert advanced['par60'] == round(canonical['par60'], 2)
    assert advanced['par90'] == round(canonical['par90'], 2)
    compliance = build_compliance_dashboard(loans, payments_df=pd.DataFrame())
    assert compliance['actuals']['par30_pct'] == round(canonical['par30'], 1)
    assert compliance['actuals']['par90_pct'] == round(canonical['par90'], 1)
    assert compliance['actuals']['npl_180_pct'] == round(canonical['npl180'], 1)
    graph = npl_benchmarks(_intermedia_from_loans(loans))
    assert graph['npl_90_pct'] == round(canonical['npl90'], 2)
    assert graph['npl_180_pct'] == round(canonical['npl180'], 2)
    category = credit_line_category_kpis(loans)
    row = category['by_category'][0]
    assert row['par30_pct'] == round(canonical['par30'], 1)
    assert row['par90_pct'] == round(canonical['par90'], 1)
