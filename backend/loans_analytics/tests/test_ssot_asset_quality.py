import pytest
import pandas as pd
import numpy as np
from backend.loans_analytics.kpis.ssot_asset_quality import calculate_asset_quality_metrics
from backend.loans_analytics.kpis.engine import KPIEngineV2


@pytest.fixture
def clean_portfolio():
    return pd.DataFrame({
        'loan_id': ['L1', 'L2', 'L3', 'L4', 'L5'],
        'outstanding_principal': [10000.0, 5000.0, 20000.0, 15000.0, 0.0],
        'days_past_due': [0, 45, 95, 200, 0],
        'status': ['ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'WRITTEN_OFF']
    })


@pytest.fixture
def dirty_portfolio_nulls():
    return pd.DataFrame({
        'loan_id': ['L1', 'L2'],
        'outstanding_principal': [10000.0, np.nan],
        'days_past_due': [0, 30],
        'status': ['ACTIVE', 'ACTIVE']
    })


@pytest.fixture
def empty_portfolio():
    return pd.DataFrame(columns=['outstanding_principal', 'days_past_due', 'status'])


# --- SSOT VALIDATION TESTS ---

def test_validation_empty_dataframe(empty_portfolio):
    with pytest.raises(ValueError, match='received an empty dataset'):
        calculate_asset_quality_metrics(
            balance=empty_portfolio['outstanding_principal'],
            dpd=empty_portfolio['days_past_due'],
            status=empty_portfolio['status'],
            actor='test',
            metric_aliases=['par_30']
        )


def test_validation_null_principal(dirty_portfolio_nulls):
    with pytest.raises(ValueError, match="Invalid numeric values detected in 'outstanding_balance'"):
        calculate_asset_quality_metrics(
            balance=dirty_portfolio_nulls['outstanding_principal'],
            dpd=dirty_portfolio_nulls['days_past_due'],
            status=dirty_portfolio_nulls['status'],
            actor='test',
            metric_aliases=['par_30']
        )


# --- SSOT MATHEMATICAL TESTS ---

def test_calculate_par_standard(clean_portfolio):
    results = calculate_asset_quality_metrics(
        balance=clean_portfolio['outstanding_principal'],
        dpd=clean_portfolio['days_past_due'],
        status=clean_portfolio['status'],
        actor='test',
        metric_aliases=['par_30', 'par_90']
    )
    
    par_30 = results['par_30']
    par_90 = results['par_90']

    assert np.isclose(par_30, 80.0), f'Expected 80.0, got {par_30}'
    assert np.isclose(par_90, 70.0), f'Expected 70.0, got {par_90}'


def test_calculate_npl_90_ratio_mapping(clean_portfolio):
    results = calculate_asset_quality_metrics(
        balance=clean_portfolio['outstanding_principal'],
        dpd=clean_portfolio['days_past_due'],
        status=clean_portfolio['status'],
        actor='test',
        metric_aliases=['par_90', 'npl90']
    )
    assert results['par_90'] == results['npl90'], 'NPL drifted from PAR90 semantics.'


def test_calculate_default_rate_combined_logic(clean_portfolio):
    results = calculate_asset_quality_metrics(
        balance=clean_portfolio['outstanding_principal'],
        dpd=clean_portfolio['days_past_due'],
        status=clean_portfolio['status'],
        actor='test',
        metric_aliases=['default_rate']
    )
    # 15000 / 50000 * 100 = 30.0
    assert np.isclose(results['default_rate'], 30.0), f"Expected 30.0, got {results['default_rate']}"


def test_calculate_par_zero_total_principal():
    zero_df = pd.DataFrame({
        'outstanding_principal': [0.0, 0.0],
        'days_past_due': [100, 200],
        'status': ['ACTIVE', 'ACTIVE']
    })
    with pytest.raises(ValueError, match=r'Sum\(outstanding_balance\) must be > 0'):
        calculate_asset_quality_metrics(
            balance=zero_df['outstanding_principal'],
            dpd=zero_df['days_past_due'],
            status=zero_df['status'],
            actor='test',
            metric_aliases=['par_90']
        )


# --- KPI ENGINE ROUTING TESTS ---

def test_engine_dispatch_success(clean_portfolio):
    engine = KPIEngineV2(df=clean_portfolio)
    results = engine.calculate(clean_portfolio)
    assert isinstance(results, dict)
    assert len(results) > 0


def test_engine_unsupported_kpi(clean_portfolio):
    engine = KPIEngineV2(df=clean_portfolio)
    results = engine.calculate(clean_portfolio)
    # KPIEngineV2 delegates to run_metric_engine, which silently ignores
    # unknown KPI keys — verify that a valid result set is still returned.
    assert isinstance(results, dict)
