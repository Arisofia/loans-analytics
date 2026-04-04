from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


from decimal import Decimal, ROUND_HALF_UP

def compute_avg_ticket(sales_mart: pd.DataFrame) -> Decimal:
    if sales_mart.empty or "approved_ticket" not in sales_mart.columns:
        return Decimal("0.0")
    val = sales_mart["approved_ticket"].dropna().mean()
    if pd.isna(val):
        return Decimal("0.0")
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_win_rate(sales_mart: pd.DataFrame) -> Decimal:
    if sales_mart.empty:
        return Decimal("0.0")
    total = len(sales_mart)
    if total == 0:
        return Decimal("0.0")
    wins = int(sales_mart["funded_flag"].fillna(False).sum())
    return (Decimal(wins) / Decimal(total)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def compute_contribution_margin(finance_mart: pd.DataFrame) -> Decimal:
    if finance_mart.empty:
        return Decimal("0.0")
    val = finance_mart["gross_margin"].sum()
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_arpu_by_segment(
    portfolio: pd.DataFrame,
    revenue_col: str = "funded_amount",
    segment_col: str = "segment",
    customer_col: str = "customer_id",
    period_col: str = "origination_month",
) -> List[Dict[str, Any]]:
    """Average Revenue Per User (ARPU) broken down by customer segment.

    ARPU is computed as:
        ARPU(segment, month) = total_revenue(segment, month) / unique_customers(segment, month)

    Segments follow the platform convention: Nimal / Gob / OC / Top.

    Parameters
    ----------
    portfolio:
        Portfolio mart DataFrame — output of ``build_portfolio_mart()``.
        Must contain ``revenue_col``, ``segment_col``, ``customer_col``,
        and ``period_col``.
    revenue_col:
        Column used as the revenue proxy per loan.  Defaults to
        ``funded_amount`` (disbursed principal).  Pass ``'interest_income'``
        when a revenue/interest mart is joined upstream.
    segment_col:
        Column that holds the business segment label.
    customer_col:
        Column for unique customer identifier.
    period_col:
        Month-grain period column (string or Period).

    Returns
    -------
    List of dicts, one per (segment, month) combination:
        ``segment``, ``month``, ``total_revenue``, ``unique_customers``,
        ``arpu``.
    Sorted by segment then month.
    """
    if portfolio.empty:
        return []

    required = [revenue_col, segment_col, customer_col, period_col]
    missing = [c for c in required if c not in portfolio.columns]
    if missing:
        return []

    df = portfolio[[revenue_col, segment_col, customer_col, period_col]].copy()
    df[revenue_col] = pd.to_numeric(df[revenue_col], errors="coerce").fillna(0)
    df[segment_col] = df[segment_col].fillna("Unassigned").astype(str)
    df[period_col] = df[period_col].astype(str)

    grouped = (
        df.groupby([segment_col, period_col])
        .agg(
            total_revenue=(revenue_col, "sum"),
            unique_customers=(customer_col, "nunique"),
        )
        .reset_index()
        .rename(columns={segment_col: "segment", period_col: "month"})
    )

    grouped["arpu"] = grouped.apply(
        lambda r: round(r["total_revenue"] / r["unique_customers"], 2)
        if r["unique_customers"] > 0
        else 0.0,
        axis=1,
    )

    return grouped.sort_values(["segment", "month"]).to_dict("records")


def compute_customer_lifespan(
    portfolio: pd.DataFrame,
    customer_col: str = "customer_id",
    date_col: str = "origination_date",
    segment_col: Optional[str] = "segment",
) -> Dict[str, Any]:
    """Average customer lifespan in months, overall and by segment.

    Lifespan for a customer is defined as:
        days between their FIRST and LAST loan origination date.

    Customers with only one loan have lifespan = 0 days (point-in-time),
    which is correct: they have not yet demonstrated repeat behaviour.

    The result is expressed in months (÷ 30.44) for compatibility with
    the LTV formula:  LTV = ARPU_monthly × lifespan_months.

    Parameters
    ----------
    portfolio:
        Portfolio mart DataFrame.
    customer_col:
        Customer identifier column.
    date_col:
        Loan origination date column.
    segment_col:
        Optional segment column.  When present, per-segment lifespans
        are also returned.

    Returns
    -------
    dict with keys:
        ``avg_lifespan_months`` – overall average across all customers,
        ``median_lifespan_months`` – median (more robust to outliers),
        ``repeat_customer_count`` – customers with > 1 loan,
        ``total_customers`` – distinct customers observed,
        ``by_segment`` – list[dict] with per-segment stats (empty when
            ``segment_col`` is None or missing).
    """
    if portfolio.empty:
        return {
            "avg_lifespan_months": 0.0,
            "median_lifespan_months": 0.0,
            "repeat_customer_count": 0,
            "total_customers": 0,
            "by_segment": [],
        }

    df = portfolio.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
    df = df.dropna(subset=[customer_col, date_col])

    # Per-customer first/last origination
    customer_dates = (
        df.groupby(customer_col)[date_col]
        .agg(first_loan="min", last_loan="max")
        .reset_index()
    )
    customer_dates["lifespan_days"] = (
        customer_dates["last_loan"] - customer_dates["first_loan"]
    ).dt.days.clip(lower=0)

    _DAYS_PER_MONTH = 30.44
    customer_dates["lifespan_months"] = customer_dates["lifespan_days"] / _DAYS_PER_MONTH

    total = int(len(customer_dates))
    repeat = int((customer_dates["lifespan_days"] > 0).sum())
    avg_months = round(float(customer_dates["lifespan_months"].mean()), 2)
    median_months = round(float(customer_dates["lifespan_months"].median()), 2)

    by_segment: List[Dict[str, Any]] = []
    if segment_col and segment_col in df.columns:
        # Attach segment to customer_dates via first-loan segment label
        first_segment = (
            df.sort_values(date_col)
            .groupby(customer_col)[segment_col]
            .first()
            .reset_index()
            .rename(columns={segment_col: "segment"})
        )
        augmented = customer_dates.merge(first_segment, on=customer_col, how="left")
        augmented["segment"] = augmented["segment"].fillna("Unassigned")

        seg_stats = (
            augmented.groupby("segment")["lifespan_months"]
            .agg(
                avg_lifespan_months="mean",
                median_lifespan_months="median",
                customer_count="count",
            )
            .reset_index()
        )
        seg_stats["avg_lifespan_months"] = seg_stats["avg_lifespan_months"].round(2)
        seg_stats["median_lifespan_months"] = seg_stats["median_lifespan_months"].round(2)
        by_segment = seg_stats.to_dict("records")

    return {
        "avg_lifespan_months": avg_months,
        "median_lifespan_months": median_months,
        "repeat_customer_count": repeat,
        "total_customers": total,
        "by_segment": by_segment,
    }


def classify_customer_type(
    loan_history: pd.DataFrame,
    snapshot_date: Optional[Any] = None,
    customer_col: str = "customer_id",
    date_col: str = "origination_date",
    inactivity_gap_days: int = 90,
) -> pd.DataFrame:
    """Classify each customer as Nuevo, Recurrente, or Recuperado.

    Applies the legacy customer-type taxonomy used by the commercial
    team:

    * **Nuevo** — First-time borrower: no prior loan exists before the current
      one (only one loan in the system, or all their loans start at/after the
      ``snapshot_date``).
    * **Recurrente** — Repeat borrower who has been continuously active.
      Defined as a customer whose last loan *before* the snapshot was ≤
      ``inactivity_gap_days`` ago (default 90 days).
    * **Recuperado** — Lapsed borrower who has returned.  They had at least
      one prior loan, but their last activity before the snapshot was more than
      ``inactivity_gap_days`` ago, meaning they were classified as churned and
      have now come back.

    Parameters
    ----------
    loan_history:
        All historical loans in the system.  Must contain ``customer_col``
        and ``date_col`` (loan origination date).  Each row is one loan.
    snapshot_date:
        The "as-of" date for the classification.  Defaults to the maximum
        date in ``loan_history``.
    customer_col:
        Column with the customer identifier.
    date_col:
        Column with the loan origination date.
    inactivity_gap_days:
        Number of days of inactivity that separates *Recurrente* from
        *Recuperado*.  Defaults to 90.

    Returns
    -------
    DataFrame with columns ``customer_id``, ``first_loan_date``,
    ``last_loan_date``, ``loan_count``, ``customer_type``.
    One row per unique customer.
    """
    if loan_history.empty:
        return pd.DataFrame(
            columns=[customer_col, "first_loan_date", "last_loan_date", "loan_count", "customer_type"]
        )

    required = [customer_col, date_col]
    missing = [c for c in required if c not in loan_history.columns]
    if missing:
        return pd.DataFrame(
            columns=[customer_col, "first_loan_date", "last_loan_date", "loan_count", "customer_type"]
        )

    df = loan_history[[customer_col, date_col]].copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
    df = df.dropna(subset=[date_col])

    # Aggregate per customer
    agg = (
        df.groupby(customer_col)[date_col]
        .agg(first_loan_date="min", last_loan_date="max", loan_count="count")
        .reset_index()
    )

    # Classify
    def _classify(row: "pd.Series") -> str:
        if row["loan_count"] == 1:
            # Only one loan → definitely Nuevo
            return "Nuevo"
        # Find second-to-last loan (most recent *before* last_loan_date)
        prior = df.loc[
            (df[customer_col] == row[customer_col]) & (df[date_col] < row["last_loan_date"]),
            date_col,
        ]
        if prior.empty:
            return "Nuevo"
        last_prior = prior.max()
        gap = (row["last_loan_date"] - last_prior).days
        if gap <= inactivity_gap_days:
            return "Recurrente"
        return "Recuperado"

    agg["customer_type"] = agg.apply(_classify, axis=1)

    return agg.rename(columns={customer_col: customer_col})[
        [customer_col, "first_loan_date", "last_loan_date", "loan_count", "customer_type"]
    ]


def calculate_weighted_statistics(
    df: pd.DataFrame,
    metrics: List[str],
    weight_col: str = "outstanding_balance",
) -> Dict[str, float]:
    """Calculate weighted statistics (APR, EIR, Term) by OLB.

    Legacy method — Calcular promedios ponderados para métricas específicas.

    Args:
        df: DataFrame con métricas y columna de peso.
        metrics: Lista de métricas para calcular promedios ponderados.
        weight_col: Columna para usar como peso (default: outstanding_balance).

    Returns:
        Diccionario con promedios ponderados.
    """
    if df.empty:
        return {m: 0.0 for m in metrics}

    weights = pd.to_numeric(df.get(weight_col, pd.Series(dtype=float)), errors="coerce").fillna(0)
    total_weight = float(weights.sum())

    result: Dict[str, float] = {}
    for metric in metrics:
        if metric not in df.columns:
            result[metric] = 0.0
            continue
        values = pd.to_numeric(df[metric], errors="coerce").fillna(0)
        if total_weight <= 0:
            result[metric] = round(float(values.mean()), 6) if len(values) > 0 else 0.0
        else:
            result[metric] = round(float((values * weights).sum() / total_weight), 6)

    return result


def calculate_line_utilization(
    loan_df: pd.DataFrame,
    credit_line_field: str = "line_amount",
    loan_amount_field: str = "outstanding_balance",
) -> pd.DataFrame:
    """Calculate line utilization.

    Args:
        loan_df: DataFrame with loan data.
        credit_line_field: Name of credit line column.
        loan_amount_field: Name of loan amount column.

    Returns:
        DataFrame with line_utilization added.
    """
    df = loan_df.copy()

    if credit_line_field not in df.columns or loan_amount_field not in df.columns:
        logger.warning(
            "calculate_line_utilization: columns '%s' or '%s' not found — line_utilization set to 0",
            credit_line_field,
            loan_amount_field,
        )
        df["line_utilization"] = 0.0
        return df

    credit_line = pd.to_numeric(df[credit_line_field], errors="coerce").fillna(0)
    loan_amount = pd.to_numeric(df[loan_amount_field], errors="coerce").fillna(0)

    df["line_utilization"] = (
        (loan_amount / credit_line.replace(0, float("nan")))
        .clip(upper=1.0)
        .fillna(0.0)
        .round(4)
    )

    return df

