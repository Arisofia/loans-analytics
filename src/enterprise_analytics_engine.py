"""Portfolio analytics utilities for credit KPIs and risk metrics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

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
        frame["exposure_at_default"] = (frame["status"] == "default").astype(float) * frame["balance"]

        if "currency" not in frame.columns:
            frame["currency"] = pd.Series(self.config.currency, index=frame.index)
        else:
            frame["currency"] = frame["currency"].fillna(self.config.currency)

        return frame

    def _portfolio_kpis_from_df(self, df: pd.DataFrame) -> dict:
        exposure = df["principal"].sum()
        if exposure <= 0:
            raise ValueError("Total exposure cannot be zero")

        weighted_interest_rate = (df["interest_rate"] * df["principal"]).sum() / exposure
        arrears_exposure = df.loc[df["arrears_flag"], "principal"].sum()
        default_exposure = df.loc[df["status"] == "default", "principal"].sum()
        prepaid_exposure = df.loc[df["status"] == "prepaid", "principal"].sum()

        lgd = self._calculate_lgd(df)
        repayment_velocity = self._repayment_velocity(df)

        currencies = df["currency"].dropna().unique()
        currency = currencies[0] if len(currencies) else self.config.currency

        return {
            "currency": currency,
            "exposure": exposure,
            "weighted_interest_rate": weighted_interest_rate,
            "npl_ratio": arrears_exposure / exposure,
            "default_rate": default_exposure / exposure,
            "lgd": lgd,
            "prepayment_rate": prepaid_exposure / exposure,
            "repayment_velocity": repayment_velocity,
        }

    def portfolio_kpis(self) -> dict:
        return self._portfolio_kpis_from_df(self.data)

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

    def segment_kpis(self, segment: str) -> pd.DataFrame:
        """Compute KPIs grouped by a segment column."""

        if segment not in self.data.columns:
            raise ValueError(f"Segment column '{segment}' not found")

        rows: List[dict] = []
        for value, group in self.data.groupby(segment):
            metrics = self._portfolio_kpis_from_df(group)
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
            term_months = max(int(row["term_months"]), 1)
            periods = pd.date_range(start=row["origination_date"], periods=term_months, freq="M")
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
            raise ValueError("Principal must be greater than zero.")
        if self.annual_interest_rate < 0:
            raise ValueError("Annual interest rate cannot be negative.")
        if self.term_months <= 0:
            raise ValueError("Term months must be greater than zero.")
        if not 0 <= self.default_probability <= 1:
            raise ValueError("Default probability must be between 0 and 1.")


def _monthly_interest_rate(loan: LoanPosition) -> float:
    """Return the monthly interest rate as a decimal."""

    return loan.annual_interest_rate / 12


def calculate_monthly_payment(loan: LoanPosition) -> float:
    """Return the amortized monthly payment for a fixed-rate loan."""
    monthly_rate = _monthly_interest_rate(loan)
    if monthly_rate == 0:
        return loan.principal / loan.term_months

    numerator = monthly_rate * loan.principal
    denominator = 1 - (1 + monthly_rate) ** (-loan.term_months)
    return numerator / denominator


def expected_loss(loan: LoanPosition, loss_given_default: float) -> float:
    """Compute expected loss for a single loan position."""
    if not 0 <= loss_given_default <= 1:
        raise ValueError("Loss given default must be between 0 and 1.")

    exposure_at_default = loan.principal
    return exposure_at_default * loan.default_probability * loss_given_default


def portfolio_interest_and_risk(
    loans: Iterable[LoanPosition], loss_given_default: float
) -> Tuple[float, float]:
    """
    Aggregate expected first-month interest and expected loss across a portfolio.

    Returns:
        A tuple with (expected_monthly_interest, expected_loss_value).
    """
    expected_interest = 0.0
    aggregated_loss = 0.0

    for loan in loans:
        expected_interest += loan.principal * _monthly_interest_rate(loan)
        aggregated_loss += expected_loss(loan, loss_given_default)

    return expected_interest, aggregated_loss


@dataclass(frozen=True)
class PortfolioKPIs:
    """Aggregate indicators for portfolio performance and risk."""

    exposure: float
    weighted_rate: float
    weighted_term_months: float
    weighted_default_probability: float
    expected_monthly_payment: float
    expected_monthly_interest: float
    expected_loss: float
    expected_loss_rate: float
    interest_yield_rate: float
    risk_adjusted_return: float


def calculate_portfolio_kpis(
    loans: Iterable[LoanPosition], loss_given_default: float
) -> PortfolioKPIs:
    """
    Compute weighted averages and expected first-month cash flows for a portfolio.

    The calculation returns exposure, weighted rate and term (principal weighted),
    expected total monthly payment, first-month interest, and expected loss.
    """

    exposure = 0.0
    weighted_rate = 0.0
    weighted_term = 0.0
    weighted_default_probability = 0.0
    expected_payment = 0.0
    expected_interest = 0.0
    aggregated_loss = 0.0

    for loan in loans:
        exposure += loan.principal
        weighted_rate += loan.annual_interest_rate * loan.principal
        weighted_term += loan.term_months * loan.principal
        weighted_default_probability += loan.default_probability * loan.principal
        monthly_payment = calculate_monthly_payment(loan)
        expected_payment += monthly_payment
        expected_interest += loan.principal * _monthly_interest_rate(loan)
        aggregated_loss += expected_loss(loan, loss_given_default)

    if exposure == 0:
        return PortfolioKPIs(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    expected_loss_rate = aggregated_loss / exposure
    interest_yield_rate = expected_interest / exposure
    risk_adjusted_return = (expected_interest - aggregated_loss) / exposure
    weighted_default_prob = weighted_default_probability / exposure

    return PortfolioKPIs(
        exposure=exposure,
        weighted_rate=weighted_rate / exposure,
        weighted_term_months=weighted_term / exposure,
        weighted_default_probability=weighted_default_prob,
        expected_monthly_payment=expected_payment,
        expected_monthly_interest=expected_interest,
        expected_loss=aggregated_loss,
        expected_loss_rate=expected_loss_rate,
        interest_yield_rate=interest_yield_rate,
        risk_adjusted_return=risk_adjusted_return,
    )
