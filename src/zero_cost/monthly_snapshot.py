"""
Monthly snapshot builder for the star-schema fact table.

Produces one row per (loan, month) pair capturing:
  - outstanding principal
  - overdue amount
  - days-past-due (DPD)
  - mora bucket classification
  - computed KPIs: portfolio-at-risk (PAR), net yield proxy

Compatible with both the unified pipeline output and the
Control-de-Mora CSV adapter output.

Usage
-----
    builder = MonthlySnapshotBuilder()
    snap_df = builder.build(loans_df, as_of_month="2026-01-31", payments_df=payments_df)
    builder.to_star_schema(snap_df, storage)
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

import pandas as pd

from .storage import ZeroCostStorage

logger = logging.getLogger(__name__)

# DPD → mora bucket mapping (industry standard for microfinance)
_DPD_BUCKETS: list[tuple[int, int, str]] = [
    (0, 0, "current"),
    (1, 30, "1-30"),
    (31, 60, "31-60"),
    (61, 90, "61-90"),
    (91, 180, "91-180"),
    (181, 360, "181-360"),
    (361, 9999, "360+"),
]


def _dpd_to_bucket(dpd: float | int | None) -> str:
    if dpd is None or pd.isna(dpd):
        return "unknown"
    dpd = int(dpd)
    for lo, hi, label in _DPD_BUCKETS:
        if lo <= dpd <= hi:
            return label
    return "360+"


class MonthlySnapshotBuilder:
    """Build ``fact_monthly_snapshot`` rows from pipeline / mora data.

    Parameters
    ----------
    par_thresholds:
        DPD thresholds for PAR buckets.  Defaults to ``[1, 30, 60, 90]``.
    currency_col:
        Name of the currency column in the input DataFrame.
    """

    def __init__(
        self,
        par_thresholds: list[int] | None = None,
        currency_col: str = "currency",
    ) -> None:
        self.par_thresholds = par_thresholds or [1, 30, 60, 90]
        self.currency_col = currency_col

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(
        self,
        loans_df: pd.DataFrame,
        as_of_month: str | date | None = None,
        payments_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Build a monthly snapshot DataFrame.

        Parameters
        ----------
        loans_df:
            Loan-level DataFrame with at minimum:
            ``lend_id`` (or ``numero_desembolso``),
            ``principal_outstanding``,
            ``dpd``,
            ``disbursement_date``.
        as_of_month:
            Reference month-end date (``YYYY-MM-DD`` or ``YYYY-MM``).  When
            ``None``, infers from ``snapshot_month`` column in *loans_df*.
        payments_df:
            Optional payments DataFrame for income/yield calculations.

        Returns
        -------
        pd.DataFrame
            One row per loan with snapshot KPIs.
        """
        df = loans_df.copy()

        # Ensure snapshot_month
        df = self._set_snapshot_month(df, as_of_month)

        # Ensure loan key
        if "lend_id" not in df.columns and "numero_desembolso" in df.columns:
            df["lend_id"] = df["numero_desembolso"]

        # Mora bucket
        if "dpd" in df.columns:
            df["mora_bucket"] = df["dpd"].apply(_dpd_to_bucket)
        elif "mora_bucket" not in df.columns:
            df["mora_bucket"] = "unknown"

        # Overdue flag
        if "dpd" in df.columns:
            df["is_overdue"] = df["dpd"].fillna(0) > 0

        # PAR flags
        for threshold in self.par_thresholds:
            col = f"par_{threshold}"
            if "dpd" in df.columns:
                df[col] = df["dpd"].fillna(0) >= threshold

        # Monthly income (from payments if available)
        if payments_df is not None:
            df = self._join_monthly_income(df, payments_df)

        # Vintage (months-on-book)
        if "disbursement_date" in df.columns:
            snap_dates = pd.to_datetime(df["snapshot_month"])
            disb_dates = pd.to_datetime(df["disbursement_date"])
            df["months_on_book"] = (
                (snap_dates.dt.year - disb_dates.dt.year) * 12
                + (snap_dates.dt.month - disb_dates.dt.month)
            ).clip(lower=0)

        logger.info(
            "MonthlySnapshotBuilder: built %d snapshot rows for %s",
            len(df),
            df["snapshot_month"].iloc[0] if len(df) > 0 else "n/a",
        )
        return df

    # ------------------------------------------------------------------
    # Star-schema output
    # ------------------------------------------------------------------

    def to_star_schema(
        self,
        snapshot_df: pd.DataFrame,
        storage: ZeroCostStorage,
    ) -> dict[str, pd.DataFrame]:
        """Decompose *snapshot_df* into star-schema dimension and fact tables
        and persist them via *storage*.

        Returns
        -------
        dict
            Keys: ``dim_loan``, ``dim_client``, ``dim_time``,
            ``fact_monthly_snapshot``.
        """
        tables: dict[str, pd.DataFrame] = {}

        # dim_loan
        loan_cols = [
            c
            for c in [
                "lend_id",
                "numero_desembolso",
                "product_type",
                "branch_code",
                "currency",
                "disbursement_date",
            ]
            if c in snapshot_df.columns
        ]
        if loan_cols:
            dim_loan = (
                snapshot_df[loan_cols]
                .drop_duplicates(
                    subset=["lend_id"] if "lend_id" in loan_cols else loan_cols[:1]
                )
                .reset_index(drop=True)
            )
            # Surrogate key for loans
            dim_loan["loan_sk"] = range(1, len(dim_loan) + 1)
            tables["dim_loan"] = dim_loan

        # dim_client
        client_cols = [
            c for c in ["lend_id", "client_id", "client_name"] if c in snapshot_df.columns
        ]
        if len(client_cols) > 1:
            dim_client = (
                snapshot_df[client_cols]
                .drop_duplicates()
                .reset_index(drop=True)
            )
            # Surrogate key for clients
            dim_client["client_sk"] = range(1, len(dim_client) + 1)
            tables["dim_client"] = dim_client

        # dim_time
        if "snapshot_month" in snapshot_df.columns:
            time_df = (
                snapshot_df[["snapshot_month"]]
                .drop_duplicates()
                .copy()
            )
            time_df["snapshot_month"] = pd.to_datetime(time_df["snapshot_month"])
            time_df["year"] = time_df["snapshot_month"].dt.year
            time_df["month"] = time_df["snapshot_month"].dt.month
            time_df["quarter"] = time_df["snapshot_month"].dt.quarter
            time_df["year_month"] = time_df["snapshot_month"].dt.strftime("%Y-%m")
            time_df = time_df.reset_index(drop=True)
            # Surrogate key for time dimension
            time_df["time_id"] = range(1, len(time_df) + 1)
            tables["dim_time"] = time_df

        # fact_monthly_snapshot (all KPI columns, with surrogate keys)
        fact_df = snapshot_df.copy()

        # Attach loan surrogate key
        if "dim_loan" in tables and "lend_id" in fact_df.columns:
            fact_df = fact_df.merge(
                tables["dim_loan"][["lend_id", "loan_sk"]],
                on="lend_id",
                how="left",
            )

        # Attach client surrogate key (if available)
        if "dim_client" in tables:
            # Use the intersection of columns used to build dim_client as join keys
            dim_client = tables["dim_client"]
            join_keys = [c for c in ["lend_id", "client_id"] if c in fact_df.columns and c in dim_client.columns]
            if join_keys:
                fact_df = fact_df.merge(
                    dim_client[join_keys + ["client_sk"]],
                    on=join_keys,
                    how="left",
                )

        # Attach time surrogate key
        if "dim_time" in tables and "snapshot_month" in fact_df.columns:
            fact_df = fact_df.merge(
                tables["dim_time"][["snapshot_month", "time_id"]],
                on="snapshot_month",
                how="left",
            )

        tables["fact_monthly_snapshot"] = fact_df.reset_index(drop=True)

        for name, table_df in tables.items():
            storage.write_parquet(table_df, name)
            logger.info("Wrote %s (%d rows)", name, len(table_df))

        return tables

    # ------------------------------------------------------------------
    # Portfolio KPIs (aggregate view)
    # ------------------------------------------------------------------

    def compute_portfolio_kpis(self, snapshot_df: pd.DataFrame) -> dict:
        """Return a dictionary of portfolio-level KPIs for *snapshot_df*.

        KPIs
        ----
        total_loans, active_loans, total_outstanding, total_overdue,
        par_1, par_30, par_60, par_90 (as % of outstanding),
        avg_dpd, weighted_avg_dpd
        """
        kpis: dict = {}
        kpis["total_loans"] = len(snapshot_df)

        # Use Decimal for monetary aggregates to avoid floating-point drift.
        if "principal_outstanding" in snapshot_df.columns:
            total_os_raw = snapshot_df["principal_outstanding"].sum()
            if pd.notna(total_os_raw):
                # Convert via str() to preserve value while avoiding binary float issues.
                total_os = Decimal(str(total_os_raw))
                kpis["total_outstanding"] = float(total_os)
            else:
                total_os = Decimal("0")
                kpis["total_outstanding"] = 0.0
        else:
            total_os = Decimal("0")
            kpis["total_outstanding"] = 0.0

        if "total_overdue_amount" in snapshot_df.columns:
            total_overdue_raw = snapshot_df["total_overdue_amount"].sum()
            if pd.notna(total_overdue_raw):
                total_overdue = Decimal(str(total_overdue_raw))
                kpis["total_overdue"] = float(total_overdue)
            else:
                kpis["total_overdue"] = 0.0
        else:
            kpis["total_overdue"] = 0.0

        for threshold in self.par_thresholds:
            par_col = f"par_{threshold}"
            if par_col in snapshot_df.columns and total_os > Decimal("0"):
                par_amount_raw = snapshot_df.loc[
                    snapshot_df[par_col], "principal_outstanding"
                ].sum()
                if pd.notna(par_amount_raw):
                    par_amount = Decimal(str(par_amount_raw))
                    par_pct = (par_amount / total_os) * Decimal("100")
                    kpis[f"par_{threshold}_pct"] = float(par_pct)

        if "dpd" in snapshot_df.columns:
            kpis["avg_dpd"] = float(snapshot_df["dpd"].mean())

        if "mora_bucket" in snapshot_df.columns:
            kpis["mora_distribution"] = snapshot_df["mora_bucket"].value_counts().to_dict()

        return kpis

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _set_snapshot_month(
        self, df: pd.DataFrame, as_of_month: str | date | None
    ) -> pd.DataFrame:
        if as_of_month is not None:
            df["snapshot_month"] = pd.to_datetime(str(as_of_month))
        elif "snapshot_month" not in df.columns:
            # Default to the current month-end to keep snapshot semantics consistent
            today = pd.Timestamp("today").normalize()
            current_month_end = today + pd.offsets.MonthEnd(0)
            df["snapshot_month"] = current_month_end
            logger.warning(
                "snapshot_month not provided — defaulting to current month-end %s",
                current_month_end.date(),
            )
        else:
            df["snapshot_month"] = pd.to_datetime(df["snapshot_month"], errors="coerce")
        return df

    def _join_monthly_income(
        self, df: pd.DataFrame, payments_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Aggregate monthly payments and join to *df*."""
        if "lend_id" not in payments_df.columns or "amount" not in payments_df.columns:
            return df
        monthly_income = (
            payments_df.groupby("lend_id")["amount"]
            .sum()
            .rename("monthly_income")
            .reset_index()
        )
        return df.merge(monthly_income, on="lend_id", how="left")
