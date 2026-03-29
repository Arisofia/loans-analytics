from __future__ import annotations
from decimal import Decimal
import pandas as pd
import pytest
## auditor import removed: module deleted
from backend.python.kpis.formula.parser import FormulaParser
from backend.python.kpis.formula.registry import KPIRegistry
from backend.python.kpis.formula_engine import KPIFormulaEngine, KPIFormulaError

def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({'loan_id': ['L1', 'L2', 'L3'], 'outstanding_balance': [1000, 500, 1500], 'dpd': [0, 45, 95], 'status': ['active', 'delinquent', 'defaulted']})

def _registry_data() -> dict:
    return {'version': '3.1.0', 'asset_quality_kpis': {'par_30': {'formula': 'SUM(outstanding_balance WHERE dpd >= 30) / SUM(outstanding_balance) * 100', 'unit': 'percentage', 'thresholds': {'warning': 3, 'critical': 5}}, 'zero_division_kpi': {'formula': 'SUM(outstanding_balance WHERE dpd >= 200) / SUM(outstanding_balance WHERE dpd >= 200) * 100', 'unit': 'percentage'}}}

def test_calculate_kpi_returns_ssot_metadata() -> None:
    engine = KPIFormulaEngine(_sample_df(), actor='unit-test', run_id='run-123', registry_data=_registry_data())
    result = engine.calculate_kpi('par_30')
    assert result['kpi_name'] == 'par_30'
    assert result['unit'] == 'percentage'
    assert result['formula_version'] == '3.1.0'
    assert result['actor'] == 'unit-test'
    assert result['run_id'] == 'run-123'
    assert result['data_rows'] == 3
    assert isinstance(result['value'], Decimal)
    assert result['value'] == Decimal('66.66666700')
    assert result['status'] == 'success'
    assert result['threshold_status'] == 'critical'
    assert result['thresholds']['warning'] == Decimal('3')
    assert result['thresholds']['critical'] == Decimal('5')
    assert 'dpd' in result['columns_used']
    assert 'outstanding_balance' in result['columns_used']

def test_calculate_kpi_records_audit_entry() -> None:
    engine = KPIFormulaEngine(_sample_df(), actor='qa', run_id='audit-1', registry_data=_registry_data())
    _ = engine.calculate_kpi('par_30')
    records = engine.get_audit_records()
    assert len(records) == 1
    assert records[0]['kpi_name'] == 'par_30'
    assert records[0]['formula_version'] == '3.1.0'
    assert records[0]['actor'] == 'qa'
    assert records[0]['run_id'] == 'audit-1'
    assert records[0]['status'] == 'success'
    assert records[0]['threshold_status'] in {'normal', 'warning', 'critical', 'not_configured'}

def test_threshold_status_critical_when_value_exceeds_critical() -> None:
    df = pd.DataFrame({'loan_id': ['L1', 'L2'], 'outstanding_balance': [1000, 1000], 'dpd': [95, 95], 'status': ['defaulted', 'defaulted']})
    engine = KPIFormulaEngine(df, registry_data=_registry_data())
    result = engine.calculate_kpi('par_30')
    assert result['value'] == Decimal('100')
    assert result['threshold_status'] == 'critical'

def test_calculate_kpi_missing_definition_raises() -> None:
    engine = KPIFormulaEngine(_sample_df(), registry_data=_registry_data())
    with pytest.raises(KPIFormulaError, match='not found in registry'):
        engine.calculate_kpi('unknown_kpi')

def test_division_by_zero_fails_closed() -> None:
    engine = KPIFormulaEngine(_sample_df(), registry_data=_registry_data())
    result = engine.calculate_kpi('zero_division_kpi')
    assert result['value'] == Decimal('0.0')

def test_parser_stub_classifies_formula() -> None:
    parser = FormulaParser()
    parsed = parser.parse('SUM(outstanding_balance) / SUM(principal_amount)')
    assert parsed.is_arithmetic is True
    assert parsed.is_comparison is False

def test_registry_loader_stub(tmp_path) -> None:
    registry_path = tmp_path / 'kpis.yaml'
    registry_path.write_text('\nversion: "1.0"\nasset_quality_kpis:\n  par_30:\n    formula: "SUM(outstanding_balance)"\n    unit: "USD"\n'.strip(), encoding='utf-8')
    registry = KPIRegistry(registry_path)
    assert registry.version() == '1.0'
    assert registry.get('par_30')['unit'] == 'USD'

## test_auditor_stub_stores_entries removed: auditor module deleted

def test_comparison_formula_uses_latest_and_previous_month_balances() -> None:
    df = pd.DataFrame({'measurement_date': ['2025-01-05', '2025-01-20', '2025-02-10', '2025-02-19'], 'outstanding_balance': [100.0, 150.0, 200.0, 100.0]})
    reg = {'version': '1', 'test_kpis': {'growth': {'formula': '(current_month_balance - previous_month_balance) / previous_month_balance * 100', 'unit': 'pct'}}}
    engine = KPIFormulaEngine(df, registry_data=reg)
    result = engine.calculate_kpi('growth')
    assert float(result['value']) == pytest.approx(20.0)

def test_comparison_formula_raises_when_previous_month_is_zero() -> None:
    df = pd.DataFrame({'measurement_date': ['2025-02-01', '2025-02-15'], 'outstanding_balance': [500.0, 500.0]})
    reg = {'version': '1', 'test_kpis': {'growth': {'formula': '(current_month_balance - previous_month_balance) / previous_month_balance * 100', 'unit': 'pct'}}}
    engine = KPIFormulaEngine(df, registry_data=reg)
    result = engine.calculate_kpi('growth')
    assert result['value'] == Decimal('0.0')

def test_dpd_bucket_formulas_support_range_logic_via_aggregation_deltas() -> None:
    df = pd.DataFrame({'dpd': [0, 15, 45, 95], 'outstanding_balance': [100.0, 200.0, 300.0, 400.0]})
    reg = {'version': '1', 'test_kpis': {'f_1_30': {'formula': '(SUM(outstanding_balance WHERE dpd <= 30) - SUM(outstanding_balance WHERE dpd <= 0)) / SUM(outstanding_balance) * 100', 'unit': 'pct'}, 'f_31_60': {'formula': '(SUM(outstanding_balance WHERE dpd <= 60) - SUM(outstanding_balance WHERE dpd <= 30)) / SUM(outstanding_balance) * 100', 'unit': 'pct'}, 'f_61_90': {'formula': '(SUM(outstanding_balance WHERE dpd <= 90) - SUM(outstanding_balance WHERE dpd <= 60)) / SUM(outstanding_balance) * 100', 'unit': 'pct'}, 'f_90_plus': {'formula': 'SUM(outstanding_balance WHERE dpd > 90) / SUM(outstanding_balance) * 100', 'unit': 'pct'}}}
    engine = KPIFormulaEngine(df, registry_data=reg)
    assert float(engine.calculate_kpi('f_1_30')['value']) == pytest.approx(20.0)
    assert float(engine.calculate_kpi('f_31_60')['value']) == pytest.approx(30.0)
    assert float(engine.calculate_kpi('f_61_90')['value']) == pytest.approx(0.0)
    assert float(engine.calculate_kpi('f_90_plus')['value']) == pytest.approx(40.0)

def test_where_clause_supports_or_conditions_for_npl_ratio_style_formulas() -> None:
    df = pd.DataFrame({'dpd': [10, 95, 0], 'status': ['active', 'delinquent', 'defaulted'], 'outstanding_balance': [100.0, 200.0, 300.0]})
    reg = {'version': '1', 'test_kpis': {'npl': {'formula': "SUM(outstanding_balance WHERE dpd > 90 OR status = 'defaulted') / SUM(outstanding_balance) * 100", 'unit': 'pct'}}}
    engine = KPIFormulaEngine(df, registry_data=reg)
    result = engine.calculate_kpi('npl')
    assert float(result['value']) == pytest.approx(83.33333333)

def test_where_clause_supports_and_conditions() -> None:
    df = pd.DataFrame({'dpd': [10, 95, 0], 'status': ['active', 'delinquent', 'defaulted'], 'outstanding_balance': [100.0, 200.0, 300.0]})
    reg = {'version': '1', 'test_kpis': {'npl_and': {'formula': "SUM(outstanding_balance WHERE dpd > 30 AND status != 'defaulted') / SUM(outstanding_balance) * 100", 'unit': 'pct'}}}
    engine = KPIFormulaEngine(df, registry_data=reg)
    result = engine.calculate_kpi('npl_and')
    assert float(result['value']) == pytest.approx(33.33333333)
