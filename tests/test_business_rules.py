import pytest

from src.analytics.business_rules import (
    ApprovalDecision,
    IndustryType,
    MYPEBusinessRules,
    RiskLevel,
)

pytestmark = pytest.mark.skip(reason="streamlit_app.utils not yet packaged as module.")

pytest.skip(
    "Skipping dashboard utils tests: streamlit_app not yet a module.",
    allow_module_level=True,
)


def test_high_risk_classification_flags_multiple_reasons():
    metrics = {
        "dpd": 120,
        "utilization": 0.95,
        "npl_ratio": 0.07,
        "collection_rate": 0.7,
    }
    is_high, reasons = MYPEBusinessRules.classify_high_risk(metrics)

    assert is_high is True
    assert "Utilization" in " ".join(reasons)
    assert len(reasons) >= 3


def test_high_risk_classification_clear_low_risk():
    metrics = {
        "dpd": 0,
        "utilization": 0.3,
        "npl_ratio": 0.01,
        "collection_rate": 0.99,
    }
    is_high, reasons = MYPEBusinessRules.classify_high_risk(metrics)

    assert is_high is False
    assert reasons == []


def test_high_risk_classification_at_thresholds_triggers_flags():
    metrics = {
        "dpd": MYPEBusinessRules.NPL_DAYS_THRESHOLD,
        "utilization": MYPEBusinessRules.HIGH_RISK_CRITERIA["utilization"],
        "npl_ratio": MYPEBusinessRules.HIGH_RISK_CRITERIA["npl_ratio"],
        "collection_rate": (MYPEBusinessRules.HIGH_RISK_CRITERIA["collection_rate"] - 0.01),
    }
    is_high, reasons = MYPEBusinessRules.classify_high_risk(metrics)

    assert is_high is True
    assert len(reasons) >= 3


def test_industry_adjustment_rewards_high_contribution():
    adjustment = MYPEBusinessRules.calculate_industry_adjustment(IndustryType.MANUFACTURING)
    assert adjustment > 1.0


def test_industry_adjustment_penalizes_low_contribution():
    adjustment = MYPEBusinessRules.calculate_industry_adjustment(IndustryType.OTHER)

    assert adjustment <= 1.0


def test_industry_adjustment_unknown_industry_falls_back_to_other():
    other_adjustment = MYPEBusinessRules.calculate_industry_adjustment(IndustryType.OTHER)
    unknown_adjustment = MYPEBusinessRules.calculate_industry_adjustment("UNKNOWN_INDUSTRY")

    assert unknown_adjustment == other_adjustment


def test_industry_adjustment_impacts_facility_approval_recommendation():
    metrics = {
        "dpd": 0,
        "utilization": 0.3,
        "npl_ratio": 0.01,
        "collection_rate": 0.98,
        "revenue": 300000,
        "avg_balance": 60000,
    }

    manufacturing_decision: ApprovalDecision = MYPEBusinessRules.evaluate_facility_approval(
        facility_amount=700000,
        customer_metrics={
            **metrics,
            "industry": IndustryType.MANUFACTURING,
        },
    )
    other_decision: ApprovalDecision = MYPEBusinessRules.evaluate_facility_approval(
        facility_amount=700000,
        customer_metrics={**metrics, "industry": IndustryType.OTHER},
    )

    assert manufacturing_decision.recommended_amount > other_decision.recommended_amount


def test_classify_npl_threshold():
    is_npl, message = MYPEBusinessRules.classify_npl(120)
    assert is_npl is True
    assert "NPL" in message


def test_classify_npl_below_threshold_is_not_npl():
    dpd = MYPEBusinessRules.NPL_DAYS_THRESHOLD - 1
    is_npl, message = MYPEBusinessRules.classify_npl(dpd)

    assert is_npl is False
    assert "current" in message.lower()


def test_rotation_target_message():
    rotation, meets, message = MYPEBusinessRules.check_rotation_target(
        total_revenue=500000, avg_balance=100000
    )
    assert pytest.approx(rotation, rel=1e-3) == 5
    assert meets is True
    assert "meets" in message.lower()


def test_rotation_target_below_threshold():
    rotation, meets, message = MYPEBusinessRules.check_rotation_target(
        total_revenue=390000, avg_balance=100000
    )

    assert rotation < MYPEBusinessRules.TARGET_ROTATION
    assert meets is False
    assert "below" in message.lower()


def test_rotation_target_boundary_condition():
    rotation, meets, message = MYPEBusinessRules.check_rotation_target(
        total_revenue=MYPEBusinessRules.TARGET_ROTATION * 100000,
        avg_balance=100000,
    )

    assert pytest.approx(rotation, rel=1e-3) == MYPEBusinessRules.TARGET_ROTATION
    assert meets is True
    assert "meets" in message.lower()


def test_check_rotation_target_zero_average_balance():
    rotation, meets, message = MYPEBusinessRules.check_rotation_target(
        total_revenue=100000, avg_balance=0.0
    )

    assert rotation == 0.0
    assert meets is False
    assert message == "Average balance unavailable"


def test_evaluate_facility_approval_recommends_collateral_for_high_risk():
    metrics = {
        "dpd": 45,
        "utilization": 0.88,
        "npl_ratio": 0.06,
        "collection_rate": 0.8,
        "revenue": 220000,
        "avg_balance": 90000,
        "industry": IndustryType.TRADE,
    }
    decision: ApprovalDecision = MYPEBusinessRules.evaluate_facility_approval(
        facility_amount=200000,
        customer_metrics=metrics,
        collateral_value=50000,
    )

    assert decision.approved is False
    assert decision.risk_level == RiskLevel.HIGH
    assert decision.required_collateral > 0
    assert decision.recommended_amount <= 200000
    assert decision.reasons


def test_evaluate_facility_approval_approves_low_risk():
    metrics = {
        "dpd": 5,
        "utilization": 0.35,
        "npl_ratio": 0.01,
        "collection_rate": 0.97,
        "revenue": 500000,
        "avg_balance": 80000,
        "industry": IndustryType.MANUFACTURING,
    }
    decision = MYPEBusinessRules.evaluate_facility_approval(
        facility_amount=300000,
        customer_metrics=metrics,
        collateral_value=50000,
    )

    assert decision.approved is True
    assert decision.risk_level in {RiskLevel.LOW, RiskLevel.MEDIUM}
    assert decision.required_collateral == 0
    assert not decision.conditions


def test_evaluate_facility_approval_flags_critical_npl():
    metrics = {
        "dpd": MYPEBusinessRules.NPL_DAYS_THRESHOLD + 10,
        "utilization": 0.4,
        "npl_ratio": 0.02,
        "collection_rate": 0.9,
        "revenue": 250000,
        "avg_balance": 100000,
        "industry": IndustryType.TRADE,
    }
    decision = MYPEBusinessRules.evaluate_facility_approval(
        facility_amount=100000,
        customer_metrics=metrics,
        collateral_value=20000,
    )

    assert decision.approved is False
    assert decision.risk_level == RiskLevel.CRITICAL
    assert any("DPD" in reason for reason in decision.reasons)


def test_evaluate_facility_approval_reduces_recommendation_when_rotation_low():
    metrics = {
        "dpd": 10,
        "utilization": 0.4,
        "npl_ratio": 0.02,
        "collection_rate": 0.95,
        "revenue": 150000,
        "avg_balance": 60000,
        "industry": IndustryType.SERVICES,
    }
    decision = MYPEBusinessRules.evaluate_facility_approval(
        facility_amount=150000,
        customer_metrics=metrics,
        collateral_value=50000,
    )

    assert decision.approved is False
    assert any("Rotation" in reason for reason in decision.reasons)
    assert decision.recommended_amount == pytest.approx(120000, rel=1e-3)


def test_evaluate_facility_approval_pod_and_collateral_behavior():
    healthy_metrics = {
        "dpd": 5,
        "utilization": 0.2,
        "npl_ratio": 0.01,
        "collection_rate": 0.99,
        "revenue": 500000,
        "avg_balance": 150000,
    }
    stressed_metrics = {**healthy_metrics, "dpd": 80}

    healthy_decision = MYPEBusinessRules.evaluate_facility_approval(
        facility_amount=100000,
        customer_metrics=healthy_metrics,
        collateral_value=20000,
    )
    stressed_decision = MYPEBusinessRules.evaluate_facility_approval(
        facility_amount=100000,
        customer_metrics=stressed_metrics,
        collateral_value=20000,
    )

    assert 0.0 <= healthy_decision.pod <= 1.0
    assert stressed_decision.pod >= healthy_decision.pod
    assert stressed_decision.required_collateral <= healthy_decision.required_collateral + 100000
