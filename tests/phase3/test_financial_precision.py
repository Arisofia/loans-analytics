import pytest
import pandas as pd
from decimal import Decimal
from backend.src.kpi_engine import risk, revenue, unit_economics

def test_par30_decimal_precision():
    # Test that PAR30 returns a Decimal and has correct precision
    df = pd.DataFrame({
        "outstanding_principal": [Decimal("100.00"), Decimal("200.00")],
        "days_past_due": [10, 35]
    })
    result = risk.compute_par30(df)
    assert isinstance(result, Decimal)
    # 200 / 300 = 0.666666... -> quantize(0.0001) -> 0.6667
    assert result == Decimal("0.6667")

def test_provision_coverage_ratio_logic():
    portfolio = pd.DataFrame({
        "outstanding_principal": [Decimal("1000.00"), Decimal("2000.00")],
        "days_past_due": [0, 95],
        "default_flag": [False, False]
    })
    finance = pd.DataFrame({
        "provision_expense": [Decimal("500.00")]
    })
    # Provisions = 500, NPL = 2000 -> Ratio = 0.25
    result = risk.compute_provision_coverage_ratio(portfolio, finance)
    assert result == Decimal("0.2500")

def test_eir_compounding():
    # APR 10% -> (1 + 0.1/365)^365 - 1
    portfolio = pd.DataFrame({
        "apr": [Decimal("0.10")]
    })
    result = revenue.compute_eir(portfolio)
    # (1 + 0.1/365)^365 - 1 is approx 0.10515... -> 0.1052
    assert result == Decimal("0.1052")

def test_win_rate_decimal():
    sales = pd.DataFrame({
        "funded_flag": [True, False, True]
    })
    result = unit_economics.compute_win_rate(sales)
    assert isinstance(result, Decimal)
    # 2 / 3 = 0.66666... -> 0.6667
    assert result == Decimal("0.6667")
