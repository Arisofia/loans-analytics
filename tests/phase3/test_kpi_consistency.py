import pytest
import pandas as pd
from decimal import Decimal
from backend.src.kpi_engine.engine import run_metric_engine

def test_run_metric_engine_consistency():
    # Setup mock marts
    portfolio_mart = pd.DataFrame([
        {
            "loan_id": "L1",
            "outstanding_principal": Decimal("1000.00"),
            "days_past_due": 95,
            "default_flag": True,
            "apr": Decimal("0.12"),
            "cohort": "2024-01",
            "vintage": "2024-01",
            "status": "defaulted"
        },
        {
            "loan_id": "L2",
            "outstanding_principal": Decimal("2000.00"),
            "days_past_due": 0,
            "default_flag": False,
            "apr": Decimal("0.10"),
            "cohort": "2024-01",
            "vintage": "2024-01",
            "status": "active"
        }
    ])
    
    finance_mart = pd.DataFrame([
        {
            "interest_income": Decimal("100.00"),
            "fee_income": Decimal("20.00"),
            "funding_cost": Decimal("30.00"),
            "debt_balance": Decimal("5000.00"),
            "gross_margin": Decimal("90.00"),
            "provision_expense": Decimal("150.00")
        }
    ])
    
    sales_mart = pd.DataFrame([
        {
            "approved_ticket": Decimal("1500.00"),
            "funded_flag": True
        }
    ])
    
    marts = {
        "portfolio_mart": portfolio_mart,
        "finance_mart": finance_mart,
        "sales_mart": sales_mart
    }
    
    results = run_metric_engine(marts)
    
    # Verify risk metrics
    risk_results = {m.metric_id: m.value for m in results["risk_metrics"]}
    # total = 3000, overdue (90+) = 1000 -> par90 = 0.3333
    assert risk_results["par90"] == pytest.approx(0.3333)
    # provisions = 150, npl = 1000 -> coverage = 0.15
    assert risk_results["provision_coverage"] == pytest.approx(0.15)
    
    # Verify pricing metrics
    pricing_results = {m.metric_id: m.value for m in results["pricing_metrics"]}
    # avg_apr = 0.11 -> eir = (1 + 0.11/365)^365 - 1 = 0.1162...
    assert pricing_results["eir"] == pytest.approx(0.1162, rel=1e-3)
    # income = 120, debt = 5000 -> irr = 0.024
    assert pricing_results["portfolio_irr"] == pytest.approx(0.024)
