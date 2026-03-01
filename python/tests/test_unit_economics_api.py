"""API and service tests for the /analytics/unit-economics endpoint."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from python.apps.analytics.api.main import app
from python.apps.analytics.api.models import LoanRecord
from python.apps.analytics.api.service import KPIService


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_loan(
    loan_id: str,
    principal_balance: float,
    loan_amount: float,
    interest_rate: float,
    loan_status: str,
    days_past_due: float = 0.0,
    last_payment_amount: float = 0.0,
    total_scheduled: float = 0.0,
    recovery_value: float | None = None,
) -> dict:
    payload = {
        "id": loan_id,
        "loan_amount": loan_amount,
        "principal_balance": principal_balance,
        "interest_rate": interest_rate,
        "loan_status": loan_status,
        "days_past_due": days_past_due,
        "last_payment_amount": last_payment_amount,
        "total_scheduled": total_scheduled,
    }
    if recovery_value is not None:
        payload["recovery_value"] = recovery_value
    return payload


def _mixed_portfolio() -> list[dict]:
    """Portfolio with current, delinquent, and defaulted loans for non-trivial KPI values."""
    return [
        # Current loan – 1000 balance, pays on time
        _make_loan("L1", 1000.0, 1000.0, 0.15, "current", 0.0, 100.0, 100.0),
        # Early delinquent – 500 balance, 45 DPD
        _make_loan("L2", 500.0, 500.0, 0.20, "30-59 days past due", 45.0, 20.0, 50.0),
        # Defaulted – 800 balance, 95 DPD, partial recovery
        _make_loan("L3", 800.0, 800.0, 0.25, "default", 95.0, 0.0, 80.0, 200.0),
        # Severe delinquent – 300 balance, 75 DPD
        _make_loan("L4", 300.0, 300.0, 0.18, "60-89 days past due", 75.0, 10.0, 30.0),
    ]


# ---------------------------------------------------------------------------
# FastAPI integration tests (via TestClient)
# ---------------------------------------------------------------------------

class TestUnitEconomicsEndpoint:
    """Tests for POST /analytics/unit-economics."""

    def test_returns_200_with_valid_payload(self):
        client = TestClient(app)
        payload = {"loans": _mixed_portfolio()}
        response = client.post("/analytics/unit-economics", json=payload)
        assert response.status_code == 200

    def test_response_has_all_top_level_keys(self):
        client = TestClient(app)
        payload = {"loans": _mixed_portfolio()}
        body = client.post("/analytics/unit-economics", json=payload).json()

        expected_keys = {
            "generated_at",
            "npl",
            "lgd",
            "cost_of_risk",
            "nim",
            "payback",
            "cure_rate",
            "dpd_migration",
        }
        assert expected_keys.issubset(body.keys())

    def test_npl_structure(self):
        client = TestClient(app)
        payload = {"loans": _mixed_portfolio()}
        body = client.post("/analytics/unit-economics", json=payload).json()

        npl = body["npl"]
        assert "npl_ratio" in npl
        assert "npl_balance" in npl
        assert "total_balance" in npl
        assert "npl_loan_count" in npl
        assert "formula" in npl
        # At minimum, L3 (800, default, 95 DPD) should be classified as NPL; L4 (300, 75 DPD in 60–89 bucket)
        # may or may not be included depending on the NPL rule, so npl_ratio should be greater than zero.
        assert npl["npl_ratio"] > 0

    def test_lgd_structure(self):
        client = TestClient(app)
        payload = {"loans": _mixed_portfolio()}
        body = client.post("/analytics/unit-economics", json=payload).json()

        lgd = body["lgd"]
        assert "lgd_pct" in lgd
        assert "recovery_rate_pct" in lgd
        assert "defaulted_balance" in lgd
        assert "recovered_amount" in lgd
        # LGD should be in [0, 100]
        assert 0.0 <= lgd["lgd_pct"] <= 100.0

    def test_cost_of_risk_structure(self):
        client = TestClient(app)
        payload = {"loans": _mixed_portfolio()}
        body = client.post("/analytics/unit-economics", json=payload).json()

        cor = body["cost_of_risk"]
        assert "cost_of_risk_pct" in cor
        assert "npl_ratio" in cor
        assert "lgd_pct" in cor
        assert "expected_loss_balance" in cor

    def test_nim_structure_and_values(self):
        client = TestClient(app)
        # Provide explicit funding_cost_rate
        payload = {"loans": _mixed_portfolio(), "funding_cost_rate": 0.06}
        body = client.post("/analytics/unit-economics", json=payload).json()

        nim = body["nim"]
        assert "nim_pct" in nim
        assert "gross_yield_pct" in nim
        assert "funding_cost_pct" in nim
        # funding_cost_pct should reflect the provided rate (6%)
        assert nim["funding_cost_pct"] == pytest.approx(6.0, abs=0.01)

    def test_payback_period_with_cac_and_arpu(self):
        client = TestClient(app)
        payload = {"loans": _mixed_portfolio(), "cac": 100.0, "monthly_arpu": 25.0}
        body = client.post("/analytics/unit-economics", json=payload).json()

        payback = body["payback"]
        assert "payback_months" in payback
        assert payback["payback_months"] == pytest.approx(4.0, abs=0.01)  # 100 / 25 = 4 months
        assert payback["cac"] == pytest.approx(100.0)
        assert payback["monthly_arpu"] == pytest.approx(25.0)

    def test_payback_period_zero_arpu(self):
        client = TestClient(app)
        payload = {"loans": _mixed_portfolio(), "cac": 100.0, "monthly_arpu": 0.0}
        body = client.post("/analytics/unit-economics", json=payload).json()

        # payback_months should be None when ARPU is zero
        assert body["payback"]["payback_months"] is None

    def test_cure_rate_structure(self):
        client = TestClient(app)
        payload = {"loans": _mixed_portfolio()}
        body = client.post("/analytics/unit-economics", json=payload).json()

        cure = body["cure_rate"]
        assert "cure_rate_pct" in cure
        assert "delinquent_count" in cure
        assert "curing_count" in cure
        assert "note" in cure
        # cure_rate_pct is in [0, 100]
        assert 0.0 <= cure["cure_rate_pct"] <= 100.0

    def test_dpd_migration_structure(self):
        client = TestClient(app)
        payload = {"loans": _mixed_portfolio()}
        body = client.post("/analytics/unit-economics", json=payload).json()

        migration = body["dpd_migration"]
        assert isinstance(migration, list)
        assert len(migration) > 0

        for bucket in migration:
            assert "bucket" in bucket
            assert "loan_count" in bucket
            assert "balance" in bucket
            assert "balance_share_pct" in bucket
            assert "risk_level" in bucket
            assert "recommended_action" in bucket
            # All risk levels should be one of the known values
            assert bucket["risk_level"] in {"low", "medium", "high", "critical"}

    def test_dpd_migration_recommended_actions_present(self):
        client = TestClient(app)
        payload = {"loans": _mixed_portfolio()}
        body = client.post("/analytics/unit-economics", json=payload).json()

        # Every bucket must have a non-empty recommended_action
        for bucket in body["dpd_migration"]:
            assert bucket["recommended_action"].strip() != ""

    def test_dpd_migration_bucket_names_normalized(self):
        """DPD migration bucket names must use the same convention as /analytics/advanced-risk
        (no 'dpd_' prefix): current, 1_30, 31_60, 61_90, 90_plus."""
        client = TestClient(app)
        payload = {"loans": _mixed_portfolio()}
        body = client.post("/analytics/unit-economics", json=payload).json()

        bucket_names = {b["bucket"] for b in body["dpd_migration"]}
        # Normalized names must NOT carry the 'dpd_' prefix
        assert not any(name.startswith("dpd_") for name in bucket_names), (
            f"Found un-normalized bucket names: {bucket_names}"
        )
        # All returned names must be from the expected set
        expected = {"current", "1_30", "31_60", "61_90", "90_plus"}
        assert bucket_names.issubset(expected), (
            f"Unexpected bucket names: {bucket_names - expected}"
        )

    def test_single_current_loan(self):
        """All metrics should return sane zero/near-zero values for a healthy portfolio."""
        client = TestClient(app)
        payload = {
            "loans": [
                _make_loan("L1", 1000.0, 1000.0, 0.15, "current", 0.0, 100.0, 100.0),
            ]
        }
        body = client.post("/analytics/unit-economics", json=payload).json()

        assert body["npl"]["npl_ratio"] == 0.0
        # No defaults → LGD should be 0
        assert body["lgd"]["lgd_pct"] == 0.0
        assert body["cost_of_risk"]["cost_of_risk_pct"] == 0.0

    def test_generated_at_is_datetime(self):
        client = TestClient(app)
        payload = {"loans": _mixed_portfolio()}
        body = client.post("/analytics/unit-economics", json=payload).json()

        # generated_at should be parseable as an ISO datetime; handle 'Z' suffix for Python < 3.11
        raw_ts = body["generated_at"].replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw_ts)
        assert isinstance(dt, datetime)


# ---------------------------------------------------------------------------
# Service-level unit tests (without HTTP layer)
# ---------------------------------------------------------------------------

class TestKPIServiceUnitEconomics:
    """Unit tests for KPIService.calculate_unit_economics()."""

    @pytest.mark.asyncio
    async def test_calculate_unit_economics_basic(self):
        service = KPIService(actor="test")
        loans = [
            LoanRecord(
                id="L1",
                loan_amount=1000.0,
                principal_balance=1000.0,
                interest_rate=0.15,
                loan_status="current",
                days_past_due=0.0,
                total_scheduled=100.0,
                last_payment_amount=100.0,
            ),
            LoanRecord(
                id="L2",
                loan_amount=1000.0,
                principal_balance=1000.0,
                interest_rate=0.20,
                loan_status="default",
                days_past_due=95.0,
                total_scheduled=100.0,
                last_payment_amount=0.0,
                recovery_value=200.0,
            ),
        ]

        result = await service.calculate_unit_economics(loans)

        # L2 is defaulted (1000 out of 2000 total → 50% NPL)
        assert result.npl.npl_ratio == pytest.approx(50.0, abs=0.01)

        # Defaulted balance 1000, recovered 200 → recovery_rate = 20%, LGD = 80%
        assert result.lgd.lgd_pct == pytest.approx(80.0, abs=0.01)
        assert result.lgd.recovery_rate_pct == pytest.approx(20.0, abs=0.01)

        # COR = NPL * LGD / 100 = 50 * 80 / 100 = 40%
        assert result.cost_of_risk.cost_of_risk_pct == pytest.approx(40.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_calculate_unit_economics_dpd_migration_action_flags(self):
        service = KPIService(actor="test")
        loans = [
            LoanRecord(
                id="L1",
                loan_amount=500.0,
                principal_balance=500.0,
                interest_rate=0.1,
                loan_status="current",
                days_past_due=0.0,
            ),
            LoanRecord(
                id="L2",
                loan_amount=500.0,
                principal_balance=500.0,
                interest_rate=0.2,
                loan_status="30-59 days past due",
                days_past_due=45.0,
            ),
        ]

        result = await service.calculate_unit_economics(loans)

        # Should have at least 2 buckets using normalized names (e.g., "current" and "1_30")
        assert len(result.dpd_migration) >= 2

        # Every action should be non-empty
        for bucket in result.dpd_migration:
            assert bucket.recommended_action.strip() != ""
            assert bucket.risk_level in {"low", "medium", "high", "critical"}

    @pytest.mark.asyncio
    async def test_calculate_unit_economics_empty_loans(self):
        """Empty loan list should return zero-value metrics gracefully."""
        service = KPIService(actor="test")
        result = await service.calculate_unit_economics([])

        assert result.npl.npl_ratio == 0.0
        assert result.lgd.lgd_pct == 0.0
        assert result.cost_of_risk.cost_of_risk_pct == 0.0
        assert result.nim.nim_pct == 0.0
        assert result.cure_rate.cure_rate_pct == 0.0
        assert result.payback.payback_months is None

    @pytest.mark.asyncio
    async def test_calculate_unit_economics_nim_with_custom_funding_cost(self):
        service = KPIService(actor="test")
        loans = [
            LoanRecord(
                id="L1",
                loan_amount=1000.0,
                principal_balance=1000.0,
                interest_rate=0.30,  # 30% APR
                loan_status="current",
                days_past_due=0.0,
            ),
        ]

        result = await service.calculate_unit_economics(loans, funding_cost_rate=0.05)

        # gross_yield ≈ 30%, funding_cost = 5% → NIM ≈ 25%
        assert result.nim.funding_cost_pct == pytest.approx(5.0, abs=0.01)
        assert result.nim.gross_yield_pct > 0.0
        assert result.nim.nim_pct > 0.0

    @pytest.mark.asyncio
    async def test_calculate_unit_economics_payback_period(self):
        service = KPIService(actor="test")
        loans = [
            LoanRecord(
                id="L1",
                loan_amount=1000.0,
                principal_balance=1000.0,
                interest_rate=0.1,
                loan_status="current",
                days_past_due=0.0,
            ),
        ]

        result = await service.calculate_unit_economics(
            loans, cac=240.0, monthly_arpu=20.0
        )

        # Payback = 240 / 20 = 12 months
        assert result.payback.payback_months == pytest.approx(12.0, abs=0.01)
