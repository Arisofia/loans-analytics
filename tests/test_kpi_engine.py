import pandas as pd
import pytest

from python.kpi_engine import KPIEngine


def sample_portfolio():
    return pd.DataFrame({
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
    })


def test_calculate_par_30():
    engine = KPIEngine(sample_portfolio())
    par_30, details = engine.calculate_par_30()
    total_receivable = 3000.0
    dpd_sum = 450.0
    assert par_30 == pytest.approx(dpd_sum / total_receivable * 100)
    assert details["30_plus_balance"] == pytest.approx(dpd_sum)
    assert details["total_receivable"] == pytest.approx(total_receivable)
    assert any(r["metric"] == "par_30" and r["calculation_status"] == "success" for r in engine.audit_trail)


def test_calculate_collection_rate():
    engine = KPIEngine(sample_portfolio())
    rate, details = engine.calculate_collection_rate()
    eligible_total = 2700.0
    cash_total = 2700.0
    assert rate == pytest.approx((cash_total / eligible_total) * 100)
    for key in ["eligible", "cash", "total"]:
        assert key in details
    assert details["cash"] == pytest.approx(cash_total)
    assert any(r["metric"] == "collection_rate" and r["calculation_status"] == "success" for r in engine.audit_trail)


def test_calculate_collection_rate_with_collections_data():
    engine = KPIEngine(sample_portfolio())
    collections_data = pd.DataFrame({"amount": [500.0, 700.0]})
    rate, details = engine.calculate_collection_rate(collections_data)
    assert details["collections"] == pytest.approx(1200.0)
    assert rate == pytest.approx((1200.0 / 2700.0) * 100)


def test_calculate_portfolio_health():
    engine = KPIEngine(sample_portfolio())
    par_30, _ = engine.calculate_par_30()
    rate, _ = engine.calculate_collection_rate()
    health = engine.calculate_portfolio_health(par_30, rate)
    assert 0 <= health <= 10
    assert health == pytest.approx((rate - par_30) / 10.0)
    assert any(r["metric"] == "portfolio_health" and r["calculation_status"] == "success" for r in engine.audit_trail)


def test_get_audit_trail():
    engine = KPIEngine(sample_portfolio())
    engine.calculate_par_30()
    engine.calculate_collection_rate()
    engine.calculate_portfolio_health(10, 90)
    trail = engine.get_audit_trail()
    assert not trail.empty
    for col in ["metric", "run_id", "timestamp", "calculation_status"]:
        assert col in trail.columns


def test_validate_calculations():
    engine = KPIEngine(sample_portfolio())
    par_30, _ = engine.calculate_par_30()
    rate, _ = engine.calculate_collection_rate()
    engine.calculate_portfolio_health(par_30, rate)
    results = engine.validate_calculations()
    for key in ["par_30", "collection_rate", "portfolio_health"]:
        assert key in results
        assert bool(results[key]) is True


def test_par_30_zero_receivable():
    df = pd.DataFrame({
        "total_receivable_usd": [0.0],
        "total_eligible_usd": [0.0],
        "cash_available_usd": [0.0],
        "dpd_0_7_usd": [0.0],
        "dpd_7_30_usd": [0.0],
        "dpd_30_60_usd": [0.0],
        "dpd_60_90_usd": [0.0],
        "dpd_90_plus_usd": [0.0],
    })
    engine = KPIEngine(df)
    par_30, details = engine.calculate_par_30()
    assert par_30 == 0
    assert details["total_receivable"] == pytest.approx(0.0)
    assert any(r["metric"] == "par_30" and r.get("value") == 0 for r in engine.audit_trail)


def test_collection_rate_missing_column():
    df = pd.DataFrame({"total_receivable_usd": [1000.0]})
    engine = KPIEngine(df)
    with pytest.raises(ValueError, match="Missing required columns"):
        engine.calculate_collection_rate()


def test_portfolio_health_exception():
    df = pd.DataFrame({"total_receivable_usd": [1000.0]})
    engine = KPIEngine(df)
    with pytest.raises(ValueError, match="required"):
        engine.calculate_portfolio_health(None, 50.0)
    assert any(r["metric"] == "portfolio_health" and r["calculation_status"] == "failed" for r in engine.audit_trail)


def test_audit_trail_tracks_multiple_operations():
    engine = KPIEngine(sample_portfolio())
    engine.calculate_par_30()
    engine.calculate_collection_rate()
    engine.calculate_portfolio_health(15.0, 90.0)
    trail = engine.get_audit_trail()
    assert len(trail) == 3
    assert set(trail["metric"]) == {"par_30", "collection_rate", "portfolio_health"}
