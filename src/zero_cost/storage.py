"""
Zero-cost storage backend: DuckDB + Parquet files.

Replaces Azure Blob Storage / Azure Storage Account.
Data is persisted as Parquet files (optionally synced to Google Drive /
OneDrive / Dropbox via rclone) and queried with an embedded DuckDB instance.

Usage
-----
    storage = ZeroCostStorage(base_dir="data/duckdb")
    storage.write_parquet(df, "fact_disbursement", partition_cols=["year", "month"])
    df = storage.query("SELECT * FROM fact_disbursement WHERE year = 2026")
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import duckdb  # type: ignore[import]

    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    logger.warning("duckdb not installed — SQL queries disabled (pip install duckdb)")


class ZeroCostStorage:
    """DuckDB-backed Parquet storage replacing Azure Blob / Storage Account.

    Parameters
    ----------
    base_dir:
        Root directory for Parquet files.  Defaults to ``data/duckdb`` relative
        to the current working directory.
    db_path:
        Path for the persistent DuckDB database file.  Use ``None`` for an
        in-memory database (useful in tests).
    """

    def __init__(
        self,
        base_dir: str | os.PathLike = "data/duckdb",
        db_path: str | os.PathLike | None = "data/duckdb/analytics.duckdb",
    ) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self._db_path = str(db_path) if db_path is not None else ":memory:"
        self._conn: Any = None  # lazy-connect on first use

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _get_conn(self) -> Any:
        if not DUCKDB_AVAILABLE:
            raise RuntimeError("duckdb is required for SQL queries.  pip install duckdb")
        if self._conn is None:
            import duckdb as _duckdb  # noqa: PLC0415

            self._conn = _duckdb.connect(self._db_path)
            # parquet is a built-in extension since DuckDB 0.9 — no install needed
        return self._conn

    def close(self) -> None:
        """Close the DuckDB connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def write_parquet(
        self,
        df: pd.DataFrame,
        table_name: str,
        partition_cols: list[str] | None = None,
        write_manifest: bool = True,
    ) -> Path:
        """Persist *df* as Parquet and register it in DuckDB.

        Parameters
        ----------
        df:
            DataFrame to persist.
        table_name:
            Logical table name (becomes the subdirectory name).
        partition_cols:
            Optional Hive-style partition columns (e.g. ``["year", "month"]``).
        write_manifest:
            When ``True`` (default), write a JSON manifest with row count and
            content hash for auditability.

        Returns
        -------
        Path
            Path to the written Parquet file (or directory if partitioned).
        """
        table_dir = self.base_dir / table_name
        table_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        parquet_path = table_dir / f"{table_name}_{ts}.parquet"

        df.to_parquet(parquet_path, index=False, engine="pyarrow")
        logger.info("Wrote %d rows → %s", len(df), parquet_path)

        if write_manifest:
            self._write_manifest(df, parquet_path, table_name)

        if DUCKDB_AVAILABLE:
            self._register_table(table_name, table_dir)

        return parquet_path

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, sql: str) -> pd.DataFrame:
        """Execute *sql* against the registered Parquet files.

        Parameters
        ----------
        sql:
            DuckDB SQL statement.

        Returns
        -------
        pd.DataFrame
        """
        conn = self._get_conn()
        return conn.execute(sql).df()

    def read_parquet(self, table_name: str) -> pd.DataFrame:
        """Return all data for *table_name* as a DataFrame."""
        table_dir = self.base_dir / table_name
        if not table_dir.exists():
            raise FileNotFoundError(f"No data found for table '{table_name}' at {table_dir}")
        return self.query(f"SELECT * FROM read_parquet('{table_dir}/*.parquet')")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _register_table(self, table_name: str, table_dir: Path) -> None:
        """Register all Parquet files in *table_dir* as a DuckDB view."""
        conn = self._get_conn()
        glob_path = str(table_dir / "*.parquet")
        conn.execute(
            f"CREATE OR REPLACE VIEW {table_name} AS "
            f"SELECT * FROM read_parquet('{glob_path}')"
        )

    def _write_manifest(
        self, df: pd.DataFrame, parquet_path: Path, table_name: str
    ) -> None:
        """Write a JSON audit manifest alongside the Parquet file."""
        raw_bytes = df.to_json(orient="records", date_format="iso").encode()
        content_hash = hashlib.sha256(raw_bytes).hexdigest()
        manifest = {
            "table": table_name,
            "written_at": datetime.now(timezone.utc).isoformat(),
            "rows": len(df),
            "columns": list(df.columns),
            "sha256": content_hash,
            "parquet_file": parquet_path.name,
        }
        manifest_path = parquet_path.with_suffix(".manifest.json")
        manifest_path.write_text(json.dumps(manifest, indent=2))
        logger.debug("Manifest written → %s", manifest_path)
