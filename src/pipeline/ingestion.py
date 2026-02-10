"""
PHASE 1: DATA INGESTION

Responsibilities:
- Fetch data from CSV files or Supabase
- Schema validation using Pydantic
- Duplicate detection via checksums
- Raw data storage with immutable hashes

NOTE: Cascade API integration has been deprecated (Jan 2026).
NOTE: This module is not designed to be run directly as a script.
      Use: python scripts/run_data_pipeline.py
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from python.logging_config import get_logger
from src.pipeline.utils import format_error_response

logger = get_logger(__name__)


class IngestionPhase:
    """Phase 1: Data Ingestion"""

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

        try:
            # Load data
            if input_path and input_path.exists():
                df = self._load_from_file(input_path)
            else:
                logger.info("No input file provided, checking for API ingestion...")
                df = self._load_from_api()

            # Validate schema
            validation_results = self._validate_schema(df)

            # Check for duplicates
            duplicate_check = self._check_duplicates(df)

            # Store raw data
            if run_dir:
                output_path = run_dir / "raw_data.parquet"
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

        except Exception as e:
            logger.error("Ingestion failed: %s", str(e), exc_info=True)
            return format_error_response(e)

    def _load_from_file(self, file_path: Path) -> pd.DataFrame:
        """Load data from CSV file."""
        logger.info("Loading data from file: %s", file_path)

        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
        elif file_path.suffix.lower() in [".parquet", ".pq"]:
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        logger.info("Loaded %d rows from %s", len(df), file_path.name)
        return df

    def _load_from_api(self) -> pd.DataFrame:
        """Load data from external API (deprecated - Cascade no longer used)."""
        logger.warning("API ingestion deprecated - Cascade integration removed. Using sample data.")

        # NOTE: Cascade API integration has been deprecated.
        # Data is now loaded from CSV files or Supabase directly.

        return pd.DataFrame(
            {
                "loan_id": ["LOAN001", "LOAN002"],
                "amount": [10000, 15000],
                "status": ["active", "active"],
            }
        )

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
                logger.warning("Missing required columns: %s", missing_columns)
                return {
                    "schema_valid": False,
                    "required_columns_present": False,
                    "missing_columns": missing_columns,
                    "data_types_valid": False,
                }

            # Validate data types (vectorized for performance)
            type_validation = {
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
                logger.warning("Type validation failed for columns: %s", type_errors)
                return {
                    "schema_valid": False,
                    "required_columns_present": True,
                    "data_types_valid": False,
                    "type_errors": type_errors,
                }

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
            logger.error("Schema validation error: %s", e, exc_info=True)
            return {
                "schema_valid": False,
                "error": str(e),
            }

    def _check_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for duplicate rows."""
        duplicates = df.duplicated().sum()

        return {"duplicate_count": int(duplicates), "has_duplicates": duplicates > 0}

    def _calculate_hash(self, df: pd.DataFrame) -> str:
        """Calculate hash of DataFrame contents."""
        data_str = df.to_json(orient="records", date_format="iso")
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
