"""Tests for advanced risk calculation features in CalculationPhase.

Covers:
- _calculate_ltv_sintetico: Synthetic Factoring LTV per loan
- _calculate_velocity_of_default: First derivative of default rate over time
- _calculate_segment_par_metrics: Kiting/carousel adjustment via dpd_adjusted
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


def test_ltv_sintetico_valid_row_not_nan():
    """Valid loans (non-zero adjusted value) must not produce np.nan."""
    df = pd.DataFrame(
        {
            "capital_desembolsado": [100.0],
            "valor_nominal_factura": [200.0],
            "tasa_dilucion": [0.1],
        }
    )
    result = CalculationPhase._calculate_ltv_sintetico(df)
    assert not pd.isna(result.iloc[0])
    assert result.iloc[0] == pytest.approx(100 / 180, rel=1e-4)


def test_ltv_sintetico_zero_nominal_returns_nan():
    """Invoice with zero nominal value must also yield np.nan (denominator is 0)."""
    df = pd.DataFrame(
        {
            "capital_desembolsado": [50.0],
            "valor_nominal_factura": [0.0],
            "tasa_dilucion": [0.0],
        }
    )
    result = CalculationPhase._calculate_ltv_sintetico(df)
    assert pd.isna(result.iloc[0])


# ---------------------------------------------------------------------------
# _ltv_sintetico_invalid_mask — opacity flag
# ---------------------------------------------------------------------------


def test_ltv_sintetico_invalid_mask_fully_diluted():
    """Fully-diluted row must be flagged as invalid."""
    df = pd.DataFrame(
        {
            "valor_nominal_factura": [100.0, 200.0],
            "tasa_dilucion": [1.0, 0.1],  # row 0 fully diluted, row 1 valid
        }
    )
    mask = CalculationPhase._ltv_sintetico_invalid_mask(df)
    assert mask.iloc[0]
    assert not mask.iloc[1]


def test_ltv_sintetico_invalid_mask_zero_nominal():
    """Zero nominal invoice must be flagged as invalid regardless of dilution."""
    df = pd.DataFrame(
        {
            "valor_nominal_factura": [0.0],
            "tasa_dilucion": [0.5],
        }
    )
    mask = CalculationPhase._ltv_sintetico_invalid_mask(df)
    assert mask.iloc[0]


def test_ltv_sintetico_invalid_mask_no_invalids_all_valid():
    """All valid loans: mask must be all False."""
    df = pd.DataFrame(
        {
            "valor_nominal_factura": [100.0, 200.0],
            "tasa_dilucion": [0.0, 0.2],
        }
    )
    mask = CalculationPhase._ltv_sintetico_invalid_mask(df)
    assert not mask.any()


def test_ltv_sintetico_invalid_mask_missing_columns_returns_empty_series():
    """Missing columns → empty Series (no information available, not conservative False)."""
    df = pd.DataFrame({"capital_desembolsado": [100.0]})
    mask = CalculationPhase._ltv_sintetico_invalid_mask(df)
    assert mask.empty


def test_ltv_sintetico_invalid_mask_empty_dataframe():
    """Empty DataFrame → empty bool Series."""
    df = pd.DataFrame(columns=["valor_nominal_factura", "tasa_dilucion"])
    mask = CalculationPhase._ltv_sintetico_invalid_mask(df)
    assert mask.empty


def test_ltv_sintetico_nan_and_mask_are_consistent():
    """NaN positions in LTV must exactly match True positions in the invalid mask."""
    df = pd.DataFrame(
        {
            "capital_desembolsado": [100.0, 50.0, 200.0],
            "valor_nominal_factura": [200.0, 0.0, 500.0],
            "tasa_dilucion": [0.1, 0.0, 1.0],  # rows 1 and 2 are invalid
        }
    )
    ltv = CalculationPhase._calculate_ltv_sintetico(df)
    mask = CalculationPhase._ltv_sintetico_invalid_mask(df)

    # Wherever mask is True, LTV must be NaN
    assert ltv[mask].isna().all()
    # Wherever mask is False, LTV must not be NaN
    assert ltv[~mask].notna().all()


# ---------------------------------------------------------------------------
# _calculate_velocity_of_default (extended: chronology & units)
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


def test_velocity_of_default_unsorted_input_normalized_by_period_col():
    """When period_col is provided, rows are sorted chronologically before differencing."""
    # Intentionally reversed input order
    df_ts = pd.DataFrame(
        {
            "period": ["2025-03", "2025-01", "2025-02"],
            "default_rate": [2.0, 1.0, 2.5],  # Jan=1.0, Feb=2.5, Mar=2.0
        }
    )
    vd = CalculationPhase._calculate_velocity_of_default(
        df_ts, default_rate_col="default_rate", period_col="period"
    )
    # After chronological sort: Jan(1.0) → Feb(2.5) → Mar(2.0)
    # diff:                      NaN,       +1.5,       -0.5
    assert pd.isna(vd.iloc[0])
    assert vd.iloc[1] == pytest.approx(1.5)
    assert vd.iloc[2] == pytest.approx(-0.5)


def test_velocity_of_default_no_period_col_preserves_row_order():
    """Without period_col, rows are diffed in their original (caller-managed) order."""
    # Descending order — without period_col the result honours input order
    df_ts = pd.DataFrame(
        {
            "period": ["2025-03", "2025-02", "2025-01"],
            "default_rate": [2.0, 2.5, 1.0],
        }
    )
    vd = CalculationPhase._calculate_velocity_of_default(df_ts)
    # Row order: 2.0, 2.5, 1.0 → diffs: NaN, +0.5, -1.5
    assert pd.isna(vd.iloc[0])
    assert vd.iloc[1] == pytest.approx(0.5)
    assert vd.iloc[2] == pytest.approx(-1.5)


def test_velocity_of_default_units_are_percentage_points():
    """Vd units: if default_rate is in %, the diff is in percentage points (1 pp = 100 bps).

    A move from 1.0 % to 2.5 % is +1.5 percentage points (+150 basis points).
    """
    df_ts = pd.DataFrame({"default_rate": [1.0, 2.5]})  # values in %
    vd = CalculationPhase._calculate_velocity_of_default(df_ts)
    # Δ = 2.5% − 1.0% = 1.5 pp (150 bps)
    assert vd.iloc[1] == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# _compute_portfolio_velocity_of_default — extended edge cases
# ---------------------------------------------------------------------------


def test_compute_portfolio_velocity_of_default_unsorted_input():
    """Records arriving out of chronological order must still produce the correct Vd."""
    from decimal import Decimal

    phase = CalculationPhase.__new__(CalculationPhase)
    # Intentionally shuffled: Mar, Jan, Feb
    df = pd.DataFrame(
        {
            "as_of_date": [
                "2025-03-05",
                "2025-01-15",
                "2025-02-10",
                "2025-03-18",
                "2025-01-20",
                "2025-02-25",
            ],
            "status": [
                "active",
                "defaulted",
                "defaulted",
                "active",
                "active",
                "defaulted",
            ],
        }
    )
    result = phase._compute_portfolio_velocity_of_default(df)

    # Jan: 1/2 = 50%, Feb: 2/2 = 100%, Mar: 0/2 = 0%
    # Vd (Mar − Feb) = 0 − 100 = −100 pp
    assert result is not None
    assert isinstance(result, Decimal)
    assert result == pytest.approx(-100.0, rel=1e-4)


def test_compute_portfolio_velocity_of_default_all_closed_returns_none():
    """When all non-closed records are filtered out the result must be None."""
    phase = CalculationPhase.__new__(CalculationPhase)
    df = pd.DataFrame(
        {
            "as_of_date": ["2025-01-10", "2025-02-10"],
            "status": ["closed", "closed"],
        }
    )
    assert phase._compute_portfolio_velocity_of_default(df) is None


def test_compute_portfolio_velocity_of_default_no_status_column():
    """Without a status column all loans are treated as non-defaulted (0% default rate)."""
    from decimal import Decimal

    phase = CalculationPhase.__new__(CalculationPhase)
    df = pd.DataFrame(
        {
            "as_of_date": ["2025-01-01", "2025-01-15", "2025-02-05", "2025-02-20"],
        }
    )
    result = phase._compute_portfolio_velocity_of_default(df)

    # No defaults in either period → rate 0% both months → Vd = 0
    assert result is not None
    assert isinstance(result, Decimal)
    assert float(result) == pytest.approx(0.0, abs=1e-4)


def test_compute_portfolio_velocity_of_default_units_are_percentage_points():
    """Vd is expressed in percentage points (pp); 1 pp = 100 basis points.

    Moving from a 0% default rate to a 100% default rate in one month
    yields Vd = +100 pp = +10 000 bps.
    """
    from decimal import Decimal

    phase = CalculationPhase.__new__(CalculationPhase)
    df = pd.DataFrame(
        {
            "as_of_date": ["2025-01-01", "2025-02-01"],
            "status": ["active", "defaulted"],
        }
    )
    result = phase._compute_portfolio_velocity_of_default(df)

    # Jan: 0/1 = 0%; Feb: 1/1 = 100%  → Vd = +100 pp
    assert result is not None
    assert float(result) == pytest.approx(100.0, rel=1e-4)


# ---------------------------------------------------------------------------
# _calculate_segment_par_metrics — kiting adjustment
# ---------------------------------------------------------------------------


def test_par_metrics_no_dpd_adjusted_uses_raw_dpd():
    """Without dpd_adjusted, PAR metrics use raw DPD as before."""
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

