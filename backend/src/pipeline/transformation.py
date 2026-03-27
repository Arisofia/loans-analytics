import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from backend.python.logging_config import get_logger

logger = get_logger(__name__)
DATETIME64_NS_DTYPE = "datetime64[ns]"


class TransformationPhase:
    _PII_COLUMN_RE = re.compile(
        "\\b(name|nombre|apellido|surname|email|phone|telefono|celular|ssn|cedula|dni|passport|pasaporte|address|direccion|rfc|curp|nss|cuenta|account)\\b",
        re.IGNORECASE,
    )
    NUMERIC_COLUMNS: Set[str] = {
        "amount",
        "current_balance",
        "original_amount",
        "interest_rate",
        "dpd",
        "payment_amount",
    }
    NUMERIC_NAME_PATTERN = re.compile(
        "(^|[_\\s])(amount|balance|rate|count|dpd)([_\\s]|$)", re.IGNORECASE
    )
    DATE_COLUMNS: Set[str] = {
        "disbursement_date",
        "origination_date",
        "due_date",
        "payment_date",
        "measurement_date",
    }
    STATUS_MAPPINGS: Dict[str, str] = {
        "active": "active",
        "current": "active",
        "activo": "active",
        "vigente": "active",
        "al_dia": "active",
        "al dia": "active",
        "delinquent": "delinquent",
        "moroso": "delinquent",
        "en_mora": "delinquent",
        "en mora": "delinquent",
        "complete": "closed",
        "closed": "closed",
        "paid": "closed",
        "paid_off": "closed",
        "paid off": "closed",
        "cancelled": "closed",
        "canceled": "closed",
        "liquidated": "closed",
        "cerrado": "closed",
        "liquidado": "closed",
        "cancelado": "closed",
        "default": "defaulted",
        "defaulted": "defaulted",
        "charged_off": "defaulted",
        "charge_off": "defaulted",
        "written_off": "defaulted",
        "incumplimiento": "defaulted",
        "en_incumplimiento": "defaulted",
        "en incumplimiento": "defaulted",
        "vencido": "defaulted",
        "castigado": "defaulted",
    }
    LOW_NULL_THRESHOLD_PCT: float = 5.0
    HIGH_NULL_THRESHOLD_PCT: float = 30.0
    MISSING_NUMERIC_INDICATOR: int = -999
    FORCE_ZERO_NUMERIC_COLUMNS: Set[str] = {
        "last_payment_amount",
        "payment_amount",
        "recovery_value",
    }
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
    STRUCTURAL_EMPTY_MARKERS: Set[str] = {"", "nan", "none", "null", "missing", "n/a"}
    STRUCTURAL_KEY_COLUMNS: Tuple[str, ...] = (
        "loan_id",
        "borrower_id",
        "amount",
        "principal_amount",
        "status",
        "current_balance",
        "outstanding_balance",
        "dpd",
        "days_past_due",
    )

    def __init__(self, config: Dict[str, Any], business_rules: Optional[Dict[str, Any]] = None):
        self.config = config
        self.business_rules = business_rules or {}
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
        logger.info("Starting Phase 2: Transformation")
        try:
            return self._execute_transformation(raw_data_path=raw_data_path, df=df, run_dir=run_dir)
        except Exception as e:
            logger.error("Transformation failed: %s", str(e), exc_info=True)
            raise ValueError(f"CRITICAL: Transformation phase failed: {e}") from e

    def _execute_transformation(
        self, raw_data_path: Optional[Path], df: Optional[pd.DataFrame], run_dir: Optional[Path]
    ) -> Dict[str, Any]:
        df = self._resolve_input_dataframe(raw_data_path=raw_data_path, df=df)
        initial_rows = len(df)
        df, transformation_metrics = self._run_transformation_pipeline(df)
        output_path = None
        if run_dir:
            output_path = run_dir / "clean_data.parquet"
            df.to_parquet(output_path, index=False)
            logger.info("Saved clean data to %s", output_path)
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

    def _resolve_input_dataframe(
        self, raw_data_path: Optional[Path], df: Optional[pd.DataFrame]
    ) -> pd.DataFrame:
        if df is not None:
            return df
        if not raw_data_path:
            raise ValueError("No data provided for transformation")
        if not raw_data_path.exists():
            raise ValueError("No data provided for transformation")
        return pd.read_parquet(raw_data_path)

    def _run_transformation_pipeline(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        transformation_metrics: Dict[str, Any] = {}
        df = self._normalize_column_names(df)
        df = self._collapse_duplicate_columns(df)
        df = self._map_canonical_semantic_layer(df)
        df = self._derive_canonical_financial_columns(df)
        df, structural_filter_metrics = self._drop_structurally_empty_rows(df)
        transformation_metrics["structural_row_filter"] = structural_filter_metrics
        df, control_metrics = self._derive_control_mora_fields(df)
        transformation_metrics["control_derivations"] = control_metrics
        df, null_metrics = self._handle_nulls(df)
        transformation_metrics["null_handling"] = null_metrics
        df, type_metrics = self._normalize_types(df)
        transformation_metrics["type_normalization"] = type_metrics
        df, rule_metrics = self._apply_business_rules(df)
        transformation_metrics["business_rules"] = rule_metrics
        df, risk_state_metrics = self._derive_canonical_risk_state(df)
        transformation_metrics["canonical_risk_state"] = risk_state_metrics
        df, outlier_metrics = self._detect_outliers(df)
        transformation_metrics["outlier_detection"] = outlier_metrics
        df, integrity_metrics = self._check_referential_integrity(df)
        transformation_metrics["referential_integrity"] = integrity_metrics
        return (df, transformation_metrics)

    def _drop_structurally_empty_rows(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        key_columns = [column for column in self.STRUCTURAL_KEY_COLUMNS if column in df.columns]
        candidate_columns = key_columns or list(df.columns)
        if not candidate_columns:
            return (df, {"rows_removed": 0, "basis": "none"})
        probe = df[candidate_columns].astype("string")
        normalized = probe.apply(lambda col: col.str.strip().str.lower())
        missing_mask = normalized.isna() | normalized.isin(self.STRUCTURAL_EMPTY_MARKERS)
        structural_empty_mask = missing_mask.all(axis=1)
        if (rows_removed := int(structural_empty_mask.sum())) == 0:
            return (
                df,
                {"rows_removed": 0, "basis": "key_columns" if key_columns else "all_columns"},
            )
        logger.warning("Removed %d structurally empty rows before null handling", rows_removed)
        cleaned_df = df.loc[~structural_empty_mask].reset_index(drop=True)
        metrics = {
            "rows_removed": rows_removed,
            "basis": "key_columns" if key_columns else "all_columns",
            "key_columns_used": candidate_columns,
        }
        return (cleaned_df, metrics)

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        # Surface normalisation: lowercase, strip, spaces → underscores.
        # Handles Google Sheets columns like "Fecha actual" → "fecha_actual".
        surface = {
            col: col.strip().lower().replace(" ", "_")
            for col in df.columns
            if col != col.strip().lower().replace(" ", "_")
        }
        if surface:
            df = df.rename(columns=surface)
            logger.info("Surface-normalised %d column names", len(surface))
        column_mapping = {
            "days_past_due": "dpd",
            "dias_vencido": "dpd",
            "mora_en_dias": "dpd",
            "diias_mora_m": "dpd",
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
            "totalsaldovigente": "current_balance",
            "garantiaretenida": "guarantee_retained",
            "fecha_actual": "as_of_date",
            "term_max": "term_months",
            "term_ponderado": "term_months",
            "apr__term__ponderado": "term_months",
            "ingreso_total_por_desembolso": "tpv",
            "ingreso_pagadopendiente": "tpv",
        }
        if rename_dict := {
            source: target
            for source, target in column_mapping.items()
            if source in df.columns and target not in df.columns
        }:
            df = df.rename(columns=rename_dict)
            logger.info("Renamed columns: %s", rename_dict)
        # Overwrite targets that exist but are all-null with non-null source
        for source, target in column_mapping.items():
            if source in df.columns and target in df.columns and source != target:
                target_valid = df[target].notna().sum()
                source_valid = df[source].notna().sum()
                if target_valid == 0 and source_valid > 0:
                    df[target] = df[source]
                    logger.info("Overwrote empty %s with %s (%d values)", target, source, source_valid)
        # Collapse duplicates created by surface normalisation + rename
        # (e.g. FechaDesembolso and "Fecha de Desembolso" both → origination_date)
        df = self._collapse_duplicate_columns(df)
        if "loan_id" in df.columns and "origination_date" in df.columns:
            dates = pd.to_datetime(df["origination_date"], errors="coerce").dt.strftime("%Y%m%d")
            df["loan_uid"] = df["loan_id"].astype(str) + "_" + dates.fillna("00000000")
            logger.info("Generated composite loan_uid for %d records", len(df))
        if "outstanding_balance" in df.columns:
            if "current_balance" not in df.columns:
                df = df.rename(columns={"outstanding_balance": "current_balance"})
                logger.info("Renamed outstanding_balance to current_balance")
            else:
                null_or_zero = df["current_balance"].isna() | (df["current_balance"] == 0)
                if null_or_zero.mean() > 0.8:
                    df["current_balance"] = df["outstanding_balance"]
                    logger.info(
                        "Overwrote current_balance with outstanding_balance (due to high null/zero rate)"
                    )
        return df

    def _map_canonical_semantic_layer(self, df: pd.DataFrame) -> pd.DataFrame:
        semantic_mapping: Dict[str, str] = {
            "application_date": "approved_at",
            "fecha_aprobacion": "approved_at",
            "approval_date": "approved_at",
            "origination_date": "funded_at",
            "disbursement_date": "funded_at",
            "fecha_desembolso": "funded_at",
            "total_scheduled": "scheduled_amount",
            "monto_programado": "scheduled_amount",
            "total_due": "scheduled_amount",
            "last_payment_amount": "actual_payment_amount",
            "total_payment_received": "actual_payment_amount",
        }
        if rename_dict := {
            source: target
            for source, target in semantic_mapping.items()
            if source in df.columns and target not in df.columns
        }:
            df = df.rename(columns=rename_dict)
            logger.info("Canonical semantic layer applied: %s", rename_dict)
        return df

    def _derive_canonical_financial_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Derive canonical financial columns from Spanish source columns.

        Creates outstanding_balance, principal_amount, interest_rate, and
        status when they are missing or empty, using the actual source data
        (montodesembolsado, valororiginal, tasainteres, dpd).
        """
        derived: List[str] = []

        # --- outstanding_balance ---
        if "outstanding_balance" not in df.columns or df["outstanding_balance"].isna().all():
            balance = self._coalesce_numeric_columns(
                df,
                [
                    "montodesembolsado",
                    "totalsaldovigente",
                    "valororiginal",
                    "approved_value",
                    "current_balance",
                    "amount",
                ],
            )
            if balance.notna().any():
                df["outstanding_balance"] = balance
                derived.append("outstanding_balance")

        # --- principal_amount ---
        if "principal_amount" not in df.columns or df["principal_amount"].isna().all():
            principal = self._coalesce_numeric_columns(
                df,
                [
                    "montodesembolsado",
                    "valororiginal",
                    "approved_value",
                    "amount",
                ],
            )
            if principal.notna().any():
                df["principal_amount"] = principal
                derived.append("principal_amount")

        # --- current_balance (backfill when all-NaN) ---
        if "current_balance" in df.columns and df["current_balance"].isna().all():
            cb = self._coalesce_numeric_columns(
                df,
                [
                    "outstanding_balance",
                    "montodesembolsado",
                    "totalsaldovigente",
                    "valororiginal",
                    "approved_value",
                ],
            )
            if cb.notna().any():
                df["current_balance"] = cb
                derived.append("current_balance")

        # --- interest_rate from tasainteres ("1.50%" → 0.015) ---
        if "interest_rate" not in df.columns or df["interest_rate"].isna().all():
            for rate_col in ("tasainteres", "tasa_interes", "tasa_de_interes"):
                if rate_col in df.columns:
                    raw = df[rate_col].astype(str).str.strip()
                    raw = raw.str.replace("%", "", regex=False)
                    raw = raw.str.replace(",", ".", regex=False)
                    numeric_rate = pd.to_numeric(raw, errors="coerce")
                    # Rates > 1 are likely percentages; convert to decimal
                    numeric_rate = numeric_rate.where(
                        numeric_rate <= 1, numeric_rate / 100
                    )
                    if numeric_rate.notna().any():
                        df["interest_rate"] = numeric_rate
                        derived.append("interest_rate")
                        break

        # --- status derived from dpd when empty ---
        if "status" in df.columns and "dpd" in df.columns:
            empty_status = (
                df["status"].isna()
                | (df["status"].astype(str).str.strip() == "")
            )
            if empty_status.mean() > 0.5:
                dpd_vals = pd.to_numeric(df["dpd"], errors="coerce").fillna(0)
                status_from_dpd = pd.Series("active", index=df.index, dtype="object")
                status_from_dpd.loc[dpd_vals > 0] = "delinquent"
                status_from_dpd.loc[dpd_vals > 90] = "defaulted"
                df.loc[empty_status, "status"] = status_from_dpd.loc[empty_status]
                derived.append("status")
        elif "status" not in df.columns and "dpd" in df.columns:
            dpd_vals = pd.to_numeric(df["dpd"], errors="coerce").fillna(0)
            status_from_dpd = pd.Series("active", index=df.index, dtype="object")
            status_from_dpd.loc[dpd_vals > 0] = "delinquent"
            status_from_dpd.loc[dpd_vals > 90] = "defaulted"
            df["status"] = status_from_dpd
            derived.append("status")

        if derived:
            logger.info("Derived canonical financial columns: %s", derived)
        return df

    @staticmethod
    def _collapse_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
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
        if isinstance(series, pd.DataFrame):
            base = series.iloc[:, 0]
            for idx in range(1, series.shape[1]):
                candidate = series.iloc[:, idx]
                base = base.where(base.notna(), candidate)
            series = base
        text = series.astype("string").str.strip()
        text = text.mask(text.isin({"", "nan", "none", "null", "missing"}), pd.NA)
        cleaned = text.str.replace("[^0-9,.\\-]", "", regex=True)
        comma_only_mask = cleaned.str.contains(",", na=False) & ~cleaned.str.contains(
            "\\.", na=False
        )
        thousands_mask = comma_only_mask & cleaned.str.contains(",\\d{3}$", regex=True, na=False)
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
        series_list = [self._to_datetime_mixed(df[col]) for col in candidates if col in df.columns]
        if not series_list:
            return pd.Series(pd.NaT, index=df.index, dtype=DATETIME64_NS_DTYPE)
        merged = series_list[0]
        for candidate in series_list[1:]:
            merged = merged.where(merged.notna(), candidate)
        return merged

    def _coalesce_numeric_columns(self, df: pd.DataFrame, candidates: List[str]) -> pd.Series:
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

    @staticmethod
    def _track_derived_field(metrics: Dict[str, Any], field_name: str, mask: pd.Series) -> None:
        metrics["fields_derived"][field_name] = int(mask.fillna(False).sum())

    def _derive_control_mora_dates_and_terms(
        self, df: pd.DataFrame, metrics: Dict[str, Any]
    ) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
        inferred_origination = self._coalesce_datetime_columns(
            df, ["origination_date", "funded_at", "disbursement_date", "fecha_de_desembolso", "fechadesembolso", "fechaoriginal"]
        )
        existing_origination = (
            self._to_datetime_mixed(df["origination_date"])
            if "origination_date" in df.columns
            else pd.Series(pd.NaT, index=df.index, dtype=DATETIME64_NS_DTYPE)
        )
        final_origination = existing_origination.where(
            existing_origination.notna(), inferred_origination
        )
        df["origination_date"] = final_origination
        self._track_derived_field(
            metrics, "origination_date", existing_origination.isna() & final_origination.notna()
        )
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
            else pd.Series(pd.NaT, index=df.index, dtype=DATETIME64_NS_DTYPE)
        )
        due_base = existing_due.where(existing_due.notna(), inferred_due)
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
        ).where(lambda series: (series > 0) & (series <= 720))
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
        # Ensure all components are plain float64 to avoid Int64/object cast errors
        final_term_months = existing_term_months.astype("float64").where(
            existing_term_months.notna(), raw_term_months.astype("float64")
        )
        final_term_months = final_term_months.astype("float64").where(
            (final_term_months > 0) & (final_term_months <= 240)
        )
        final_term_months = final_term_months.astype("float64").where(
            final_term_months.notna(), term_months_from_days.astype("float64")
        )
        df["term_months"] = final_term_months
        self._track_derived_field(
            metrics, "term_months", existing_term_months.isna() & final_term_months.notna()
        )
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
        self._track_derived_field(
            metrics,
            "payment_frequency",
            existing_payment_frequency.isna() & payment_frequency_final.notna(),
        )
        due_from_days = final_origination + pd.to_timedelta(
            term_days.round().astype("Int64"), unit="D"
        )
        due_from_months = pd.Series(pd.NaT, index=df.index, dtype=DATETIME64_NS_DTYPE)
        month_offsets = raw_term_months.round().astype("Int64")
        valid_month_mask = month_offsets.notna() & final_origination.notna()
        if valid_month_mask.any():
            orig = pd.to_datetime(final_origination[valid_month_mask])
            months = month_offsets[valid_month_mask].astype(int)
            new_year = orig.dt.year + (orig.dt.month - 1 + months) // 12
            new_month = (orig.dt.month - 1 + months) % 12 + 1
            dim_common = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
            dim_leap = np.array([31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
            is_leap = (new_year % 4 == 0) & ((new_year % 100 != 0) | (new_year % 400 == 0))
            days_in_new_month = pd.Series(
                np.where(
                    is_leap.values, dim_leap[new_month.values - 1], dim_common[new_month.values - 1]
                ),
                index=orig.index,
            )
            new_day = orig.dt.day.clip(upper=days_in_new_month)
            due_from_months.loc[valid_month_mask] = pd.to_datetime(
                {"year": new_year, "month": new_month, "day": new_day}
            )
        inferred_due_from_term = due_from_days.where(due_from_days.notna(), due_from_months)
        final_due = due_base.where(due_base.notna(), inferred_due_from_term)
        df["due_date"] = final_due
        self._track_derived_field(metrics, "due_date", due_base.isna() & final_due.notna())
        existing_maturity = (
            self._to_datetime_mixed(df["maturity_date"])
            if "maturity_date" in df.columns
            else pd.Series(pd.NaT, index=df.index, dtype=DATETIME64_NS_DTYPE)
        )
        final_maturity = existing_maturity.where(existing_maturity.notna(), final_due)
        df["maturity_date"] = final_maturity
        self._track_derived_field(
            metrics, "maturity_date", existing_maturity.isna() & final_maturity.notna()
        )
        return (df, final_due, term_days)

    def _derive_control_mora_as_of_and_dpd(
        self, df: pd.DataFrame, final_due: pd.Series, metrics: Dict[str, Any]
    ) -> tuple[pd.DataFrame, pd.Series]:
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
            else pd.Series(pd.NaT, index=df.index, dtype=DATETIME64_NS_DTYPE)
        )
        has_any_as_of = bool(existing_as_of.notna().any() or as_of_candidates.notna().any())
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
        ).where(lambda series: series >= 0)
        if not has_any_as_of and dpd_source.isna().all():
            raise ValueError(
                "CRITICAL: CONTROL DE MORA derivation requires either as_of_date-like columns or a non-null DPD source; neither was found."
            )
        final_as_of = existing_as_of.where(existing_as_of.notna(), as_of_candidates)
        df["as_of_date"] = final_as_of
        self._track_derived_field(
            metrics, "as_of_date", existing_as_of.isna() & final_as_of.notna()
        )
        derived_dpd = (final_as_of - final_due).dt.days.astype(float).clip(lower=0)
        dpd_merged = dpd_source.where(dpd_source.notna(), derived_dpd)
        df["dpd_is_missing"] = dpd_merged.isna().astype(int)
        dpd_final = dpd_merged
        df["dpd"] = dpd_final
        self._track_derived_field(metrics, "dpd", dpd_source.isna() & dpd_final.notna())
        if "days_past_due" in df.columns:
            existing_days_past_due = self._coerce_numeric_loose(df["days_past_due"])
            days_past_due = existing_days_past_due.where(existing_days_past_due.notna(), dpd_final)
        else:
            existing_days_past_due = pd.Series(np.nan, index=df.index, dtype=float)
            days_past_due = dpd_final
        df["days_past_due"] = days_past_due
        self._track_derived_field(
            metrics, "days_past_due", existing_days_past_due.isna() & days_past_due.notna()
        )
        return (df, dpd_final)

    def _derive_control_mora_collections(
        self, df: pd.DataFrame, dpd_final: pd.Series, metrics: Dict[str, Any]
    ) -> tuple[pd.DataFrame, pd.Series]:
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
        self._track_derived_field(
            metrics, "collections_eligible", existing_collections.isna() & collections_final.notna()
        )
        return (df, exposure)

    def _derive_control_mora_utilization(
        self, df: pd.DataFrame, exposure: pd.Series, metrics: Dict[str, Any]
    ) -> pd.DataFrame:
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
        self._track_derived_field(
            metrics, "utilization_pct", valid_existing_util.isna() & util_final.notna()
        )
        return df

    def _derive_control_mora_government(
        self, df: pd.DataFrame, metrics: Dict[str, Any]
    ) -> pd.DataFrame:
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
            gov_hint_upper = df[gov_hint_col].astype(str).str.strip().str.upper()
            hint_is_gov = ~gov_hint_upper.isin(
                {"", "NO", "NAN", "NONE", "NULL", "MISSING", "PRIVATE"}
            )
        else:
            hint_is_gov = pd.Series(False, index=df.index, dtype=bool)
        issuer_col = next((c for c in ("issuer_name", "emisor", "issuer") if c in df.columns), None)
        if issuer_col is not None:
            issuer_upper = df[issuer_col].astype(str).str.upper()
            keyword_pattern = "GOES|MINISTERIO|INSTITUTO|ALCALDIA|MUNICIPALIDAD|GOBIERNO|ASAMBLEA|CORTE|AUTORIDAD|SUPERINTENDENCIA|PRESIDENCIA|PUBLIC"
            issuer_is_gov = issuer_upper.str.contains(keyword_pattern, regex=True, na=False)
        else:
            issuer_is_gov = pd.Series(False, index=df.index, dtype=bool)
        sector_is_gov = existing_sector.fillna("").str.contains("GOES|GOV|PUBLIC", regex=True)
        derived_sector = pd.Series("PRIVATE", index=df.index, dtype="object")
        derived_sector.loc[hint_is_gov | issuer_is_gov | sector_is_gov] = "GOES"
        sector_final = existing_sector.where(existing_sector.notna(), derived_sector)
        df["government_sector"] = sector_final
        self._track_derived_field(
            metrics, "government_sector", existing_sector.isna() & sector_final.notna()
        )
        if "gov" not in df.columns:
            df["gov"] = pd.NA
        gov_existing = df["gov"].astype(str).str.strip()
        gov_missing = gov_existing.isin({"", "nan", "None", "none", "missing", "NO", "No"})
        if gov_hint_col is not None:
            gov_fill = df[gov_hint_col].astype(str).str.strip()
            gov_fill_mask = (
                gov_missing & (gov_fill != "") & ~gov_fill.str.upper().isin({"NAN", "NONE"})
            )
            df.loc[gov_fill_mask, "gov"] = gov_fill.loc[gov_fill_mask]
            self._track_derived_field(metrics, "gov", gov_fill_mask)
        else:
            self._track_derived_field(metrics, "gov", pd.Series(False, index=df.index, dtype=bool))
        return df

    def _derive_control_mora_payment_fields(
        self, df: pd.DataFrame, term_days: pd.Series, metrics: Dict[str, Any]
    ) -> tuple[pd.DataFrame, pd.Series]:
        existing_last_payment_date = (
            self._to_datetime_mixed(df["last_payment_date"])
            if "last_payment_date" in df.columns
            else pd.Series(pd.NaT, index=df.index, dtype=DATETIME64_NS_DTYPE)
        )
        inferred_last_payment_date = self._coalesce_datetime_columns(
            df, ["payment_date", "fecha_de_pago", "fechacobro", "fecha_pago"]
        )
        final_last_payment_date = existing_last_payment_date.where(
            existing_last_payment_date.notna(), inferred_last_payment_date
        )
        df["last_payment_date"] = final_last_payment_date
        self._track_derived_field(
            metrics,
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
        self._track_derived_field(
            metrics,
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
        self._track_derived_field(
            metrics,
            "total_scheduled",
            existing_total_scheduled.isna() & final_total_scheduled.notna(),
        )
        return (df, final_last_payment_amount)

    def _derive_control_mora_tpv(self, df: pd.DataFrame, metrics: Dict[str, Any]) -> pd.DataFrame:
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
        final_tpv = existing_tpv.copy()
        fill_tpv_mask = existing_tpv.isna() & inferred_tpv.notna()
        final_tpv.loc[fill_tpv_mask] = inferred_tpv.loc[fill_tpv_mask]
        df["tpv"] = final_tpv.fillna(0.0)
        self._track_derived_field(metrics, "tpv", existing_tpv.isna() & final_tpv.notna())
        return df

    def _derive_control_mora_fields(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        metrics: Dict[str, Any] = {"enabled": True, "fields_derived": {}}
        df, final_due, term_days = self._derive_control_mora_dates_and_terms(df, metrics)
        df, dpd_final = self._derive_control_mora_as_of_and_dpd(df, final_due, metrics)
        df, exposure = self._derive_control_mora_collections(df, dpd_final, metrics)
        df = self._derive_control_mora_utilization(df, exposure, metrics)
        df = self._derive_control_mora_government(df, metrics)
        df, _ = self._derive_control_mora_payment_fields(df, term_days, metrics)
        df = self._derive_control_mora_tpv(df, metrics)
        return (df, metrics)

    def _derive_canonical_risk_state(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        metrics: Dict[str, Any] = {"enabled": True}
        paid_amount = self._coalesce_numeric_columns(
            df,
            [
                "last_payment_amount",
                "payment_amount",
                "total_payment_received",
                "montototalabonado",
                "capital_collected",
                "capitalcobrado",
            ],
        )
        scheduled_amount = self._coalesce_numeric_columns(
            df, ["total_scheduled", "scheduled_amount", "total_due", "monto_programado"]
        )
        dpd_source = df["dpd"] if "dpd" in df.columns else pd.Series(np.nan, index=df.index)
        dpd = pd.to_numeric(dpd_source, errors="coerce")
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio_pago_real = np.where(scheduled_amount > 0, paid_amount / scheduled_amount, np.nan)
        is_kiting_suspected = (
            pd.Series(ratio_pago_real, index=df.index).gt(0.0)
            & pd.Series(ratio_pago_real, index=df.index).lt(1.0)
            & pd.Series(ratio_pago_real, index=df.index).notna()
            & dpd.lt(30)
        )
        dpd_adjusted = np.where(
            is_kiting_suspected, np.maximum(dpd.to_numpy(), 90.0), dpd.to_numpy()
        )
        df["ratio_pago_real"] = pd.Series(ratio_pago_real, index=df.index, dtype=float)
        df["is_kiting_suspected"] = is_kiting_suspected.astype(int)
        df["dpd_adjusted"] = pd.Series(dpd_adjusted, index=df.index, dtype=float)
        metrics["kiting_rows"] = int(is_kiting_suspected.sum())
        metrics["opaque_ratio_rows"] = int(pd.Series(ratio_pago_real, index=df.index).isna().sum())
        return (df, metrics)

    def _handle_nulls(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        logger.info("Handling null values (strategy: %s)", self.null_strategy)
        initial_nulls = df.isnull().sum()
        total_nulls = initial_nulls.sum()
        null_columns = initial_nulls[initial_nulls > 0].to_dict()
        if total_nulls == 0:
            logger.info("No null values found")
            return (df, {"total_nulls": 0, "strategy_applied": "none", "columns_affected": []})
        metrics = self._create_null_metrics(total_nulls, null_columns)
        df, strategy_metrics = self._apply_null_strategy(df, null_columns)
        metrics.update(strategy_metrics)
        final_nulls = df.isnull().sum().sum()
        metrics["final_total_nulls"] = final_nulls
        return (df, metrics)

    def _create_null_metrics(
        self, total_nulls: int, null_columns: Dict[str, int]
    ) -> Dict[str, Any]:
        return {
            "initial_total_nulls": total_nulls,
            "null_columns": null_columns,
            "strategy_applied": self.null_strategy,
            "columns_affected": list(null_columns.keys()),
        }

    def _apply_null_strategy(
        self, df: pd.DataFrame, null_columns: Dict[str, int]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        strategy_handlers = {
            "drop": lambda: self._apply_drop_strategy(df),
            "fill": lambda: self._apply_fill_strategy(df),
            "smart": lambda: self._smart_null_handling(df, null_columns),
        }
        handler = strategy_handlers.get(self.null_strategy)
        return handler() if handler else (df, {})

    def _apply_drop_strategy(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        rows_before = len(df)
        df = df.dropna()
        rows_dropped = rows_before - len(df)
        logger.info("Dropped %d rows with null values", rows_dropped)
        return (df, {"rows_dropped": rows_dropped})

    def _apply_fill_strategy(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df = self._fill_nulls_by_type(df)
        logger.info("Filled null values with configured defaults")
        return (df, {"fill_values_used": self.fill_values})

    def _fill_nulls_by_type(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if not df[col].isnull().any():
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(self.fill_values.get("numeric", 0))
            else:
                df[col] = df[col].fillna(self.fill_values.get("categorical", "unknown"))
        return df

    def _smart_null_handling(
        self, df: pd.DataFrame, null_columns: Dict[str, int]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        total_rows = len(df)
        actions, opacity_counts = self._process_null_columns(df, null_columns, total_rows)
        return (df, {"smart_actions": actions, "opacity_counts": opacity_counts})

    def _process_null_columns(
        self, df: pd.DataFrame, null_columns: Dict[str, int], total_rows: int
    ) -> Tuple[Dict[str, str], Dict[str, int]]:
        actions: Dict[str, str] = {}
        opacity_counts: Dict[str, int] = {}
        for col, null_count in null_columns.items():
            null_pct = null_count / total_rows * 100
            action = (
                self._handle_numeric_nulls(df, col, null_pct)
                if pd.api.types.is_numeric_dtype(df[col])
                else self._handle_categorical_nulls(df, col)
            )
            actions[col] = action
            flag_col = f"{col}_is_missing"
            if flag_col in df.columns:
                opacity_counts[flag_col] = null_count
        return (actions, opacity_counts)

    def _handle_numeric_nulls(self, df: pd.DataFrame, col: str, null_pct: float) -> str:
        if col in self.FORCE_ZERO_NUMERIC_COLUMNS:
            df[col] = df[col].fillna(0)
            return "filled_zero (cashflow_semantics)"
        if null_pct < self.LOW_NULL_THRESHOLD_PCT:
            return self._fill_numeric_with_structural_zero(df, col)
        if null_pct < self.HIGH_NULL_THRESHOLD_PCT:
            return self._fill_numeric_with_indicator(df, col)
        return self._fill_numeric_with_zero(df, col, null_pct)

    def _fill_numeric_with_structural_zero(self, df: pd.DataFrame, col: str) -> str:
        null_mask = df[col].isna()
        flag_col = f"{col}_is_missing"
        df[flag_col] = null_mask.astype(int)
        df[col] = df[col].fillna(0)
        return f"filled_structural_zero+flag ({null_mask.sum()} nulls → {flag_col})"

    def _fill_numeric_with_indicator(self, df: pd.DataFrame, col: str) -> str:
        df[col] = df[col].fillna(self.MISSING_NUMERIC_INDICATOR)
        return f"filled_missing_indicator ({self.MISSING_NUMERIC_INDICATOR})"

    def _fill_numeric_with_zero(self, df: pd.DataFrame, col: str, null_pct: float) -> str:
        if null_pct > 99.5:
            return f"skipped_zero_fill (null_pct={null_pct:.1f}% > 99.5%)"
        df[col] = df[col].fillna(0)
        if col in self.HIGH_NULL_WARNING_NUMERIC_COLUMNS:
            logger.error(
                "Column '%s' exceeds missing threshold (%.1f%% nulls). Fail-fast requires structural integrity for critical KPIs.",
                col,
                null_pct,
            )
            raise ValueError(f"Critical column {col} exceeds missing threshold ({null_pct:.1f}%)")
        return f"filled_zero (high_null: {null_pct:.1f}%)"

    def _handle_categorical_nulls(self, df: pd.DataFrame, col: str) -> str:
        return self._fill_categorical_with_missing_data(df, col)

    def _fill_categorical_with_missing_data(self, df: pd.DataFrame, col: str) -> str:
        null_mask = df[col].isna()
        flag_col = f"{col}_is_missing"
        df[flag_col] = null_mask.astype(int)
        df[col] = df[col].fillna("missing_data")
        return f"filled_missing_data+flag ({null_mask.sum()} nulls → {flag_col})"

    def _normalize_types(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        logger.info("Normalizing data types")
        if not self.type_normalization_enabled:
            return (df, {"enabled": False})
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
        return (df, metrics)

    def _normalize_date_columns(
        self, df: pd.DataFrame, conversions: Dict[str, Dict[str, str]]
    ) -> None:
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
        for col in df.columns:
            is_numeric_name = col in self.NUMERIC_COLUMNS or self.NUMERIC_NAME_PATTERN.search(col)
            is_string_obj = pd.api.types.is_string_dtype(df[col]) or df[col].dtype == "object"
            if is_numeric_name and "country" not in col.lower() and is_string_obj:
                try:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    conversions[col] = {"from": "string", "to": "numeric"}
                except Exception as e:
                    logger.warning("Could not convert %s to numeric: %s", col, e)

    def _normalize_status_column(
        self, df: pd.DataFrame, conversions: Dict[str, Dict[str, str]]
    ) -> None:
        if "status" not in df.columns:
            return
        original_values = df["status"].unique().tolist()
        original_status = df["status"]
        normalized_status = original_status.astype("string").str.strip().str.lower()
        mapped_status = normalized_status.map(self.STATUS_MAPPINGS)
        mask_missing = original_status.isna()
        mask_unmapped = ~mask_missing & mapped_status.isna()
        final_status = mapped_status.where(~mask_unmapped, normalized_status).where(
            ~mask_missing, original_status
        )
        df["status"] = final_status
        conversions["status"] = {"normalized_values": original_values}

    def _apply_business_rules(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
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
        return (df, metrics)

    def _automate_gov_identification(
        self, df: pd.DataFrame, rules_applied: List[str], fields_created: List[str]
    ) -> None:
        pagador_col = next(
            (c for c in ("emisor", "issuer_name", "issuer") if c in df.columns), None
        )
        if not pagador_col:
            return
        for col in ["gov", "industry"]:
            if col not in df.columns:
                df[col] = "No" if col == "gov" else "Other"
                fields_created.append(col)
        if "government_sector" not in df.columns:
            df["government_sector"] = "PRIVATE"
            fields_created.append("government_sector")
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
        keyword_gov_mask = (
            df[pagador_col].astype(str).str.upper().str.contains(gov_pattern, na=False)
        )
        is_gov_mask = keyword_gov_mask | (
            df[goes_source].astype(str).str.upper().str.strip() == "GOES"
            if (
                goes_source := next(
                    (c for c in ("government_sector", "goes") if c in df.columns), None
                )
            )
            else pd.Series(False, index=df.index)
        )
        needs_gov_name = is_gov_mask & df["gov"].astype(str).str.lower().isin(
            ["", "no", "nan", "none", "missing"]
        )
        needs_industry = (
            df["industry"]
            .astype(str)
            .str.lower()
            .isin(["", "other", "nan", "none", "missing", "unknown"])
        )
        df.loc[needs_gov_name, "gov"] = df.loc[needs_gov_name, pagador_col]
        df.loc[is_gov_mask, "government_sector"] = "GOES"
        df.loc[is_gov_mask, "industry"] = "Government"
        if (~is_gov_mask).any():
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
            for industry, pattern in industry_map.items():
                match_mask = (
                    ~is_gov_mask
                    & needs_industry
                    & df[pagador_col].astype(str).str.upper().str.contains(pattern, na=False)
                )
                df.loc[match_mask, "industry"] = industry
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
        if "doc_type" not in df.columns:
            df["doc_type"] = "Other"
            fields_created.append("doc_type")
        candidates = ["numeroquedan", "oc", "numerointerno"]
        doc_map = {
            "Quedan": "QUEDAN|^Q/|^QF/|^Q\\d",
            "CCF": "CCF|CREDITO FISCAL",
            "DTE": "DTE|ELECTRONIC",
            "Factura": "FACTURA|^FAC|^F\\d|COMPROBANTE",
            "Factura Export": "EXPORT|EXP\\d",
            "Purchase Order": "PO|OC|PURCHASE|ORDEN",
        }
        for doc_label, pattern in doc_map.items():
            for col in candidates:
                if col in df.columns:
                    mask = (
                        df[col].astype(str).str.upper().str.contains(pattern, na=False, regex=True)
                    )
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
        """Normalize interest_rate to an annual decimal (e.g. 0.24 = 24 %/yr).

        The heuristic uses the column's *median* plus the median loan term to
        guess the original unit.  Because this is inherently fallible, the
        method stamps every row with ``interest_rate_normalization`` so that
        downstream consumers can audit which conversion was applied:

        * ``monthly_pct_to_annual`` – median ∈ [0.2, 5) and median term < 6
        * ``pct_to_decimal``        – median > 1  (whole-percentage data)
        * ``none``                  – already looks like an annual decimal
        """
        if "interest_rate" not in df.columns:
            return
        rates = pd.to_numeric(df["interest_rate"], errors="coerce")
        valid = rates.dropna()
        if valid.empty:
            return
        median_rate = valid.median()
        median_term = None
        if "term_months" in df.columns:
            terms = pd.to_numeric(df["term_months"], errors="coerce").dropna()
            if not terms.empty:
                median_term = terms.median()
        if 0.2 <= median_rate < 5 and median_term is not None and (median_term < 6):
            df["interest_rate"] = rates * 12 / 100
            df["interest_rate_normalization"] = "monthly_pct_to_annual"
            logger.info(
                "Normalized interest_rate: monthly %% → annual decimal (median %.4f%%/mo → %.4f annual)",
                median_rate,
                median_rate * 12 / 100,
            )
            rules_applied.append("interest_rate_monthly_pct_to_annual")
        elif median_rate > 1:
            df["interest_rate"] = rates / 100
            df["interest_rate_normalization"] = "pct_to_decimal"
            logger.info(
                "Normalized interest_rate: whole %% → annual decimal (median %.2f%% → %.4f)",
                median_rate,
                median_rate / 100,
            )
            rules_applied.append("interest_rate_pct_to_decimal")
        else:
            df["interest_rate_normalization"] = "none"
            logger.info(
                "interest_rate appears to be annual decimal already (median=%.4f); no conversion applied",
                median_rate,
            )

    def _apply_dpd_bucket_rule(
        self, df: pd.DataFrame, rules_applied: List[str], fields_created: List[str]
    ) -> None:
        if "dpd" not in df.columns:
            return
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
        if "status" in df.columns and "dpd" in df.columns:
            status = df["status"].fillna("").astype(str)
            dpd = pd.to_numeric(df["dpd"], errors="coerce")
            dpd_missing = dpd.isna()
            dpd_safe = dpd.fillna(0)
            conditions = [
                status.str.contains("default", case=False, na=False) | (dpd_safe >= 90),
                (dpd_safe >= 30) & (dpd_safe < 90),
                (dpd_safe > 0) & (dpd_safe < 30),
                dpd_safe <= 0,
            ]
            choices = ["critical", "high", "medium", "low"]
            df["risk_category"] = np.select(conditions, choices, default="low")
            df.loc[dpd_missing, "risk_category"] = "unknown"
            fields_created.append("risk_category")
            rules_applied.append("risk_categorization")

    def _apply_amount_tier_rule(
        self, df: pd.DataFrame, rules_applied: List[str], fields_created: List[str]
    ) -> None:
        if "amount" not in df.columns:
            return
        self._categorize_amount_tiers(df)
        self._record_applied_rule(rules_applied, fields_created)

    def _record_applied_rule(self, rules_applied: List[str], fields_created: List[str]) -> None:
        fields_created.append("amount_tier")
        rules_applied.append("amount_tier_classification")

    def _categorize_amount_tiers(self, df: pd.DataFrame) -> None:
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
        custom_rules = self.business_rules.get("transformations", [])
        for rule in custom_rules:
            try:
                df, success = self._apply_custom_rule(df, rule)
                if success:
                    rules_applied.append(rule.get("name", "unnamed_rule"))
            except Exception as e:
                logger.warning("Failed to apply custom rule: %s", e)

    def _normalize_equifax_score(self, df: pd.DataFrame, rules_applied: List[str]) -> None:
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
        if pd.isna(dpd) or dpd < 0:
            return "unknown"
        if dpd == 0:
            return "current"
        if dpd < 30:
            return "1-29"
        if dpd < 60:
            return "30-59"
        if dpd < 90:
            return "60-89"
        return "90-179" if dpd < 180 else "180+"

    def _calculate_risk_category(self, row: pd.Series) -> str:
        status = row.get("status", "")
        dpd = row.get("dpd", 0)
        if status == "defaulted":
            return "critical"
        if status == "delinquent" or (pd.notna(dpd) and dpd >= 90):
            return "high"
        if pd.notna(dpd) and dpd >= 30:
            return "medium"
        if status == "active" and (pd.isna(dpd) or dpd < 30):
            return "low"
        return "unknown"

    def _assign_amount_tier(self, amount: float) -> str:
        if pd.isna(amount) or amount <= 0:
            return "invalid"
        if amount < 5000:
            return "micro"
        if amount < 25000:
            return "small"
        if amount < 100000:
            return "medium"
        return "large" if amount < 500000 else "jumbo"

    def _apply_custom_rule(
        self, df: pd.DataFrame, rule: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, bool]:
        if (rule_type := rule.get("type")) == "column_mapping":
            return self._apply_column_mapping_rule(df, rule)
        if rule_type == "derived_field":
            return self._apply_derived_field_rule(df, rule)
        return (df, False)

    def _apply_column_mapping_rule(
        self, df: pd.DataFrame, rule: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, bool]:
        source_col = rule.get("source_column")
        target_col = rule.get("target_column")
        mapping = rule.get("mapping", {})
        if source_col and target_col and (source_col in df.columns):
            df[target_col] = df[source_col].map(mapping).fillna(df[source_col])
            return (df, True)
        logger.warning(
            f"Invalid column_mapping rule configuration or missing source column: source_column={source_col!r}, target_column={target_col!r}"
        )
        return (df, False)

    def _apply_derived_field_rule(
        self, df: pd.DataFrame, rule: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, bool]:
        if not (target_col := rule.get("target_column")) or not (
            expression := rule.get("expression", "")
        ):
            return (df, False)
        if not self._is_safe_expression(expression):
            return (df, False)
        tokens = re.findall("[A-Za-z_]\\w*", expression)
        if pii_cols := [t for t in tokens if t in df.columns and self._PII_COLUMN_RE.search(t)]:
            logger.warning(
                "Derived field expression '%s' references potential PII column(s) %s — skipping",
                expression,
                pii_cols,
            )
            return (df, False)
        try:
            df[target_col] = df.eval(expression)
            return (df, True)
        except Exception as e:
            logger.warning("Failed to evaluate expression '%s': %s", expression, e)
            return (df, False)

    def _is_safe_expression(self, expression: str) -> bool:
        if not self._check_allowed_chars(expression):
            return False
        return not self._check_dangerous_patterns(expression)

    def _check_allowed_chars(self, expression: str) -> bool:
        allowed_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-*/(). "
        )
        if any((c not in allowed_chars for c in expression)):
            logger.warning("Unsafe characters in expression '%s', skipping rule", expression)
            return False
        return True

    def _check_dangerous_patterns(self, expression: str) -> bool:
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
        has_dangerous_pattern = any((pattern in expression_lower for pattern in dangerous_patterns))
        if has_dangerous_pattern:
            logger.warning(
                "Dangerous pattern detected in expression '%s', skipping rule", expression
            )
        return has_dangerous_pattern

    def _detect_outliers(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        logger.info("Detecting outliers (method: %s)", self.outlier_method)
        if not self.outlier_enabled:
            return (df, {"enabled": False})
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        skip_cols = {"loan_id", "id", "dpd"}
        check_cols = [col for col in numeric_cols if col not in skip_cols]
        df, outlier_counts, total_outlier_rows = self._flag_outliers(df, check_cols)
        metrics = self._create_outlier_metrics(check_cols, outlier_counts, total_outlier_rows)
        return (df, metrics)

    def _flag_outliers(
        self, df: pd.DataFrame, check_cols: List[str]
    ) -> Tuple[pd.DataFrame, Dict[str, int], int]:
        outlier_counts: Dict[str, int] = {}
        outlier_flags: Dict[str, pd.Series] = {}
        any_outlier_mask = pd.Series(False, index=df.index, dtype=bool)
        for col in check_cols:
            outliers = (
                self._detect_outliers_iqr(df[col])
                if self.outlier_method == "iqr"
                else self._detect_outliers_zscore(df[col])
            )
            outlier_flags[f"{col}_outlier"] = outliers.fillna(False).astype(bool)
            outlier_count = outliers.sum()
            if outlier_count > 0:
                outlier_counts[col] = int(outlier_count)
                any_outlier_mask = any_outlier_mask | outlier_flags[f"{col}_outlier"]
                logger.info("Found %d outliers in column '%s'", int(outlier_count), col)
        if outlier_flags:
            flags_df = pd.DataFrame(outlier_flags, index=df.index)
            df = pd.concat([df, flags_df], axis=1)
        return (df, outlier_counts, int(any_outlier_mask.sum()))

    def _create_outlier_metrics(
        self, check_cols: List[str], outlier_counts: Dict[str, int], total_outlier_rows: int
    ) -> Dict[str, Any]:
        return {
            "enabled": True,
            "method": self.outlier_method,
            "threshold": self.outlier_threshold,
            "columns_checked": len(check_cols),
            "outliers_detected": outlier_counts,
            "total_outlier_rows": total_outlier_rows,
        }

    def _detect_outliers_iqr(self, series: pd.Series) -> pd.Series:
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        if IQR == 0 or np.isclose(IQR, 0):
            return pd.Series([False] * len(series), index=series.index)
        lower_bound = Q1 - self.outlier_threshold * IQR
        upper_bound = Q3 + self.outlier_threshold * IQR
        return ((series < lower_bound) | (series > upper_bound)).fillna(False)

    def _detect_outliers_zscore(self, series: pd.Series) -> pd.Series:
        non_null = series.dropna()
        if non_null.empty or non_null.std() == 0:
            return pd.Series(False, index=series.index)
        mean = non_null.mean()
        std = non_null.std()
        z_scores = np.abs((non_null - mean) / std)
        outliers_non_null = z_scores > self.outlier_threshold
        outliers = pd.Series(False, index=series.index)
        outliers.loc[non_null.index] = outliers_non_null.fillna(False)
        return outliers

    def _check_referential_integrity(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
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
            "integrity_status": "warning" if integrity_issues else "pass",
        }
        if not integrity_issues:
            logger.info("Referential integrity checks passed")
        else:
            logger.warning("Found %d referential integrity issues", len(integrity_issues))
        return (df, metrics)

    def _check_primary_key_integrity(
        self, df: pd.DataFrame, integrity_issues: List[Dict[str, Any]]
    ) -> None:
        pk_col = "loan_uid" if "loan_uid" in df.columns else "loan_id"
        if pk_col not in df.columns:
            return
        duplicates = df[pk_col].duplicated().sum()
        if duplicates > 0:
            integrity_issues.append(
                {"type": "duplicate_primary_key", "column": pk_col, "count": int(duplicates)}
            )
            logger.warning("Found %d duplicate %s values", duplicates, pk_col)

    def _check_foreign_key_integrity(
        self, df: pd.DataFrame, integrity_issues: List[Dict[str, Any]]
    ) -> None:
        if "borrower_id" not in df.columns:
            return
        null_borrowers = df["borrower_id"].isnull().sum()
        if null_borrowers > 0:
            integrity_issues.append(
                {"type": "null_foreign_key", "column": "borrower_id", "count": int(null_borrowers)}
            )

    def _check_date_consistency(
        self, df: pd.DataFrame, integrity_issues: List[Dict[str, Any]]
    ) -> None:
        date_cols = [col for col in df.columns if col.endswith("_date")]
        has_both_dates = (
            "origination_date" in date_cols
            and "due_date" in date_cols
            and (df["origination_date"].dtype == DATETIME64_NS_DTYPE)
            and (df["due_date"].dtype == DATETIME64_NS_DTYPE)
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
        positive_cols = ["amount", "current_balance", "original_amount"]
        for col in positive_cols:
            if col not in df.columns:
                continue
            valid_values = df[col].dropna()
            negative_count = (valid_values < 0).sum()
            if negative_count > 0:
                integrity_issues.append(
                    {"type": "negative_value", "column": col, "count": int(negative_count)}
                )
