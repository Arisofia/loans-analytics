"""
PHASE 1: DATA INGESTION

Responsibilities:
- Fetch data from CSV files or Supabase
- Schema validation using Pydantic
- Duplicate detection via checksums
- Raw data storage with immutable hashes

NOTE: Cascade API integration has been deprecated (Jan 2026).
NOTE: This module is not designed to be run directly as a script.
      Use: python scripts/data/run_data_pipeline.py
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from backend.python.logging_config import get_logger
from backend.src.infrastructure.google_sheets_adapter import ControlMoraSheetsAdapter

logger = get_logger(__name__)


class IngestionPhase:
    """Phase 1: Data Ingestion"""

    _GSHEETS_URI_PREFIX = "gsheets://"

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ingestion phase.

        Args:
            config: Ingestion configuration from pipeline.yml
        """
        self.config = config
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info("Initialized ingestion phase (run_id: %s)", self.run_id)

    def execute(
        self, input_path: Optional[Path] = None, run_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Execute ingestion phase.

        Args:
            input_path: Path to input CSV file (if file-based)
            run_dir: Directory for this pipeline run

        Returns:
            Ingestion results including data path and metadata
        """
        logger.info("Starting Phase 1: Ingestion")

        # Load data
        if self._should_use_google_sheets(input_path):
            df = self._load_from_google_sheets(input_path)
        elif input_path and input_path.exists():
            df = self._load_from_file(input_path)
        elif input_path and not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        else:
            logger.info("No input file provided; API ingestion is disabled")
            df = self._load_from_api()

        # Validate schema (Raises ValueError on failure)
        validation_results = self._validate_schema(df)

        # Check for duplicates
        duplicate_check = self._check_duplicates(df)

        # Store raw data
        if run_dir:
            output_path = run_dir / "raw_data.parquet"
            try:
                df.to_parquet(output_path, index=False)
            except Exception as parquet_error:
                logger.warning(
                    "Parquet write failed on raw frame; applying Arrow-safe coercion. Error: %s",
                    parquet_error,
                )
                df = self._make_arrow_safe(df)
                df.to_parquet(output_path, index=False)
            logger.info("Saved raw data to %s", output_path)
        else:
            output_path = None

        # Calculate data hash
        data_hash = self._calculate_hash(df)

        results = {
            "status": "success",
            "row_count": len(df),
            "column_count": len(df.columns),
            "data_hash": data_hash,
            "validation": validation_results,
            "duplicates": duplicate_check,
            "output_path": str(output_path) if output_path else None,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            "Ingestion completed: %d rows, %d columns",
            results["row_count"],
            results["column_count"],
        )
        return results

    def _load_from_file(self, file_path: Path) -> pd.DataFrame:
        """Load data from CSV file."""
        logger.info("Loading data from file: %s", file_path)

        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path, low_memory=False)
        elif file_path.suffix.lower() in [".parquet", ".pq"]:
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        logger.info("Loaded %d rows from %s", len(df), file_path.name)
        return df

    def _make_arrow_safe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Coerce object columns to nullable strings so PyArrow can serialize mixed-type columns.
        """
        safe = df.copy()
        safe.columns = [str(col) for col in safe.columns]

        for col in safe.columns:
            series = safe[col]
            if series.dtype == "object":
                safe[col] = series.map(self._to_nullable_string).astype("string")

        return safe

    @staticmethod
    def _to_nullable_string(value: Any) -> Any:
        if pd.isna(value):
            return pd.NA
        if isinstance(value, bytes):
            for encoding in ("utf-8", "latin-1"):
                try:
                    return value.decode(encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError(
                f"CRITICAL: decode failure for bytes value {repr(value)}. Aborting batch."
            )
        return str(value)

    def _load_from_api(self) -> pd.DataFrame:
        """No-op API loader kept for backward compatibility; always fails closed."""
        raise RuntimeError(
            "No input file provided. API ingestion was deprecated and dummy/sample fallback "
            "is disabled. Pass --input with a real dataset."
        )

    def _should_use_google_sheets(self, input_path: Optional[Path]) -> bool:
        """Return True when ingestion should pull from Google Sheets."""
        if input_path is not None and self._extract_google_sheet_tab(input_path):
            return True
        sheets_cfg = self.config.get("google_sheets", {})
        return bool(sheets_cfg.get("enabled", False) and input_path is None)

    def _extract_google_sheet_tab(self, input_path: Path) -> Optional[str]:
        """Extract worksheet tab from a gsheets URI regardless of OS path normalization."""
        normalized = str(input_path).replace("\\", "/")
        if normalized.startswith(self._GSHEETS_URI_PREFIX):
            return normalized[len(self._GSHEETS_URI_PREFIX) :].strip("/") or None
        if normalized.startswith("gsheets:/"):
            return normalized[len("gsheets:/") :].strip("/") or None
        return None

    def _load_from_google_sheets(self, input_path: Optional[Path] = None) -> pd.DataFrame:
        """Load Control de Mora rows from Google Sheets through the institutional adapter."""
        sheets_cfg = self.config.get("google_sheets", {})
        credentials_path = sheets_cfg.get("credentials_path") or os.getenv(
            "GOOGLE_SHEETS_CREDENTIALS_PATH"
        )
        spreadsheet_id = sheets_cfg.get("spreadsheet_id") or os.getenv(
            "GOOGLE_SHEETS_SPREADSHEET_ID"
        )

        if not credentials_path or not spreadsheet_id:
            raise ValueError(
                "CRITICAL: Google Sheets ingestion enabled but credentials_path/spreadsheet_id "
                "are missing. Set google_sheets config or environment variables."
            )

        adapter = ControlMoraSheetsAdapter(
            credentials_path=str(credentials_path),
            spreadsheet_id=str(spreadsheet_id),
        )
        requested_tab = self._extract_google_sheet_tab(input_path) if input_path else None
        target_tab = requested_tab or str(sheets_cfg.get("worksheet", "")).strip() or "DESEMBOLSOS"

        if target_tab.upper() == "DESEMBOLSOS":
            records = adapter.fetch_desembolsos_raw()
        else:
            records = adapter.fetch_sheet_raw(target_tab)

        if not records:
            raise ValueError(f"CRITICAL: Google Sheets tab '{target_tab}' returned zero records")

        df = pd.DataFrame(records)
        df = self._coerce_google_sheets_schema(df)
        logger.info("Loaded %d rows from Google Sheets adapter tab '%s'", len(df), target_tab)
        return df

    def _coerce_google_sheets_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Coerce common Google Sheets source columns into canonical ingestion fields."""

        def first_existing(columns: list[str]) -> Optional[str]:
            return next((col for col in columns if col in df.columns), None)

        loan_id_col = first_existing(["loan_id", "NumeroInterno", "NumeroQuedan", "numerointerno"])
        amount_col = first_existing(
            ["amount", "ValorAprobado", "MontoDesembolsado", "valoraprobado", "montodesembolsado"]
        )
        borrower_id_col = first_existing(["borrower_id", "CodCliente", "codcliente"])
        status_col = first_existing(["status", "mdscPosteado", "mdscposteado", "infoclientefinal"])

        if loan_id_col and "loan_id" not in df.columns:
            df["loan_id"] = df[loan_id_col]
        if amount_col and "amount" not in df.columns:
            df["amount"] = pd.to_numeric(df[amount_col], errors="coerce")
        if borrower_id_col and "borrower_id" not in df.columns:
            df["borrower_id"] = df[borrower_id_col]

        if "status" not in df.columns:
            if status_col:
                normalized = df[status_col].astype(str).str.strip().str.lower()
                df["status"] = normalized.replace(
                    {
                        "vigente": "active",
                        "al_dia": "active",
                        "posted": "active",
                        "mora": "delinquent",
                        "vencido": "delinquent",
                        "castigado": "defaulted",
                        "default": "defaulted",
                    }
                )
            else:
                raise ValueError(
                    "CRITICAL: Google Sheets data cannot be normalized to canonical schema; "
                    "missing status source column (expected one of: status, mdscPosteado, "
                    "mdscposteado, infoclientefinal)."
                )

        missing = [
            col for col in ("loan_id", "amount", "status", "borrower_id") if col not in df.columns
        ]
        if missing:
            raise ValueError(
                "CRITICAL: Google Sheets data cannot be normalized to canonical schema; "
                f"missing columns after mapping: {missing}. Available columns: {sorted(df.columns)}"
            )

        return df

    def _validate_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate DataFrame schema using Pydantic."""
        try:
            # Define required columns from config or defaults
            required_columns = self.config.get(
                "required_columns", ["loan_id", "amount", "status", "borrower_id"]
            )

            # Check for required columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                error_msg = f"CRITICAL: SCHEMA VALIDATION FAILED: Missing required columns: {missing_columns}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Validate data types (vectorized for performance)
            type_validation: Dict[str, Any] = {
                "loan_id": str,
                "amount": (int, float),
                "status": str,
            }

            type_errors = []
            for col, expected_type in type_validation.items():
                if col in df.columns and not all(
                    isinstance(val, expected_type) for val in df[col].dropna()
                ):
                    type_errors.append(col)

            if type_errors:
                error_msg = f"CRITICAL: SCHEMA VALIDATION FAILED: Type validation failed for columns: {type_errors}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.info(
                "Schema validation passed",
                extra={
                    "column_count": len(df.columns),
                    "row_count": len(df),
                },
            )
            return {
                "schema_valid": True,
                "required_columns_present": True,
                "data_types_valid": True,
                "column_count": len(df.columns),
                "row_count": len(df),
            }
        except Exception as e:
            if isinstance(e, ValueError) and "CRITICAL: SCHEMA VALIDATION FAILED" in str(e):
                raise
            logger.error("Schema validation error: %s", e, exc_info=True)
            raise ValueError(f"CRITICAL: Schema validation pipeline failure: {e}") from e

    def _check_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for duplicate rows."""
        duplicates = df.duplicated().sum()

        return {"duplicate_count": int(duplicates), "has_duplicates": duplicates > 0}

    def _calculate_hash(self, df: pd.DataFrame) -> str:
        """Calculate hash of DataFrame contents."""
        # Canonicalize column order so semantically identical frames hash identically.
        canonical_df = df.reindex(sorted(df.columns), axis=1)
        data_str = canonical_df.to_json(orient="records", date_format="iso")
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
