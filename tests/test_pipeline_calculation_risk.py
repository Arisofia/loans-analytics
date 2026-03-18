"""Tests for advanced risk calculation features in CalculationPhase.

Covers:
- _calculate_ltv_sintetico: Synthetic Factoring LTV per loan
- _calculate_velocity_of_default: First derivative of default rate over time
- _calculate_segment_par_metrics: Kiting/carousel adjustment via ratio_pago_real
"""

import pandas as pd
import pytest

import numpy as np
import pandas as pd
import pytest

from backend.src.pipeline.calculation import CalculationPhase
from backend.python.kpis.engine import KPIEngineV2

# ---------------------------------------------------------------------------
# _calculate_ltv_sintetico
# ---------------------------------------------------------------------------


def test_ltv_sintetico_basic_calculation():
    """LTV Sintético = capital_desembolsado / (valor_nominal * (1 - tasa_dilucion))."""
    df = pd.DataFrame(
        {
            "capital_desembolsado": [100.0, 200.0],
            "valor_nominal_factura": [200.0, 500.0],
            "tasa_dilucion": [0.1, 0.2],
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)

    # loan 0: 100 / (200 * 0.9) = 100/180 ≈ 0.5556
    # loan 1: 200 / (500 * 0.8) = 200/400 = 0.5
    assert result.iloc[0] == pytest.approx(100 / 180, rel=1e-4)
    assert result.iloc[1] == pytest.approx(0.5, rel=1e-4)


def test_ltv_sintetico_zero_adjusted_value_is_opaque_and_nan():
    """When adjusted invoice value is zero, the observation is opaque and LTV is NaN."""
    df = pd.DataFrame(
        {
            "capital_desembolsado": [50.0],
            "valor_nominal_factura": [100.0],
            "tasa_dilucion": [1.0],  # fully diluted → valor_ajustado = 0
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert np.isnan(result.iloc[0])
    assert df.loc[0, "ltv_sintetico_is_opaque"] == 1


def test_ltv_sintetico_missing_denominator_is_opaque_and_nan():
    """NaN denominator must be treated as opaque and produce NaN LTV."""
    df = pd.DataFrame(
        {
            "capital_desembolsado": [50.0],
            "valor_nominal_factura": [None],
            "tasa_dilucion": [0.1],
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert np.isnan(result.iloc[0])
    assert df.loc[0, "ltv_sintetico_is_opaque"] == 1


def test_ltv_sintetico_missing_columns_returns_empty_series():
    """Returns an empty Series when required columns are absent."""
    df = pd.DataFrame({"capital_desembolsado": [100.0]})  # missing two columns
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert result.empty


def test_ltv_sintetico_empty_dataframe():
    """Returns an empty Series for an empty DataFrame."""
    df = pd.DataFrame(columns=["capital_desembolsado", "valor_nominal_factura", "tasa_dilucion"])
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert len(result) == 0


def test_ltv_sintetico_strict_positive_denominator_rule():
    """Denominator <= 0 must be opaque (np.nan)."""
    df = pd.DataFrame(
        {
            "capital_desembolsado": [100.0, 100.0],
            "valor_nominal_factura": [100.0, -50.0], # negative nominal is invalid
            "tasa_dilucion": [1.1, 0.1], # >100% dilution makes it negative
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert np.isnan(result.iloc[0])
    assert np.isnan(result.iloc[1])
    assert (df["ltv_sintetico_is_opaque"] == 1).all()


def test_ltv_sintetico_preserves_indices():
    """Output series must have the same index as input dataframe."""
    df = pd.DataFrame(
        {
            "capital_desembolsado": [100.0],
            "valor_nominal_factura": [200.0],
            "tasa_dilucion": [0.0],
        },
        index=[42]
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert result.index[0] == 42


# ---------------------------------------------------------------------------
# _compute_portfolio_velocity_of_default (portfolio-level integration)
# ---------------------------------------------------------------------------


def test_compute_portfolio_velocity_of_default_uses_as_of_date():
    """Uses canonical 'as_of_date' column and returns a Decimal Vd value."""
    from decimal import Decimal

    engine = KPIEngineV2.__new__(KPIEngineV2)
    df = pd.DataFrame(
        {
            "as_of_date": [
                "2025-01-15",
                "2025-01-20",
                "2025-02-10",
                "2025-02-25",
                "2025-03-05",
                "2025-03-18",
            ],
            "status": [
                "defaulted",
                "active",
                "defaulted",
                "defaulted",
                "active",
                "active",
            ],
        }
    )
    result = engine._compute_portfolio_velocity_of_default(df)

    # Jan: 1 defaulted / 2 total active = 50.0%
    # Feb: 2 defaulted / 2 total active = 100.0%
    # Mar: 0 defaulted / 2 total active = 0.0%
    # Latest Vd: Mar(0.0) - Feb(100.0) = -100.0
    assert result is not None
    assert isinstance(result, Decimal)
    assert result == pytest.approx(-100.0, rel=1e-4)


def test_compute_portfolio_velocity_of_default_excludes_closed_loans():
    """Closed loans must not affect the default-rate denominator."""
    engine = KPIEngineV2.__new__(KPIEngineV2)
    df = pd.DataFrame(
        {
            "as_of_date": [
                "2025-01-10",
                "2025-01-20",
                "2025-01-25",  # closed — should be excluded
                "2025-02-05",
                "2025-02-15",
                "2025-02-20",  # closed — should be excluded
            ],
            "status": [
                "defaulted",
                "active",
                "closed",
                "defaulted",
                "active",
                "closed",
            ],
        }
    )
    result = engine._compute_portfolio_velocity_of_default(df)

    # Active set only: Jan: 1/2 = 50%, Feb: 1/2 = 50% → Vd = 0
    assert result is not None
    assert float(result) == pytest.approx(0.0, abs=1e-4)


def test_compute_portfolio_velocity_of_default_returns_none_without_date():
    """Returns None when no recognised date column exists."""
    engine = KPIEngineV2.__new__(KPIEngineV2)
    df = pd.DataFrame({"status": ["active", "defaulted"]})
    assert engine._compute_portfolio_velocity_of_default(df) is None


def test_compute_portfolio_velocity_of_default_returns_none_single_period():
    """Returns None when all records fall in the same month (Vd needs ≥2 periods)."""
    engine = KPIEngineV2.__new__(KPIEngineV2)
    df = pd.DataFrame(
        {
            "as_of_date": ["2025-01-01", "2025-01-15"],
            "status": ["active", "defaulted"],
        }
    )
    assert engine._compute_portfolio_velocity_of_default(df) is None


def test_vd_chronology_unsorted_input():
    """Vd must handle unsorted input data correctly by internal sorting."""
    df = pd.DataFrame({
        "measurement_date": ["2025-02-01", "2025-01-01", "2025-02-15", "2025-01-15"],
        "status": ["defaulted", "active", "defaulted", "active"]
    })
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    # Jan: 0/2 = 0%, Feb: 2/2 = 100% -> Vd = +100
    assert float(result) == 100.0


def test_vd_units_percentage_points():
    """Vd should return diff in percentage points, not decimal ratios."""
    df = pd.DataFrame({
        "as_of_date": ["2025-01-01", "2025-02-01"],
        "status": ["defaulted", "active"] # 100% -> 0%
    })
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == -100.0


def test_vd_handles_mixed_date_formats():
    """Vd should handle mixed date formats via 'mixed' parser."""
    df = pd.DataFrame({
        "as_of_date": ["2025-01-01", "02/01/2025"], # ISO and US-ish (Feb 1st)
        "status": ["active", "defaulted"]
    })
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == 100.0


def test_vd_ignores_nan_dates():
    """Rows with unparseable dates should be excluded from Vd calculation."""
    df = pd.DataFrame({
        "as_of_date": ["2025-01-01", "not-a-date", "2025-02-01"],
        "status": ["active", "active", "defaulted"]
    })
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == 100.0


# ---------------------------------------------------------------------------
# _calculate_segment_par_metrics — kiting adjustment
# ---------------------------------------------------------------------------


def test_par_metrics_without_ratio_pago_real_unchanged():
    """Without ratio_pago_real, PAR metrics use raw DPD as before."""
    grp = pd.DataFrame(
        {
            "outstanding_balance": [100.0, 200.0, 300.0],
            "dpd": [0.0, 45.0, 100.0],
        }
    )
    result = CalculationPhase._calculate_segment_par_metrics(
        grp, "outstanding_balance", "dpd", 600.0
    )

    # PAR30: 200+300 = 500 → 83.3333%
    assert result["par_30"] == pytest.approx(500 / 600 * 100, rel=1e-3)
    # PAR60: only 300 → 50%
    assert result["par_60"] == pytest.approx(300 / 600 * 100, rel=1e-3)
    # PAR90: only 300 → 50%
    assert result["par_90"] == pytest.approx(300 / 600 * 100, rel=1e-3)


def test_par_metrics_uses_canonical_dpd_adjusted():
    """Segment PAR must use upstream canonical dpd_adjusted when present."""
    grp = pd.DataFrame(
        {
            "outstanding_balance": [100.0, 200.0],
            "dpd": [0.0, 0.0],  # both appear current in legacy system
            "dpd_adjusted": [0.0, 90.0],
        }
    )
    result = CalculationPhase._calculate_segment_par_metrics(
        grp, "outstanding_balance", "dpd", 300.0
    )

    # The second account is canonically adjusted upstream to 90
    assert result["par_90"] == pytest.approx(200 / 300 * 100, rel=1e-3)
    # The first account stays at DPD 0, not captured in PAR30
    assert result["par_30"] == pytest.approx(200 / 300 * 100, rel=1e-3)


def test_par_metrics_all_canonical_adjusted_accounts_captured():
    """All accounts with canonical dpd_adjusted >= 90 are captured in PAR90."""
    grp = pd.DataFrame(
        {
            "outstanding_balance": [100.0, 100.0, 100.0],
            "dpd": [0.0, 45.0, 80.0],  # second is already >= 30, third almost at 90
            "dpd_adjusted": [90.0, 90.0, 90.0],
        }
    )
    result = CalculationPhase._calculate_segment_par_metrics(
        grp, "outstanding_balance", "dpd", 300.0
    )

    # All three are canonically adjusted upstream
    assert result["par_90"] == pytest.approx(100.0)


def test_par_metrics_zero_total_balance():
    """If total balance is zero, PAR metrics should probably handle it (avoid Div0)."""
    # Note: _calculate_segment_par_metrics uses total_bal from argument
    grp = pd.DataFrame({"outstanding_balance": [0.0], "dpd": [30.0]})
    result = CalculationPhase._calculate_segment_par_metrics(grp, "outstanding_balance", "dpd", 0.0)
    # Currently it would crash or return NaN/Inf depending on pandas
    # Let's check current behavior or define it
    try:
        res = result["par_30"]
        assert np.isnan(res) or np.isinf(res) or res == 0.0
    except ZeroDivisionError:
        pytest.fail("Should handle zero balance gracefully")


def test_par_metrics_empty_group():
    """Empty group should return 0.0 for all PAR buckets."""
    grp = pd.DataFrame(columns=["outstanding_balance", "dpd"])
    result = CalculationPhase._calculate_segment_par_metrics(grp, "outstanding_balance", "dpd", 100.0)
    assert result["par_30"] == 0.0
    assert result["par_60"] == 0.0
    assert result["par_90"] == 0.0


def test_ltv_sintetico_all_nan_input():
    """If all required columns are present but all NaN, result should be all NaN."""
    df = pd.DataFrame({
        "capital_desembolsado": [np.nan, np.nan],
        "valor_nominal_factura": [np.nan, np.nan],
        "tasa_dilucion": [np.nan, np.nan]
    })
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert np.isnan(result).all()
    assert (df["ltv_sintetico_is_opaque"] == 1).all()


def test_vd_no_active_loans():
    """Vd should return None if no active/defaulted/delinquent loans exist."""
    df = pd.DataFrame({
        "as_of_date": ["2025-01-01", "2025-02-01"],
        "status": ["closed", "closed"]
    })
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert result is None


def test_vd_all_defaulted_steady():
    """Vd should be 0.0 if default rate is constant at 100%."""
    df = pd.DataFrame({
        "as_of_date": ["2025-01-01", "2025-02-01"],
        "status": ["defaulted", "defaulted"]
    })
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == 0.0


def test_vd_three_periods_delta():
    """Vd should return the difference between the LAST two periods."""
    df = pd.DataFrame({
        "as_of_date": ["2025-01-01", "2025-02-01", "2025-03-01"],
        "status": ["active", "defaulted", "active"] 
        # Jan: 0%, Feb: 100%, Mar: 0%
        # Vd(Feb) = +100, Vd(Mar) = -100
    })
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == -100.0


def test_ltv_sintetico_zero_dilution():
    """Zero dilution should result in simple capital/nominal ratio."""
    df = pd.DataFrame({
        "capital_desembolsado": [100.0],
        "valor_nominal_factura": [200.0],
        "tasa_dilucion": [0.0]
    })
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert result.iloc[0] == 0.5
    assert df.loc[0, "ltv_sintetico_is_opaque"] == 0




