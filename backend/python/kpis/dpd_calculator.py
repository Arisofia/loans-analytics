"""
DPD (Days Past Due) calculator.

Computes "real" DPD by comparing cumulative scheduled payments to cumulative
actual payments for each loan at each reference date.

The algorithm
-------------
For each (loan_id, reference_date):
  1. Identify all scheduled installments due on or before *reference_date*.
  2. Sum the cumulative scheduled principal due.
  3. Sum the cumulative principal actually paid on or before *reference_date*.
  4. If paid_cum < scheduled_cum → there is a shortfall.
  5. Find the earliest installment whose cumulative scheduled amount exceeds
     the cumulative paid amount → that installment's due date is the "first
     unpaid date".
  6. DPD = (reference_date - first_unpaid_date).days  (0 if fully paid).

Outstanding principal
---------------------
outstanding(ref_date) = original_principal − cumulative_principal_paid(ref_date)

Usage
-----
    calc = DPDCalculator()
    snap_df = calc.build_snapshots(dim_loan, fact_schedule, fact_real_payment,
                                   month_ends=["2025-12-31", "2026-01-31"])
"""

from __future__ import annotations

from typing import Iterable, Optional, Union

import pandas as pd

from backend.python.logging_config import get_logger

logger = get_logger(__name__)

_DateLike = Union[str, pd.Timestamp]

# Floating-point tolerance for payment shortfall detection.
# A loan is considered to have an unpaid installment when
# cum_sched > cum_paid + _PAYMENT_TOLERANCE, preventing false positives
# from floating-point rounding in payment amounts.
_PAYMENT_TOLERANCE: float = 1e-6

# DPD → mora bucket mapping
DPD_BUCKETS: list[tuple[int, int, str]] = [
    (0, 0, "current"),
    (1, 30, "1-30"),
    (31, 60, "31-60"),
    (61, 90, "61-90"),
    (91, 180, "91-180"),
    (181, 360, "181-360"),
    (361, 9999, "360+"),
]


def dpd_to_bucket(dpd: Optional[int]) -> str:
    if dpd is None or pd.isna(dpd):
        return "unknown"
    dpd = int(dpd)
    for lo, hi, label in DPD_BUCKETS:
        if lo <= dpd <= hi:
            return label
    return "360+"


class DPDCalculator:
    """Calculate DPD and outstanding principal from base data.

    Parameters
    ----------
    par_thresholds:
        DPD thresholds for PAR bucket flags.  Defaults to [1, 30, 60, 90].
    """

    def __init__(self, par_thresholds: list[int] | None = None) -> None:
        self.par_thresholds = par_thresholds or [1, 30, 60, 90]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_snapshots(
        self,
        dim_loan: pd.DataFrame,
        fact_schedule: pd.DataFrame,
        fact_real_payment: pd.DataFrame,
        month_ends: Iterable[_DateLike],
        *,
        loan_id_col: str = "loan_id",
        disb_col: str = "original_principal",
        sched_date_col: str = "scheduled_date",
        sched_principal_col: str = "scheduled_principal",
        pay_date_col: str = "payment_date",
        pay_principal_col: str = "paid_principal",
    ) -> pd.DataFrame:
        """Build a monthly snapshot DataFrame with DPD and outstanding principal.

        Parameters
        ----------
        dim_loan:
            Loan dimension table.
        fact_schedule:
            Scheduled payment table.
        fact_real_payment:
            Actual payment table.
        month_ends:
            Sequence of reference dates (month-end dates).

        Returns
        -------
        pd.DataFrame
            Columns: loan_id, snapshot_month, original_principal,
            outstanding_principal, dpd, mora_bucket, par_1 … par_90.
        """
        ref_dates = [pd.Timestamp(d) for d in month_ends]
        rows = []

        # Pre-process: ensure numeric columns
        fact_schedule = fact_schedule.copy()
        fact_real_payment = fact_real_payment.copy()

        if sched_principal_col in fact_schedule.columns:
            fact_schedule[sched_principal_col] = pd.to_numeric(
                fact_schedule[sched_principal_col], errors="coerce"
            ).fillna(0.0)
        if sched_date_col in fact_schedule.columns:
            fact_schedule[sched_date_col] = pd.to_datetime(
                fact_schedule[sched_date_col], errors="coerce"
            )

        if pay_principal_col in fact_real_payment.columns:
            fact_real_payment[pay_principal_col] = pd.to_numeric(
                fact_real_payment[pay_principal_col], errors="coerce"
            ).fillna(0.0)
        if pay_date_col in fact_real_payment.columns:
            fact_real_payment[pay_date_col] = pd.to_datetime(
                fact_real_payment[pay_date_col], errors="coerce"
            )

        for ref in ref_dates:
            batch = self._snapshot_at(
                dim_loan,
                fact_schedule,
                fact_real_payment,
                ref_date=ref,
                loan_id_col=loan_id_col,
                disb_col=disb_col,
                sched_date_col=sched_date_col,
                sched_principal_col=sched_principal_col,
                pay_date_col=pay_date_col,
                pay_principal_col=pay_principal_col,
            )
            rows.append(batch)

        if not rows:
            return pd.DataFrame()

        result = pd.concat(rows, ignore_index=True)
        result["mora_bucket"] = result["dpd"].apply(dpd_to_bucket)
        for t in self.par_thresholds:
            result[f"par_{t}"] = result["dpd"].fillna(0) >= t

        logger.info(
            "DPDCalculator: built %d snapshots across %d reference dates",
            len(result),
            len(ref_dates),
        )
        return result

    def dpd_at(
        self,
        loan_id: str,
        ref_date: _DateLike,
        fact_schedule: pd.DataFrame,
        fact_real_payment: pd.DataFrame,
        *,
        loan_id_col: str = "loan_id",
        sched_date_col: str = "scheduled_date",
        sched_principal_col: str = "scheduled_principal",
        pay_date_col: str = "payment_date",
        pay_principal_col: str = "paid_principal",
    ) -> int:
        """Compute DPD for a single loan at a reference date.

        Returns
        -------
        int
            Days Past Due (0 if current).
        """
        ref = pd.Timestamp(ref_date)

        # Scheduled: cumulative amounts due up to ref
        sched = fact_schedule[fact_schedule[loan_id_col] == loan_id].copy()
        sched = sched[sched[sched_date_col] <= ref].sort_values(sched_date_col)

        if sched.empty:
            return 0  # No installments due yet

        sched["cum_sched"] = sched[sched_principal_col].cumsum()

        # Paid: cumulative principal paid up to ref
        pays = fact_real_payment[fact_real_payment[loan_id_col] == loan_id]
        pays = pays[pays[pay_date_col] <= ref]
        cum_paid = float(pays[pay_principal_col].sum())

        # Find the earliest unpaid installment
        unpaid = sched[sched["cum_sched"] > cum_paid + _PAYMENT_TOLERANCE]
        if unpaid.empty:
            return 0  # Fully paid up

        first_unpaid_date = unpaid[sched_date_col].iloc[0]
        dpd = int((ref - first_unpaid_date).days)
        return max(dpd, 0)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _snapshot_at(
        self,
        dim_loan: pd.DataFrame,
        fact_schedule: pd.DataFrame,
        fact_real_payment: pd.DataFrame,
        ref_date: pd.Timestamp,
        *,
        loan_id_col: str,
        disb_col: str,
        sched_date_col: str,
        sched_principal_col: str,
        pay_date_col: str,
        pay_principal_col: str,
    ) -> pd.DataFrame:
        """Return one row per loan for *ref_date*."""
        # Ensure required columns exist before accessing them. In Control-de-Mora
        # months the schedule/payment tables may be empty or lack some columns;
        # in that case we fall back to dpd=0 and use only dim_loan to compute
        # a sensible outstanding principal.
        required_sched_cols = {loan_id_col, sched_date_col, sched_principal_col}
        required_pay_cols = {loan_id_col, pay_date_col, pay_principal_col}
        has_sched_cols = required_sched_cols.issubset(fact_schedule.columns)
        has_pay_cols = required_pay_cols.issubset(fact_real_payment.columns)

        if not has_sched_cols or not has_pay_cols:
            missing_sched = required_sched_cols.difference(fact_schedule.columns)
            missing_pay = required_pay_cols.difference(fact_real_payment.columns)
            logger.warning(
                "Missing required schedule/payment columns for snapshot at %s. "
                "Using fallback with dpd=0. missing_schedule=%s missing_payment=%s",
                ref_date,
                sorted(missing_sched) if missing_sched else [],
                sorted(missing_pay) if missing_pay else [],
            )

            base = dim_loan[[loan_id_col]].copy()
            if disb_col in dim_loan.columns:
                base["original_principal"] = pd.to_numeric(
                    dim_loan[disb_col], errors="coerce"
                ).values

            # With no reliable schedule/payment information, we assume no scheduled
            # or paid principal yet for the purpose of the snapshot.
            base["cum_sched_principal"] = 0.0
            base["cum_paid_principal"] = 0.0

            if "original_principal" in base.columns:
                base["outstanding_principal"] = (
                    base["original_principal"] - base["cum_paid_principal"]
                ).clip(lower=0.0)

            # Without schedule/payment tables, we cannot compute a meaningful DPD,
            # so we default to 0 as required.
            base["dpd"] = 0
            base["snapshot_month"] = ref_date
            return base.reset_index(drop=True)

        # Cumulative scheduled principal per loan up to ref_date
        sched_upto = fact_schedule[fact_schedule[sched_date_col] <= ref_date]
        cum_sched = (
            sched_upto.groupby(loan_id_col)[sched_principal_col].sum().rename("cum_sched_principal")
        )

        # Cumulative paid principal per loan up to ref_date
        paid_upto = fact_real_payment[fact_real_payment[pay_date_col] <= ref_date]
        cum_paid = (
            paid_upto.groupby(loan_id_col)[pay_principal_col].sum().rename("cum_paid_principal")
        )

        # Base: all loans from dim_loan
        base = dim_loan[[loan_id_col]].copy()
        if disb_col in dim_loan.columns:
            base["original_principal"] = pd.to_numeric(dim_loan[disb_col], errors="coerce").values

        base = base.join(cum_sched, on=loan_id_col, how="left")
        base = base.join(cum_paid, on=loan_id_col, how="left")
        base["cum_sched_principal"] = base["cum_sched_principal"].fillna(0.0)
        base["cum_paid_principal"] = base["cum_paid_principal"].fillna(0.0)

        # Outstanding principal
        if "original_principal" in base.columns:
            base["outstanding_principal"] = (
                base["original_principal"] - base["cum_paid_principal"]
            ).clip(lower=0.0)

        # DPD per loan — vectorized to avoid O(N×M) per-loan filter loop.
        # Reuse the already-filtered schedule (sched_upto) to avoid a duplicate
        # full-table boolean filter and copy within this snapshot computation.
        sched_sorted = sched_upto.sort_values([loan_id_col, sched_date_col]).copy()
        if not sched_sorted.empty:
            sched_sorted["_cum_sched"] = sched_sorted.groupby(loan_id_col)[
                sched_principal_col
            ].cumsum()

            # Reuse already-computed per-loan cumulative principal paid instead of
            # re-filtering and re-grouping fact_real_payment for each snapshot.
            total_paid = base.set_index(loan_id_col)["cum_paid_principal"].rename("_total_paid")
            sched_sorted = sched_sorted.join(total_paid, on=loan_id_col, how="left")
            sched_sorted["_total_paid"] = sched_sorted["_total_paid"].fillna(0.0)

            unpaid_mask = (
                sched_sorted["_cum_sched"] > sched_sorted["_total_paid"] + _PAYMENT_TOLERANCE
            )
            first_unpaid_date = (
                sched_sorted[unpaid_mask].groupby(loan_id_col)[sched_date_col].first()
            )
            dpd_days = (ref_date - first_unpaid_date).dt.days.clip(lower=0).astype(int)
            base["dpd"] = base[loan_id_col].map(dpd_days).fillna(0).astype(int)
        else:
            base["dpd"] = 0
        base["snapshot_month"] = ref_date

        return base.reset_index(drop=True)
