import pandas as pd
import pytest

from src.kpi_engine_v2 import KPIEngineV2


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
    engine = KPIEngineV2(sample_portfolio())
    par_30, details = engine.calculate_par_30()
    # 30-60: 300, 60-90: 100, 90+: 50 -> Total DPD: 450
    # Total Receivable: 3000
    # PAR 30 = (450 / 3000) * 100 = 15.0
    assert par_30 == pytest.approx(15.0)
    assert details["metric"] == "PAR30"


def test_calculate_par_90():
    engine = KPIEngineV2(sample_portfolio())
    par_90, details = engine.calculate_par_90()
    # 90+: 50
    # Total Receivable: 3000
    # PAR 90 = (50 / 3000) * 100 = 1.666...
    assert par_90 == pytest.approx(1.6666666666666667)
    assert details["metric"] == "PAR90"


def test_calculate_collection_rate():
    engine = KPIEngineV2(sample_portfolio())
    rate, details = engine.calculate_collection_rate()
    # Cash: 2700, Eligible: 2700 -> 100%
    assert rate == pytest.approx(100.0)
    assert details["metric"] == "CollectionRate"


def test_calculate_all():
    engine = KPIEngineV2(sample_portfolio())
    results = engine.calculate_all()
    assert results["PAR30"]["value"] == pytest.approx(15.0)
    assert results["PAR90"]["value"] == pytest.approx(1.6666666666666667)
    assert results["CollectionRate"]["value"] == pytest.approx(100.0)
    assert results["PortfolioHealth"]["value"] == 10.0


def test_get_audit_trail():
    engine = KPIEngineV2(sample_portfolio())
    engine.calculate_all()
    trail = engine.get_audit_trail()
    assert not trail.empty
    assert "event" in trail.columns
    assert "status" in trail.columns
    assert "calculate_all" in trail["event"].values
