import os

content = open('tests/unit/test_kpi_formula_engine_ssot.py', encoding='utf-8').read()

new_tests = '''

def test_comparison_formula_uses_latest_and_previous_month_balances() -> None:
    df = pd.DataFrame(
        {
            "measurement_date": ["2025-01-05", "2025-01-20", "2025-02-10", "2025-02-19"],
            "outstanding_balance": [100.0, 150.0, 200.0, 100.0],
        }
    )
    reg = {"version": "1", "test_kpis": {"growth": {"formula": "(current_month_balance - previous_month_balance) / previous_month_balance * 100", "unit": "pct"}}}
    engine = KPIFormulaEngine(df, registry_data=reg)
    result = engine.calculate_kpi("growth")
    
    assert float(result["value"]) == pytest.approx(20.0)

def test_comparison_formula_raises_when_previous_month_is_zero() -> None:
    df = pd.DataFrame(
        {
            "measurement_date": ["2025-02-01", "2025-02-15"],
            "outstanding_balance": [500.0, 500.0],
        }
    )
    reg = {"version": "1", "test_kpis": {"growth": {"formula": "(current_month_balance - previous_month_balance) / previous_month_balance * 100", "unit": "pct"}}}
    engine = KPIFormulaEngine(df, registry_data=reg)
    
    with pytest.raises((ValueError, KPIFormulaError), match="calculation failed|Division by zero"):
        engine.calculate_kpi("growth")

def test_dpd_bucket_formulas_support_range_logic_via_aggregation_deltas() -> None:
    df = pd.DataFrame(
        {
            "dpd": [0, 15, 45, 95],
            "outstanding_balance": [100.0, 200.0, 300.0, 400.0],
        }
    )
    reg = {
        "version": "1", 
        "test_kpis": {
            "f_1_30": {"formula": "(SUM(outstanding_balance WHERE dpd <= 30) - SUM(outstanding_balance WHERE dpd <= 0)) / SUM(outstanding_balance) * 100", "unit": "pct"},
            "f_31_60": {"formula": "(SUM(outstanding_balance WHERE dpd <= 60) - SUM(outstanding_balance WHERE dpd <= 30)) / SUM(outstanding_balance) * 100", "unit": "pct"},
            "f_61_90": {"formula": "(SUM(outstanding_balance WHERE dpd <= 90) - SUM(outstanding_balance WHERE dpd <= 60)) / SUM(outstanding_balance) * 100", "unit": "pct"},
            "f_90_plus": {"formula": "SUM(outstanding_balance WHERE dpd > 90) / SUM(outstanding_balance) * 100", "unit": "pct"},
        }
    }
    engine = KPIFormulaEngine(df, registry_data=reg)
    
    assert float(engine.calculate_kpi("f_1_30")["value"]) == pytest.approx(20.0)
    assert float(engine.calculate_kpi("f_31_60")["value"]) == pytest.approx(30.0)
    assert float(engine.calculate_kpi("f_61_90")["value"]) == pytest.approx(0.0)
    assert float(engine.calculate_kpi("f_90_plus")["value"]) == pytest.approx(40.0)

def test_where_clause_supports_or_conditions_for_npl_ratio_style_formulas() -> None:
    df = pd.DataFrame(
        {
            "dpd": [10, 95, 0],
            "status": ["active", "delinquent", "defaulted"],
            "outstanding_balance": [100.0, 200.0, 300.0],
        }
    )
    reg = {"version": "1", "test_kpis": {"npl": {"formula": "SUM(outstanding_balance WHERE dpd > 90 OR status = 'defaulted') / SUM(outstanding_balance) * 100", "unit": "pct"}}}
    engine = KPIFormulaEngine(df, registry_data=reg)
    result = engine.calculate_kpi("npl")
    
    assert float(result["value"]) == pytest.approx(83.33333333)

def test_where_clause_supports_and_conditions() -> None:
    df = pd.DataFrame(
        {
            "dpd": [10, 95, 0],
            "status": ["active", "delinquent", "defaulted"],
            "outstanding_balance": [100.0, 200.0, 300.0],
        }
    )
    reg = {"version": "1", "test_kpis": {"npl_and": {"formula": "SUM(outstanding_balance WHERE dpd > 30 AND status != 'defaulted') / SUM(outstanding_balance) * 100", "unit": "pct"}}}
    engine = KPIFormulaEngine(df, registry_data=reg)
    result = engine.calculate_kpi("npl_and")
    
    assert float(result["value"]) == pytest.approx(33.33333333)
'''

with open('tests/unit/test_kpi_formula_engine_ssot.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

if os.path.exists('tests/test_pipeline_formula_engine.py'):
    os.remove('tests/test_pipeline_formula_engine.py')
print('Migration complete')
