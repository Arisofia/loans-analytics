"""Local ETL utilities for Azure-free daily analytics pipeline.

Builds a monthly star schema snapshot from raw Control de Mora and loan-tape CSVs.
Includes:
- real DPD based on schedule vs. paid principal
- contractual APR (EAR from nominal rate)
- realized XIRR per loan
- payment reconciliation with reason_code logging
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
import csv

import pandas as pd

from .dpd_calculator import DPDCalculator
from .loan_tape_loader import LoanTapeLoader
from .xirr import contractual_apr, portfolio_xirr

logger = logging.getLogger(__name__)

NOT_SPECIFIED_VALUES = {"no especificado", "no_especificado", "not specified", ""}


@dataclass
class ETLResult:
    """Container for ETL outputs."""

    dim_loan: pd.DataFrame
    fact_schedule: pd.DataFrame
    fact_real_payment: pd.DataFrame
    fact_monthly_snapshot: pd.DataFrame
    payment_reconciliation: pd.DataFrame
    unmatched_records: pd.DataFrame


def _normalize_not_specified(value: object) -> bool:
    if value is None or pd.isna(value):
        return True
    return str(value).strip().lower() in NOT_SPECIFIED_VALUES


def build_not_specified_log(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Build reason_code logs for fields with not specified values."""
    records: list[dict[str, object]] = []
    for col in df.columns:
        # Consider all logical string-like columns (object, pandas string, pyarrow string, etc.)
        if not (
            pd.api.types.is_object_dtype(df[col])
            or pd.api.types.is_string_dtype(df[col])
        ):
            continue
        mask = df[col].apply(_normalize_not_specified)
        if not mask.any():
            continue
        for idx in df.index[mask]:
            records.append(
                {
                    "table_name": table_name,
                    "record_ref": str(idx),
                    "field_name": col,
                    "reason_code": "no_especificado",
                    "reason_detail": f"Field '{col}' has no especificado/blank value",
                }
            )
    return pd.DataFrame(records)


def reconcile_payments(
    fact_schedule: pd.DataFrame,
    fact_real_payment: pd.DataFrame,
    *,
    tolerance: float = 0.01,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reconcile scheduled vs real payments by loan/date.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        - reconciliation table with status/mismatch amount
        - unmatched rows with non-empty reason_code
    """
    schedule = fact_schedule.copy()
    paid = fact_real_payment.copy()

    schedule["scheduled_date"] = pd.to_datetime(schedule["scheduled_date"], errors="coerce")
    paid["payment_date"] = pd.to_datetime(paid["payment_date"], errors="coerce")

    schedule["scheduled_total"] = pd.to_numeric(schedule["scheduled_total"], errors="coerce").fillna(0.0)
    paid["paid_total"] = pd.to_numeric(paid["paid_total"], errors="coerce").fillna(0.0)

    sched_agg = (
        schedule.groupby(["loan_id", "scheduled_date"], as_index=False, dropna=False)[
            "scheduled_total"
        ].sum()
    )
    paid_agg = paid.groupby(["loan_id", "payment_date"], as_index=False, dropna=False)[
        "paid_total"
    ].sum()

    merged = sched_agg.merge(
        paid_agg,
        how="outer",
        left_on=["loan_id", "scheduled_date"],
        right_on=["loan_id", "payment_date"],
        indicator=True,
    )

    merged["scheduled_total"] = merged["scheduled_total"].fillna(0.0)
    merged["paid_total"] = merged["paid_total"].fillna(0.0)
    merged["amount_diff"] = merged["paid_total"] - merged["scheduled_total"]

    merged["status"] = "reconciled"
    merged.loc[merged["_merge"] == "left_only", "status"] = "missing_payment"
    merged.loc[merged["_merge"] == "right_only", "status"] = "missing_schedule"

    amount_mismatch = (merged["_merge"] == "both") & (merged["amount_diff"].abs() > tolerance)
    merged.loc[amount_mismatch, "status"] = "amount_mismatch"

    status_to_reason = {
        "missing_payment": "scheduled_without_payment",
        "missing_schedule": "payment_without_schedule",
        "amount_mismatch": "amount_mismatch",
    }

    unmatched = merged[merged["status"] != "reconciled"].copy()
    unmatched["reason_code"] = unmatched["status"].map(status_to_reason).fillna("not_specified")
    unmatched["reason_detail"] = (
        "loan_id="
        + unmatched["loan_id"].astype(str)
        + ", amount_diff="
        + unmatched["amount_diff"].round(2).astype(str)
    )

    return merged.drop(columns=["_merge"]), unmatched


class LocalMonthlySnapshotETL:
    """Generate monthly star-schema snapshot from local raw CSV files."""

    def __init__(self, snapshot_month: str) -> None:
        snapshot_ts = pd.Timestamp(snapshot_month)
        self.snapshot_month = snapshot_ts + pd.offsets.MonthEnd(0)
        self.loader = LoanTapeLoader(data_dir="data/raw")
        self.dpd_calculator = DPDCalculator()

    def run(
        self,
        *,
        loan_tape_dir: str | Path,
        control_mora_path: str | Path | None = None,
    ) -> ETLResult:
        tables = self.loader.load_all(data_dir=loan_tape_dir)

        dim_loan = tables["dim_loan"].copy()
        fact_schedule = tables["fact_schedule"].copy()
        fact_real_payment = tables["fact_real_payment"].copy()

        dim_loan["disbursement_date"] = pd.to_datetime(dim_loan["disbursement_date"], errors="coerce")
        dim_loan["original_principal"] = pd.to_numeric(
            dim_loan["original_principal"], errors="coerce"
        ).fillna(0.0)
        if "interest_rate" in dim_loan.columns:
            dim_loan["interest_rate"] = pd.to_numeric(
                dim_loan["interest_rate"], errors="coerce"
            ).fillna(0.0)
        else:
            dim_loan["interest_rate"] = 0.0

        snapshots = self.dpd_calculator.build_snapshots(
            dim_loan,
            fact_schedule,
            fact_real_payment,
            month_ends=[self.snapshot_month],
        )

        dim_loan["contractual_apr"] = dim_loan["interest_rate"].apply(contractual_apr)

        # Only compute XIRR for loans with a valid disbursement_date and positive principal
        valid_xirr_mask = dim_loan["disbursement_date"].notna() & (dim_loan["original_principal"] > 0)
        loan_xirr_series = portfolio_xirr(dim_loan[valid_xirr_mask], fact_real_payment)

        fact_monthly_snapshot = snapshots.merge(
            dim_loan[["loan_id", "contractual_apr"]],
            on="loan_id",
            how="left",
        )
        fact_monthly_snapshot = fact_monthly_snapshot.merge(
            loan_xirr_series.rename("realized_xirr"),
            left_on="loan_id",
            right_index=True,
            how="left",
        )

        reconciliation, unmatched_reconciliation = reconcile_payments(fact_schedule, fact_real_payment)

        not_specified_logs = [
            build_not_specified_log(dim_loan, "dim_loan"),
            build_not_specified_log(fact_schedule, "fact_schedule"),
            build_not_specified_log(fact_real_payment, "fact_real_payment"),
        ]
        unmatched_records = pd.concat(
            [unmatched_reconciliation, *[df for df in not_specified_logs if not df.empty]],
            ignore_index=True,
        )

        if control_mora_path:
            # Auto-detect delimiter to match ControlMoraAdapter behavior and handle Excel-style exports.
            control_mora_path = Path(control_mora_path)
            with control_mora_path.open("r", encoding="utf-8-sig", newline="") as f:
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
                    delimiter = dialect.delimiter
                except csv.Error:
                    # Fallback to comma if sniffing fails.
                    delimiter = ","
                control_mora_df = pd.read_csv(f, dtype=str, sep=delimiter)
            unmatched_records = pd.concat(
                [unmatched_records, build_not_specified_log(control_mora_df, "control_mora")],
                ignore_index=True,
            )

        if "reason_code" in unmatched_records.columns:
            unmatched_records["reason_code"] = unmatched_records["reason_code"].fillna("not_specified")

        logger.info(
            "LocalMonthlySnapshotETL completed snapshot=%s loans=%d unmatched=%d",
            self.snapshot_month.date(),
            len(dim_loan),
            len(unmatched_records),
        )

        return ETLResult(
            dim_loan=dim_loan,
            fact_schedule=fact_schedule,
            fact_real_payment=fact_real_payment,
            fact_monthly_snapshot=fact_monthly_snapshot,
            payment_reconciliation=reconciliation,
            unmatched_records=unmatched_records,
        )
