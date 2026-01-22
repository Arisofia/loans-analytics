import pytest

from src.kpis.growth import calculate_growth


def test_calculate_growth_positive():
    pct, ctx = calculate_growth(110.0, 100.0)
    assert pct == pytest.approx(10.0)
    assert ctx["current"] == 110.0
    assert ctx["previous"] == 100.0
    assert ctx["net_change"] == 10.0


def test_calculate_growth_negative():
    pct, ctx = calculate_growth(90.0, 100.0)
    assert pct == pytest.approx(-10.0)
    assert ctx["net_change"] == -10.0


def test_calculate_growth_zero_previous():
    pct, ctx = calculate_growth(50.0, 0.0)
    assert pct == pytest.approx(0.0)
    assert ctx["net_change"] == 50.0
