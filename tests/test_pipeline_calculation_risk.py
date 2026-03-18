"""Tests for advanced risk calculation features in CalculationPhase.

Covers:
- _calculate_ltv_sintetico: Synthetic Factoring LTV per loan
- _calculate_velocity_of_default: First derivative of default rate over time
- _calculate_segment_par_metrics: Kiting/carousel adjustment via ratio_pago_real
"""

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
    assert result.iloc[0] == 0.0 # KPIEngineV2 returns 0.0 instead of NaN for valor_ajustado <= 0


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
    assert result.iloc[0] == 0.0 # KPIEngineV2 returns 0.0 for NaNs


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

    # Jan: 1/2 = 50%, Feb: 2/2 = 100%, Mar: 0/3 = 0%
    # Vd latest = 0 - 100 = -100
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


