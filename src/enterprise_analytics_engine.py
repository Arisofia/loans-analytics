from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Optional

import pandas as pd


@dataclass
class LoanAnalyticsConfig:
    arrears_threshold: int = 90
    currency: str = "USD"


class LoanAnalyticsEngine:
    """Prepare loan data and compute portfolio analytics.

    The engine enforces schema validation and derives normalized fields that are
    reused across KPI calculations.
    """

    REQUIRED_COLUMNS = {
        "loan_id",
        "principal",
        "interest_rate",
        "term_months",
        "origination_date",
        "status",
        "days_in_arrears",
        "balance",
        "payments_made",
        "write_off_amount",
    }
    NUMERIC_COLUMNS = [
        "principal",
        "interest_rate",
        "term_months",
        "days_in_arrears",
        "balance",
        "payments_made",
        "write_off_amount",
    ]

    def __init__(self, frame: pd.DataFrame, config: Optional[LoanAnalyticsConfig] = None):
        self.config = config or LoanAnalyticsConfig()
        self.data = self._prepare_data(frame.copy())

    def _prepare_data(self, frame: pd.DataFrame) -> pd.DataFrame:
        missing = self.REQUIRED_COLUMNS.difference(frame.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        # strict date validation
        try:
            frame["origination_date"] = pd.to_datetime(frame["origination_date"], errors="raise")
        except Exception as exc:  # pragma: no cover - error rewrapped
            raise ValueError("Invalid origination_date values") from exc

        # numeric coercion with validation
        coerced = frame[self.NUMERIC_COLUMNS].apply(pd.to_numeric, errors="coerce")
        if coerced.isna().any().any():
            invalid_cols = coerced.columns[coerced.isna().any()].tolist()
            raise ValueError(f"Invalid numeric values encountered in columns: {invalid_cols}")
        frame[self.NUMERIC_COLUMNS] = coerced

        frame["status"] = frame["status"].astype(str).str.lower().str.strip().replace({"nan": ""})

        frame["arrears_flag"] = (
            frame["status"].isin({"arrears", "npl", "default"})
            | (frame["days_in_arrears"] >= self.config.arrears_threshold)
        )

        frame["origination_quarter"] = frame["origination_date"].dt.to_period("Q").astype(str)
        frame["exposure_at_default"] = frame.apply(
            lambda row: row["balance"] if row["status"] == "default" else 0.0, axis=1
        )
        frame["currency"] = frame.get(
            "currency",
            pd.Series(self.config.currency, index=frame.index),
        )

        return frame

    def portfolio_kpis(self) -> dict:
        df = self.data
        exposure = df["principal"].sum()
        if exposure <= 0:
            raise ValueError("Total exposure cannot be zero")

        weighted_interest_rate = (df["interest_rate"] * df["principal"]).sum() / exposure
        arrears_exposure = df.loc[df["arrears_flag"], "principal"].sum()
        default_exposure = df.loc[df["status"] == "default", "principal"].sum()
        prepaid_exposure = df.loc[df["status"] == "prepaid", "principal"].sum()

        lgd = self._calculate_lgd(df)
        repayment_velocity = self._repayment_velocity(df)

        return {
            "currency": df["currency"].iloc[0],
            "exposure": exposure,
            "weighted_interest_rate": weighted_interest_rate,
            "npl_ratio": arrears_exposure / exposure,
            "default_rate": default_exposure / exposure,
            "lgd": lgd,
            "prepayment_rate": prepaid_exposure / exposure,
            "repayment_velocity": repayment_velocity,
        }

    def _calculate_lgd(self, df: pd.DataFrame) -> float:
        default_exposure = df.loc[df["status"] == "default", "principal"].sum()
        if default_exposure == 0:
            return 0.0
        write_offs = df.loc[df["status"] == "default", "write_off_amount"].sum()
        return write_offs / default_exposure

    def _repayment_velocity(self, df: pd.DataFrame) -> float:
        exposure = df["principal"].sum()
        if exposure == 0:
            return 0.0
        payments = df["payments_made"].sum()
        return payments / exposure

    def _portfolio_kpis_for_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute portfolio KPIs for an already-prepared DataFrame without
        re-running data normalization or schema checks.
        This reuses the existing `portfolio_kpis` implementation by
        temporarily swapping `self.data`.
        """
        original_data = self.data
        try:
            self.data = df
            return self.portfolio_kpis()
        finally:
            self.data = original_data

    def segment_kpis(self, segment: str) -> pd.DataFrame:
        if segment not in self.data.columns:
            raise ValueError(f"Segment column '{segment}' not found")

        rows = []
        for value, group in self.data.groupby(segment):
            metrics = self._portfolio_kpis_for_frame(group)
            metrics[segment] = value
            rows.append(metrics)
        return pd.DataFrame(rows)

    def vintage_default_table(self) -> pd.DataFrame:
        df = self.data
        grouped = df.groupby("origination_quarter")
        rows = []
        for quarter, group in grouped:
            principal = group["principal"].sum()
            defaulted = group.loc[group["status"] == "default", "principal"].sum()
            rows.append(
                {
                    "origination_quarter": quarter,
                    "principal": principal,
                    "default_rate": defaulted / principal if principal else 0.0,
                    "defaults_principal": defaulted,
                }
            )
        result = pd.DataFrame(rows)
        return result.sort_values("origination_quarter").reset_index(drop=True)

    def cashflow_curve(self, freq: str = "M") -> pd.DataFrame:
        """Simulate expected cashflows by spreading payments evenly across term."""

        records = []
        for _, row in self.data.iterrows():
            monthly_payment = row["payments_made"] / max(row["term_months"], 1)
            periods = pd.date_range(start=row["origination_date"], periods=row["term_months"], freq="M")
            for period in periods:
                records.append({"period": period, "cashflow": monthly_payment})

        curve = pd.DataFrame(records)
        if curve.empty:
            return pd.DataFrame(columns=["period", "cashflow", "cumulative_cashflow"])

        agg = (
            curve.set_index("period")
            .groupby(pd.Grouper(freq=freq))
            .sum(numeric_only=True)
            .rename_axis("period")
            .reset_index()
        )
        agg["cumulative_cashflow"] = agg["cashflow"].cumsum()
        return agg

    def scorecard(self) -> pd.DataFrame:
        kpis = self.portfolio_kpis()
        return pd.DataFrame([kpis])


# Backwards-compatible exports for legacy callers
@dataclass
class LoanPosition:
    principal: float
    annual_interest_rate: float
    term_months: int
    default_probability: float = 0.0

    def __post_init__(self) -> None:
        if self.principal <= 0:
            raise ValueError("principal must be positive")
        if self.annual_interest_rate <= 0:
            raise ValueError("annual_interest_rate must be positive")
        if self.term_months <= 0:
            raise ValueError("term_months must be positive")
        if not (0.0 <= self.default_probability <= 1.0):
            raise ValueError("default_probability must be between 0 and 1")


@dataclass
class PortfolioKPIs:
    exposure: float
    weighted_rate: float
    weighted_term_months: float
    weighted_default_probability: float
    expected_monthly_interest: float
    expected_monthly_payment: float
    expected_loss: float
    expected_loss_rate: float
    interest_yield_rate: float
    risk_adjusted_return: float


def calculate_monthly_payment(loan: LoanPosition) -> float:
    monthly_rate = loan.annual_interest_rate / 12
    return (monthly_rate * loan.principal) / (1 - math.pow(1 + monthly_rate, -loan.term_months))


def expected_loss(loan: LoanPosition, loss_given_default: float) -> float:
    if not (0.0 <= loss_given_default <= 1.0):
        raise ValueError("loss_given_default must be between 0 and 1")
    return loan.principal * loan.default_probability * loss_given_default


def portfolio_interest_and_risk(loans: Iterable[LoanPosition], loss_given_default: float) -> tuple[float, float]:
    monthly_interest = sum(loan.principal * (loan.annual_interest_rate / 12) for loan in loans)
    portfolio_loss = sum(expected_loss(loan, loss_given_default) for loan in loans)
    return monthly_interest, portfolio_loss


def calculate_portfolio_kpis(loans: List[LoanPosition], loss_given_default: float) -> PortfolioKPIs:
    exposure = sum(loan.principal for loan in loans)
    if exposure == 0:
        raise ValueError("Total exposure cannot be zero")

    weighted_rate = sum(loan.annual_interest_rate * loan.principal for loan in loans) / exposure
    weighted_term = sum(loan.term_months * loan.principal for loan in loans) / exposure
    weighted_default_probability = (
        sum(loan.default_probability * loan.principal for loan in loans) / exposure
    )

    expected_monthly_interest, expected_loss_value = portfolio_interest_and_risk(loans, loss_given_default)
    expected_monthly_payment = sum(calculate_monthly_payment(loan) for loan in loans)
    expected_loss_rate = expected_loss_value / exposure
    interest_yield_rate = expected_monthly_interest / exposure
    risk_adjusted_return = (expected_monthly_interest - expected_loss_value) / exposure

    return PortfolioKPIs(
        exposure=exposure,
        weighted_rate=weighted_rate,
        weighted_term_months=weighted_term,
        weighted_default_probability=weighted_default_probability,
        expected_monthly_interest=expected_monthly_interest,
        expected_monthly_payment=expected_monthly_payment,
        expected_loss=expected_loss_value,
        expected_loss_rate=expected_loss_rate,
        interest_yield_rate=interest_yield_rate,
        risk_adjusted_return=risk_adjusted_return,
    )
