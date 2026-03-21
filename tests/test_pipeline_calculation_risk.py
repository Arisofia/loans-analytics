"""Tests for advanced risk calculation features in CalculationPhase.

Covers:
- _calculate_ltv_sintetico: Synthetic Factoring LTV per loan
- _calculate_velocity_of_default: First derivative of default rate over time
- _calculate_segment_par_metrics: Kiting/carousel adjustment via dpd_adjusted
"""

import types

import pandas as pd
import pytest
import numpy as np

import backend.src.pipeline.calculation as calc_module
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
            "valor_nominal_factura": [100.0, -50.0],  # negative nominal is invalid
            "tasa_dilucion": [1.1, 0.1],  # >100% dilution makes it negative
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert np.isnan(result.iloc[0])
    assert np.isnan(result.iloc[1])
    assert (df["ltv_sintetico_is_opaque"] == 1).all()


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
    assert pd.isna(vd.iloc[0])
    assert vd.iloc[1] == pytest.approx(1.5)
    assert vd.iloc[2] == pytest.approx(-0.5)


def test_ltv_sintetico_preserves_indices():
    """Output series must have the same index as input dataframe."""
    df = pd.DataFrame(
        {
            "capital_desembolsado": [100.0],
            "valor_nominal_factura": [200.0],
            "tasa_dilucion": [0.0],
        },
        index=[42],
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
    df = pd.DataFrame(
        {
            "measurement_date": ["2025-02-01", "2025-01-01", "2025-02-15", "2025-01-15"],
            "status": ["defaulted", "active", "defaulted", "active"],
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    # Jan: 0/2 = 0%, Feb: 2/2 = 100% -> Vd = +100
    assert float(result) == 100.0


def test_vd_units_percentage_points():
    """Vd should return diff in percentage points, not decimal ratios."""
    df = pd.DataFrame(
        {
            "as_of_date": ["2025-01-01", "2025-02-01"],
            "status": ["defaulted", "active"],  # 100% -> 0%
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == -100.0


def test_vd_handles_mixed_date_formats():
    """Vd should handle mixed date formats via 'mixed' parser."""
    df = pd.DataFrame(
        {
            "as_of_date": ["2025-01-01", "02/01/2025"],  # ISO and US-ish (Feb 1st)
            "status": ["active", "defaulted"],
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == 100.0


def test_vd_ignores_nan_dates():
    """Rows with unparseable dates should be excluded from Vd calculation."""
    df = pd.DataFrame(
        {
            "as_of_date": ["2025-01-01", "not-a-date", "2025-02-01"],
            "status": ["active", "active", "defaulted"],
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == 100.0


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


def test_compute_portfolio_velocity_of_default_unsorted_input_v2():
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


def test_compute_portfolio_velocity_of_default_units_are_percentage_points_v2():
    """Vd is expressed in percentage points (pp); 1 pp = 100 basis points.

    Moving from a 0% default rate to a 100% default rate in one month
    yields Vd = +100 pp = +10 000 bps.
    """

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


def test_par_metrics_zero_total_balance():
    """If total balance is zero, PAR metrics should return 0.0 (avoid Div0)."""
    grp = pd.DataFrame({"outstanding_balance": [0.0], "dpd": [30.0]})
    result = CalculationPhase._calculate_segment_par_metrics(grp, "outstanding_balance", "dpd", 0.0)
    assert result["par_30"] == 0.0
    assert result["par_60"] == 0.0
    assert result["par_90"] == 0.0


def test_par_metrics_empty_group():
    """Empty group should return 0.0 for all PAR buckets."""
    grp = pd.DataFrame(columns=["outstanding_balance", "dpd"])
    result = CalculationPhase._calculate_segment_par_metrics(
        grp, "outstanding_balance", "dpd", 100.0
    )
    assert result["par_30"] == 0.0
    assert result["par_60"] == 0.0
    assert result["par_90"] == 0.0


def test_ltv_sintetico_all_nan_input():
    """If all required columns are present but all NaN, result should be all NaN."""
    df = pd.DataFrame(
        {
            "capital_desembolsado": [np.nan, np.nan],
            "valor_nominal_factura": [np.nan, np.nan],
            "tasa_dilucion": [np.nan, np.nan],
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert np.isnan(result).all()
    assert (df["ltv_sintetico_is_opaque"] == 1).all()


def test_vd_no_active_loans():
    """Vd should return None if no active/defaulted/delinquent loans exist."""
    df = pd.DataFrame({"as_of_date": ["2025-01-01", "2025-02-01"], "status": ["closed", "closed"]})
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert result is None


def test_vd_all_defaulted_steady():
    """Vd should be 0.0 if default rate is constant at 100%."""
    df = pd.DataFrame(
        {"as_of_date": ["2025-01-01", "2025-02-01"], "status": ["defaulted", "defaulted"]}
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == 0.0


def test_vd_three_periods_delta():
    """Vd should return the difference between the LAST two periods."""
    df = pd.DataFrame(
        {
            "as_of_date": ["2025-01-01", "2025-02-01", "2025-03-01"],
            "status": ["active", "defaulted", "active"],
            # Jan: 0%, Feb: 100%, Mar: 0%
            # Vd(Feb) = +100, Vd(Mar) = -100
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._compute_portfolio_velocity_of_default(df)
    assert float(result) == -100.0


def test_ltv_sintetico_zero_dilution():
    """Zero dilution should result in simple capital/nominal ratio."""
    df = pd.DataFrame(
        {"capital_desembolsado": [100.0], "valor_nominal_factura": [200.0], "tasa_dilucion": [0.0]}
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    result = engine._calculate_ltv_sintetico(df)
    assert result.iloc[0] == 0.5
    assert df.loc[0, "ltv_sintetico_is_opaque"] == 0


# ---------------------------------------------------------------------------
# _rollup_sum — period key regression tests
# ---------------------------------------------------------------------------


def test_rollup_sum_monthly_includes_period_key():
    """Monthly rollup records must include the period key, not just numeric totals."""
    df = pd.DataFrame(
        {
            "payment_date": pd.to_datetime(["2025-01-10", "2025-01-20", "2025-02-15"]),
            "amount": [100.0, 200.0, 300.0],
        }
    )
    phase = object.__new__(CalculationPhase)
    records = phase._rollup_sum(df, "payment_date", ["amount"], "monthly", 12)

    assert len(records) == 2, f"Expected 2 monthly buckets, got {len(records)}"
    for record in records:
        assert "payment_date" in record, f"Period key missing from monthly record: {record}"


def test_rollup_sum_daily_includes_date_key():
    """Daily rollup records must include the date key."""
    df = pd.DataFrame(
        {
            "payment_date": pd.to_datetime(["2025-01-10", "2025-01-10", "2025-01-11"]),
            "amount": [50.0, 50.0, 75.0],
        }
    )
    phase = object.__new__(CalculationPhase)
    records = phase._rollup_sum(df, "payment_date", ["amount"], "daily", 30)

    assert len(records) == 2, f"Expected 2 daily buckets, got {len(records)}"
    for record in records:
        assert "payment_date" in record, f"Date key missing from daily record: {record}"


def test_dimension_segment_kpis_are_sorted_deterministically():
    """Segment dimension keys should be deterministic regardless of input row order."""
    work = pd.DataFrame(
        {
            "company": ["Zeta", "Alpha"],
            "outstanding_balance": [100.0, 200.0],
            "dpd": [0.0, 45.0],
            "status": ["active", "delinquent"],
        }
    )
    phase = object.__new__(CalculationPhase)

    result = phase._calculate_dimension_segment_kpis(
        work,
        dim="company",
        balance_col="outstanding_balance",
        dpd_col="dpd",
        status_col="status",
    )

    assert list(result.keys()) == ["Alpha", "Zeta"]


# ---------------------------------------------------------------------------
# _calculate_derived_risk_kpis — npl_ratio vs npl_90_ratio divergence
# ---------------------------------------------------------------------------


def test_npl_ratio_and_npl_90_ratio_are_distinct():
    """npl_ratio (DPD≥30 broad) must differ from npl_90_ratio (DPD≥90 strict)."""
    df = pd.DataFrame(
        {
            "outstanding_balance": [1000.0, 1000.0, 1000.0, 1000.0, 1000.0],
            "dpd": [0, 35, 60, 95, 0],
            "status": ["active", "active", "delinquent", "delinquent", "defaulted"],
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    kpis = engine._calculate_derived_risk_kpis(df)

    # npl_90_ratio: DPD≥90 or defaulted → rows 3 (dpd=95) and 4 (defaulted) = 2/5 = 40%
    assert float(kpis["npl_90_ratio"]) == pytest.approx(40.0, rel=1e-4)
    # npl_ratio (broad): DPD≥30 or delinquent/defaulted → rows 1,2,3,4 = 4/5 = 80%
    assert float(kpis["npl_ratio"]) == pytest.approx(80.0, rel=1e-4)
    assert (
        kpis["npl_ratio"] != kpis["npl_90_ratio"]
    ), "npl_ratio and npl_90_ratio must be distinct; they were identical before fix"


def test_npl_90_ratio_strictly_subset_of_npl_ratio():
    """npl_90_ratio (strict) must always be <= npl_ratio (broad)."""
    df = pd.DataFrame(
        {
            "outstanding_balance": [500.0, 500.0, 1000.0],
            "dpd": [0, 45, 120],
            "status": ["active", "active", "active"],
        }
    )
    engine = KPIEngineV2.__new__(KPIEngineV2)
    kpis = engine._calculate_derived_risk_kpis(df)

    assert float(kpis["npl_90_ratio"]) <= float(
        kpis["npl_ratio"]
    ), "npl_90_ratio should never exceed npl_ratio"


# ---------------------------------------------------------------------------
# _normalize_status_column — Spanish + casing variant regression tests
# ---------------------------------------------------------------------------


def test_status_normalization_spanish_values():
    """Spanish status labels (various casings) must map to canonical English values."""
    from backend.src.pipeline.transformation import TransformationPhase

    raw_statuses = [
        # active
        "Activo",
        "ACTIVO",
        "activo",
        "Vigente",
        "VIGENTE",
        "vigente",
        "AL_DIA",
        "Al_dia",
        "al_dia",
        # delinquent
        "Moroso",
        "MOROSO",
        "moroso",
        "EN_MORA",
        "En_mora",
        "en_mora",
        # defaulted
        "Incumplimiento",
        "INCUMPLIMIENTO",
        "incumplimiento",
        "EN_INCUMPLIMIENTO",
        "En_incumplimiento",
        "en_incumplimiento",
        "Vencido",
        "VENCIDO",
        "vencido",
        "Castigado",
        "CASTIGADO",
        "castigado",
        # closed
        "Cerrado",
        "CERRADO",
        "cerrado",
        "Liquidado",
        "LIQUIDADO",
        "liquidado",
        "Cancelado",
        "CANCELADO",
        "cancelado",
    ]
    expected = (
        ["active"] * 9  # activo + vigente + al_dia
        + ["delinquent"] * 6  # moroso + en_mora
        + ["defaulted"] * 12  # incumplimiento + en_incumplimiento + vencido + castigado
        + ["closed"] * 9  # cerrado + liquidado + cancelado
    )

    df = pd.DataFrame({"status": raw_statuses})
    phase = TransformationPhase.__new__(TransformationPhase)
    phase._normalize_status_column(df, {})

    for raw, got, exp in zip(raw_statuses, df["status"].tolist(), expected):
        assert got == exp, f"'{raw}' mapped to '{got}', expected '{exp}'"


def test_status_normalization_english_values():
    """Standard English status labels (various casings) map to canonical values."""
    from backend.src.pipeline.transformation import TransformationPhase

    cases = [
        ("Active", "active"),
        ("ACTIVE", "active"),
        ("Current", "active"),
        ("CURRENT", "active"),
        ("Delinquent", "delinquent"),
        ("DELINQUENT", "delinquent"),
        ("Defaulted", "defaulted"),
        ("DEFAULT", "defaulted"),
        ("Complete", "closed"),
        ("Closed", "closed"),
        ("CLOSED", "closed"),
    ]
    df = pd.DataFrame({"status": [c[0] for c in cases]})
    phase = TransformationPhase.__new__(TransformationPhase)
    phase._normalize_status_column(df, {})

    for (raw, expected), got in zip(cases, df["status"].tolist()):
        assert got == expected, f"'{raw}' mapped to '{got}', expected '{expected}'"


# ---------------------------------------------------------------------------
# Silent-handler hardening regression tests (Block 3b)
# ---------------------------------------------------------------------------


class TestSilentHandlerHardening:
    """Regression tests: previously-silent exception paths now raise CRITICAL errors."""

    def test_rollup_sum_raises_on_nonexistent_date_column(self):
        """_rollup_sum must raise CRITICAL ValueError if the date column does not exist."""
        df = pd.DataFrame({"amount": [100.0, 200.0]})
        phase = object.__new__(CalculationPhase)
        with pytest.raises(ValueError, match="CRITICAL:"):
            phase._rollup_sum(df, "nonexistent_date_col", ["amount"], "monthly", 12)

    def test_rollup_sum_raises_on_non_datetime_column(self):
        """_rollup_sum must raise CRITICAL ValueError when the date column is not datetime-like."""
        df = pd.DataFrame({"txn_date": ["not-a-date", "also-not-a-date"], "amount": [100.0, 200.0]})
        phase = object.__new__(CalculationPhase)
        with pytest.raises(ValueError, match="CRITICAL:"):
            phase._rollup_sum(df, "txn_date", ["amount"], "daily", 30)

    def test_apply_umap_raises_when_umap_errors_while_available(self, monkeypatch):
        """When UMAP is available but raises, _apply_umap must re-raise CRITICAL ValueError."""

        class FakeUMAP:
            def __init__(self, **kwargs):
                raise RuntimeError("UMAP internal error")

        fake_umap_module = types.SimpleNamespace(UMAP=FakeUMAP)
        monkeypatch.setattr(calc_module, "_UMAP_AVAILABLE", True)
        monkeypatch.setattr(calc_module, "umap", fake_umap_module, raising=False)

        X_pca = np.zeros((20, 2))
        metrics: dict = {}
        with pytest.raises(ValueError, match="CRITICAL:.*UMAP"):
            CalculationPhase._apply_umap(X_pca, metrics)

    def test_apply_hdbscan_raises_when_hdbscan_errors_while_available(self, monkeypatch):
        """When HDBSCAN is available but raises, _apply_hdbscan must re-raise CRITICAL ValueError."""

        class FakeHDBSCAN:
            def __init__(self, **kwargs):
                raise RuntimeError("HDBSCAN internal error")

        fake_hdbscan_module = types.SimpleNamespace(HDBSCAN=FakeHDBSCAN)
        monkeypatch.setattr(calc_module, "_HDBSCAN_AVAILABLE", True)
        monkeypatch.setattr(calc_module, "hdbscan_module", fake_hdbscan_module, raising=False)

        X_embed = np.zeros((20, 2))
        X_fallback = np.zeros((20, 2))
        metrics: dict = {}
        with pytest.raises(ValueError, match="CRITICAL:.*HDBSCAN"):
            CalculationPhase._apply_hdbscan(X_embed, X_fallback, metrics)

    def test_run_advanced_clustering_propagates_critical_on_inner_failure(self, monkeypatch):
        """_run_advanced_clustering must propagate CRITICAL ValueError when a step fails."""
        phase = object.__new__(CalculationPhase)

        def _bad_build(df):
            raise RuntimeError("simulated feature-matrix failure")

        monkeypatch.setattr(phase, "_build_feature_matrix", _bad_build)

        df = pd.DataFrame({"ltv_sintetico": [1.0, 2.0, 3.0] * 5})
        with pytest.raises(ValueError, match="CRITICAL:"):
            phase._run_advanced_clustering(df)
