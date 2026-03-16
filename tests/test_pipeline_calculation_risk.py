"""Tests for advanced risk calculation features in CalculationPhase.

Covers:
- _calculate_ltv_sintetico: Synthetic Factoring LTV per loan
- _calculate_velocity_of_default: First derivative of default rate over time
- _calculate_segment_par_metrics: Kiting/carousel adjustment via ratio_pago_real
"""

import numpy as np
import pandas as pd
import pytest

from src.pipeline.calculation import CalculationPhase


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


def test_ltv_sintetico_zero_adjusted_value_returns_zero():
    """When the adjusted invoice value is zero, LTV should be 0 (no division by zero)."""
    df = pd.DataFrame(
        {
            "capital_desembolsado": [50.0],
            "valor_nominal_factura": [100.0],
            "tasa_dilucion": [1.0],  # fully diluted → valor_ajustado = 0
        }
    )
    result = CalculationPhase._calculate_ltv_sintetico(df)
    assert result.iloc[0] == 0.0


def test_ltv_sintetico_missing_columns_returns_empty_series():
    """Returns an empty Series when required columns are absent."""
    df = pd.DataFrame({"capital_desembolsado": [100.0]})  # missing two columns
    result = CalculationPhase._calculate_ltv_sintetico(df)
    assert result.empty


def test_ltv_sintetico_empty_dataframe():
    """Returns an empty Series for an empty DataFrame."""
    df = pd.DataFrame(
        columns=["capital_desembolsado", "valor_nominal_factura", "tasa_dilucion"]
    )
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
    result = CalculationPhase._calculate_segment_par_metrics(grp, "outstanding_balance", "dpd", 600.0)

    # PAR30: 200+300 = 500 → 83.3333%
    assert result["par_30"] == pytest.approx(500 / 600 * 100, rel=1e-3)
    # PAR60: only 300 → 50%
    assert result["par_60"] == pytest.approx(300 / 600 * 100, rel=1e-3)
    # PAR90: only 300 → 50%
    assert result["par_90"] == pytest.approx(300 / 600 * 100, rel=1e-3)


def test_par_metrics_kiting_forces_dpd_to_90():
    """Accounts with ratio_pago_real < 1.0 are forced to DPD >= 90, inflating PAR90."""
    grp = pd.DataFrame(
        {
            "outstanding_balance": [100.0, 200.0],
            "dpd": [0.0, 0.0],  # both appear current in legacy system
            "ratio_pago_real": [1.0, 0.8],  # second account is kiting
        }
    )
    result = CalculationPhase._calculate_segment_par_metrics(grp, "outstanding_balance", "dpd", 300.0)

    # The kiting account (200) gets DPD forced to 90, so PAR90 = 200/300 * 100
    assert result["par_90"] == pytest.approx(200 / 300 * 100, rel=1e-3)
    # The non-kiting account stays at DPD 0, not captured in PAR30
    assert result["par_30"] == pytest.approx(200 / 300 * 100, rel=1e-3)


def test_par_metrics_all_kiting_accounts_captured():
    """All accounts with ratio_pago_real < 1.0 are penalised, even if DPD is partially elevated."""
    grp = pd.DataFrame(
        {
            "outstanding_balance": [100.0, 100.0, 100.0],
            "dpd": [0.0, 45.0, 80.0],  # second is already >= 30, third almost at 90
            "ratio_pago_real": [0.9, 0.95, 0.99],  # all kiting
        }
    )
    result = CalculationPhase._calculate_segment_par_metrics(
        grp, "outstanding_balance", "dpd", 300.0
    )

    # All three are kiting → all forced to DPD >= 90
    assert result["par_90"] == pytest.approx(100.0)


def test_par_metrics_ratio_exactly_one_not_penalised():
    """Accounts with ratio_pago_real exactly 1.0 retain their original DPD."""
    grp = pd.DataFrame(
        {
            "outstanding_balance": [100.0],
            "dpd": [0.0],
            "ratio_pago_real": [1.0],
        }
    )
    result = CalculationPhase._calculate_segment_par_metrics(grp, "outstanding_balance", "dpd", 100.0)
    assert result["par_30"] == 0.0
    assert result["par_60"] == 0.0
    assert result["par_90"] == 0.0
