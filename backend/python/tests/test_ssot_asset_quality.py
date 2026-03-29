import pytest
import pandas as pd
import numpy as np
from backend.python.kpis.ssot_asset_quality import AssetQualitySSOT
from backend.python.kpis.engine import KPIEngine


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
    return pd.DataFrame()


# --- SSOT VALIDATION TESTS ---

def test_validation_empty_dataframe(empty_portfolio):
    with pytest.raises(ValueError, match='Input DataFrame is empty'):
        AssetQualitySSOT.calculate_par(empty_portfolio, 30)


def test_validation_missing_columns(clean_portfolio):
    df_missing_col = clean_portfolio.drop(columns=['days_past_due'])
    with pytest.raises(KeyError, match='Missing critical columns'):
        AssetQualitySSOT.calculate_par(df_missing_col, 30)


def test_validation_null_principal(dirty_portfolio_nulls):
    with pytest.raises(ValueError, match="Null values detected in 'outstanding_principal'"):
        AssetQualitySSOT.calculate_par(dirty_portfolio_nulls, 30)


# --- SSOT MATHEMATICAL TESTS ---

def test_calculate_par_standard(clean_portfolio):
    par_30 = AssetQualitySSOT.calculate_par(clean_portfolio, 30)
    par_90 = AssetQualitySSOT.calculate_par(clean_portfolio, 90)

    assert np.isclose(par_30, 0.8), f'Expected 0.8, got {par_30}'
    assert np.isclose(par_90, 0.7), f'Expected 0.7, got {par_90}'


def test_calculate_npl_90_ratio_mapping(clean_portfolio):
    par_90 = AssetQualitySSOT.calculate_par(clean_portfolio, 90)
    npl_ratio = AssetQualitySSOT.calculate_npl_90_ratio(clean_portfolio)
    assert par_90 == npl_ratio, 'NPL drifted from PAR90 semantics.'


def test_calculate_npl_90_ratio_counts_written_off_even_if_dpd_below_90():
    df = pd.DataFrame(
        {
            "outstanding_principal": [100.0, 100.0, 100.0],
            "days_past_due": [0, 95, 10],
            "status": ["ACTIVE", "ACTIVE", "WRITTEN_OFF"],
        }
    )
    npl_ratio = AssetQualitySSOT.calculate_npl_90_ratio(df)
    assert np.isclose(npl_ratio, 2 / 3), f"Expected 0.6667, got {npl_ratio}"


def test_calculate_default_rate_combined_logic(clean_portfolio):
    default_rate = AssetQualitySSOT.calculate_default_rate(clean_portfolio)
    assert np.isclose(default_rate, 0.3), f'Expected 0.3, got {default_rate}'


def test_calculate_par_zero_total_principal():
    zero_df = pd.DataFrame({
        'outstanding_principal': [0.0, 0.0],
        'days_past_due': [100, 200],
        'status': ['ACTIVE', 'ACTIVE']
    })
    assert AssetQualitySSOT.calculate_par(zero_df, 90) == 0.0
    assert AssetQualitySSOT.calculate_default_rate(zero_df) == 0.0


# --- KPI ENGINE ROUTING TESTS ---

def test_engine_dispatch_success(clean_portfolio):
    config = {'requested_kpis': ['par_30', 'npl_90_ratio', 'default_rate']}
    engine = KPIEngine(config)

    results = engine.compute_all(clean_portfolio)

    assert 'par_30' in results
    assert 'npl_90_ratio' in results
    assert 'default_rate' in results
    assert np.isclose(results['par_30'], 0.8)


def test_engine_unsupported_kpi(clean_portfolio):
    config = {'requested_kpis': ['par_30', 'rogue_legacy_metric']}
    engine = KPIEngine(config)

    with pytest.raises(NotImplementedError, match='lacks an SSOT mapping'):
        engine.compute_all(clean_portfolio)
