import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

from src.compliance import create_access_log_entry, mask_pii_in_dataframe
from src.pipeline.data_validation import (
    validate_iso8601_dates,
    validate_no_nulls,
    validate_numeric_bounds,
    validate_percentage_bounds,
)
from src.pipeline.utils import hash_dataframe, utc_now  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass
class TransformationResult:
    """Container for transformation outputs and lineage."""

    df: pd.DataFrame
    run_id: str
    lineage: List[Dict[str, Any]]
    quality_checks: Dict[str, Any]
    masked_columns: List[str]
    access_log: List[Dict[str, Any]]
    timestamp: str


class NormalizationProcessor:
    """Handles data normalization and null handling."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        clean_df = df.copy()
        normalization = self.config.get("normalization", {})

        if normalization.get("lowercase_columns", True):
            clean_df.columns = [str(c).lower().strip() for c in clean_df.columns]

        if normalization.get("strip_whitespace", True):
            clean_df = clean_df.map(lambda val: val.strip() if isinstance(val, str) else val)

        clean_df = self._handle_nulls(clean_df)
        return clean_df

    def _handle_nulls(self, df: pd.DataFrame) -> pd.DataFrame:
        null_cfg = self.config.get("null_handling", {})
        strategy = null_cfg.get("strategy", "fill_zero")
        columns = null_cfg.get("columns", [])
        if not columns:
            return df
        updated = df.copy()
        if strategy == "fill_zero":
            updated[columns] = updated[columns].fillna(0)
        elif strategy == "drop_rows":
            updated = updated.dropna(subset=columns)
        return updated


class ComplianceProcessor:
    """Handles PII masking and access logging."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pii_config = self._load_pii_config()

    def _load_pii_config(self) -> Dict[str, Any]:
        from src.config.paths import get_project_root  # noqa: E402

        config_path = get_project_root() / "config" / "pii_fields.yaml"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception as exc:
                logger.error("Failed to load PII config: %s", exc)
        return {}

    def process(
        self, df: pd.DataFrame, user: str
    ) -> Tuple[pd.DataFrame, List[str], List[Dict[str, Any]]]:
        masked_columns: List[str] = []
        access_log: List[Dict[str, Any]] = []

        pii_cfg = self.config.get("pii_masking", {})
        clean_df = df.copy()

        if pii_cfg.get("enabled", True):
            clean_df, masked_columns = mask_pii_in_dataframe(
                clean_df,
                keywords=self.pii_config.get("keywords") or pii_cfg.get("keywords"),
                pii_columns=self.pii_config.get("explicit_columns"),
                action=self.pii_config.get("default_action", "mask"),
            )
            access_log.append(
                create_access_log_entry("transformation", user, "mask_pii", "success")
            )

        return clean_df, masked_columns, access_log


class QualityChecker:
    """Handles outlier detection and quality checks."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        outlier_cfg = self.config.get("outlier_detection", {})
        if not outlier_cfg.get("enabled", False):
            return {}

        threshold = float(outlier_cfg.get("zscore_threshold", 4.0))
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result: Dict[str, Any] = {}

        for col in numeric_cols:
            series = df[col].dropna()
            if series.empty:
                continue
            mean = series.mean()
            std = series.std()
            if std == 0 or np.isnan(std):
                continue
            zscores = (series - mean) / std
            outlier_count = int((zscores.abs() > threshold).sum())
            if outlier_count:
                result[col] = {"outliers": outlier_count, "threshold": threshold}
        return result

    def perform_checks(self, df: pd.DataFrame) -> Dict[str, Any]:
        quality_checks: Dict[str, Any] = {}
        quality_checks.update(validate_numeric_bounds(df))
        quality_checks.update(validate_percentage_bounds(df))
        quality_checks.update(validate_iso8601_dates(df))
        quality_checks.update(validate_no_nulls(df))
        return quality_checks


class UnifiedTransformation:
    """Phase 2: Data transformation, normalization, and compliance masking."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, run_id: Optional[str] = None):
        root_cfg: Dict[str, Any] = config or {}
        self.config = root_cfg.get("pipeline", {}).get("phases", {}).get("transformation", {})
        self.run_id = run_id or f"tx_{uuid.uuid4().hex[:12]}"
        self.lineage: List[Dict[str, Any]] = []
        self.transformations_count = 0

        # Initialize processors
        self.normalizer = NormalizationProcessor(self.config)
        self.compliance = ComplianceProcessor(self.config)
        self.quality = QualityChecker(self.config)

    def _log_step(self, step: str, status: str, **details: Any) -> None:
        entry = {
            "run_id": self.run_id,
            "step": step,
            "status": status,
            "timestamp": utc_now(),
            **details,
        }
        self.lineage.append(entry)
        logger.info("[Transformation:%s] %s | %s", step, status, details)

    def transform(self, df: pd.DataFrame, user: str = "system") -> TransformationResult:
        self._log_step("start", "initiated", input_rows=len(df))
        access_log: List[Dict[str, Any]] = []
        access_log.append(create_access_log_entry("transformation", user, "read", "success"))

        try:
            # 1. Normalization
            clean_df = self.normalizer.process(df)
            self._log_step("normalization", "success", columns=list(clean_df.columns))

            # 2. Outlier Detection
            outliers = self.quality.detect_outliers(clean_df)
            if outliers:
                self._log_step("outlier_detection", "flagged", details=outliers)
            else:
                self._log_step("outlier_detection", "clean")

            # 3. Compliance & PII Masking
            clean_df, masked_columns, comp_logs = self.compliance.process(clean_df, user)
            access_log.extend(comp_logs)
            self._log_step("pii_masking", "completed", masked_columns=masked_columns)

            # 4. Lineage
            input_hash = hash_dataframe(df)
            output_hash = hash_dataframe(clean_df)
            self._log_step("lineage", "captured", input_hash=input_hash, output_hash=output_hash)

            clean_df["_tx_run_id"] = self.run_id
            clean_df["_tx_timestamp"] = utc_now()

            # 5. Quality Checks
            quality_checks = self.quality.perform_checks(clean_df)
            self._log_step("quality_checks", "completed", checks=len(quality_checks))
            self._log_step("complete", "success", output_rows=len(clean_df))

            return TransformationResult(
                df=clean_df,
                run_id=self.run_id,
                lineage=self.lineage,
                quality_checks=quality_checks,
                masked_columns=masked_columns,
                access_log=access_log,
                timestamp=utc_now(),
            )

        except Exception as exc:
            access_log.append(create_access_log_entry("transformation", user, "error", "failed"))
            self._log_step("fatal_error", "failed", error=str(exc))
            raise
