from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class RiskLevel(str, Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'

class IndustryType(str, Enum):
    MANUFACTURING = 'MANUFACTURING'
    TRADE = 'TRADE'
    SERVICES = 'SERVICES'
    OTHER = 'OTHER'

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
    HIGH_RISK_CRITERIA = {'utilization': 0.85, 'npl_ratio': 0.05, 'collection_rate': 0.85}
    INDUSTRY_MULTIPLIERS = {IndustryType.MANUFACTURING: 1.1, IndustryType.TRADE: 1.0, IndustryType.SERVICES: 0.95, IndustryType.OTHER: 0.9}

    @classmethod
    def classify_high_risk(cls, metrics: dict[str, Any]) -> tuple[bool, list[str]]:
        dpd = float(metrics.get('dpd', 0) or 0)
        utilization = float(metrics.get('utilization', 0) or 0)
        npl_ratio = float(metrics.get('npl_ratio', 0) or 0)
        collection_rate = float(metrics.get('collection_rate', 1) or 0)
        reasons: list[str] = []
        if dpd >= cls.NPL_DAYS_THRESHOLD:
            reasons.append(f'DPD >= {cls.NPL_DAYS_THRESHOLD}')
        if utilization >= cls.HIGH_RISK_CRITERIA['utilization']:
            reasons.append('Utilization above high-risk threshold')
        if npl_ratio >= cls.HIGH_RISK_CRITERIA['npl_ratio']:
            reasons.append('NPL ratio above high-risk threshold')
        if collection_rate < cls.HIGH_RISK_CRITERIA['collection_rate']:
            reasons.append('Collection rate below high-risk threshold')
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
            return (True, f'NPL: DPD {int(value)} >= {cls.NPL_DAYS_THRESHOLD}')
        return (False, f'Loan current/watchlist: DPD {int(value)}')

    @classmethod
    def check_rotation_target(cls, annual_disbursement: float, average_balance: float) -> tuple[float, bool, str]:
        if average_balance <= 0:
            return (0.0, False, 'Average balance unavailable')
        rotation = annual_disbursement / average_balance
        meets = rotation >= cls.TARGET_ROTATION
        message = f'Rotation meets target ({rotation:.2f}x >= {cls.TARGET_ROTATION:.2f}x)' if meets else f'Rotation below target ({rotation:.2f}x < {cls.TARGET_ROTATION:.2f}x)'
        return (rotation, meets, message)

    @classmethod
    def calculate_pod(cls, dpd: float, utilization: float, npl_ratio: float, collection_rate: float) -> float:
        return min(1.0, max(0.0, dpd / cls.NPL_DAYS_THRESHOLD * 0.5 + utilization * 0.2 + npl_ratio * 2.0 * 0.2 + (1.0 - collection_rate) * 0.1))

    @classmethod
    def calculate_recommended_amount(cls, requested: float, meets_rotation: bool, industry: IndustryType | str | None) -> float:
        if not meets_rotation:
            return min(round(requested * 0.8, 2), requested)
        industry_multiplier = cls.calculate_industry_adjustment(industry)
        return min(round(requested * industry_multiplier, 2), requested)

    @classmethod
    def determine_risk_level(cls, is_npl: bool, is_high_risk: bool, pod: float) -> RiskLevel:
        if is_npl:
            return RiskLevel.CRITICAL
        elif is_high_risk:
            return RiskLevel.HIGH
        elif pod >= 0.35:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    @classmethod
    def collateral_requirements(cls, approved: bool, risk_level: RiskLevel, recommended_amount: float) -> tuple[float, list[str]]:
        if approved:
            return (0.0, [])
        collateral_ratio = 0.0
        if risk_level == RiskLevel.CRITICAL:
            collateral_ratio = 0.5
        elif risk_level == RiskLevel.HIGH:
            collateral_ratio = 0.25
        required_collateral = recommended_amount * collateral_ratio
        if required_collateral <= 0:
            return (0.0, [])
        return (required_collateral, ['Additional collateral required'])

    @classmethod
    def evaluate_facility_approval(cls, requested_amount: float, metrics: dict[str, Any], collateral_available: float=0.0) -> ApprovalDecision:
        requested = requested_amount
        dpd = metrics.get('dpd', 0) or 0
        utilization = metrics.get('utilization', 0) or 0
        npl_ratio = metrics.get('npl_ratio', 0) or 0
        collection_rate = metrics.get('collection_rate', 1) or 0
        annual_revenue = metrics.get('revenue', 0) or 0
        avg_balance = metrics.get('avg_balance', 0) or 0
        industry = metrics.get('industry', IndustryType.OTHER)
        pod = cls.calculate_pod(dpd, utilization, npl_ratio, collection_rate)
        reasons: list[str] = []
        is_npl, npl_message = cls.classify_npl(dpd)
        if is_npl:
            reasons.append(npl_message)
        is_high_risk, high_risk_reasons = cls.classify_high_risk(metrics)
        reasons.extend(high_risk_reasons)
        _, meets_rotation, rotation_message = cls.check_rotation_target(annual_revenue, avg_balance)
        if not meets_rotation:
            reasons.append(rotation_message.replace('below', 'below (Rotation)'))
        recommended_amount = cls.calculate_recommended_amount(requested, meets_rotation, industry)
        risk_level = cls.determine_risk_level(is_npl, is_high_risk, pod)
        approved = risk_level in {RiskLevel.LOW, RiskLevel.MEDIUM} and meets_rotation
        required_collateral, conditions = cls.collateral_requirements(approved, risk_level, recommended_amount)
        return ApprovalDecision(approved=approved, risk_level=risk_level, recommended_amount=recommended_amount, required_collateral=round(required_collateral, 2), pod=round(pod, 4), reasons=reasons, conditions=conditions)
