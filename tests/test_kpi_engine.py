import pandas as pd
import pytest

from python.kpi_engine import KPIEngine


def sample_portfolio():
    return pd.DataFrame(
        {
            "segment": ["Consumer", "SME"],
            "measurement_date": ["2025-01-31", "2025-01-31"],
            "total_receivable_usd": [1000.0, 2000.0],
            "total_eligible_usd": [900.0, 1800.0],
            "cash_available_usd": [900.0, 1800.0],
            "discounted_balance_usd": [800.0, 1600.0],
            "dpd_0_7_usd": [100.0, 200.0],
            "dpd_7_30_usd": [50.0, 100.0],
            "dpd_30_60_usd": [100.0, 200.0],
            "dpd_60_90_usd": [50.0, 50.0],
            "dpd_90_plus_usd": [25.0, 25.0],
        }
    )


def test_calculate_par_30():
    engine = KPIEngine(sample_portfolio())
    par_30, details = engine.calculate_par_30()
    # 30-60: 300, 60-90: 100, 90+: 50 -> Total DPD: 450
    # Total Receivable: 3000
    # PAR 30 = (450 / 3000) * 100 = 15.0
    assert par_30 == pytest.approx(15.0)
    assert details["metric"] == "PAR30"
    assert any(r["metric"] == "PAR30" and r["value"] == par_30 for r in engine.audit_trail)


def test_calculate_par_90():
    engine = KPIEngine(sample_portfolio())
    par_90, details = engine.calculate_par_90()
    # 90+: 50
    # Total Receivable: 3000
    # PAR 90 = (50 / 3000) * 100 = 1.666...
    assert par_90 == pytest.approx(1.6666666666666667)
    assert details["metric"] == "PAR90"
    assert any(r["metric"] == "PAR90" and r["value"] == par_90 for r in engine.audit_trail)


def test_calculate_collection_rate():
    engine = KPIEngine(sample_portfolio())
    rate, details = engine.calculate_collection_rate()
    # Cash: 2700, Eligible: 2700 -> 100%
    assert rate == pytest.approx(100.0)
    assert details["metric"] == "CollectionRate"
    assert any(r["metric"] == "CollectionRate" and r["value"] == rate for r in engine.audit_trail)


def test_calculate_portfolio_health():
    engine = KPIEngine(sample_portfolio())
    par_30, _ = engine.calculate_par_30()
    rate, _ = engine.calculate_collection_rate()
    health, details = engine.calculate_portfolio_health(par_30, rate)

    # PAR30 = 15.0, Collection = 100.0
    # Health = (10 - 1.5) * (100 / 10) = 8.5 * 10 = 85
    # Capped at 10
    assert health == 10.0
    assert details["metric"] == "HealthScore"
    assert any(r["metric"] == "HealthScore" and r["value"] == health for r in engine.audit_trail)


def test_get_audit_trail():
    engine = KPIEngine(sample_portfolio())
    engine.calculate_par_30()
    trail = engine.get_audit_trail()
    assert not trail.empty
    assert "metric" in trail.columns
    assert "value" in trail.columns
    assert "PAR30" in trail["metric"].values


def test_validate_schema_missing_columns():
    df = pd.DataFrame({"total_receivable_usd": [100.0]})
    engine = KPIEngine(df)
    with pytest.raises(ValueError, match="Missing required columns"):
        engine.validate_schema()
