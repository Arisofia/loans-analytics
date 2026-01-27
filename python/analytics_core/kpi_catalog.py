from __future__ import annotations

from typing import Dict, List

from .kpi_models import KPILevel, KPIType


class KPICatalogEntry:
    def __init__(
        self,
        kpi_id: str,
        name: str,
        description: str,
        kpi_type: KPIType,
        level: KPILevel,
        formula: str,
        tags: List[str] | None = None,
    ) -> None:
        self.kpi_id = kpi_id
        self.name = name
        self.description = description
        self.kpi_type = kpi_type
        self.level = level
        self.formula = formula
        self.tags = tags or []


def loan_book_kpis() -> Dict[str, KPICatalogEntry]:
    return {
        "loan_book_size": KPICatalogEntry(
            kpi_id="loan_book_size",
            name="Loan Book Size",
            description="Total outstanding principal of active loans.",
            kpi_type=KPIType.CURRENCY,
            level=KPILevel.PORTFOLIO,
            formula="sum(outstanding_principal where status in {current, delinquent})",
            tags=["loan", "portfolio", "volume"],
        ),
        "npl_ratio": KPICatalogEntry(
            kpi_id="npl_ratio",
            name="NPL Ratio",
            description="Non-performing loans as a percentage of total loan book.",
            kpi_type=KPIType.PERCENTAGE,
            level=KPILevel.PORTFOLIO,
            formula="(exposure_non_performing / total_exposure) * 100",
            tags=["risk", "loan", "portfolio"],
        ),
        "par30": KPICatalogEntry(
            kpi_id="par30",
            name="PAR30",
            description="Portfolio at risk > 30 days as a percentage of outstanding principal.",
            kpi_type=KPIType.PERCENTAGE,
            level=KPILevel.PORTFOLIO,
            formula="(principal_past_due_gt_30 / total_principal) * 100",
            tags=["risk", "early_warning", "loan"],
        ),
        "charge_off_rate": KPICatalogEntry(
            kpi_id="charge_off_rate",
            name="Charge-off Rate (12m)",
            description="Charge-offs over the last 12 months as a percentage of average loan book.",
            kpi_type=KPIType.PERCENTAGE,
            level=KPILevel.PORTFOLIO,
            formula="(charge_off_amount_12m / average_loan_book_12m) * 100",
            tags=["risk", "losses"],
        ),
        "nim": KPICatalogEntry(
            kpi_id="nim",
            name="Net Interest Margin",
            description="Net interest income divided by average earning assets.",
            kpi_type=KPIType.PERCENTAGE,
            level=KPILevel.PORTFOLIO,
            formula="(interest_income - interest_expense) / avg_earning_assets * 100",
            tags=["profitability", "income"],
        ),
        "ecl_ratio": KPICatalogEntry(
            kpi_id="ecl_ratio",
            name="Expected Credit Loss Ratio",
            description="Expected credit losses as a percentage of total exposure.",
            kpi_type=KPIType.PERCENTAGE,
            level=KPILevel.PORTFOLIO,
            formula="total_ecl / total_exposure * 100",
            tags=["ifrs9", "risk", "provision"],
        ),
    }


def growth_kpis() -> Dict[str, KPICatalogEntry]:
    return {
        "approval_rate": KPICatalogEntry(
            kpi_id="approval_rate",
            name="Approval Rate",
            description="Approved applications divided by total applications.",
            kpi_type=KPIType.PERCENTAGE,
            level=KPILevel.PORTFOLIO,
            formula="approved_applications / total_applications * 100",
            tags=["growth", "funnel", "acquisition"],
        ),
        "conversion_rate": KPICatalogEntry(
            kpi_id="conversion_rate",
            name="Conversion Rate",
            description="Funded loans divided by approved applications.",
            kpi_type=KPIType.PERCENTAGE,
            level=KPILevel.PORTFOLIO,
            formula="funded_loans / approved_applications * 100",
            tags=["growth", "funnel"],
        ),
        "arpu": KPICatalogEntry(
            kpi_id="arpu",
            name="ARPU",
            description="Average revenue per active customer over a period.",
            kpi_type=KPIType.CURRENCY,
            level=KPILevel.PORTFOLIO,
            formula="total_revenue / active_customers",
            tags=["revenue", "unit_economics"],
        ),
        "cac": KPICatalogEntry(
            kpi_id="cac",
            name="Customer Acquisition Cost",
            description="Total acquisition cost divided by number of new customers.",
            kpi_type=KPIType.CURRENCY,
            level=KPILevel.PORTFOLIO,
            formula="acquisition_cost / new_customers",
            tags=["marketing", "unit_economics"],
        ),
        "cac_payback_months": KPICatalogEntry(
            kpi_id="cac_payback_months",
            name="CAC Payback Period (months)",
            description="Months to recover CAC from contribution margin.",
            kpi_type=KPIType.DURATION,
            level=KPILevel.PORTFOLIO,
            formula="cac / monthly_contribution_margin",
            tags=["growth", "unit_economics"],
        ),
        "churn_rate": KPICatalogEntry(
            kpi_id="churn_rate",
            name="Churn Rate",
            description="Customers lost over a period as a percentage of starting customers.",
            kpi_type=KPIType.PERCENTAGE,
            level=KPILevel.PORTFOLIO,
            formula="lost_customers / starting_customers * 100",
            tags=["retention"],
        ),
    }


def operational_kpis() -> Dict[str, KPICatalogEntry]:
    return {
        "tat_median": KPICatalogEntry(
            kpi_id="tat_median",
            name="Median Turnaround Time",
            description="Median time from application to decision.",
            kpi_type=KPIType.DURATION,
            level=KPILevel.OPERATIONAL,
            formula="median(decision_time - application_time)",
            tags=["ops", "sla"],
        ),
        "automation_rate": KPICatalogEntry(
            kpi_id="automation_rate",
            name="Automation Rate",
            description="Share of applications processed without manual intervention.",
            kpi_type=KPIType.PERCENTAGE,
            level=KPILevel.OPERATIONAL,
            formula="auto_decisions / total_decisions * 100",
            tags=["ops", "automation"],
        ),
        "manual_review_share": KPICatalogEntry(
            kpi_id="manual_review_share",
            name="Manual Review Share",
            description="Share of decisions requiring manual review.",
            kpi_type=KPIType.PERCENTAGE,
            level=KPILevel.OPERATIONAL,
            formula="manual_reviews / total_decisions * 100",
            tags=["ops", "capacity"],
        ),
    }


def full_catalog() -> Dict[str, KPICatalogEntry]:
    catalog: Dict[str, KPICatalogEntry] = {}
    for section in (loan_book_kpis(), growth_kpis(), operational_kpis()):
        catalog.update(section)
    return catalog
