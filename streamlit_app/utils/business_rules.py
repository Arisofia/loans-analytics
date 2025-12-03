"""Business rules governing MYPE facility approvals and risk classification."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IndustryType(Enum):
    TRADE = 0.13
    SERVICES = 0.21
    MANUFACTURING = 0.16
    AGRICULTURE = 0.08
    CONSTRUCTION = 0.1
    TRANSPORT = 0.09
    OTHER = 0.05

    @classmethod
    def default(cls) -> "IndustryType":
        return cls.SERVICES


@dataclass
class ApprovalDecision:
    approved: bool
    risk_level: RiskLevel
    recommended_amount: float
    required_collateral: float
    conditions: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    pod: float = 0.0


class MYPEBusinessRules:
    FACILITY_THRESHOLDS: Dict[RiskLevel, float] = {
        RiskLevel.LOW: 600000,
        RiskLevel.MEDIUM: 400000,
        RiskLevel.HIGH: 200000,
        RiskLevel.CRITICAL: 50000,
    }
    HIGH_RISK_CRITERIA: Dict[str, float] = {
        "dpd": 30,
        "utilization": 0.9,
        "npl_ratio": 0.05,
        "collection_rate": 0.85,
    }
    INDUSTRY_GDP_CONTRIBUTION: Dict[IndustryType, float] = {industry: industry.value for industry in IndustryType}
    EINVOICE_THRESHOLD = 10000
    TARGET_ROTATION = 4.0
    NPL_DAYS_THRESHOLD = 90
    TARGET_COLLECTION_RATE = 0.92

    @classmethod
    def default_industry(cls) -> IndustryType:
        return IndustryType.default()

    @classmethod
    def classify_high_risk(cls, customer_metrics: Dict) -> Tuple[bool, List[str]]:
        reasons: List[str] = []
        dpd = customer_metrics.get("dpd", 0)
        utilization = customer_metrics.get("utilization", 0)
        npl_ratio = customer_metrics.get("npl_ratio", 0)
        collection_rate = customer_metrics.get("collection_rate", 1)

        if dpd >= cls.NPL_DAYS_THRESHOLD:
            reasons.append("DPD above NPL threshold")
        if utilization >= cls.HIGH_RISK_CRITERIA["utilization"]:
            reasons.append("Utilization above tolerance")
        if npl_ratio >= cls.HIGH_RISK_CRITERIA["npl_ratio"]:
            reasons.append("NPL ratio elevated")
        if collection_rate < cls.HIGH_RISK_CRITERIA["collection_rate"]:
            reasons.append("Collections below target")

        return bool(reasons), reasons

    @classmethod
    def calculate_risk_level(cls, pod: float) -> RiskLevel:
        """Derive risk level from probability of default using clear thresholds.

        The previous implementation relied on sequential ``if`` statements that
        could overwrite a ``HIGH`` classification with ``CRITICAL`` even when the
        intent was to return the first matching bucket. This method uses an
        explicit ``if``/``elif`` ladder to ensure a single risk bucket is
        selected based on POD.
        """

        if pod >= 0.75:
            return RiskLevel.CRITICAL
        if pod >= 0.5:
            return RiskLevel.HIGH
        if pod >= 0.25:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @classmethod
    def evaluate_facility_approval(
        cls, facility_amount: float, customer_metrics: Dict, collateral_value: float = 0.0
    ) -> ApprovalDecision:
        is_high_risk, reasons = cls.classify_high_risk(customer_metrics)
        dpd = customer_metrics.get("dpd", 0)
        pod = min(1.0, (dpd / cls.NPL_DAYS_THRESHOLD) * 0.8 + customer_metrics.get("npl_ratio", 0.02))

        risk_level = cls.calculate_risk_level(pod)
        if dpd >= cls.NPL_DAYS_THRESHOLD:
            risk_level = RiskLevel.CRITICAL
        elif is_high_risk:
            risk_level = max(risk_level, RiskLevel.HIGH, key=lambda level: list(RiskLevel).index(level))
        elif customer_metrics.get("utilization", 0) > 0.75:
            risk_level = max(risk_level, RiskLevel.MEDIUM, key=lambda level: list(RiskLevel).index(level))

        industry = customer_metrics.get("industry", cls.default_industry())
        adjustment = cls.calculate_industry_adjustment(industry)
        recommended_amount = min(facility_amount, cls.FACILITY_THRESHOLDS[risk_level] * adjustment)

        rotation, meets_rotation, rotation_message = cls.check_rotation_target(
            total_revenue=customer_metrics.get("revenue", 0),
            avg_balance=customer_metrics.get("avg_balance", 1),
        )
        if not meets_rotation:
            reasons.append(rotation_message)
            recommended_amount *= 0.8

        approved = risk_level in {RiskLevel.LOW, RiskLevel.MEDIUM} and not is_high_risk and meets_rotation
        required_collateral = max(0.0, facility_amount - collateral_value - recommended_amount)
        if not approved:
            required_collateral = max(required_collateral, facility_amount * 0.1)
        conditions = []
        if approved and facility_amount > recommended_amount:
            conditions.append("Provide collateral for amount above recommendation")
        if not approved:
            conditions.append("Strengthen collections and reduce DPD")

        return ApprovalDecision(
            approved=approved,
            risk_level=risk_level,
            recommended_amount=round(recommended_amount, 2),
            required_collateral=round(required_collateral, 2),
            conditions=conditions,
            reasons=reasons,
            pod=round(pod, 4),
        )

    @classmethod
    def calculate_industry_adjustment(cls, industry: IndustryType) -> float:
        contribution = cls.INDUSTRY_GDP_CONTRIBUTION.get(industry, IndustryType.OTHER.value)
        return 1.0 + (contribution - 0.1) * 0.5

    @classmethod
    def check_rotation_target(cls, total_revenue: float, avg_balance: float) -> Tuple[float, bool, str]:
        if avg_balance <= 0:
            return 0.0, False, "Average balance unavailable"
        rotation = total_revenue / avg_balance
        meets = rotation >= cls.TARGET_ROTATION
        message = "Rotation meets target" if meets else "Rotation below target"
        return rotation, meets, message

    @classmethod
    def classify_npl(cls, dpd: int) -> Tuple[bool, str]:
        is_npl = dpd >= cls.NPL_DAYS_THRESHOLD
        message = "Customer is in NPL status" if is_npl else "Customer is current"
        return is_npl, message

    @classmethod
    def get_industry_benchmarks(cls, industry: IndustryType) -> Dict:
        return {
            "gdp_contribution": cls.INDUSTRY_GDP_CONTRIBUTION.get(industry, IndustryType.OTHER.value),
            "rotation_target": cls.TARGET_ROTATION,
            "collection_target": cls.TARGET_COLLECTION_RATE,
        }
