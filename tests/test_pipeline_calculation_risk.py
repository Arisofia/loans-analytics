import types
from decimal import ROUND_HALF_UP, Decimal
import pandas as pd
import pytest
import numpy as np
import backend.src.pipeline.calculation as calc_module
from backend.src.pipeline.calculation import CalculationPhase
from backend.python.kpis.engine import KPIEngineV2

def test_ltv_sintetico_basic_calculation():
    df = pd.DataFrame({'capital_desembolsado': [100.0, 200.0], 'valor_nominal_factura': [200.0, 500.0], 'tasa_dilucion': [0.1, 0.2]})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert result.iloc[0] == pytest.approx(100 / 180, rel=0.0001)
    assert result.iloc[1] == pytest.approx(0.5, rel=0.0001)

def test_ltv_sintetico_zero_adjusted_value_is_opaque_and_nan():
    df = pd.DataFrame({'capital_desembolsado': [50.0], 'valor_nominal_factura': [100.0], 'tasa_dilucion': [1.0]})
    result = CalculationPhase._calculate_ltv_sintetico(df)
    assert pd.isna(result.iloc[0])
    assert df.loc[0, 'ltv_sintetico_is_opaque'] == 1

def test_ltv_sintetico_missing_denominator_is_opaque_and_nan():
    df = pd.DataFrame({'capital_desembolsado': [50.0], 'valor_nominal_factura': [None], 'tasa_dilucion': [0.1]})
    result = CalculationPhase._calculate_ltv_sintetico(df)
    assert pd.isna(result.iloc[0])
    assert df.loc[0, 'ltv_sintetico_is_opaque'] == 1

def test_ltv_sintetico_missing_columns_returns_empty_series():
    df = pd.DataFrame({'capital_desembolsado': [100.0]})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert result.empty

def test_ltv_sintetico_empty_dataframe():
    df = pd.DataFrame(columns=['capital_desembolsado', 'valor_nominal_factura', 'tasa_dilucion'])
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert len(result) == 0

def test_ltv_sintetico_strict_positive_denominator_rule():
    df = pd.DataFrame({'capital_desembolsado': [100.0, 100.0], 'valor_nominal_factura': [100.0, -50.0], 'tasa_dilucion': [1.1, 0.1]})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert np.isnan(result.iloc[0])
    assert np.isnan(result.iloc[1])
    assert (df['ltv_sintetico_is_opaque'] == 1).all()

def test_ltv_sintetico_valid_row_not_nan():
    df = pd.DataFrame({'capital_desembolsado': [100.0], 'valor_nominal_factura': [200.0], 'tasa_dilucion': [0.1]})
    result = CalculationPhase._calculate_ltv_sintetico(df)
    assert not pd.isna(result.iloc[0])
    assert result.iloc[0] == pytest.approx(100 / 180, rel=0.0001)

def test_ltv_sintetico_zero_nominal_returns_nan():
    df = pd.DataFrame({'capital_desembolsado': [50.0], 'valor_nominal_factura': [0.0], 'tasa_dilucion': [0.0]})
    result = CalculationPhase._calculate_ltv_sintetico(df)
    assert pd.isna(result.iloc[0])

def test_ltv_sintetico_invalid_mask_fully_diluted():
    df = pd.DataFrame({'valor_nominal_factura': [100.0, 200.0], 'tasa_dilucion': [1.0, 0.1]})
    mask = CalculationPhase._ltv_sintetico_invalid_mask(df)
    assert mask.iloc[0]
    assert not mask.iloc[1]

def test_ltv_sintetico_invalid_mask_zero_nominal():
    df = pd.DataFrame({'valor_nominal_factura': [0.0], 'tasa_dilucion': [0.5]})
    mask = CalculationPhase._ltv_sintetico_invalid_mask(df)
    assert mask.iloc[0]

def test_ltv_sintetico_invalid_mask_no_invalids_all_valid():
    df = pd.DataFrame({'valor_nominal_factura': [100.0, 200.0], 'tasa_dilucion': [0.0, 0.2]})
    mask = CalculationPhase._ltv_sintetico_invalid_mask(df)
    assert not mask.any()

def test_ltv_sintetico_invalid_mask_missing_columns_returns_empty_series():
    df = pd.DataFrame({'capital_desembolsado': [100.0]})
    mask = CalculationPhase._ltv_sintetico_invalid_mask(df)
    assert mask.empty

def test_ltv_sintetico_invalid_mask_empty_dataframe():
    df = pd.DataFrame(columns=['valor_nominal_factura', 'tasa_dilucion'])
    mask = CalculationPhase._ltv_sintetico_invalid_mask(df)
    assert mask.empty

def test_ltv_sintetico_nan_and_mask_are_consistent():
    df = pd.DataFrame({'capital_desembolsado': [100.0, 50.0, 200.0], 'valor_nominal_factura': [200.0, 0.0, 500.0], 'tasa_dilucion': [0.1, 0.0, 1.0]})
    ltv = CalculationPhase._calculate_ltv_sintetico(df)
    mask = CalculationPhase._ltv_sintetico_invalid_mask(df)
    assert ltv[mask].isna().all()
    assert ltv[~mask].notna().all()

def test_velocity_of_default_basic_diff():
    df_ts = pd.DataFrame({'period': ['2025-01', '2025-02', '2025-03'], 'default_rate': [1.0, 2.5, 2.0]})
    vd = CalculationPhase._calculate_velocity_of_default(df_ts)
    assert pd.isna(vd.iloc[0])
    assert vd.iloc[1] == pytest.approx(1.5)
    assert vd.iloc[2] == pytest.approx(-0.5)

def test_ltv_sintetico_preserves_indices():
    df = pd.DataFrame({'capital_desembolsado': [100.0], 'valor_nominal_factura': [200.0], 'tasa_dilucion': [0.0]}, index=[42])
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert result.index[0] == 42

def test_compute_portfolio_velocity_of_default_uses_as_of_date():
    from decimal import Decimal
    engine = KPIEngineV2.__new__(KPIEngineV2)
    df = pd.DataFrame({'as_of_date': ['2025-01-15', '2025-01-20', '2025-02-10', '2025-02-25', '2025-03-05', '2025-03-18'], 'status': ['defaulted', 'active', 'defaulted', 'defaulted', 'active', 'active']})
    result = engine._compute_portfolio_velocity_of_default(df)
    assert result is not None
    assert isinstance(result, Decimal)
    assert result == pytest.approx(-100.0, rel=0.0001)

def test_compute_portfolio_velocity_of_default_excludes_closed_loans():
    engine = KPIEngineV2.__new__(KPIEngineV2)
    df = pd.DataFrame({'as_of_date': ['2025-01-10', '2025-01-20', '2025-01-25', '2025-02-05', '2025-02-15', '2025-02-20'], 'status': ['defaulted', 'active', 'closed', 'defaulted', 'active', 'closed']})
    result = engine._compute_portfolio_velocity_of_default(df)
    assert result is not None
    assert float(result) == pytest.approx(0.0, abs=0.0001)

def test_compute_portfolio_velocity_of_default_returns_none_without_date():
    engine = KPIEngineV2.__new__(KPIEngineV2)
    df = pd.DataFrame({'status': ['active', 'defaulted']})
    assert engine._compute_portfolio_velocity_of_default(df) is None

def test_compute_portfolio_velocity_of_default_returns_none_single_period():
    engine = KPIEngineV2.__new__(KPIEngineV2)
    df = pd.DataFrame({'as_of_date': ['2025-01-01', '2025-01-15'], 'status': ['active', 'defaulted']})
    assert engine._compute_portfolio_velocity_of_default(df) is None

def test_vd_chronology_unsorted_input():
    df = pd.DataFrame({'measurement_date': ['2025-02-01', '2025-01-01', '2025-02-15', '2025-01-15'], 'status': ['defaulted', 'active', 'defaulted', 'active']})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == 100.0

def test_vd_units_percentage_points():
    df = pd.DataFrame({'as_of_date': ['2025-01-01', '2025-02-01'], 'status': ['defaulted', 'active']})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == -100.0

def test_vd_handles_mixed_date_formats():
    df = pd.DataFrame({'as_of_date': ['2025-01-01', '02/01/2025'], 'status': ['active', 'defaulted']})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == 100.0

def test_vd_ignores_nan_dates():
    df = pd.DataFrame({'as_of_date': ['2025-01-01', 'not-a-date', '2025-02-01'], 'status': ['active', 'active', 'defaulted']})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == 100.0

def test_velocity_of_default_unsorted_input_normalized_by_period_col():
    df_ts = pd.DataFrame({'period': ['2025-03', '2025-01', '2025-02'], 'default_rate': [2.0, 1.0, 2.5]})
    vd = CalculationPhase._calculate_velocity_of_default(df_ts, default_rate_col='default_rate', period_col='period')
    assert pd.isna(vd.iloc[0])
    assert vd.iloc[1] == pytest.approx(1.5)
    assert vd.iloc[2] == pytest.approx(-0.5)

def test_velocity_of_default_no_period_col_preserves_row_order():
    df_ts = pd.DataFrame({'period': ['2025-03', '2025-02', '2025-01'], 'default_rate': [2.0, 2.5, 1.0]})
    vd = CalculationPhase._calculate_velocity_of_default(df_ts)
    assert pd.isna(vd.iloc[0])
    assert vd.iloc[1] == pytest.approx(0.5)
    assert vd.iloc[2] == pytest.approx(-1.5)

def test_velocity_of_default_units_are_percentage_points():
    df_ts = pd.DataFrame({'default_rate': [1.0, 2.5]})
    vd = CalculationPhase._calculate_velocity_of_default(df_ts)
    assert vd.iloc[1] == pytest.approx(1.5)

def test_compute_portfolio_velocity_of_default_unsorted_input_v2():
    from decimal import Decimal
    phase = CalculationPhase.__new__(CalculationPhase)
    df = pd.DataFrame({'as_of_date': ['2025-03-05', '2025-01-15', '2025-02-10', '2025-03-18', '2025-01-20', '2025-02-25'], 'status': ['active', 'defaulted', 'defaulted', 'active', 'active', 'defaulted']})
    result = phase._compute_portfolio_velocity_of_default(df)
    assert result is not None
    assert isinstance(result, Decimal)
    assert result == pytest.approx(-100.0, rel=0.0001)

def test_compute_portfolio_velocity_of_default_all_closed_returns_none():
    phase = CalculationPhase.__new__(CalculationPhase)
    df = pd.DataFrame({'as_of_date': ['2025-01-10', '2025-02-10'], 'status': ['closed', 'closed']})
    assert phase._compute_portfolio_velocity_of_default(df) is None

def test_compute_portfolio_velocity_of_default_no_status_column():
    from decimal import Decimal
    phase = CalculationPhase.__new__(CalculationPhase)
    df = pd.DataFrame({'as_of_date': ['2025-01-01', '2025-01-15', '2025-02-05', '2025-02-20']})
    result = phase._compute_portfolio_velocity_of_default(df)
    assert result is not None
    assert isinstance(result, Decimal)
    assert float(result) == pytest.approx(0.0, abs=0.0001)

def test_compute_portfolio_velocity_of_default_units_are_percentage_points_v2():
    phase = CalculationPhase.__new__(CalculationPhase)
    df = pd.DataFrame({'as_of_date': ['2025-01-01', '2025-02-01'], 'status': ['active', 'defaulted']})
    result = phase._compute_portfolio_velocity_of_default(df)
    assert result is not None
    assert float(result) == pytest.approx(100.0, rel=0.0001)

def test_par_metrics_no_dpd_adjusted_uses_raw_dpd():
    grp = pd.DataFrame({'outstanding_balance': [100.0, 200.0, 300.0], 'dpd': [0.0, 45.0, 100.0]})
    result = CalculationPhase._calculate_segment_par_metrics(grp, 'outstanding_balance', 'dpd', 600.0)
    assert result['par_30'] == pytest.approx(500 / 600 * 100, rel=0.001)
    assert result['par_60'] == pytest.approx(300 / 600 * 100, rel=0.001)
    assert result['par_90'] == pytest.approx(300 / 600 * 100, rel=0.001)

def test_par_metrics_uses_canonical_dpd_adjusted():
    grp = pd.DataFrame({'outstanding_balance': [100.0, 200.0], 'dpd': [0.0, 0.0], 'dpd_adjusted': [0.0, 90.0]})
    result = CalculationPhase._calculate_segment_par_metrics(grp, 'outstanding_balance', 'dpd', 300.0)
    assert result['par_90'] == pytest.approx(200 / 300 * 100, rel=0.001)
    assert result['par_30'] == pytest.approx(200 / 300 * 100, rel=0.001)

def test_par_metrics_all_canonical_adjusted_accounts_captured():
    grp = pd.DataFrame({'outstanding_balance': [100.0, 100.0, 100.0], 'dpd': [0.0, 45.0, 80.0], 'dpd_adjusted': [90.0, 90.0, 90.0]})
    result = CalculationPhase._calculate_segment_par_metrics(grp, 'outstanding_balance', 'dpd', 300.0)
    assert result['par_90'] == pytest.approx(100.0)

def test_par_metrics_zero_total_balance():
    grp = pd.DataFrame({'outstanding_balance': [0.0], 'dpd': [30.0]})
    result = CalculationPhase._calculate_segment_par_metrics(grp, 'outstanding_balance', 'dpd', 0.0)
    assert result['par_30'] == 0.0
    assert result['par_60'] == 0.0
    assert result['par_90'] == 0.0

def test_par_metrics_empty_group():
    grp = pd.DataFrame(columns=['outstanding_balance', 'dpd'])
    result = CalculationPhase._calculate_segment_par_metrics(grp, 'outstanding_balance', 'dpd', 100.0)
    assert result['par_30'] == 0.0
    assert result['par_60'] == 0.0
    assert result['par_90'] == 0.0

def test_ltv_sintetico_all_nan_input():
    df = pd.DataFrame({'capital_desembolsado': [np.nan, np.nan], 'valor_nominal_factura': [np.nan, np.nan], 'tasa_dilucion': [np.nan, np.nan]})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert np.isnan(result).all()
    assert (df['ltv_sintetico_is_opaque'] == 1).all()

def test_vd_no_active_loans():
    df = pd.DataFrame({'as_of_date': ['2025-01-01', '2025-02-01'], 'status': ['closed', 'closed']})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert result is None

def test_vd_all_defaulted_steady():
    df = pd.DataFrame({'as_of_date': ['2025-01-01', '2025-02-01'], 'status': ['defaulted', 'defaulted']})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == 0.0

def test_vd_three_periods_delta():
    df = pd.DataFrame({'as_of_date': ['2025-01-01', '2025-02-01', '2025-03-01'], 'status': ['active', 'defaulted', 'active']})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == -100.0

def test_ltv_sintetico_zero_dilution():
    df = pd.DataFrame({'capital_desembolsado': [100.0], 'valor_nominal_factura': [200.0], 'tasa_dilucion': [0.0]})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert result.iloc[0] == 0.5
    assert df.loc[0, 'ltv_sintetico_is_opaque'] == 0

def test_rollup_sum_monthly_includes_period_key():
    df = pd.DataFrame({'payment_date': pd.to_datetime(['2025-01-10', '2025-01-20', '2025-02-15']), 'amount': [100.0, 200.0, 300.0]})
    phase = object.__new__(CalculationPhase)
    records = phase._rollup_sum(df, 'payment_date', ['amount'], 'monthly', 12)
    assert len(records) == 2, f'Expected 2 monthly buckets, got {len(records)}'
    for record in records:
        assert 'payment_date' in record, f'Period key missing from monthly record: {record}'

def test_rollup_sum_daily_includes_date_key():
    df = pd.DataFrame({'payment_date': pd.to_datetime(['2025-01-10', '2025-01-10', '2025-01-11']), 'amount': [50.0, 50.0, 75.0]})
    phase = object.__new__(CalculationPhase)
    records = phase._rollup_sum(df, 'payment_date', ['amount'], 'daily', 30)
    assert len(records) == 2, f'Expected 2 daily buckets, got {len(records)}'
    for record in records:
        assert 'payment_date' in record, f'Date key missing from daily record: {record}'

def test_dimension_segment_kpis_are_sorted_deterministically():
    work = pd.DataFrame({'company': ['Zeta', 'Alpha'], 'outstanding_balance': [100.0, 200.0], 'dpd': [0.0, 45.0], 'status': ['active', 'delinquent']})
    phase = object.__new__(CalculationPhase)
    result = phase._calculate_dimension_segment_kpis(work, dim='company', balance_col='outstanding_balance', dpd_col='dpd', status_col='status')
    assert list(result.keys()) == ['Alpha', 'Zeta']

def test_npl_ratio_and_npl_90_ratio_are_distinct():
    df = pd.DataFrame({'outstanding_balance': [1000.0, 1000.0, 1000.0, 1000.0, 1000.0], 'dpd': [0, 35, 60, 95, 0], 'status': ['active', 'active', 'delinquent', 'delinquent', 'defaulted']})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    kpis = engine._calculate_derived_risk_kpis(df)
    assert float(kpis['npl_90_ratio']) == pytest.approx(40.0, rel=0.0001)
    assert float(kpis['npl_ratio']) == pytest.approx(80.0, rel=0.0001)
    assert kpis['npl_ratio'] != kpis['npl_90_ratio'], 'npl_ratio and npl_90_ratio must be distinct; npl uses dpd>=30 while npl_90 uses dpd>=90'

def test_npl_90_ratio_strictly_subset_of_npl_ratio():
    df = pd.DataFrame({'outstanding_balance': [500.0, 500.0, 1000.0], 'dpd': [0, 45, 120], 'status': ['active', 'active', 'active']})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    kpis = engine._calculate_derived_risk_kpis(df)
    assert float(kpis['npl_90_ratio']) <= float(kpis['npl_ratio']), 'npl_90_ratio should never exceed npl_ratio'

def test_status_normalization_spanish_values():
    from backend.src.pipeline.transformation import TransformationPhase
    raw_statuses = ['Activo', 'ACTIVO', 'activo', 'Vigente', 'VIGENTE', 'vigente', 'AL_DIA', 'Al_dia', 'al_dia', 'Moroso', 'MOROSO', 'moroso', 'EN_MORA', 'En_mora', 'en_mora', 'Incumplimiento', 'INCUMPLIMIENTO', 'incumplimiento', 'EN_INCUMPLIMIENTO', 'En_incumplimiento', 'en_incumplimiento', 'Vencido', 'VENCIDO', 'vencido', 'Castigado', 'CASTIGADO', 'castigado', 'Cerrado', 'CERRADO', 'cerrado', 'Liquidado', 'LIQUIDADO', 'liquidado', 'Cancelado', 'CANCELADO', 'cancelado']
    expected = ['active'] * 9 + ['delinquent'] * 6 + ['defaulted'] * 12 + ['closed'] * 9
    df = pd.DataFrame({'status': raw_statuses})
    phase = TransformationPhase.__new__(TransformationPhase)
    phase._normalize_status_column(df, {})
    for raw, got, exp in zip(raw_statuses, df['status'].tolist(), expected):
        assert got == exp, f"'{raw}' mapped to '{got}', expected '{exp}'"

def test_status_normalization_english_values():
    from backend.src.pipeline.transformation import TransformationPhase
    cases = [('Active', 'active'), ('ACTIVE', 'active'), ('Current', 'active'), ('CURRENT', 'active'), ('Delinquent', 'delinquent'), ('DELINQUENT', 'delinquent'), ('Defaulted', 'defaulted'), ('DEFAULT', 'defaulted'), ('Complete', 'closed'), ('Closed', 'closed'), ('CLOSED', 'closed')]
    df = pd.DataFrame({'status': [c[0] for c in cases]})
    phase = TransformationPhase.__new__(TransformationPhase)
    phase._normalize_status_column(df, {})
    for (raw, expected), got in zip(cases, df['status'].tolist()):
        assert got == expected, f"'{raw}' mapped to '{got}', expected '{expected}'"

class TestSilentHandlerHardening:

    def test_rollup_sum_raises_on_nonexistent_date_column(self):
        df = pd.DataFrame({'amount': [100.0, 200.0]})
        phase = object.__new__(CalculationPhase)
        with pytest.raises(ValueError, match='CRITICAL:'):
            phase._rollup_sum(df, 'nonexistent_date_col', ['amount'], 'monthly', 12)

    def test_rollup_sum_raises_on_non_datetime_column(self):
        df = pd.DataFrame({'txn_date': ['not-a-date', 'also-not-a-date'], 'amount': [100.0, 200.0]})
        phase = object.__new__(CalculationPhase)
        with pytest.raises(ValueError, match='CRITICAL:'):
            phase._rollup_sum(df, 'txn_date', ['amount'], 'daily', 30)

    def test_apply_umap_raises_when_umap_errors_while_available(self, monkeypatch):

        class FakeUMAP:

            def __init__(self, **kwargs):
                raise RuntimeError('UMAP internal error')
        fake_umap_module = types.SimpleNamespace(UMAP=FakeUMAP)
        monkeypatch.setattr(calc_module, '_UMAP_AVAILABLE', True)
        monkeypatch.setattr(calc_module, 'umap', fake_umap_module, raising=False)
        X_pca = np.zeros((20, 2))
        metrics: dict = {}
        with pytest.raises(ValueError, match='CRITICAL:.*UMAP'):
            CalculationPhase._apply_umap(X_pca, metrics)

    def test_apply_hdbscan_raises_when_hdbscan_errors_while_available(self, monkeypatch):

        class FakeHDBSCAN:

            def __init__(self, **kwargs):
                raise RuntimeError('HDBSCAN internal error')
        fake_hdbscan_module = types.SimpleNamespace(HDBSCAN=FakeHDBSCAN)
        monkeypatch.setattr(calc_module, '_HDBSCAN_AVAILABLE', True)
        monkeypatch.setattr(calc_module, 'hdbscan_module', fake_hdbscan_module, raising=False)
        X_embed = np.zeros((20, 2))
        X_fallback = np.zeros((20, 2))
        metrics: dict = {}
        with pytest.raises(ValueError, match='CRITICAL:.*HDBSCAN'):
            CalculationPhase._apply_hdbscan(X_embed, X_fallback, metrics)

    def test_run_advanced_clustering_propagates_critical_on_inner_failure(self, monkeypatch):
        phase = object.__new__(CalculationPhase)

        def _bad_build(df):
            raise RuntimeError('simulated feature-matrix failure')
        monkeypatch.setattr(phase, '_build_feature_matrix', _bad_build)
        df = pd.DataFrame({'ltv_sintetico': [1.0, 2.0, 3.0] * 5})
        with pytest.raises(ValueError, match='CRITICAL:'):
            phase._run_advanced_clustering(df)


# ---------------------------------------------------------------------------
# Tests for KPIEngineV2.calculate_ltv — Decimal arithmetic
# ---------------------------------------------------------------------------


def test_calculate_ltv_uses_decimal_arithmetic():
    """Verify that calculate_ltv returns a Decimal and avoids float rounding."""
    df = pd.DataFrame({'loan_amount': [100.0], 'collateral_value': [300.0]})
    engine = KPIEngineV2(df=df)
    value, ctx = engine.calculate_ltv()
    assert isinstance(value, Decimal)
    assert value == Decimal('33.33')
    assert ctx['calculation_method'] == 'v2_engine'


def test_calculate_ltv_result_matches_pure_decimal_division():
    """Ensure Decimal division matches end-to-end Decimal arithmetic.
    Both the test expectation and the engine use per-row Decimal(str(v)) conversion,
    so the results should be exactly equal and ROUND_HALF_UP is applied consistently."""
    loan = Decimal('1234567890.123456')
    collateral = Decimal('9876543210.987654')
    expected = (loan / collateral * Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    df = pd.DataFrame({'loan_amount': [float(loan)], 'collateral_value': [float(collateral)]})
    engine = KPIEngineV2(df=df)
    value, _ = engine.calculate_ltv()
    assert value == expected


def test_calculate_ltv_raises_when_collateral_is_zero():
    df = pd.DataFrame({'loan_amount': [500.0], 'collateral_value': [0.0]})
    engine = KPIEngineV2(df=df)
    with pytest.raises(ValueError, match='CRITICAL: LTV denominator'):
        engine.calculate_ltv()


def test_calculate_ltv_raises_when_collateral_is_negative():
    df = pd.DataFrame({'loan_amount': [500.0], 'collateral_value': [-100.0]})
    engine = KPIEngineV2(df=df)
    with pytest.raises(ValueError, match='CRITICAL: LTV denominator'):
        engine.calculate_ltv()


def test_calculate_ltv_raises_on_missing_columns():
    df = pd.DataFrame({'loan_amount': [100.0]})
    engine = KPIEngineV2(df=df)
    with pytest.raises(ValueError, match='missing required columns'):
        engine.calculate_ltv()
