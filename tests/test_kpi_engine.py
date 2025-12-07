import pandas as pd
import pytest
from python.kpi_engine import KPIEngine

def sample_portfolio():
    return pd.DataFrame({
        "total_receivable_usd": [1000.0, 2000.0],
        "dpd_30_60_usd": [100.0, 200.0],
        "dpd_60_90_usd": [50.0, 50.0],
        "dpd_90_plus_usd": [25.0, 25.0],
        "total_eligible_usd": [900.0, 1800.0]
    })

def test_calculate_par_30():
    engine = KPIEngine(sample_portfolio())
    par_30, details = engine.calculate_par_30()
    assert par_30 == pytest.approx((100+200+50+50+25+25)/(1000+2000)*100)
    for key in ["30_plus_balance", "total_receivable"]:
        assert key in details
    assert details["30_plus_balance"] == pytest.approx(450.0)
    assert details["total_receivable"] == pytest.approx(3000.0)
    # Check instance variables
    assert hasattr(engine, "run_id")
    assert isinstance(engine.run_id, str)
    assert hasattr(engine, "audit_trail")
    assert isinstance(engine.audit_trail, list)
    # Check audit trail entry
    assert any(r["metric"] == "par_30" and r["calculation_status"] == "success" for r in engine.audit_trail)

def test_calculate_collection_rate():
    engine = KPIEngine(sample_portfolio())
    rate, details = engine.calculate_collection_rate()
    assert rate == pytest.approx((900+1800)/3000*100)
    for key in ["eligible", "total"]:
        assert key in details
    assert details["eligible"] == pytest.approx(2700.0)
    assert details["total"] == pytest.approx(3000.0)
    # Check audit trail entry
    assert any(r["metric"] == "collection_rate" and r["calculation_status"] == "success" for r in engine.audit_trail)

def test_calculate_collection_rate_with_collections_data():
    engine = KPIEngine(sample_portfolio())
    collections_data = pd.DataFrame({"amount": [500.0, 700.0]})
    _, details = engine.calculate_collection_rate(collections_data)
    assert "collections" in details
    assert details["collections"] == pytest.approx(1200.0)

def test_calculate_portfolio_health():
    engine = KPIEngine(sample_portfolio())
    par_30, _ = engine.calculate_par_30()
    rate, _ = engine.calculate_collection_rate()
    health = engine.calculate_portfolio_health(par_30, rate)
    assert 0 <= health <= 10
    # Check audit trail entry
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
    # Check audit trail values
    assert all(isinstance(val, str) for val in trail["run_id"])

def test_validate_calculations():
    engine = KPIEngine(sample_portfolio())
    par_30, _ = engine.calculate_par_30()
    rate, _ = engine.calculate_collection_rate()
    engine.calculate_portfolio_health(par_30, rate)
    results = engine.validate_calculations()
    for key in ["par_30", "collection_rate", "portfolio_health"]:
        assert key in results
        assert results[key] == True

def test_par_30_zero_receivable():
    df = pd.DataFrame({"total_receivable_usd": [0.0], "dpd_30_60_usd": [0.0]})
    engine = KPIEngine(df)
    par_30, details = engine.calculate_par_30()
    assert par_30 == 0
    assert details["total_receivable"] == pytest.approx(0.0)
    # Check audit trail for zero receivable
    assert any(r["metric"] == "par_30" and r["value"] == 0 for r in engine.audit_trail)

def test_collection_rate_missing_column():
    df = pd.DataFrame({"total_receivable_usd": [1000.0]})
    engine = KPIEngine(df)
    rate, details = engine.calculate_collection_rate()
    assert rate == 0
    assert details["eligible"] == pytest.approx(0)
    # Check audit trail for missing eligible column
    assert any(r["metric"] == "collection_rate" and r["value"] == 0 for r in engine.audit_trail)
