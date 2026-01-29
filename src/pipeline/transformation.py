"""
PHASE 2: DATA TRANSFORMATION

Responsibilities:
- Data cleaning and normalization
- Null/outlier handling
- Type conversion
- Business rules application
- Referential integrity checks
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from python.logging_config import get_logger

logger = get_logger(__name__)


class TransformationPhase:
    """Phase 2: Data Transformation"""

    def __init__(self, config: Dict[str, Any], business_rules: Dict[str, Any]):
        """
        Initialize transformation phase.

        Args:
            config: Transformation configuration from pipeline.yml
            business_rules: Business rules from business_rules.yaml
        """
        self.config = config
        self.business_rules = business_rules
        logger.info("Initialized transformation phase")

    def execute(
        self,
        raw_data_path: Optional[Path] = None,
        df: Optional[pd.DataFrame] = None,
        run_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Execute transformation phase.

        Args:
            raw_data_path: Path to raw data from Phase 1
            df: DataFrame (if already loaded)
            run_dir: Directory for this pipeline run

        Returns:
            Transformation results including cleaned data path
        """
        logger.info("Starting Phase 2: Transformation")

        try:
            # Load data
            if df is None:
                if raw_data_path and raw_data_path.exists():
                    df = pd.read_parquet(raw_data_path)
                else:
                    raise ValueError("No data provided for transformation")

            initial_rows = len(df)

            # Apply transformations
            df = self._handle_nulls(df)
            df = self._normalize_types(df)
            df = self._apply_business_rules(df)
            df = self._detect_outliers(df)
            df = self._check_referential_integrity(df)

            # Store clean data
            if run_dir:
                output_path = run_dir / "clean_data.parquet"
                df.to_parquet(output_path, index=False)
                logger.info(f"Saved clean data to {output_path}")
            else:
                output_path = None

            results = {
                "status": "success",
                "initial_rows": initial_rows,
                "final_rows": len(df),
                "rows_removed": initial_rows - len(df),
                "columns": len(df.columns),
                "output_path": str(output_path) if output_path else None,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Transformation completed: {initial_rows} → {len(df)} rows")
            return results

        except Exception as e:
            logger.error(f"Transformation failed: {str(e)}", exc_info=True)
            return {"status": "failed", "error": str(e), "timestamp": datetime.now().isoformat()}

    def _handle_nulls(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values."""
        logger.info("Handling null values")

        # TODO: Implement configurable null handling strategies
        # For now, just log null counts
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            logger.warning(f"Null values found:\n{null_counts[null_counts > 0]}")

        return df

    def _normalize_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize data types."""
        logger.info("Normalizing data types")

        # TODO: Implement type conversion logic
        return df

    def _apply_business_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply business rules from configuration."""
        logger.info("Applying business rules")

        # TODO: Implement business rule engine
        # Example: status mappings, bucket assignments, etc.
        return df

    def _detect_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect and handle outliers."""
        logger.info("Detecting outliers")

        # TODO: Implement outlier detection
        # Example: Z-score, IQR method
        return df

    def _check_referential_integrity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Check referential integrity across entities."""
        logger.info("Checking referential integrity")

        # TODO: Implement referential integrity checks
        return df
