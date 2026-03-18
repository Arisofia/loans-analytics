"""Tests for advanced risk calculation features in CalculationPhase.

Covers:
- _calculate_ltv_sintetico: Synthetic Factoring LTV per loan
- _calculate_velocity_of_default: First derivative of default rate over time
- _calculate_segment_par_metrics: Kiting/carousel adjustment via ratio_pago_real
"""

import pandas as pd
import pytest

from backend.src.pipeline.calculation import CalculationPhase

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
    result = CalculationPhase._calculate_ltv_sintetico(df)

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
    result = CalculationPhase._calculate_ltv_sintetico(df)
    assert pd.isna(result.iloc[0])
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
    result = CalculationPhase._calculate_ltv_sintetico(df)
    assert pd.isna(result.iloc[0])
    assert df.loc[0, "ltv_sintetico_is_opaque"] == 1


def test_ltv_sintetico_missing_columns_returns_empty_series():
    """Returns an empty Series when required columns are absent."""
    df = pd.DataFrame({"capital_desembolsado": [100.0]})  # missing two columns
    result = CalculationPhase._calculate_ltv_sintetico(df)
    assert result.empty


def test_ltv_sintetico_empty_dataframe():
    """Returns an empty Series for an empty DataFrame."""
    df = pd.DataFrame(columns=["capital_desembolsado", "valor_nominal_factura", "tasa_dilucion"])
    result = CalculationPhase._calculate_ltv_sintetico(df)
    assert len(result) == 0


# ---------------------------------------------------------------------------
# _calculate_velocity_of_default
# ---------------------------------------------------------------------------


def test_velocity_of_default_basic_diff():
    """Vd should be the period-over-period diff of the default_rate column."""
    df_ts = pd.DataFrame(
        {"period": ["2025-01", "2025-02", "2025-03"], "default_rate": [1.0, 2.5, 2.0]}
    )
    vd = CalculationPhase._calculate_velocity_of_default(df_ts)

    assert pd.isna(vd.iloc[0])  # first value is NaN (no previous period)
    assert vd.iloc[1] == pytest.approx(1.5)
    assert vd.iloc[2] == pytest.approx(-0.5)


def test_velocity_of_default_missing_column_returns_empty():
    """Returns an empty Series when the default_rate column is absent."""
    df_ts = pd.DataFrame({"period": ["2025-01", "2025-02"], "other_col": [1.0, 2.0]})
    vd = CalculationPhase._calculate_velocity_of_default(df_ts)
    assert vd.empty


def test_velocity_of_default_single_row_returns_nan():
    """With one row, the diff produces a single NaN."""
    df_ts = pd.DataFrame({"default_rate": [3.0]})
    vd = CalculationPhase._calculate_velocity_of_default(df_ts)
    assert len(vd) == 1
    assert pd.isna(vd.iloc[0])


def test_velocity_of_default_custom_column_name():
    """Accepts a custom column name for the default rate."""
    df_ts = pd.DataFrame({"mora_pct": [0.5, 1.0, 0.8]})
    vd = CalculationPhase._calculate_velocity_of_default(df_ts, default_rate_col="mora_pct")
    assert vd.iloc[1] == pytest.approx(0.5)
    assert vd.iloc[2] == pytest.approx(-0.2)


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


# ---------------------------------------------------------------------------
# _compute_portfolio_velocity_of_default (portfolio-level integration)
# ---------------------------------------------------------------------------


def test_compute_portfolio_velocity_of_default_uses_as_of_date():
    """Uses canonical 'as_of_date' column and returns a Decimal Vd value."""
    from decimal import Decimal

    phase = CalculationPhase.__new__(CalculationPhase)
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
    result = phase._compute_portfolio_velocity_of_default(df)

    # Jan: 1/2 = 50%, Feb: 2/2 = 100%, Mar: 0/3 = 0%
    # Vd latest = 0 - 100 = -100
    assert result is not None
    assert isinstance(result, Decimal)
    assert result == pytest.approx(-100.0, rel=1e-4)


def test_compute_portfolio_velocity_of_default_excludes_closed_loans():
    """Closed loans must not affect the default-rate denominator."""
    phase = CalculationPhase.__new__(CalculationPhase)
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
    result = phase._compute_portfolio_velocity_of_default(df)

    # Active set only: Jan: 1/2 = 50%, Feb: 1/2 = 50% → Vd = 0
    assert result is not None
    assert float(result) == pytest.approx(0.0, abs=1e-4)


def test_compute_portfolio_velocity_of_default_returns_none_without_date():
    """Returns None when no recognised date column exists."""
    phase = CalculationPhase.__new__(CalculationPhase)
    df = pd.DataFrame({"status": ["active", "defaulted"]})
    assert phase._compute_portfolio_velocity_of_default(df) is None


def test_compute_portfolio_velocity_of_default_returns_none_single_period():
    """Returns None when all records fall in the same month (Vd needs ≥2 periods)."""
    phase = CalculationPhase.__new__(CalculationPhase)
    df = pd.DataFrame(
        {
            "as_of_date": ["2025-01-01", "2025-01-15"],
            "status": ["active", "defaulted"],
        }
    )
    assert phase._compute_portfolio_velocity_of_default(df) is None

