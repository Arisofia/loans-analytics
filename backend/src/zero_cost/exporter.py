"""
Exporter — writes pipeline outputs to exports/*.csv and exports/*.parquet.

Produces:
  exports/dim_loan.{csv,parquet}
  exports/fact_schedule.{csv,parquet}
  exports/fact_real_payment.{csv,parquet}
  exports/fact_monthly_snapshot.{csv,parquet}
  exports/unmatched_records.csv
  exports/kpi_summary.{csv,parquet}
  exports/run_manifest.json

Usage
-----
    exporter = Exporter("exports/")
    exporter.export_tables(tables)
    exporter.export_unmatched(unmatched_df)
    exporter.write_manifest(meta)
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class Exporter:
    """Export DataFrames to CSV and Parquet under *output_dir*.

    Parameters
    ----------
    output_dir:
        Root directory for exports.  Created if it does not exist.
    write_csv:
        When ``True`` (default), also write CSV alongside Parquet.
    """

    def __init__(
        self,
        output_dir: str | Path = "exports",
        write_csv: bool = True,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.write_csv = write_csv
        self._written: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_tables(
        self,
        tables: dict[str, pd.DataFrame],
        *,
        skip_internal_keys: bool = True,
    ) -> None:
        """Export all DataFrames in *tables* to Parquet (and CSV).

        Parameters
        ----------
        tables:
            Dict of table_name → DataFrame.
        skip_internal_keys:
            Skip keys starting with ``_`` (e.g. ``_source``).
        """
        for name, df in tables.items():
            if skip_internal_keys and name.startswith("_"):
                continue
            if isinstance(df, pd.DataFrame) and not df.empty:
                self._write(df, name)
            else:
                logger.debug("Skipping empty table: %s", name)

    def export_snapshot(self, df: pd.DataFrame, name: str = "fact_monthly_snapshot") -> None:
        """Export a monthly snapshot DataFrame."""
        self._write(df, name)

    def export_kpis(self, kpis: dict[str, Any], name: str = "kpi_summary") -> None:
        """Export a KPI dict as a single-row CSV/Parquet."""
        df = pd.DataFrame([kpis])
        self._write(df, name)

    def export_unmatched(self, unmatched_df: pd.DataFrame) -> None:
        """Export unmatched records to CSV only (reason_code populated)."""
        if "reason_code" not in unmatched_df.columns:
            unmatched_df = unmatched_df.copy()
            unmatched_df["reason_code"] = "not_specified"
        else:
            unmatched_df = unmatched_df.copy()
            unmatched_df["reason_code"] = unmatched_df["reason_code"].fillna("not_specified")

        path = self.output_dir / "unmatched_records.csv"
        unmatched_df.to_csv(path, index=False)
        self._written.append(str(path))
        logger.info("Unmatched records → %s (%d rows)", path, len(unmatched_df))

    def write_manifest(
        self,
        meta: dict[str, Any] | None = None,
        *,
        snapshot_month: str | None = None,
        source: str | None = None,
    ) -> Path:
        """Write a JSON run manifest with file hashes and metadata.

        Returns
        -------
        Path
            Path to the written manifest.
        """
        manifest: dict[str, Any] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "snapshot_month": snapshot_month,
            "source": source,
            "files": [],
        }
        if meta:
            manifest.update(meta)

        for file_path in self._written:
            fp = Path(file_path)
            if fp.exists():
                manifest["files"].append(
                    {
                        "name": fp.name,
                        "path": str(fp),
                        "size_bytes": fp.stat().st_size,
                        "sha256": self._file_hash(fp),
                    }
                )

        manifest_path = self.output_dir / "run_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        logger.info("Run manifest → %s", manifest_path)
        return manifest_path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _write(self, df: pd.DataFrame, name: str) -> None:
        """Write *df* as both Parquet and CSV."""
        parquet_path = self.output_dir / f"{name}.parquet"
        df.to_parquet(parquet_path, index=False)
        self._written.append(str(parquet_path))
        logger.info("Wrote %s.parquet (%d rows)", name, len(df))

        if self.write_csv:
            csv_path = self.output_dir / f"{name}.csv"
            df.to_csv(csv_path, index=False)
            self._written.append(str(csv_path))
            logger.info("Wrote %s.csv (%d rows)", name, len(df))

    @staticmethod
    def _file_hash(path: Path) -> str:
        """Compute SHA-256 hash of *path* using a streaming, bounded-memory approach."""
        h = hashlib.sha256()
        # Read the file in chunks to avoid loading large files entirely into memory
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
