"""DPD (Days Past Due) calculator for loan tape snapshot builds.

Used by the zero-cost ETL path (backend.src.zero_cost) to build monthly
PAR/DPD snapshots from loan tape tables.
"""
from __future__ import annotations

from typing import List, Union

import pandas as pd


_DEFAULT_PAR_THRESHOLDS: List[int] = [1, 30, 60, 90, 180]


class DPDCalculator:
    """Calculate Days Past Due and PAR flags for a loan tape snapshot.

    Parameters
    ----------
    par_thresholds:
        DPD thresholds at which to create boolean PAR flag columns.
        Defaults to [1, 30, 60, 90, 180].
    """

    def __init__(self, par_thresholds: List[int] | None = None) -> None:
        self.par_thresholds: List[int] = par_thresholds if par_thresholds is not None else _DEFAULT_PAR_THRESHOLDS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_snapshots(
        self,
        dim_loan: pd.DataFrame,
        fact_schedule: pd.DataFrame,
        fact_real_payment: pd.DataFrame,
        month_ends: List[Union[str, pd.Timestamp]],
    ) -> pd.DataFrame:
        """Build a DPD/PAR snapshot for each loan at each month-end date.

        Parameters
        ----------
        dim_loan:
            Loan dimension table containing at minimum ``loan_id``.
        fact_schedule:
            Scheduled payment table with ``loan_id``, ``scheduled_date``,
            and ``scheduled_principal``.
        fact_real_payment:
            Actual payment table with ``loan_id``, ``payment_date``, and
            ``paid_principal``.
        month_ends:
            List of snapshot dates.  Each date is normalised to that day's
            end (23:59:59) so that same-day payments are counted.

        Returns
        -------
        pd.DataFrame
            One row per (loan_id × month_end) with columns:
            ``loan_id``, ``snapshot_month``, ``dpd``,
            ``par_<threshold>`` for each threshold, and ``mora_bucket``.
        """
        parsed_ends = [pd.Timestamp(me) for me in month_ends]

        # Normalise date columns once
        sched = fact_schedule.copy()
        sched["scheduled_date"] = pd.to_datetime(sched["scheduled_date"], errors="coerce", format="mixed")
        sched["scheduled_principal"] = pd.to_numeric(sched["scheduled_principal"], errors="coerce").fillna(0.0)

        pays = fact_real_payment.copy()
        pays["payment_date"] = pd.to_datetime(pays["payment_date"], errors="coerce", format="mixed")
        pays["paid_principal"] = pd.to_numeric(pays["paid_principal"], errors="coerce").fillna(0.0)

        loan_ids = dim_loan["loan_id"].tolist()
        records = []
        for month_end in parsed_ends:
            for loan_id in loan_ids:
                dpd = self._calc_dpd(loan_id, month_end, sched, pays)
                row: dict = {
                    "loan_id": loan_id,
                    "snapshot_month": month_end,
                    "dpd": dpd,
                }
                for threshold in self.par_thresholds:
                    row[f"par_{threshold}"] = dpd >= threshold
                row["mora_bucket"] = self._mora_bucket(dpd)
                records.append(row)

        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _calc_dpd(
        self,
        loan_id: str,
        month_end: pd.Timestamp,
        sched: pd.DataFrame,
        pays: pd.DataFrame,
    ) -> int:
        """Return DPD for *loan_id* at *month_end*.

        Uses a greedy oldest-first principal matching algorithm:
        1. Sum paid_principal up to month_end.
        2. Walk scheduled instalments in ascending date order.
        3. Deduct each instalment from the running credit balance.
        4. The first instalment that cannot be fully covered is the
           overdue anchor; DPD = (month_end - anchor_date).days.
        """
        loan_sched = (
            sched[
                (sched["loan_id"] == loan_id)
                & (sched["scheduled_date"] <= month_end)
            ]
            .sort_values("scheduled_date")
        )
        if loan_sched.empty:
            return 0

        loan_pays = pays[
            (pays["loan_id"] == loan_id)
            & (pays["payment_date"] <= month_end)
        ]
        paid_credit = float(loan_pays["paid_principal"].sum())

        for _, row in loan_sched.iterrows():
            inst_principal = float(row["scheduled_principal"])
            if paid_credit >= inst_principal:
                paid_credit -= inst_principal
            else:
                overdue_date: pd.Timestamp = row["scheduled_date"]
                return max(0, (month_end - overdue_date).days)

        return 0

    @staticmethod
    def _mora_bucket(dpd: int) -> str:
        if dpd <= 0:
            return "current"
        if dpd <= 30:
            return "1-30"
        if dpd <= 60:
            return "31-60"
        if dpd <= 90:
            return "61-90"
        if dpd <= 180:
            return "91-180"
        return "180+"


def dpd_to_bucket(dpd: int | float | None) -> str:
    """Return canonical mora bucket for a DPD value."""
    if dpd is None or pd.isna(dpd):
        return "unknown"
    try:
        return DPDCalculator._mora_bucket(int(dpd))
    except Exception:
        return "unknown"
