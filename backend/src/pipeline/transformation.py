"""
PHASE 2: DATA TRANSFORMATION

Responsibilities:
- Data cleaning and normalization
- Null/outlier handling
- Type conversion
- Business rules application
- Referential integrity checks

NOTE: This module is not designed to be run directly as a script.
      Use: python scripts/data/run_data_pipeline.py
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from python.logging_config import get_logger
from src.pipeline.utils import format_error_response

logger = get_logger(__name__)


class TransformationPhase:
    """Phase 2: Data Transformation"""

    # Default numeric columns for financial data
    NUMERIC_COLUMNS: Set[str] = {
        "amount",
        "current_balance",
        "original_amount",
        "interest_rate",
        "dpd",
        "payment_amount",
    }
    NUMERIC_NAME_PATTERN = re.compile(
        r"(^|[_\s])(amount|balance|rate|count|dpd)([_\s]|$)",
        re.IGNORECASE,
    )

    # Default date columns
    DATE_COLUMNS: Set[str] = {
        "disbursement_date",
        "origination_date",
        "due_date",
        "payment_date",
        "measurement_date",
    }

    # Status mappings for normalization
    STATUS_MAPPINGS: Dict[str, str] = {
        "Active": "active",
        "ACTIVE": "active",
        "Current": "active",
        "current": "active",
        "CURRENT": "active",
        "Delinquent": "delinquent",
        "DELINQUENT": "delinquent",
        "Complete": "closed",
        "complete": "closed",
        "COMPLETE": "closed",
        "Closed": "closed",
        "CLOSED": "closed",
        "Default": "defaulted",
        "default": "defaulted",
        "DEFAULT": "defaulted",
        "Defaulted": "defaulted",
        "DEFAULTED": "defaulted",
    }

    # Null handling thresholds and constants
    LOW_NULL_THRESHOLD_PCT: float = 5.0  # Below this: use structural zero + opacity flag
    HIGH_NULL_THRESHOLD_PCT: float = 30.0  # Above this: use default fill
    MISSING_NUMERIC_INDICATOR: int = -999  # Indicator for missing numeric values
    # Cash-flow transaction fields where null should mean "no movement" (0),
    # never statistical imputation.
    FORCE_ZERO_NUMERIC_COLUMNS: Set[str] = {
        "last_payment_amount",
        "payment_amount",
        "recovery_value",
    }
    # Emit high-null warnings only for KPI-critical numeric fields.
    HIGH_NULL_WARNING_NUMERIC_COLUMNS: Set[str] = {
        "amount",
        "principal_amount",
        "current_balance",
        "outstanding_balance",
        "interest_rate",
        "dpd",
        "days_past_due",
        "last_payment_amount",
        "total_scheduled",
        "recovery_value",
    }

    def __init__(self, config: Dict[str, Any], business_rules: Optional[Dict[str, Any]] = None):
        """
        Initialize transformation phase.

        Args:
            config: Transformation configuration from pipeline.yml
            business_rules: Business rules from business_rules.yaml
        """
        self.config = config
        self.business_rules = business_rules or {}

        # Extract configuration settings with defaults
        null_config = config.get("null_handling", {})
        self.null_strategy = null_config.get("strategy", "smart")
        self.fill_values = null_config.get("fill_values", {"numeric": 0, "categorical": "unknown"})

        outlier_config = config.get("outlier_detection", {})
        self.outlier_enabled = outlier_config.get("enabled", True)
        self.outlier_method = outlier_config.get("method", "iqr")
        self.outlier_threshold = outlier_config.get("threshold", 3.0)

        type_config = config.get("type_normalization", {})
        self.type_normalization_enabled = type_config.get("enabled", True)
        self.date_format = type_config.get("date_format", "%Y-%m-%d")

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
            if df is None and raw_data_path and raw_data_path.exists():
                df = pd.read_parquet(raw_data_path)
            elif df is None:
                raise ValueError("No data provided for transformation")

            initial_rows = len(df)
            transformation_metrics: Dict[str, Any] = {}

            # Apply transformations with metrics tracking
            df = self._normalize_column_names(df)
            df, control_metrics = self._derive_control_mora_fields(df)
            transformation_metrics["control_derivations"] = control_metrics
            df = self._collapse_duplicate_columns(df)
            df, null_metrics = self._handle_nulls(df)
            transformation_metrics["null_handling"] = null_metrics

            df, type_metrics = self._normalize_types(df)
            transformation_metrics["type_normalization"] = type_metrics

            df, rule_metrics = self._apply_business_rules(df)
            transformation_metrics["business_rules"] = rule_metrics

            df, outlier_metrics = self._detect_outliers(df)
            transformation_metrics["outlier_detection"] = outlier_metrics

            df, integrity_metrics = self._check_referential_integrity(df)
            transformation_metrics["referential_integrity"] = integrity_metrics

            # Store clean data
            if run_dir:
                output_path = run_dir / "clean_data.parquet"
                df.to_parquet(output_path, index=False)
                logger.info("Saved clean data to %s", output_path)
            else:
                output_path = None

            results = {
                "status": "success",
                "initial_rows": initial_rows,
                "final_rows": len(df),
                "rows_removed": initial_rows - len(df),
                "columns": len(df.columns),
                "output_path": str(output_path) if output_path else None,
                "transformation_metrics": transformation_metrics,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info("Transformation completed: %d → %d rows", initial_rows, len(df))
            return results

        except Exception as e:
            logger.error("Transformation failed: %s", str(e), exc_info=True)
            return format_error_response(e)

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to standard schema.
        Maps source-specific names to canonical pipeline names.
        """
        # Mapping: Source Name -> Canonical Name
        column_mapping = {
            "days_past_due": "dpd",
            "dias_vencido": "dpd",
            "mora_en_dias": "dpd",
            "principal_amount": "amount",
            "current_status": "status",
            "loan_status": "status",
            "principal_balance": "current_balance",
            "loan_amount": "amount",
            "fechadesembolso": "origination_date",
            "fecha_de_desembolso": "origination_date",
            "fechapagoprogramado": "due_date",
            "fecha_vencimiento": "due_date",
            "fecha_de_vencimiento": "due_date",
            "fecha_de_pago": "last_payment_date",
            "fechacobro": "last_payment_date",
            "_pagado": "last_payment_amount",
            "lineacredito": "credit_line",
            "cod_kam_hunter": "kam_hunter",
            "cod_kam_farmer": "kam_farmer",
            "asesoriadigital": "advisory_channel",
            "fechasolicitado": "application_date",
            "porcentaje_utilizado": "utilization_pct",
            "procede_a_cobrar": "collections_eligible",
            "definicion_m": "delinquency_definition",
            "rango_m": "delinquency_bucket_raw",
            "rango_de_la_linea": "credit_line_range",
            "ministerio": "gov",
            "ministry": "gov",
            "goes": "government_sector",
            "capitalcobrado": "capital_collected",
            "montototalabonado": "total_payment_received",
            "mdscposteado": "mdsc_posted",
            "diasnegociacion": "negotiation_days",
            "dias_en_pagar": "days_to_pay",
            "numerodesembolsos": "disbursement_count",
            "valoraprobado": "approved_value",
            "fecha_actual": "as_of_date",
            "term_max": "term_months",
            "term_ponderado": "term_months",
            "apr__term__ponderado": "term_months",
            "ingreso_total_por_desembolso": "tpv",
            "ingreso_pagadopendiente": "tpv",
        }

        # Apply mapping for columns that exist in df
        rename_dict = {
            source: target
            for source, target in column_mapping.items()
            if source in df.columns and target not in df.columns
        }

        if rename_dict:
            df = df.rename(columns=rename_dict)
            logger.info("Renamed columns: %s", rename_dict)

        # Generate loan_uid: Composite key to handle reused loan_ids
        if "loan_id" in df.columns and "origination_date" in df.columns:
            # Convert origination_date to string for concat if it's not already
            dates = pd.to_datetime(df["origination_date"], errors="coerce").dt.strftime("%Y%m%d")
            df["loan_uid"] = df["loan_id"].astype(str) + "_" + dates.fillna("00000000")
            logger.info("Generated composite loan_uid for %d records", len(df))

        # Special case for outstanding_balance -> current_balance
        if "outstanding_balance" in df.columns:
            if "current_balance" not in df.columns:
                df = df.rename(columns={"outstanding_balance": "current_balance"})
                logger.info("Renamed outstanding_balance to current_balance")
            else:
                # If both exist, use outstanding_balance if current_balance is mostly zero/null
                null_or_zero = df["current_balance"].isna() | (df["current_balance"] == 0)
                if null_or_zero.mean() > 0.8:  # If more than 80% are zero/null
                    df["current_balance"] = df["outstanding_balance"]
                    logger.info(
                        "Overwrote current_balance with outstanding_balance "
                        "(due to high null/zero rate)"
                    )

        return df

    @staticmethod
    def _collapse_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Coalesce duplicate-named columns by first non-null value per row."""
        if not df.columns.duplicated().any():
            return df

        collapsed: Dict[str, pd.Series] = {}
        ordered_names = list(dict.fromkeys(df.columns))
        for col in ordered_names:
            col_block = df.loc[:, df.columns == col]
            if isinstance(col_block, pd.Series):
                collapsed[col] = col_block
                continue

            merged = col_block.iloc[:, 0]
            for idx in range(1, col_block.shape[1]):
                candidate = col_block.iloc[:, idx]
                merged = merged.where(merged.notna(), candidate)
            collapsed[col] = merged

        return pd.DataFrame(collapsed, index=df.index)

    @staticmethod
    def _to_datetime_mixed(series: pd.Series) -> pd.Series:
        """Parse mixed-format date values with backward compatibility."""
        if isinstance(series, pd.DataFrame):
            base = series.iloc[:, 0]
            for idx in range(1, series.shape[1]):
                candidate = series.iloc[:, idx]
                base = base.where(base.notna(), candidate)
            series = base
        try:
            return pd.to_datetime(series, errors="coerce", dayfirst=True, format="mixed")
        except TypeError:
            return pd.to_datetime(series, errors="coerce", dayfirst=True)

    @staticmethod
    def _coerce_numeric_loose(series: pd.Series) -> pd.Series:
        """Coerce numeric-like values while tolerating currency/percent strings."""
        if isinstance(series, pd.DataFrame):
            base = series.iloc[:, 0]
            for idx in range(1, series.shape[1]):
                candidate = series.iloc[:, idx]
                base = base.where(base.notna(), candidate)
            series = base
        text = series.astype("string").str.strip()
        text = text.mask(text.isin({"", "nan", "none", "null", "missing"}), pd.NA)
        cleaned = text.str.replace(r"[^0-9,.\-]", "", regex=True)

        comma_only_mask = cleaned.str.contains(",", na=False) & ~cleaned.str.contains(
            r"\.", na=False
        )
        thousands_mask = comma_only_mask & cleaned.str.contains(r",\d{3}$", regex=True, na=False)
        decimal_comma_mask = comma_only_mask & ~thousands_mask

        if thousands_mask.any():
            cleaned.loc[thousands_mask] = cleaned.loc[thousands_mask].str.replace(
                ",", "", regex=False
            )
        if decimal_comma_mask.any():
            cleaned.loc[decimal_comma_mask] = cleaned.loc[decimal_comma_mask].str.replace(
                ",", ".", regex=False
            )
        other_mask = ~comma_only_mask
        if other_mask.any():
            cleaned.loc[other_mask] = cleaned.loc[other_mask].str.replace(",", "", regex=False)

        return pd.to_numeric(cleaned, errors="coerce")

    def _coalesce_datetime_columns(self, df: pd.DataFrame, candidates: List[str]) -> pd.Series:
        """Return first non-null datetime value across candidate columns."""
        series_list = [self._to_datetime_mixed(df[col]) for col in candidates if col in df.columns]
        if not series_list:
            return pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")

        merged = series_list[0]
        for candidate in series_list[1:]:
            merged = merged.where(merged.notna(), candidate)
        return merged

    def _coalesce_numeric_columns(self, df: pd.DataFrame, candidates: List[str]) -> pd.Series:
        """Return first non-null numeric value across candidate columns."""
        series_list = [
            self._coerce_numeric_loose(df[col]) for col in candidates if col in df.columns
        ]
        if not series_list:
            return pd.Series(np.nan, index=df.index, dtype=float)

        merged = series_list[0]
        for candidate in series_list[1:]:
            merged = merged.where(merged.notna(), candidate)
        return merged

    @staticmethod
    def _normalize_yes_no_flag(series: pd.Series) -> pd.Series:
        """Normalize mixed Y/N markers to strict {'Y','N', <NA>}."""
        if isinstance(series, pd.DataFrame):
            base = series.iloc[:, 0]
            for idx in range(1, series.shape[1]):
                candidate = series.iloc[:, idx]
                base = base.where(base.notna(), candidate)
            series = base
        normalized = series.astype(str).str.strip().str.upper()
        yes_values = {"Y", "YES", "SI", "S", "TRUE", "1"}
        no_values = {"N", "NO", "FALSE", "0"}
        out = pd.Series(pd.NA, index=series.index, dtype="object")
        out.loc[normalized.isin(yes_values)] = "Y"
        out.loc[normalized.isin(no_values)] = "N"
        return out

    def _derive_control_mora_fields(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Derive computed fields from CONTROL DE MORA data so KPI inputs are complete.

        Key derivations:
        - due_date from disbursement + term when due date is missing
        - dpd / days_past_due from as_of_date - due_date
        - collections_eligible from delinquency + exposure when source flag missing
        - utilization_pct from exposure / credit_line
        - government_sector from gov/ministry/issuer inference
        - last_payment_date / last_payment_amount / total_scheduled fallbacks
        """
        metrics: Dict[str, Any] = {"enabled": True, "fields_derived": {}}

        def track(field_name: str, mask: pd.Series) -> None:
            metrics["fields_derived"][field_name] = int(mask.fillna(False).sum())

        # 1) Origination / base dates
        inferred_origination = self._coalesce_datetime_columns(
            df,
            ["origination_date", "disbursement_date", "fecha_de_desembolso", "fechadesembolso"],
        )
        existing_origination = (
            self._to_datetime_mixed(df["origination_date"])
            if "origination_date" in df.columns
            else pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        )
        final_origination = existing_origination.where(
            existing_origination.notna(), inferred_origination
        )
        df["origination_date"] = final_origination
        track("origination_date", existing_origination.isna() & final_origination.notna())

        inferred_due = self._coalesce_datetime_columns(
            df,
            [
                "due_date",
                "fechapagoprogramado",
                "fecha_vencimiento",
                "fecha_de_vencimiento",
                "maturity_date",
            ],
        )
        existing_due = (
            self._to_datetime_mixed(df["due_date"])
            if "due_date" in df.columns
            else pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        )
        due_base = existing_due.where(existing_due.notna(), inferred_due)

        # 2) Term derivation from CONTROL DE MORA columns
        term_days = self._coalesce_numeric_columns(
            df,
            [
                "days_to_pay",
                "dias_en_pagar",
                "negotiation_days",
                "diasnegociacion",
                "dias_negociados_manual",
                "term_max",
                "term_ponderado",
                "apr__term__ponderado",
            ],
        )
        term_days = term_days.where((term_days > 0) & (term_days <= 720))

        raw_term_months = self._coalesce_numeric_columns(
            df, ["term_months", "plazo", "plazo_meses"]
        )
        raw_term_months = raw_term_months.where((raw_term_months > 0) & (raw_term_months <= 240))

        existing_term_months = (
            self._coerce_numeric_loose(df["term_months"])
            if "term_months" in df.columns
            else pd.Series(np.nan, index=df.index, dtype=float)
        )
        term_months_from_days = (term_days / 30.0).round(2)
        final_term_months = existing_term_months.where(
            existing_term_months.notna(), raw_term_months
        )
        final_term_months = final_term_months.where(
            (final_term_months > 0) & (final_term_months <= 240)
        )
        final_term_months = final_term_months.where(
            final_term_months.notna(), term_months_from_days
        )
        df["term_months"] = final_term_months
        track("term_months", existing_term_months.isna() & final_term_months.notna())

        # Payment frequency fallback for automation KPI.
        existing_freq_col = next(
            (c for c in ("payment_frequency", "frecuencia_pago", "tipo_pago") if c in df.columns),
            None,
        )
        if existing_freq_col is not None:
            existing_payment_frequency = (
                df[existing_freq_col]
                .astype(str)
                .str.strip()
                .str.lower()
                .replace({"": pd.NA, "nan": pd.NA, "none": pd.NA, "missing": pd.NA})
            )
        else:
            existing_payment_frequency = pd.Series(pd.NA, index=df.index, dtype="object")

        derived_payment_frequency = pd.Series("bullet", index=df.index, dtype="object")
        derived_payment_frequency.loc[term_days > 90] = "installment"
        disbursement_count = self._coalesce_numeric_columns(
            df, ["disbursement_count", "numerodesembolsos"]
        )
        derived_payment_frequency.loc[disbursement_count > 1] = "installment"

        payment_frequency_final = existing_payment_frequency.where(
            existing_payment_frequency.notna(), derived_payment_frequency
        )
        df["payment_frequency"] = payment_frequency_final
        track(
            "payment_frequency", existing_payment_frequency.isna() & payment_frequency_final.notna()
        )

        due_from_days = final_origination + pd.to_timedelta(
            term_days.round().astype("Int64"), unit="D"
        )
        due_from_months = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        month_offsets = raw_term_months.round().astype("Int64")
        for idx, month_val in month_offsets.dropna().items():
            if pd.notna(final_origination.loc[idx]):
                due_from_months.loc[idx] = final_origination.loc[idx] + pd.DateOffset(
                    months=int(month_val)
                )

        inferred_due_from_term = due_from_days.where(due_from_days.notna(), due_from_months)
        final_due = due_base.where(due_base.notna(), inferred_due_from_term)
        df["due_date"] = final_due
        track("due_date", due_base.isna() & final_due.notna())

        existing_maturity = (
            self._to_datetime_mixed(df["maturity_date"])
            if "maturity_date" in df.columns
            else pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        )
        final_maturity = existing_maturity.where(existing_maturity.notna(), final_due)
        df["maturity_date"] = final_maturity
        track("maturity_date", existing_maturity.isna() & final_maturity.notna())

        # 3) As-of date and DPD
        as_of_candidates = self._coalesce_datetime_columns(
            df,
            [
                "as_of_date",
                "snapshot_date",
                "measurement_date",
                "reporting_date",
                "fecha_actual",
                "fecha_corte",
                "fecha_de_corte",
                "data_ingest_ts",
            ],
        )
        existing_as_of = (
            self._to_datetime_mixed(df["as_of_date"])
            if "as_of_date" in df.columns
            else pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        )
        fallback_as_of = as_of_candidates.max()
        if pd.isna(fallback_as_of):
            fallback_as_of = pd.Timestamp.now(tz="UTC").normalize().tz_localize(None)
        final_as_of = existing_as_of.where(existing_as_of.notna(), as_of_candidates).fillna(
            fallback_as_of
        )
        df["as_of_date"] = final_as_of
        track("as_of_date", existing_as_of.isna() & final_as_of.notna())

        dpd_source = self._coalesce_numeric_columns(
            df,
            [
                "dpd",
                "days_past_due",
                "dias_vencido",
                "mora_en_dias",
                "dias_mora",
                "dias_de_mora",
                "dias_en_mora",
                "diias_mora_m",
                "dias_mora_m",
            ],
        ).where(lambda s: s >= 0)
        derived_dpd = (final_as_of - final_due).dt.days.astype(float).clip(lower=0)
        dpd_final = dpd_source.where(dpd_source.notna(), derived_dpd).fillna(0.0)
        df["dpd"] = dpd_final
        track("dpd", dpd_source.isna() & dpd_final.notna())

        if "days_past_due" in df.columns:
            existing_days_past_due = self._coerce_numeric_loose(df["days_past_due"])
            days_past_due = existing_days_past_due.where(existing_days_past_due.notna(), dpd_final)
        else:
            existing_days_past_due = pd.Series(np.nan, index=df.index, dtype=float)
            days_past_due = dpd_final
        df["days_past_due"] = days_past_due
        track("days_past_due", existing_days_past_due.isna() & days_past_due.notna())

        # 4) Collections eligibility
        raw_collections_col = next(
            (c for c in ("collections_eligible", "procede_a_cobrar") if c in df.columns), None
        )
        if raw_collections_col is not None:
            existing_collections = self._normalize_yes_no_flag(df[raw_collections_col])
        else:
            existing_collections = pd.Series(pd.NA, index=df.index, dtype="object")

        exposure = self._coalesce_numeric_columns(
            df,
            [
                "outstanding_balance",
                "current_balance",
                "amount",
                "principal_amount",
                "totalsaldovigente",
            ],
        ).fillna(0.0)
        status = df["status"].astype(str).str.strip().str.lower() if "status" in df.columns else ""
        derived_collections = pd.Series("N", index=df.index, dtype="object")
        delinquent_exposed = (dpd_final > 0) & (exposure > 0)
        if isinstance(status, pd.Series):
            delinquent_exposed = delinquent_exposed & (status != "closed")
        derived_collections.loc[delinquent_exposed] = "Y"

        collections_final = existing_collections.where(
            existing_collections.notna(), derived_collections
        )
        df["collections_eligible"] = collections_final
        track("collections_eligible", existing_collections.isna() & collections_final.notna())

        # 5) Utilization from exposure / credit line
        existing_util = self._coalesce_numeric_columns(
            df, ["utilization_pct", "porcentaje_utilizado"]
        )
        valid_existing_util = existing_util.where(existing_util >= 0)
        if valid_existing_util.dropna().median() < 2.0:
            valid_existing_util = valid_existing_util * 100

        credit_limit = self._coalesce_numeric_columns(
            df, ["credit_line", "lineacredito", "approved_value", "valoraprobado"]
        )
        derived_util = pd.Series(np.nan, index=df.index, dtype=float)
        valid_limit_mask = credit_limit > 0
        derived_util.loc[valid_limit_mask] = (
            exposure.loc[valid_limit_mask] / credit_limit.loc[valid_limit_mask] * 100
        )

        util_final = valid_existing_util.where(valid_existing_util.notna(), derived_util).clip(
            lower=0
        )
        df["utilization_pct"] = util_final
        track("utilization_pct", valid_existing_util.isna() & util_final.notna())

        # 6) Government/public classification
        existing_sector_col = next(
            (c for c in ("government_sector", "goes") if c in df.columns), None
        )
        if existing_sector_col is not None:
            existing_sector = df[existing_sector_col].astype(str).str.strip().str.upper()
            existing_sector = existing_sector.mask(
                existing_sector.isin({"", "NAN", "NONE", "NULL", "MISSING"}), pd.NA
            )
        else:
            existing_sector = pd.Series(pd.NA, index=df.index, dtype="object")

        gov_hint_col = next((c for c in ("gov", "ministry", "ministerio") if c in df.columns), None)
        if gov_hint_col is not None:
            gov_hint = df[gov_hint_col].astype(str).str.strip()
            gov_hint_upper = gov_hint.str.upper()
            hint_is_gov = ~gov_hint_upper.isin(
                {"", "NO", "NAN", "NONE", "NULL", "MISSING", "PRIVATE"}
            )
        else:
            hint_is_gov = pd.Series(False, index=df.index, dtype=bool)

        issuer_col = next((c for c in ("issuer_name", "emisor", "issuer") if c in df.columns), None)
        if issuer_col is not None:
            issuer_upper = df[issuer_col].astype(str).str.upper()
            keyword_pattern = (
                r"GOES|MINISTERIO|INSTITUTO|ALCALDIA|MUNICIPALIDAD|GOBIERNO|"
                r"ASAMBLEA|CORTE|AUTORIDAD|SUPERINTENDENCIA|PRESIDENCIA|PUBLIC"
            )
            issuer_is_gov = issuer_upper.str.contains(keyword_pattern, regex=True, na=False)
        else:
            issuer_is_gov = pd.Series(False, index=df.index, dtype=bool)

        sector_is_gov = existing_sector.fillna("").str.contains("GOES|GOV|PUBLIC", regex=True)
        derived_sector = pd.Series("PRIVATE", index=df.index, dtype="object")
        derived_sector.loc[hint_is_gov | issuer_is_gov | sector_is_gov] = "GOES"
        sector_final = existing_sector.where(existing_sector.notna(), derived_sector)
        df["government_sector"] = sector_final
        track("government_sector", existing_sector.isna() & sector_final.notna())

        # Keep gov as institution label where possible.
        if "gov" not in df.columns:
            df["gov"] = pd.NA
        gov_existing = df["gov"].astype(str).str.strip()
        gov_missing = gov_existing.isin({"", "nan", "None", "none", "missing", "NO", "No"})
        if gov_hint_col is not None:
            gov_fill = df[gov_hint_col].astype(str).str.strip()
            gov_fill_mask = (
                gov_missing & (gov_fill != "") & (~gov_fill.str.upper().isin({"NAN", "NONE"}))
            )
            df.loc[gov_fill_mask, "gov"] = gov_fill.loc[gov_fill_mask]
            track("gov", gov_fill_mask)
        else:
            track("gov", pd.Series(False, index=df.index, dtype=bool))

        # 7) Payment fields
        existing_last_payment_date = (
            self._to_datetime_mixed(df["last_payment_date"])
            if "last_payment_date" in df.columns
            else pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        )
        inferred_last_payment_date = self._coalesce_datetime_columns(
            df, ["payment_date", "fecha_de_pago", "fechacobro", "fecha_pago"]
        )
        final_last_payment_date = existing_last_payment_date.where(
            existing_last_payment_date.notna(), inferred_last_payment_date
        )
        df["last_payment_date"] = final_last_payment_date
        track(
            "last_payment_date",
            existing_last_payment_date.isna() & final_last_payment_date.notna(),
        )

        existing_last_payment_amount = (
            self._coerce_numeric_loose(df["last_payment_amount"])
            if "last_payment_amount" in df.columns
            else pd.Series(np.nan, index=df.index, dtype=float)
        )
        inferred_last_payment_amount = self._coalesce_numeric_columns(
            df,
            [
                "payment_amount",
                "_pagado",
                "monto_pagado",
                "total_payment_received",
                "montototalabonado",
                "capital_collected",
                "capitalcobrado",
            ],
        )
        final_last_payment_amount = existing_last_payment_amount.where(
            existing_last_payment_amount.notna(), inferred_last_payment_amount
        ).fillna(0.0)
        df["last_payment_amount"] = final_last_payment_amount
        track(
            "last_payment_amount",
            existing_last_payment_amount.isna() & final_last_payment_amount.notna(),
        )

        existing_total_scheduled = (
            self._coerce_numeric_loose(df["total_scheduled"])
            if "total_scheduled" in df.columns
            else pd.Series(np.nan, index=df.index, dtype=float)
        )
        inferred_total_scheduled = self._coalesce_numeric_columns(
            df, ["scheduled_amount", "total_due", "monto_programado"]
        )
        principal_base = self._coalesce_numeric_columns(
            df, ["principal_amount", "amount", "monto_del_desembolso", "montodesembolsado"]
        )
        monthly_from_term = pd.Series(np.nan, index=df.index, dtype=float)
        valid_term_days = term_days > 0
        monthly_from_term.loc[valid_term_days] = (
            principal_base.loc[valid_term_days] / term_days.loc[valid_term_days] * 30
        )
        inferred_total_scheduled = inferred_total_scheduled.where(
            inferred_total_scheduled.notna(), monthly_from_term
        )
        inferred_total_scheduled = inferred_total_scheduled.where(
            inferred_total_scheduled.notna(), final_last_payment_amount
        )
        final_total_scheduled = existing_total_scheduled.where(
            existing_total_scheduled.notna(), inferred_total_scheduled
        ).fillna(0.0)
        df["total_scheduled"] = final_total_scheduled
        track("total_scheduled", existing_total_scheduled.isna() & final_total_scheduled.notna())

        # 8) TPV fallback
        existing_tpv = pd.to_numeric(
            (
                self._coerce_numeric_loose(df["tpv"])
                if "tpv" in df.columns
                else pd.Series(np.nan, index=df.index, dtype=float)
            ),
            errors="coerce",
        ).astype(float)
        inferred_tpv = pd.to_numeric(
            self._coalesce_numeric_columns(
                df,
                [
                    "total_payment_received",
                    "montototalabonado",
                    "capital_collected",
                    "capitalcobrado",
                ],
            ),
            errors="coerce",
        ).astype(float)
        fill_tpv_mask = existing_tpv.isna() & inferred_tpv.notna()
        final_tpv = existing_tpv.copy()
        final_tpv.loc[fill_tpv_mask] = inferred_tpv.loc[fill_tpv_mask]
        final_tpv = final_tpv.fillna(0.0)
        df["tpv"] = final_tpv
        track("tpv", existing_tpv.isna() & final_tpv.notna())

        return df, metrics

    def _handle_nulls(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Handle missing values based on configured strategy.

        Strategies:
        - 'drop': Remove rows with any null values
        - 'fill': Fill nulls with configured default values
        - 'smart': Intelligent handling based on column type and null percentage

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (processed DataFrame, metrics dict)
        """
        logger.info("Handling null values (strategy: %s)", self.null_strategy)

        initial_nulls = df.isnull().sum()
        total_nulls = initial_nulls.sum()
        null_columns = initial_nulls[initial_nulls > 0].to_dict()

        if total_nulls == 0:
            logger.info("No null values found")
            return df, {"total_nulls": 0, "strategy_applied": "none", "columns_affected": []}

        metrics = self._create_null_metrics(total_nulls, null_columns)
        df, strategy_metrics = self._apply_null_strategy(df, null_columns)
        metrics.update(strategy_metrics)

        final_nulls = df.isnull().sum().sum()
        metrics["final_total_nulls"] = int(final_nulls)

        return df, metrics

    def _create_null_metrics(
        self, total_nulls: int, null_columns: Dict[str, int]
    ) -> Dict[str, Any]:
        """Create initial metrics for null handling."""
        return {
            "initial_total_nulls": int(total_nulls),
            "null_columns": null_columns,
            "strategy_applied": self.null_strategy,
            "columns_affected": list(null_columns.keys()),
        }

    def _apply_null_strategy(
        self, df: pd.DataFrame, null_columns: Dict[str, int]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply the configured null handling strategy using strategy dispatch."""
        strategy_handlers = {
            "drop": lambda: self._apply_drop_strategy(df),
            "fill": lambda: self._apply_fill_strategy(df),
            "smart": lambda: self._smart_null_handling(df, null_columns),
        }
        handler = strategy_handlers.get(self.null_strategy)
        if handler:
            return handler()
        return df, {}

    def _apply_drop_strategy(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply drop strategy for null handling."""
        rows_before = len(df)
        df = df.dropna()
        rows_dropped = rows_before - len(df)
        logger.info("Dropped %d rows with null values", rows_dropped)
        return df, {"rows_dropped": rows_dropped}

    def _apply_fill_strategy(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply fill strategy for null handling."""
        df = self._fill_nulls_by_type(df)
        logger.info("Filled null values with configured defaults")
        return df, {"fill_values_used": self.fill_values}

    def _fill_nulls_by_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill nulls based on column data type."""
        for col in df.columns:
            if df[col].isnull().any() and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(self.fill_values.get("numeric", 0))
            elif df[col].isnull().any():
                df[col] = df[col].fillna(self.fill_values.get("categorical", "unknown"))
        return df

    def _smart_null_handling(
        self, df: pd.DataFrame, null_columns: Dict[str, int]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Intelligent null handling based on null percentage and column importance.

        Uses configurable thresholds:
        - < LOW_NULL_THRESHOLD_PCT: Structural zero fill + boolean opacity flag
        - LOW to HIGH_NULL_THRESHOLD_PCT: Fill with missing indicator
        - > HIGH_NULL_THRESHOLD_PCT: Log warning, fill with default

        No mean/median imputation is ever applied to financial numeric columns.
        Opacity flags (``{col}_is_missing``) let downstream ML models learn from
        the absence of data rather than being misled by statistical substitutes.
        """
        total_rows = len(df)
        actions = self._process_null_columns(df, null_columns, total_rows)
        return df, {"smart_actions": actions}

    def _process_null_columns(
        self, df: pd.DataFrame, null_columns: Dict[str, int], total_rows: int
    ) -> Dict[str, str]:
        """Process null values for each column based on column type."""
        actions: Dict[str, str] = {}
        for col, null_count in null_columns.items():
            null_pct = null_count / total_rows * 100
            action = (
                self._handle_numeric_nulls(df, col, null_pct)
                if pd.api.types.is_numeric_dtype(df[col])
                else self._handle_categorical_nulls(df, col, null_pct)
            )
            actions[col] = action
        return actions

    def _handle_numeric_nulls(self, df: pd.DataFrame, col: str, null_pct: float) -> str:
        """Apply numeric null handling strategy for a column."""
        if col in self.FORCE_ZERO_NUMERIC_COLUMNS:
            df[col] = df[col].fillna(0)
            return "filled_zero (cashflow_semantics)"

        if null_pct < self.LOW_NULL_THRESHOLD_PCT:
            return self._fill_numeric_with_structural_zero(df, col)
        if null_pct < self.HIGH_NULL_THRESHOLD_PCT:
            return self._fill_numeric_with_indicator(df, col)
        return self._fill_numeric_with_zero(df, col, null_pct)

    def _fill_numeric_with_structural_zero(self, df: pd.DataFrame, col: str) -> str:
        """Fill numeric nulls with structural zero and add a boolean opacity flag.

        Implements the "structural zeros + opacity flag" pattern:
        - Null values are filled with 0 (structural zero, not a statistical estimate).
        - A boolean indicator column ``{col}_is_missing`` is added so that ML models
          can distinguish genuine zeros from imputed ones.

        This replaces median/mean imputation to avoid injecting statistical bias
        into financial data used for credit risk models.
        """
        null_mask = df[col].isna()
        flag_col = f"{col}_is_missing"
        df[flag_col] = null_mask
        df[col] = df[col].fillna(0)
        return f"filled_structural_zero+flag ({null_mask.sum()} nulls → {flag_col})"

    def _fill_numeric_with_indicator(self, df: pd.DataFrame, col: str) -> str:
        """Fill numeric nulls with missing indicator."""
        df[col] = df[col].fillna(self.MISSING_NUMERIC_INDICATOR)
        return f"filled_missing_indicator ({self.MISSING_NUMERIC_INDICATOR})"

    def _fill_numeric_with_zero(self, df: pd.DataFrame, col: str, null_pct: float) -> str:
        """Fill numeric nulls with zero for high null percentage columns."""
        if null_pct > 99.5:
            # For columns that are effectively all-null (like Pledge Date in some feeds),
            # do not fill with 0 as it corrupts downstream logic. Keep as NaN.
            return f"skipped_zero_fill (null_pct={null_pct:.1f}% > 99.5%)"

        df[col] = df[col].fillna(0)
        if col in self.HIGH_NULL_WARNING_NUMERIC_COLUMNS:
            logger.warning("Column '%s' has %.1f%% nulls", col, null_pct)
        return f"filled_zero (high_null: {null_pct:.1f}%)"

    def _handle_categorical_nulls(self, df: pd.DataFrame, col: str, null_pct: float) -> str:
        """Apply categorical null handling strategy for a column."""
        if null_pct < self.LOW_NULL_THRESHOLD_PCT:
            return self._fill_categorical_with_mode(df, col)
        return self._fill_categorical_with_missing(df, col)

    def _fill_categorical_with_mode(self, df: pd.DataFrame, col: str) -> str:
        """Fill categorical nulls with mode value."""
        mode_val = df[col].mode()
        fill_val = mode_val.iloc[0] if len(mode_val) > 0 else "unknown"
        df[col] = df[col].fillna(fill_val)
        return f"filled_mode ({fill_val})"

    def _fill_categorical_with_missing(self, df: pd.DataFrame, col: str) -> str:
        """Fill categorical nulls with missing label."""
        df[col] = df[col].fillna("missing")
        return "filled_missing_label"

    def _normalize_types(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Normalize data types for consistency.

        - Convert date strings to datetime
        - Ensure numeric columns are proper numeric types
        - Standardize string formats (lowercase status, etc.)

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (processed DataFrame, metrics dict)
        """
        logger.info("Normalizing data types")

        if not self.type_normalization_enabled:
            return df, {"enabled": False}

        conversions: Dict[str, Dict[str, str]] = {}

        self._normalize_date_columns(df, conversions)
        self._normalize_numeric_columns(df, conversions)
        self._normalize_status_column(df, conversions)

        metrics = {
            "enabled": True,
            "conversions_applied": len(conversions),
            "conversion_details": conversions,
        }

        logger.info("Applied %d type conversions", len(conversions))
        return df, metrics

    def _normalize_date_columns(
        self, df: pd.DataFrame, conversions: Dict[str, Dict[str, str]]
    ) -> None:
        """Normalize date columns to datetime."""
        for col in df.columns:
            if (col in self.DATE_COLUMNS or col.endswith("_date")) and (
                pd.api.types.is_string_dtype(df[col]) or df[col].dtype == "object"
            ):
                try:
                    df[col] = pd.to_datetime(df[col], format=self.date_format, errors="coerce")
                    conversions[col] = {"from": "string", "to": "datetime64"}
                except Exception as e:
                    logger.warning("Could not convert %s to datetime: %s", col, e)

    def _normalize_numeric_columns(
        self, df: pd.DataFrame, conversions: Dict[str, Dict[str, str]]
    ) -> None:
        """Normalize numeric columns to numeric dtype."""
        for col in df.columns:
            is_numeric_name = col in self.NUMERIC_COLUMNS or self.NUMERIC_NAME_PATTERN.search(col)
            is_string_obj = pd.api.types.is_string_dtype(df[col]) or df[col].dtype == "object"

            # Explicitly exclude 'country' which contains 'count' but is categorical
            if is_numeric_name and "country" not in col.lower() and is_string_obj:
                try:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    conversions[col] = {"from": "string", "to": "numeric"}
                except Exception as e:
                    logger.warning("Could not convert %s to numeric: %s", col, e)

    def _normalize_status_column(
        self, df: pd.DataFrame, conversions: Dict[str, Dict[str, str]]
    ) -> None:
        """Normalize status values to standardized labels."""
        if "status" not in df.columns:
            return
        original_values = df["status"].unique().tolist()
        df["status"] = df["status"].map(
            lambda x: self.STATUS_MAPPINGS.get(x, str(x).lower() if pd.notna(x) else x)
        )
        conversions["status"] = {"normalized_values": original_values}

    def _apply_business_rules(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Apply business rules from configuration.

        Applies:
        - Status mappings and validations
        - DPD bucket assignments
        - Risk categorization
        - Custom field derivations
        - Automated Government Entity Identification

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (processed DataFrame, metrics dict)
        """
        logger.info("Applying business rules")

        rules_applied: List[str] = []
        fields_created: List[str] = []

        self._automate_gov_identification(df, rules_applied, fields_created)
        self._automate_doc_type_identification(df, rules_applied, fields_created)
        self._normalize_interest_rate(df, rules_applied)
        self._normalize_equifax_score(df, rules_applied)
        self._enforce_non_negative_balances(df, rules_applied)
        self._apply_dpd_bucket_rule(df, rules_applied, fields_created)
        self._apply_risk_category_rule(df, rules_applied, fields_created)
        self._apply_amount_tier_rule(df, rules_applied, fields_created)
        self._apply_custom_rules(df, rules_applied)

        metrics = {
            "rules_applied": len(rules_applied),
            "rule_names": rules_applied,
            "fields_created": fields_created,
        }

        logger.info("Applied %d business rules", len(rules_applied))
        return df, metrics

    def _automate_gov_identification(
        self, df: pd.DataFrame, rules_applied: List[str], fields_created: List[str]
    ) -> None:
        """
        Identify government and industry segments from 'emisor' (Pagador).
        Synchronizes 'gov', 'industry', and 'government_sector' (GOES flag).
        """
        # Determine source columns
        pagador_col = next(
            (c for c in ("emisor", "issuer_name", "issuer") if c in df.columns), None
        )
        goes_source = next((c for c in ("government_sector", "goes") if c in df.columns), None)

        if not pagador_col:
            return

        # Ensure columns exist
        for col in ["gov", "industry"]:
            if col not in df.columns:
                df[col] = "No" if col == "gov" else "Other"
                fields_created.append(col)

        if "government_sector" not in df.columns:
            df["government_sector"] = "PRIVATE"
            fields_created.append("government_sector")

        # --- 1. Government Identification ---
        gov_keywords = [
            "MINISTERIO",
            "INSTITUTO",
            "COMISION",
            "PROCURADURIA",
            "ALCALDIA",
            "MUNICIPALIDAD",
            "GOBIERNO",
            "ASAMBLEA",
            "CORTE",
            "ORGANO",
            "CONSEJO",
            "FONDO",
            "BANCO CENTRAL",
            "FISCALIA",
            "DEFENSORIA",
            "UNIVERSIDAD",
            "LOTERIA",
            "VICEPRESIDENCIA",
            "PRESIDENCIA",
            "AUTORIDAD",
            "SUPERINTENDENCIA",
            "CENTRO NACIONAL",
            "INSAFOR",
            "INCAF",
            "ANDA",
            "SIGET",
            "GOES",
        ]
        gov_pattern = "|".join(gov_keywords)

        # Identify by keywords or existing flag
        keyword_gov_mask = (
            df[pagador_col].astype(str).str.upper().str.contains(gov_pattern, na=False)
        )
        existing_goes_mask = (
            (df[goes_source].astype(str).str.upper().str.strip() == "GOES")
            if goes_source
            else pd.Series(False, index=df.index)
        )
        is_gov_mask = keyword_gov_mask | existing_goes_mask

        # --- 2. Industry Identification (Heuristic) ---
        industry_map = {
            "Retail": "TIENDA|SUPERMERCADO|BOUTIQUE|COMERCIAL|ALMACEN|DISTRIBUIDORA|RETAIL|VENTA|ABARROTES",
            "Services": "SERVICIOS|CONSULTOR|SOLUCION|ASESORIA|LIMPIEZA|MANTENIMIENTO|SEGURIDAD|HOTEL|RESTAURANTE|GASTRONOMIA",
            "Manufacturing": "INDUSTRIA|FABRICA|MANUFACTURA|TEXTIL|ALIMENTO|PLASTICO|QUIMICA|METAL|PRODUCCION",
            "Logistics": "TRANSPORTE|LOGISTICA|CARGA|ADUANA|MUDANZA|ENVIO|COURIER|PUERTO",
            "Tech": "TECNOLOGIA|SOFTWARE|SISTEMA|DIGITAL|IT|INFORMATICA|DESARROLLO",
            "Financial": "BANCO|FINANCIER|SEGURO|CREDITO|COOPERATIVA|AHORRO|BOLSA",
            "Construction": "CONSTRUCCION|INGENIERIA|EDIFIC|OBRA|PROYECTO|ARQUITECT",
            "Healthcare": "HOSPITAL|CLINICA|MEDIC|SALUD|FARMACIA|DIAGNOSTICO|LABORATORIO",
        }

        # Determine which rows need automated tagging
        needs_gov_name = is_gov_mask & df["gov"].astype(str).str.lower().isin(
            ["", "no", "nan", "none", "missing"]
        )
        needs_industry = (
            df["industry"]
            .astype(str)
            .str.lower()
            .isin(["", "other", "nan", "none", "missing", "unknown"])
        )

        # Apply Gov tagging
        df.loc[needs_gov_name, "gov"] = df.loc[needs_gov_name, pagador_col]
        df.loc[is_gov_mask, "government_sector"] = "GOES"
        df.loc[is_gov_mask, "industry"] = "Government"  # Gov is also an industry segment

        # Apply Industry tagging for non-government entities
        if not is_gov_mask.all():
            for industry, pattern in industry_map.items():
                match_mask = (
                    ~is_gov_mask
                    & needs_industry
                    & df[pagador_col].astype(str).str.upper().str.contains(pattern, na=False)
                )
                df.loc[match_mask, "industry"] = industry

        # Final Fallbacks
        df.loc[
            ~is_gov_mask & df["gov"].astype(str).str.lower().isin(["", "nan", "none", "missing"]),
            "gov",
        ] = "No"
        df.loc[~is_gov_mask, "government_sector"] = "PRIVATE"

        rules_applied.append("automated_gov_and_industry_identification")
        logger.info(
            "Automated Gov and Industry identification applied based on column: %s", pagador_col
        )

    def _automate_doc_type_identification(
        self, df: pd.DataFrame, rules_applied: List[str], fields_created: List[str]
    ) -> None:
        """
        Identify document types (Factura, Quedan, CCF, DTE, etc.) from multiple metadata columns.
        """
        if "doc_type" not in df.columns:
            df["doc_type"] = "Other"
            fields_created.append("doc_type")

        # Candidate columns for identifying document types
        # 1. numeroquedan (highly descriptive)
        # 2. oc (Purchase Order indicators)
        # 3. numerointerno (Prefixes)
        candidates = ["numeroquedan", "oc", "numerointerno"]

        doc_map = {
            "Quedan": r"QUEDAN|^Q/|^QF/|^Q\d",
            "CCF": r"CCF|CREDITO FISCAL",
            "DTE": r"DTE|ELECTRONIC",
            "Factura": r"FACTURA|^FAC|^F\d|COMPROBANTE",
            "Factura Export": r"EXPORT|EXP\d",
            "Purchase Order": r"PO|OC|PURCHASE|ORDEN",
        }

        # Apply heuristics across all candidate columns
        for doc_label, pattern in doc_map.items():
            for col in candidates:
                if col in df.columns:
                    mask = (
                        df[col].astype(str).str.upper().str.contains(pattern, na=False, regex=True)
                    )
                    # Only update if current doc_type is 'Other' or blank
                    # This gives precedence to early matches in doc_map order
                    needs_update = (
                        df["doc_type"]
                        .astype(str)
                        .str.lower()
                        .isin(["", "other", "unknown", "nan", "none"])
                    )
                    df.loc[mask & needs_update, "doc_type"] = doc_label

        rules_applied.append("automated_doc_type_identification")
        logger.info("Automated Document Type identification applied.")

    def _enforce_non_negative_balances(self, df: pd.DataFrame, rules_applied: List[str]) -> None:
        """Clip negative balances to zero to keep exposure semantics consistent."""
        affected = 0
        for col in ("outstanding_balance", "current_balance"):
            if col not in df.columns:
                continue
            series = pd.to_numeric(df[col], errors="coerce")
            negative_mask = series < 0
            negative_count = int(negative_mask.sum())
            if negative_count > 0:
                df[col] = series.clip(lower=0)
                affected += negative_count
        if affected > 0:
            logger.info("Clipped %d negative balance values to zero", affected)
            rules_applied.append("non_negative_balance_enforcement")

    def _normalize_interest_rate(self, df: pd.DataFrame, rules_applied: List[str]) -> None:
        """Normalize interest_rate to annual decimal based on data semantics.

        Abaco factoring data stores interest_rate as a monthly percentage
        (e.g. 0.65 means 0.65 %/month).  The KPI formula ``AVG(interest_rate)
        * 100`` expects an annual decimal (e.g. 0.0775 → 7.75 %).

        Detection heuristic:
        - If median rate < 5 **and** median term < 6 months, the rates are
          monthly percentages → annualize (× 12) then divide by 100.
        - If median rate > 1, rates look like whole-number percentages
          → divide by 100.
        - Otherwise, assume already annual decimal — no conversion.
        """
        if "interest_rate" not in df.columns:
            return

        rates = pd.to_numeric(df["interest_rate"], errors="coerce")
        valid = rates.dropna()
        if valid.empty:
            return

        median_rate = valid.median()

        # Determine median term length (months)
        median_term = None
        if "term_months" in df.columns:
            terms = pd.to_numeric(df["term_months"], errors="coerce").dropna()
            if not terms.empty:
                median_term = terms.median()

        if 0.2 <= median_rate < 5 and median_term is not None and median_term < 6:
            # Monthly percentage rates (factoring): annualize and
            # convert to decimal so AVG * 100 gives correct annual %.
            df["interest_rate"] = rates * 12 / 100
            logger.info(
                "Normalized interest_rate: monthly %% → annual decimal "
                "(median %.4f%%/mo → %.4f annual)",
                median_rate,
                median_rate * 12 / 100,
            )
            rules_applied.append("interest_rate_monthly_pct_to_annual")
        elif median_rate > 1:
            # Whole-number percentage (e.g. 24.5 meaning 24.5% annual)
            df["interest_rate"] = rates / 100
            logger.info(
                "Normalized interest_rate: whole %% → annual decimal " "(median %.2f%% → %.4f)",
                median_rate,
                median_rate / 100,
            )
            rules_applied.append("interest_rate_pct_to_decimal")
        else:
            logger.info(
                "interest_rate appears to be annual decimal already "
                "(median=%.4f); no conversion applied",
                median_rate,
            )

    def _apply_dpd_bucket_rule(
        self, df: pd.DataFrame, rules_applied: List[str], fields_created: List[str]
    ) -> None:
        """Apply DPD bucket assignment."""
        if "dpd" not in df.columns:
            return

        # Ensure dpd column is numeric (handle both float and Decimal types)
        if not pd.api.types.is_numeric_dtype(df["dpd"]):
            df["dpd"] = pd.to_numeric(df["dpd"], errors="coerce")

        df["dpd_bucket"] = pd.cut(
            df["dpd"],
            bins=[-np.inf, -0.001, 0.001, 30, 60, 90, 180, np.inf],
            labels=["unknown", "current", "1-29", "30-59", "60-89", "90-179", "180+"],
            include_lowest=True,
        ).astype(str)
        df.loc[df["dpd"].isna(), "dpd_bucket"] = "unknown"
        fields_created.append("dpd_bucket")
        rules_applied.append("dpd_bucket_assignment")

    def _apply_risk_category_rule(
        self, df: pd.DataFrame, rules_applied: List[str], fields_created: List[str]
    ) -> None:
        """Apply risk categorization rule."""
        if "status" in df.columns and "dpd" in df.columns:
            df["risk_category"] = df.apply(self._calculate_risk_category, axis=1)
            fields_created.append("risk_category")
            rules_applied.append("risk_categorization")

    def _apply_amount_tier_rule(
        self, df: pd.DataFrame, rules_applied: List[str], fields_created: List[str]
    ) -> None:
        """Apply amount tier classification rule."""
        if "amount" not in df.columns:
            return
        self._categorize_amount_tiers(df)
        self._record_applied_rule(rules_applied, fields_created)

    def _record_applied_rule(self, rules_applied: List[str], fields_created: List[str]) -> None:
        """Record that amount tier rule was applied."""
        fields_created.append("amount_tier")
        rules_applied.append("amount_tier_classification")

    def _categorize_amount_tiers(self, df: pd.DataFrame) -> None:
        """Categorize amounts into tiers using binning."""
        # Ensure amount column is numeric (handle both float and Decimal types)
        if not pd.api.types.is_numeric_dtype(df["amount"]):
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

        df["amount_tier"] = pd.cut(
            df["amount"],
            bins=[-np.inf, 0, 5000, 25000, 100000, 500000, np.inf],
            labels=["invalid", "micro", "small", "medium", "large", "jumbo"],
            right=False,
        ).astype(str)
        df.loc[df["amount"].isna(), "amount_tier"] = "invalid"

    def _apply_custom_rules(self, df: pd.DataFrame, rules_applied: List[str]) -> None:
        """Apply custom business rules from configuration."""
        custom_rules = self.business_rules.get("transformations", [])
        for rule in custom_rules:
            try:
                df, success = self._apply_custom_rule(df, rule)
                if success:
                    rules_applied.append(rule.get("name", "unnamed_rule"))
            except Exception as e:
                logger.warning("Failed to apply custom rule: %s", e)

    def _normalize_equifax_score(self, df: pd.DataFrame, rules_applied: List[str]) -> None:
        """Treat Equifax sentinel values as missing data for downstream analytics."""
        col = "Equifax Score"
        if col not in df.columns:
            return

        numeric_score = pd.to_numeric(df[col], errors="coerce")
        has_sentinel = bool((numeric_score == self.MISSING_NUMERIC_INDICATOR).any())
        if has_sentinel and f"{col}_raw" not in df.columns:
            df[f"{col}_raw"] = numeric_score
        if has_sentinel:
            df[col] = numeric_score.replace(self.MISSING_NUMERIC_INDICATOR, np.nan)
            rules_applied.append("equifax_missing_indicator_to_nan")

    def _assign_dpd_bucket(self, dpd: float) -> str:
        """Assign DPD (Days Past Due) bucket."""
        if pd.isna(dpd) or dpd < 0:
            bucket = "unknown"
        elif dpd == 0:
            bucket = "current"
        elif dpd < 30:
            bucket = "1-29"
        elif dpd < 60:
            bucket = "30-59"
        elif dpd < 90:
            bucket = "60-89"
        elif dpd < 180:
            bucket = "90-179"
        else:
            bucket = "180+"
        return bucket

    def _calculate_risk_category(self, row: pd.Series) -> str:
        """Calculate risk category based on status and DPD."""
        status = row.get("status", "")
        dpd = row.get("dpd", 0)

        if status == "defaulted":
            category = "critical"
        elif status == "delinquent" or (pd.notna(dpd) and dpd >= 90):
            category = "high"
        elif pd.notna(dpd) and dpd >= 30:
            category = "medium"
        elif status == "active" and (pd.isna(dpd) or dpd < 30):
            category = "low"
        else:
            category = "unknown"
        return category

    def _assign_amount_tier(self, amount: float) -> str:
        """Assign loan amount tier."""
        if pd.isna(amount) or amount <= 0:
            tier = "invalid"
        elif amount < 5000:
            tier = "micro"
        elif amount < 25000:
            tier = "small"
        elif amount < 100000:
            tier = "medium"
        elif amount < 500000:
            tier = "large"
        else:
            tier = "jumbo"
        return tier

    def _apply_custom_rule(
        self, df: pd.DataFrame, rule: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, bool]:
        """
        Apply a custom business rule from configuration.

        Note: Only safe operations (column_mapping) are fully supported.
        Derived field expressions are restricted to simple arithmetic operations.

        Returns:
            Tuple of (DataFrame, success_flag) where success_flag indicates if rule was applied.
        """
        rule_type = rule.get("type")

        if rule_type == "column_mapping":
            return self._apply_column_mapping_rule(df, rule)
        if rule_type == "derived_field":
            return self._apply_derived_field_rule(df, rule)

        return df, False

    def _apply_column_mapping_rule(
        self, df: pd.DataFrame, rule: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, bool]:
        """Apply a column mapping custom rule."""
        source_col = rule.get("source_column")
        target_col = rule.get("target_column")
        mapping = rule.get("mapping", {})
        if source_col and target_col and source_col in df.columns:
            df[target_col] = df[source_col].map(mapping).fillna(df[source_col])
            return df, True

        logger.warning(
            "Invalid column_mapping rule configuration or missing source column: "
            f"source_column={source_col!r}, target_column={target_col!r}"
        )
        return df, False

    def _apply_derived_field_rule(
        self, df: pd.DataFrame, rule: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, bool]:
        """Apply a derived field custom rule with safety checks."""
        target_col = rule.get("target_column")
        expression = rule.get("expression", "")
        if not expression or not target_col:
            return df, False

        if not self._is_safe_expression(expression):
            return df, False

        try:
            df[target_col] = df.eval(expression)
            return df, True
        except Exception as e:
            logger.warning("Failed to evaluate expression '%s': %s", expression, e)
            return df, False

    def _is_safe_expression(self, expression: str) -> bool:
        """Validate that an expression is safe for pandas eval."""
        if not self._check_allowed_chars(expression):
            return False
        return not self._check_dangerous_patterns(expression)

    def _check_allowed_chars(self, expression: str) -> bool:
        """Verify expression contains only allowed characters."""
        allowed_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-*/(). "
        )
        if not all(c in allowed_chars for c in expression):
            logger.warning("Unsafe characters in expression '%s', skipping rule", expression)
            return False
        return True

    def _check_dangerous_patterns(self, expression: str) -> bool:
        """Check for dangerous patterns in expression."""
        dangerous_patterns = [
            "import",
            "exec",
            "eval",
            "compile",
            "__import__",
            "__builtins__",
            "__class__",
            "__getattr__",
            "__setattr__",
            "open",
            "file",
        ]
        expression_lower = expression.lower()
        if any(pattern in expression_lower for pattern in dangerous_patterns):
            logger.warning(
                "Dangerous pattern detected in expression '%s', skipping rule", expression
            )
            return True
        return False

    def _detect_outliers(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Detect and flag outliers in numeric columns.

        Methods:
        - 'iqr': Interquartile Range method
        - 'zscore': Z-score method

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (processed DataFrame with outlier flags, metrics dict)
        """
        logger.info("Detecting outliers (method: %s)", self.outlier_method)

        if not self.outlier_enabled:
            return df, {"enabled": False}

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        skip_cols = {"loan_id", "id", "dpd"}
        check_cols = [col for col in numeric_cols if col not in skip_cols]

        df, outlier_counts, total_outlier_rows = self._flag_outliers(df, check_cols)
        metrics = self._create_outlier_metrics(check_cols, outlier_counts, total_outlier_rows)

        return df, metrics

    def _flag_outliers(
        self, df: pd.DataFrame, check_cols: List[str]
    ) -> Tuple[pd.DataFrame, Dict[str, int], int]:
        """Detect and flag outliers in specified columns."""
        outlier_counts: Dict[str, int] = {}
        outlier_flags: Dict[str, pd.Series] = {}
        any_outlier_mask = pd.Series(False, index=df.index, dtype=bool)

        for col in check_cols:
            outliers = (
                self._detect_outliers_iqr(df[col])
                if self.outlier_method == "iqr"
                else self._detect_outliers_zscore(df[col])
            )
            outlier_count = outliers.sum()
            if outlier_count > 0:
                outlier_counts[col] = int(outlier_count)
                outlier_flags[f"{col}_outlier"] = outliers.fillna(False).astype(bool)
                any_outlier_mask = any_outlier_mask | outlier_flags[f"{col}_outlier"]
                logger.info("Found %d outliers in column '%s'", int(outlier_count), col)

        if outlier_flags:
            # Add all outlier flag columns in one shot to avoid DataFrame fragmentation.
            flags_df = pd.DataFrame(outlier_flags, index=df.index)
            df = pd.concat([df, flags_df], axis=1)

        return df, outlier_counts, int(any_outlier_mask.sum())

    def _create_outlier_metrics(
        self,
        check_cols: List[str],
        outlier_counts: Dict[str, int],
        total_outlier_rows: int,
    ) -> Dict[str, Any]:
        """Create metrics dictionary for outlier detection results."""
        return {
            "enabled": True,
            "method": self.outlier_method,
            "threshold": self.outlier_threshold,
            "columns_checked": len(check_cols),
            "outliers_detected": outlier_counts,
            "total_outlier_rows": total_outlier_rows,
        }

    def _detect_outliers_iqr(self, series: pd.Series) -> pd.Series:
        """Detect outliers using IQR method."""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        # Handle edge case where there is no spread in the data; avoid flagging
        # any tiny deviation as an outlier when Q1 == Q3.
        if IQR == 0 or np.isclose(IQR, 0):
            return pd.Series([False] * len(series), index=series.index)
        lower_bound = Q1 - self.outlier_threshold * IQR
        upper_bound = Q3 + self.outlier_threshold * IQR
        return ((series < lower_bound) | (series > upper_bound)).fillna(False)

    def _detect_outliers_zscore(self, series: pd.Series) -> pd.Series:
        """Detect outliers using Z-score method."""
        # Work on non-null values to avoid NaN propagation in statistics and flags
        non_null = series.dropna()

        # If there are no non-null values or no variation, there can be no outliers
        if non_null.empty or non_null.std() == 0:
            return pd.Series(False, index=series.index)

        mean = non_null.mean()
        std = non_null.std()

        z_scores = np.abs((non_null - mean) / std)
        outliers_non_null = z_scores > self.outlier_threshold

        # Initialize all values as non-outliers and set only non-null outliers to True
        outliers = pd.Series(False, index=series.index)
        outliers.loc[non_null.index] = outliers_non_null.fillna(False)
        return outliers

    def _check_referential_integrity(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Check referential integrity across entities.

        Validates:
        - Unique identifiers are actually unique
        - Foreign key relationships are valid
        - Required relationships exist

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (DataFrame, integrity metrics)
        """
        logger.info("Checking referential integrity")

        integrity_issues: List[Dict[str, Any]] = []
        self._check_primary_key_integrity(df, integrity_issues)
        self._check_foreign_key_integrity(df, integrity_issues)
        self._check_date_consistency(df, integrity_issues)
        self._check_positive_amounts(df, integrity_issues)

        metrics = {
            "checks_performed": 4,
            "issues_found": len(integrity_issues),
            "issues": integrity_issues,
            "integrity_status": "pass" if len(integrity_issues) == 0 else "warning",
        }

        if integrity_issues:
            logger.warning("Found %d referential integrity issues", len(integrity_issues))
        else:
            logger.info("Referential integrity checks passed")

        return df, metrics

    def _check_primary_key_integrity(
        self, df: pd.DataFrame, integrity_issues: List[Dict[str, Any]]
    ) -> None:
        """Check for duplicate primary keys (loan_uid)."""
        # Use loan_uid if available, fallback to loan_id
        pk_col = "loan_uid" if "loan_uid" in df.columns else "loan_id"

        if pk_col not in df.columns:
            return

        duplicates = df[pk_col].duplicated().sum()
        if duplicates > 0:
            integrity_issues.append(
                {
                    "type": "duplicate_primary_key",
                    "column": pk_col,
                    "count": int(duplicates),
                }
            )
            logger.warning("Found %d duplicate %s values", duplicates, pk_col)

    def _check_foreign_key_integrity(
        self, df: pd.DataFrame, integrity_issues: List[Dict[str, Any]]
    ) -> None:
        """Check for orphan records with null foreign keys."""
        if "borrower_id" not in df.columns:
            return

        null_borrowers = df["borrower_id"].isnull().sum()
        if null_borrowers > 0:
            integrity_issues.append(
                {
                    "type": "null_foreign_key",
                    "column": "borrower_id",
                    "count": int(null_borrowers),
                }
            )

    def _check_date_consistency(
        self, df: pd.DataFrame, integrity_issues: List[Dict[str, Any]]
    ) -> None:
        """Check date consistency (due_date should not be before origination_date)."""
        date_cols = [col for col in df.columns if col.endswith("_date")]
        has_both_dates = (
            "origination_date" in date_cols
            and "due_date" in date_cols
            and df["origination_date"].dtype == "datetime64[ns]"
            and df["due_date"].dtype == "datetime64[ns]"
        )

        if not has_both_dates:
            return

        valid_mask = df["due_date"].notna() & df["origination_date"].notna()
        invalid_dates = (
            df.loc[valid_mask, "due_date"] < df.loc[valid_mask, "origination_date"]
        ).sum()
        if invalid_dates > 0:
            integrity_issues.append(
                {
                    "type": "invalid_date_sequence",
                    "description": "due_date before origination_date",
                    "count": int(invalid_dates),
                }
            )

    def _check_positive_amounts(
        self, df: pd.DataFrame, integrity_issues: List[Dict[str, Any]]
    ) -> None:
        """Check for negative amounts in columns that should be positive."""
        positive_cols = ["amount", "current_balance", "original_amount"]
        for col in positive_cols:
            if col not in df.columns:
                continue

            valid_values = df[col].dropna()
            negative_count = (valid_values < 0).sum()
            if negative_count > 0:
                integrity_issues.append(
                    {
                        "type": "negative_value",
                        "column": col,
                        "count": int(negative_count),
                    }
                )
