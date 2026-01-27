from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Optional

import pandas as pd

from .kpi_catalog import full_catalog
from .kpi_models import KPI, KPISet, KPIValue


def _safe_div(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator not in (0, 0.0, None) else 0.0


def compute_portfolio_kpis(
    loans_df: pd.DataFrame,
    income_df: Optional[pd.DataFrame] = None,
    losses_df: Optional[pd.DataFrame] = None,
    as_of: Optional[datetime] = None,
    currency: str = "USD",
    included_kpis: Optional[Iterable[str]] = None,
) -> KPISet:
    as_of = as_of or datetime.utcnow()
    catalog = full_catalog()
    kpi_ids = list(included_kpis) if included_kpis is not None else list(catalog.keys())

    loans = loans_df.copy()

    for col, default in [
        ("status", "current"),
        ("outstanding_principal", 0.0),
        ("days_past_due", 0),
    ]:
        if col not in loans.columns:
            loans[col] = default

    total_exposure = float(loans["outstanding_principal"].sum())
    non_performing_mask = loans["status"].isin(["non_performing", "defaulted", "charged_off"])
    exposure_non_performing = float(loans.loc[non_performing_mask, "outstanding_principal"].sum())
    par30_mask = loans["days_past_due"] > 30
    principal_par30 = float(loans.loc[par30_mask, "outstanding_principal"].sum())

    horizon_12m = as_of - timedelta(days=365)

    charge_off_amount_12m = 0.0
    if losses_df is not None and not losses_df.empty:
        df = losses_df.copy()
        if "event_date" in df.columns:
            df["event_date"] = pd.to_datetime(df["event_date"])
            df_12m = df[df["event_date"] >= horizon_12m]
        else:
            df_12m = df
        charge_off_amount_12m = float(df_12m.get("charge_off_amount", pd.Series(0.0)).sum())

    interest_income = 0.0
    interest_expense = 0.0
    avg_earning_assets = total_exposure

    if income_df is not None and not income_df.empty:
        df = income_df.copy()
        if "period" in df.columns:
            df["period"] = pd.to_datetime(df["period"])
        interest_income = float(df.get("interest_income", pd.Series(0.0)).sum())
        interest_expense = float(df.get("interest_expense", pd.Series(0.0)).sum())
        avg_earning_assets = float(df.get("avg_earning_assets", pd.Series(total_exposure)).mean())

    total_ecl = float(loans.get("ecl", pd.Series(0.0)).sum())

    kpis: List[KPI] = []

    for kpi_id in kpi_ids:
        if kpi_id not in catalog:
            continue
        entry = catalog[kpi_id]

        if kpi_id == "loan_book_size":
            value = total_exposure
            unit = currency
        elif kpi_id == "npl_ratio":
            value = _safe_div(exposure_non_performing, total_exposure) * 100.0
            unit = "%"
        elif kpi_id == "par30":
            value = _safe_div(principal_par30, total_exposure) * 100.0
            unit = "%"
        elif kpi_id == "charge_off_rate":
            avg_loan_book_12m = total_exposure
            value = _safe_div(charge_off_amount_12m, avg_loan_book_12m) * 100.0
            unit = "%"
        elif kpi_id == "nim":
            value = _safe_div(interest_income - interest_expense, avg_earning_assets) * 100.0
            unit = "%"
        elif kpi_id == "ecl_ratio":
            value = _safe_div(total_ecl, total_exposure) * 100.0
            unit = "%"
        else:
            continue

        kpis.append(
            KPI(
                id=kpi_id,
                name=entry.name,
                description=entry.description,
                kpi_type=entry.kpi_type,
                level=entry.level,
                value=KPIValue(value=value, unit=unit, currency=currency, as_of=as_of),
                tags=entry.tags,
                formula=entry.formula,
                source="portfolio_kpi_engine",
                metadata={},
            )
        )

    return KPISet(
        id="portfolio_core",
        name="Portfolio KPIs",
        description="Core portfolio KPIs (risk and profitability).",
        category="portfolio",
        as_of=as_of,
        kpis=kpis,
    )


def compute_growth_kpis(
    funnel_df: pd.DataFrame,
    revenue_df: Optional[pd.DataFrame] = None,
    as_of: Optional[datetime] = None,
    currency: str = "USD",
    included_kpis: Optional[Iterable[str]] = None,
) -> KPISet:
    as_of = as_of or datetime.utcnow()
    catalog = full_catalog()
    kpi_ids = list(included_kpis) if included_kpis is not None else list(catalog.keys())

    funnel = funnel_df.copy()

    for col in [
        "applications",
        "approved",
        "funded",
        "acquisition_cost",
        "new_customers",
        "starting_customers",
        "lost_customers",
        "active_customers",
    ]:
        if col not in funnel.columns:
            funnel[col] = 0

    # Use the first row if available; if multiple rows exist, this explicitly
    # takes the first one rather than relying on index values like 0.
    row = funnel.iloc[0] if not funnel.empty else None

    total_applications = float(row["applications"]) if row is not None else 0.0
    approved_applications = float(row["approved"]) if row is not None else 0.0
    funded_loans = float(row["funded"]) if row is not None else 0.0
    acquisition_cost = float(row["acquisition_cost"]) if row is not None else 0.0
    new_customers = float(row["new_customers"]) if row is not None else 0.0
    starting_customers = float(row["starting_customers"]) if row is not None else 0.0
    lost_customers = float(row["lost_customers"]) if row is not None else 0.0
    active_customers = float(row["active_customers"]) if row is not None else 0.0

    total_revenue = 0.0
    monthly_contribution_margin = 0.0

    if revenue_df is not None and not revenue_df.empty:
        df = revenue_df.copy()
        total_revenue = float(df.get("revenue", pd.Series(0.0)).sum())
        monthly_contribution_margin = float(df.get("monthly_contribution_margin", pd.Series(0.0)).mean())

    kpis: List[KPI] = []

    for kpi_id in kpi_ids:
        if kpi_id not in catalog:
            continue
        entry = catalog[kpi_id]

        if kpi_id == "approval_rate":
            value = _safe_div(approved_applications, total_applications) * 100.0
            unit = "%"
        elif kpi_id == "conversion_rate":
            value = _safe_div(funded_loans, approved_applications) * 100.0
            unit = "%"
        elif kpi_id == "arpu":
            value = _safe_div(total_revenue, active_customers) if active_customers > 0 else 0.0
            unit = currency
        elif kpi_id == "cac":
            value = _safe_div(acquisition_cost, new_customers) if new_customers > 0 else 0.0
            unit = currency
        elif kpi_id == "cac_payback_months":
            value = _safe_div(acquisition_cost, monthly_contribution_margin) if monthly_contribution_margin > 0 else 0.0
            unit = "months"
        elif kpi_id == "churn_rate":
            value = _safe_div(lost_customers, starting_customers) * 100.0
            unit = "%"
        else:
            continue

        kpis.append(
            KPI(
                id=kpi_id,
                name=entry.name,
                description=entry.description,
                kpi_type=entry.kpi_type,
                level=entry.level,
                value=KPIValue(value=value, unit=unit, currency=currency, as_of=as_of),
                tags=entry.tags,
                formula=entry.formula,
                source="growth_kpi_engine",
                metadata={},
            )
        )

    return KPISet(
        id="growth_core",
        name="Growth KPIs",
        description="Acquisition, funnel and unit economics KPIs.",
        category="growth",
        as_of=as_of,
        kpis=kpis,
    )
