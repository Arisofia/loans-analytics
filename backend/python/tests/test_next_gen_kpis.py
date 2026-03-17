"""Next Generation KPI and Risk Stratification tests."""

import pytest
import pandas as pd
from datetime import datetime

from python.apps.analytics.api.models import LoanRecord
from python.apps.analytics.api.service import KPIService


@pytest.mark.asyncio
async def test_calculate_kpis_for_portfolio_includes_next_gen_kpis():
    service = KPIService(actor="test_user")
    loans = [
        LoanRecord(
            id="L1",
            loan_amount=1000.0,
            principal_balance=1000.0,
            interest_rate=0.1,
            loan_status="current",
            days_past_due=0.0,
            total_scheduled=100.0,
            last_payment_amount=100.0,
        ),
        LoanRecord(
            id="L2",
            loan_amount=1000.0,
            principal_balance=1000.0,
            interest_rate=0.2,
            loan_status="90+ days past due",
            days_past_due=95.0,
            total_scheduled=100.0,
            last_payment_amount=0.0,
            recovery_value=200.0,
        ),
    ]

    response = await service.calculate_kpis_for_portfolio(loans)
    kpi_map = {k.id: k for k in response}

    # Verify Next-Gen KPIs presence
    assert "PAR60" in kpi_map
    assert "NPL" in kpi_map
    assert "LGD" in kpi_map
    assert "COR" in kpi_map
    assert "CURERATE" in kpi_map
    assert "NIM" in kpi_map

    # Verify values
    # Total outstanding = 2000
    # L2 is PAR60 and PAR90 (NPL)
    assert kpi_map["PAR60"].value == 50.0
    assert kpi_map["NPL"].value == 50.0

    # Recovery rate for L2 (defaulted) = 200 / 1000 = 20%
    # LGD = 100 - 20 = 80%
    assert kpi_map["LGD"].value == 80.0

    # NPL = 50% (1000/2000)
    # LGD = 80% (1 - 20% recovery)
    # COR = NPL * LGD = 50 * 0.8 = 40%
    assert kpi_map["COR"].value == 40.0


@pytest.mark.asyncio
async def test_get_risk_stratification():
    service = KPIService(actor="test_user")
    loans = [
        LoanRecord(
            id="L1",
            borrower_id="B1",
            loan_amount=1000.0,
            principal_balance=1000.0,
            interest_rate=0.1,
            loan_status="current",
            days_past_due=0.0,
            total_scheduled=100.0,
            last_payment_amount=100.0,
        ),
        LoanRecord(
            id="L2",
            borrower_id="B2",
            loan_amount=5000.0,
            principal_balance=5000.0,
            interest_rate=0.15,
            loan_status="30-59 days past due",
            days_past_due=45.0,
            total_scheduled=500.0,
            last_payment_amount=400.0,
        ),
    ]

    response = await service.get_risk_stratification(loans)

    assert len(response.buckets) > 0
    assert len(response.decision_flags) == 4

    # Verify decision flags
    flags = {f.flag: f for f in response.decision_flags}
    assert "Concentration" in flags
    assert "Asset Quality" in flags
    assert "Liquidity" in flags
    assert "Recovery" in flags

    # HHI for 1000 and 5000 in 6000 total
    # share1 = 1/6, share2 = 5/6
    # HHI = ((1/6)^2 + (5/6)^2) * 10000 = (1/36 + 25/36) * 10000 = 26/36 * 10000 approx 7222
    assert flags["Concentration"].status == "red"

    # PAR30 = 5000 / 6000 = 83.3%
    assert flags["Asset Quality"].status == "red"

    # Collections coverage = 500 / 600 = 83.3%
    assert flags["Liquidity"].status == "yellow"
    assert flags["Recovery"].status == "red"

    assert response.summary


@pytest.mark.asyncio
async def test_get_vintage_curves():
    service = KPIService(actor="test_user")
    now = datetime.now()
    loans = [
        # Older loan (6 MoB), Current
        LoanRecord(
            id="OLD",
            origination_date=now - pd.DateOffset(months=6),
            loan_amount=1000.0,
            principal_balance=800.0,
            interest_rate=0.1,
            loan_status="current",
            days_past_due=0.0,
        ),
        # Newer loan (1 MoB), Defaulted
        LoanRecord(
            id="NEW",
            origination_date=now - pd.DateOffset(months=1),
            loan_amount=1000.0,
            principal_balance=1000.0,
            interest_rate=0.1,
            loan_status="default",
            days_past_due=95.0,
        ),
    ]

    response = await service.calculate_vintage_curves(loans)

    # Verify curves exist
    assert len(response.curves) == 2
    assert len(response.portfolio_average_curve) == 2

    # The avg curve should have points at MoB 1 and MoB 6
    avg_points = {p.months_on_book: p for p in response.portfolio_average_curve}
    assert 1 in avg_points
    assert 6 in avg_points

    # MoB 1 point (New loan) should be defaulted
    assert avg_points[1].npl_ratio == 100.0

    # MoB 6 point (Old loan) should be healthy
    assert avg_points[6].npl_ratio == 0.0
