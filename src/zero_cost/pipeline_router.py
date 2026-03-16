"""
Pipeline Router — routes ingestion between loan_tape and Control de Mora
based on snapshot month.

Business rule:
  - Months ≤ January 2026  → use loan_tape (``LoanTapeLoader``)
  - Months ≥ February 2026 → use Control de Mora (``ControlMoraAdapter``)

The router returns a unified dict of canonical tables:
  ``dim_loan``, ``fact_schedule``, ``fact_real_payment``, optionally
  ``dim_customer``, ``dim_collateral``.

Usage
-----
    router = PipelineRouter()
    tables = router.route(
        snapshot_month="2026-02-28",
        loan_tape_dir="data/raw/",
        control_mora_path="data/raw/control_mora_feb2026.csv",
    )
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from .control_mora_adapter import ControlMoraAdapter
from .loan_tape_loader import LoanTapeLoader

logger = logging.getLogger(__name__)

# Pivot point: months AFTER this date use Control de Mora
_PIVOT_MONTH = pd.Timestamp("2026-02-01")  # February 2026


class PipelineRouter:
    """Route data ingestion based on snapshot month.

    Parameters
    ----------
    pivot_month:
        First month to use Control-de-Mora instead of loan tape.
        Defaults to February 2026 (``2026-02-01``).
    loan_tape_loader:
        Pre-configured :class:`LoanTapeLoader` instance.
    control_mora_adapter:
        Pre-configured :class:`ControlMoraAdapter` instance.
    """

    def __init__(
        self,
        pivot_month: str | pd.Timestamp = _PIVOT_MONTH,
        loan_tape_loader: Optional[LoanTapeLoader] = None,
        control_mora_adapter: Optional[ControlMoraAdapter] = None,
    ) -> None:
        self.pivot_month = pd.Timestamp(pivot_month)
        self._loader = loan_tape_loader or LoanTapeLoader()
        self._adapter = control_mora_adapter or ControlMoraAdapter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(
        self,
        snapshot_month: str | pd.Timestamp,
        *,
        # Loan tape inputs
        loan_tape_dir: str | Path | None = None,
        loan_path: str | Path | None = None,
        schedule_path: str | Path | None = None,
        real_payment_path: str | Path | None = None,
        customer_path: str | Path | None = None,
        collateral_path: str | Path | None = None,
        # Control de Mora input
        control_mora_path: str | Path | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Load data appropriate for *snapshot_month*.

        Parameters
        ----------
        snapshot_month:
            Reference date for the snapshot (e.g. ``"2026-01-31"``).
        loan_tape_dir:
            Directory containing loan-tape CSV files.
        control_mora_path:
            Path to the Control-de-Mora CSV for the given month.

        Returns
        -------
        dict
            Keys: ``dim_loan``, ``fact_schedule``, ``fact_real_payment``,
            and optionally ``dim_customer``, ``dim_collateral``.
            Always includes ``_source`` key (``"loan_tape"`` or
            ``"control_mora"``).
        """
        snap_ts = pd.Timestamp(snapshot_month)
        use_mora = snap_ts >= self.pivot_month

        if use_mora:
            logger.info(
                "PipelineRouter: %s ≥ pivot %s → using Control de Mora",
                snap_ts.date(),
                self.pivot_month.date(),
            )
            return self._load_control_mora(snap_ts, control_mora_path)
        else:
            logger.info(
                "PipelineRouter: %s < pivot %s → using loan tape",
                snap_ts.date(),
                self.pivot_month.date(),
            )
            return self._load_loan_tape(
                loan_tape_dir=loan_tape_dir,
                loan_path=loan_path,
                schedule_path=schedule_path,
                real_payment_path=real_payment_path,
                customer_path=customer_path,
                collateral_path=collateral_path,
            )

    def source_for(self, snapshot_month: str | pd.Timestamp) -> str:
        """Return ``"control_mora"`` or ``"loan_tape"`` for *snapshot_month*."""
        return (
            "control_mora"
            if pd.Timestamp(snapshot_month) >= self.pivot_month
            else "loan_tape"
        )

    # ------------------------------------------------------------------
    # Internal loaders
    # ------------------------------------------------------------------

    def _load_loan_tape(
        self,
        *,
        loan_tape_dir: str | Path | None,
        loan_path: str | Path | None,
        schedule_path: str | Path | None,
        real_payment_path: str | Path | None,
        customer_path: str | Path | None,
        collateral_path: str | Path | None,
    ) -> dict[str, pd.DataFrame]:
        tables = self._loader.load_all(
            data_dir=loan_tape_dir,
            loan_path=loan_path,
            schedule_path=schedule_path,
            real_payment_path=real_payment_path,
            customer_path=customer_path,
            collateral_path=collateral_path,
        )
        tables["_source"] = "loan_tape"
        return tables

    def _empty_fact_schedule(self) -> pd.DataFrame:
        """Return an empty fact_schedule with the canonical schema.

        This ensures downstream components (e.g., DPDCalculator) can rely on
        expected columns like ``scheduled_date`` even when Control de Mora
        does not provide a full schedule.
        """
        return pd.DataFrame(
            {
                # Identifier columns kept generic as object; downstream may
                # cast or join as needed.
                "loan_id": pd.Series(dtype="object"),
                "installment_number": pd.Series(dtype="Int64"),
                # Dates are explicitly typed as datetime64 for consistency.
                "scheduled_date": pd.Series(dtype="datetime64[ns]"),
                # Amounts are left as object to avoid imposing float on
                # financial values; calculators can cast to Decimal.
                "scheduled_principal": pd.Series(dtype="object"),
                "scheduled_interest": pd.Series(dtype="object"),
                "scheduled_fee": pd.Series(dtype="object"),
                "scheduled_total": pd.Series(dtype="object"),
                "scheduled_other": pd.Series(dtype="object"),
            }
        )

    def _empty_fact_real_payment(self) -> pd.DataFrame:
        """Return an empty fact_real_payment with the canonical schema.

        Provides ``payment_date`` and related columns so downstream code can
        operate safely even when no real payments are present.
        """
        return pd.DataFrame(
            {
                "loan_id": pd.Series(dtype="object"),
                "payment_id": pd.Series(dtype="object"),
                "payment_date": pd.Series(dtype="datetime64[ns]"),
                "paid_principal": pd.Series(dtype="object"),
                "paid_interest": pd.Series(dtype="object"),
                "paid_fees": pd.Series(dtype="object"),
            }
        )

    def _load_control_mora(
        self,
        snapshot_month: pd.Timestamp,
        control_mora_path: Optional[str | Path],
    ) -> dict[str, pd.DataFrame]:
        if control_mora_path is None:
            logger.warning(
                "PipelineRouter: control_mora_path not provided for %s — "
                "returning empty tables",
                snapshot_month.date(),
            )
            return {
                "dim_loan": pd.DataFrame(),
                "fact_schedule": self._empty_fact_schedule(),
                "fact_real_payment": self._empty_fact_real_payment(),
                "_source": "control_mora",
            }

        self._adapter.snapshot_month = snapshot_month.strftime("%Y-%m-%d")
        mora_df = self._adapter.load(control_mora_path)

        # Map Control-de-Mora flat structure to the canonical tables
        dim_loan_cols = [
            c for c in [
                "lend_id", "numero_desembolso", "client_id", "client_name",
                "disbursement_date", "currency", "principal_outstanding",
                "product_type", "branch_code", "snapshot_month",
            ]
            if c in mora_df.columns
        ]
        dim_loan = mora_df[dim_loan_cols].copy()
        # Alias lend_id → loan_id for schema consistency
        if "lend_id" in dim_loan.columns and "loan_id" not in dim_loan.columns:
            dim_loan = dim_loan.rename(columns={"lend_id": "loan_id"})
        dim_loan["source"] = "control_mora"

        return {
            "dim_loan": dim_loan,
            # Control de Mora does not currently provide schedule or payment
            # tables, but we return canonical-schema empties to keep
            # downstream components stable.
            "fact_schedule": self._empty_fact_schedule(),
            "fact_real_payment": self._empty_fact_real_payment(),
            "_source": "control_mora",
        }
