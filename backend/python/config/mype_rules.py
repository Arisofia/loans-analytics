from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IndustryType(str, Enum):
    MANUFACTURING = "MANUFACTURING"
    TRADE = "TRADE"
    SERVICES = "SERVICES"
    OTHER = "OTHER"


@dataclass
class ApprovalDecision:
    approved: bool
    risk_level: RiskLevel
    recommended_amount: float
    required_collateral: float
    pod: float
    reasons: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)


class MYPEBusinessRules:
    NPL_DAYS_THRESHOLD = 90
    TARGET_ROTATION = 4.5
    HIGH_RISK_CRITERIA = {
        "utilization": 0.85,
        "npl_ratio": 0.05,
        "collection_rate": 0.85,
    }

    INDUSTRY_MULTIPLIERS = {
        IndustryType.MANUFACTURING: 1.10,
        IndustryType.TRADE: 1.00,
        IndustryType.SERVICES: 0.95,
        IndustryType.OTHER: 0.90,
    }

    @classmethod
    def classify_high_risk(cls, metrics: dict[str, Any]) -> tuple[bool, list[str]]:
        dpd = float(metrics.get("dpd", 0) or 0)
        utilization = float(metrics.get("utilization", 0) or 0)
        npl_ratio = float(metrics.get("npl_ratio", 0) or 0)
        collection_rate = float(metrics.get("collection_rate", 1) or 0)

        reasons: list[str] = []
        if dpd >= cls.NPL_DAYS_THRESHOLD:
            reasons.append(f"DPD >= {cls.NPL_DAYS_THRESHOLD}")
        if utilization >= cls.HIGH_RISK_CRITERIA["utilization"]:
            reasons.append("Utilization above high-risk threshold")
        if npl_ratio >= cls.HIGH_RISK_CRITERIA["npl_ratio"]:
            reasons.append("NPL ratio above high-risk threshold")
        if collection_rate < cls.HIGH_RISK_CRITERIA["collection_rate"]:
            reasons.append("Collection rate below high-risk threshold")

        return (len(reasons) > 0, reasons)

    @classmethod
    def calculate_industry_adjustment(cls, industry: IndustryType | str | None) -> float:
        try:
            industry_key = industry if isinstance(industry, IndustryType) else IndustryType(str(industry))
        except Exception:
            industry_key = IndustryType.OTHER
        return cls.INDUSTRY_MULTIPLIERS.get(industry_key, cls.INDUSTRY_MULTIPLIERS[IndustryType.OTHER])

    @classmethod
    def classify_npl(cls, dpd: int | float) -> tuple[bool, str]:
        value = float(dpd or 0)
        if value >= cls.NPL_DAYS_THRESHOLD:
            return True, f"NPL: DPD {int(value)} >= {cls.NPL_DAYS_THRESHOLD}"
        return False, f"Loan current/watchlist: DPD {int(value)}"

    @classmethod
    def check_rotation_target(cls, annual_disbursement: float, average_balance: float) -> tuple[float, bool, str]:
        if average_balance <= 0:
            return 0.0, False, "Average balance unavailable"

        rotation = float(annual_disbursement) / float(average_balance)
        meets = rotation >= cls.TARGET_ROTATION
        message = (
            f"Rotation meets target ({rotation:.2f}x >= {cls.TARGET_ROTATION:.2f}x)"
            if meets
            else f"Rotation below target ({rotation:.2f}x < {cls.TARGET_ROTATION:.2f}x)"
        )
        return rotation, meets, message

    @classmethod
    def evaluate_facility_approval(
        cls,
        requested_amount: float,
        metrics: dict[str, Any],
        collateral_available: float = 0.0,
    ) -> ApprovalDecision:
        requested = float(requested_amount)
        dpd = float(metrics.get("dpd", 0) or 0)
        utilization = float(metrics.get("utilization", 0) or 0)
        npl_ratio = float(metrics.get("npl_ratio", 0) or 0)
        collection_rate = float(metrics.get("collection_rate", 1) or 0)
        annual_revenue = float(metrics.get("revenue", 0) or 0)
        avg_balance = float(metrics.get("avg_balance", 0) or 0)
        industry = metrics.get("industry", IndustryType.OTHER)

        # Probability of default proxy in [0,1].
        pod = min(
            1.0,
            max(
                0.0,
                (dpd / cls.NPL_DAYS_THRESHOLD) * 0.50
                + utilization * 0.20
                + npl_ratio * 2.0 * 0.20
                + (1.0 - collection_rate) * 0.10,
            ),
        )

        reasons: list[str] = []
        conditions: list[str] = []

        is_npl, npl_message = cls.classify_npl(dpd)
        if is_npl:
            reasons.append(npl_message)

        is_high_risk, high_risk_reasons = cls.classify_high_risk(metrics)
        reasons.extend(high_risk_reasons)

        rotation, meets_rotation, rotation_message = cls.check_rotation_target(annual_revenue, avg_balance)
        if not meets_rotation:
            reasons.append(rotation_message.replace("below", "below (Rotation)"))

        base_recommendation = requested
        if not meets_rotation:
            # Rotation breach applies a hard reduction cap.
            recommended_amount = round(base_recommendation * 0.80, 2)
        else:
            industry_multiplier = cls.calculate_industry_adjustment(industry)
            recommended_amount = round(base_recommendation * industry_multiplier, 2)
        recommended_amount = min(recommended_amount, requested)

        if is_npl:
            risk_level = RiskLevel.CRITICAL
        elif is_high_risk:
            risk_level = RiskLevel.HIGH
        elif pod >= 0.35:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        approved = risk_level in {RiskLevel.LOW, RiskLevel.MEDIUM} and meets_rotation

        required_collateral = 0.0
        if not approved:
            collateral_ratio = 0.0
            if risk_level == RiskLevel.CRITICAL:
                collateral_ratio = 0.50
            elif risk_level == RiskLevel.HIGH:
                collateral_ratio = 0.25

            required_collateral = recommended_amount * collateral_ratio
            if required_collateral > 0:
                conditions.append("Additional collateral required")

        if approved:
            conditions = []
            required_collateral = 0.0

        return ApprovalDecision(
            approved=approved,
            risk_level=risk_level,
            recommended_amount=recommended_amount,
            required_collateral=round(required_collateral, 2),
            pod=round(pod, 4),
            reasons=reasons,
            conditions=conditions,
        )
