import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yaml

from src.compliance import create_access_log_entry, mask_pii_in_dataframe
from src.pipeline.data_validation import (validate_iso8601_dates,
                                          validate_no_nulls,
                                          validate_numeric_bounds,
                                          validate_percentage_bounds)
from src.pipeline.utils import hash_dataframe, utc_now

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


class UnifiedTransformation:
    """Phase 2: Data transformation, normalization, and compliance masking."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, run_id: Optional[str] = None):
        root_cfg: Dict[str, Any] = config or {}
        self.config = root_cfg.get("pipeline", {}).get("phases", {}).get("transformation", {})
        self.run_id = run_id or f"tx_{uuid.uuid4().hex[:12]}"
        self.lineage: List[Dict[str, Any]] = []
        self.transformations_count = 0
        self.pii_config = self._load_pii_config()

    def _load_pii_config(self) -> Dict[str, Any]:
        config_path = Path("config/pii_fields.yaml")
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception as exc:
                logger.error("Failed to load PII config: %s", exc)
        return {}

    def calculate_receivables_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        required = [
            "total_receivable_usd",
            "total_eligible_usd",
            "discounted_balance_usd",
        ]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"missing required columns: {missing}")
        return {
            "total_receivable": float(pd.to_numeric(df["total_receivable_usd"]).sum()),
            "total_eligible": float(pd.to_numeric(df["total_eligible_usd"]).sum()),
            "discounted_balance": float(pd.to_numeric(df["discounted_balance_usd"]).sum()),
        }

    def calculate_dpd_ratios(self, df: pd.DataFrame) -> Dict[str, float]:
        dpd_cols = [
            "dpd_0_7_usd",
            "dpd_7_30_usd",
            "dpd_30_60_usd",
            "dpd_60_90_usd",
            "dpd_90_plus_usd",
        ]
        missing = [col for col in (dpd_cols + ["total_receivable_usd"]) if col not in df.columns]
        if missing:
            raise ValueError(f"missing required columns: {missing}")

        total = float(pd.to_numeric(df["total_receivable_usd"], errors="raise").sum())
        if total <= 0:
            return {col: 0.0 for col in dpd_cols}

        ratios: Dict[str, float] = {}
        for col in dpd_cols:
            amt = float(pd.to_numeric(df[col], errors="raise").sum())
            ratios[col] = (amt / total) * 100.0
        return ratios

    def _select_column_case_insensitive(self, df: pd.DataFrame, name: str) -> Optional[str]:
        lower_map = {str(c).lower(): str(c) for c in df.columns}
        return lower_map.get(name.lower())

    def transform_to_kpi_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        if "_validation_passed" in df.columns:
            try:
                if not bool(df["_validation_passed"].all()):
                    raise ValueError("missing required columns")
            except Exception as exc:
                if isinstance(exc, ValueError):
                    raise
                raise ValueError("missing required columns") from exc

        required = [
            "total_receivable_usd",
            "total_eligible_usd",
            "discounted_balance_usd",
            "dpd_0_7_usd",
            "dpd_7_30_usd",
            "dpd_30_60_usd",
            "dpd_60_90_usd",
            "dpd_90_plus_usd",
        ]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"missing required columns: {missing}")

        numeric_required = list(required)
        for col in numeric_required:
            try:
                pd.to_numeric(df[col], errors="raise")
            except Exception as exc:
                raise ValueError(f"non-numeric required column: {col}") from exc

        out = pd.DataFrame(index=df.index)
        # Preserve raw columns expected by KPIEngine (v1)
        out["total_receivable_usd"] = pd.to_numeric(df["total_receivable_usd"], errors="raise")
        out["total_eligible_usd"] = pd.to_numeric(df["total_eligible_usd"], errors="raise")
        out["discounted_balance_usd"] = pd.to_numeric(df["discounted_balance_usd"], errors="raise")
        out["dpd_0_7_usd"] = pd.to_numeric(df["dpd_0_7_usd"], errors="raise")
        out["dpd_7_30_usd"] = pd.to_numeric(df["dpd_7_30_usd"], errors="raise")
        out["dpd_30_60_usd"] = pd.to_numeric(df["dpd_30_60_usd"], errors="raise")
        out["dpd_60_90_usd"] = pd.to_numeric(df["dpd_60_90_usd"], errors="raise")
        out["dpd_90_plus_usd"] = pd.to_numeric(df["dpd_90_plus_usd"], errors="raise")

        out["receivable_amount"] = pd.to_numeric(df["total_receivable_usd"], errors="raise")
        out["eligible_amount"] = pd.to_numeric(df["total_eligible_usd"], errors="raise")
        out["discounted_amount"] = pd.to_numeric(df["discounted_balance_usd"], errors="raise")

        denom = out["receivable_amount"].replace({0: np.nan})
        for col in [
            "dpd_0_7_usd",
            "dpd_7_30_usd",
            "dpd_30_60_usd",
            "dpd_60_90_usd",
            "dpd_90_plus_usd",
        ]:
            pct_name = f"{col}_pct"
            out[pct_name] = (out[col] / denom) * 100.0
            out[pct_name] = out[pct_name].fillna(0.0)

        apr_col = self._select_column_case_insensitive(df, "avg_apr_pct")
        if apr_col is not None:
            out["interest_rate"] = df[apr_col]

        out["_transform_run_id"] = self.run_id
        out["_transform_timestamp"] = utc_now()
        self.transformations_count += 1
        return out

    def validate_transformations(self, original: pd.DataFrame, transformed: pd.DataFrame) -> bool:
        if len(original) != len(transformed):
            return False
        if "receivable_amount" not in transformed.columns:
            return False
        try:
            orig_total = float(
                pd.to_numeric(original["total_receivable_usd"], errors="raise").sum()
            )
            new_total = float(pd.to_numeric(transformed["receivable_amount"], errors="raise").sum())
        except Exception:
            return False
        return abs(orig_total - new_total) < 1e-6

    def get_processing_summary(self) -> Dict[str, Any]:
        """Return summary of transformation operations."""
        return {
            "run_id": self.run_id,
            "transformations_applied": self.transformations_count,
            "lineage_entries": len(self.lineage),
            "timestamp": utc_now(),
        }

    def get_lineage(self) -> List[Dict[str, Any]]:
        """Return full transformation lineage."""
        return list(self.lineage)

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

    def _detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
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

    def transform(self, df: pd.DataFrame, user: str = "system") -> TransformationResult:
        self._log_step("start", "initiated", input_rows=len(df))
        access_log: List[Dict[str, Any]] = []
        access_log.append(create_access_log_entry("transformation", user, "read", "success"))

        try:
            clean_df = df.copy()
            normalization = self.config.get("normalization", {})
            if normalization.get("lowercase_columns", True):
                clean_df.columns = [str(c).lower().strip() for c in clean_df.columns]
            if normalization.get("strip_whitespace", True):
                clean_df = clean_df.map(lambda val: val.strip() if isinstance(val, str) else val)
            self._log_step("normalization", "success", columns=list(clean_df.columns))

            clean_df = self._handle_nulls(clean_df)
            self._log_step("null_handling", "success")

            outliers = self._detect_outliers(clean_df)
            if outliers:
                self._log_step("outlier_detection", "flagged", details=outliers)
            else:
                self._log_step("outlier_detection", "clean")

            masked_columns: List[str] = []
            pii_cfg = self.config.get("pii_masking", {})
            if pii_cfg.get("enabled", True):
                clean_df, masked_columns = mask_pii_in_dataframe(
                    clean_df,
                    keywords=self.pii_config.get("keywords") or pii_cfg.get("keywords"),
                    pii_columns=self.pii_config.get("explicit_columns"),
                    action=self.pii_config.get("default_action", "mask"),
                )
            self._log_step("pii_masking", "completed", masked_columns=masked_columns)
            access_log.append(
                create_access_log_entry("transformation", user, "mask_pii", "success")
            )

            input_hash = hash_dataframe(df)
            output_hash = hash_dataframe(clean_df)
            self._log_step("lineage", "captured", input_hash=input_hash, output_hash=output_hash)

            clean_df["_tx_run_id"] = self.run_id
            clean_df["_tx_timestamp"] = utc_now()

            quality_checks: Dict[str, Any] = {}
            quality_checks.update(validate_numeric_bounds(clean_df))
            quality_checks.update(validate_percentage_bounds(clean_df))
            quality_checks.update(validate_iso8601_dates(clean_df))
            quality_checks.update(validate_no_nulls(clean_df))

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
