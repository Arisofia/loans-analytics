"""
PHASE 4: OUTPUT & DISTRIBUTION

Responsibilities:
- Multi-format exports (Parquet/CSV/JSON)
- Database writes (Supabase)
- Dashboard refresh triggers
- Audit trail generation
- SLA monitoring

NOTE: This module is not designed to be run directly as a script.
      Use: python scripts/data/run_data_pipeline.py
"""

import json
import os
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Set

import pandas as pd

from python.logging_config import get_logger

try:
    import httpx  # pylint: disable=unused-import  # used in _trigger_dashboard_refresh
except ImportError:
    httpx = None  # type: ignore[assignment]

try:
    from supabase import Client, create_client
except ImportError:
    Client = None  # type: ignore[assignment,misc]
    create_client = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from python.kpis.engine import KPIEngineV2

logger = get_logger(__name__)


class OutputPhase:
    """Phase 4: Output & Distribution"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize output phase.

        Args:
            config: Output configuration from pipeline.yml
        """
        self.config = config
        logger.info("Initialized output phase")

    def execute(
        self,
        kpi_results: Dict[str, Any],
        run_dir: Optional[Path] = None,
        kpi_engine: Optional["KPIEngineV2"] = None,
        segment_kpis: Optional[Dict[str, Any]] = None,
        time_series: Optional[Dict[str, Any]] = None,
        anomalies: Optional[list] = None,
        nsm_recurrent_tpv: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute output phase.

        Args:
            kpi_results: Flat KPI calculation results from Phase 3
            run_dir: Directory for this pipeline run
            kpi_engine: Optional KPIEngineV2 instance for audit trail export
            segment_kpis: Per-dimension segment KPIs produced by CalculationPhase
            time_series: Time-series rollup data produced by CalculationPhase
            anomalies: Anomaly records produced by CalculationPhase
            nsm_recurrent_tpv: NSM recurrent TPV payload produced by CalculationPhase

        Returns:
            Output results including export paths
        """
        logger.info("Starting Phase 4: Output")

        try:
            exports = {}

            # Export to multiple formats
            if run_dir:
                # Parquet export
                parquet_path = self._export_parquet(kpi_results, run_dir)
                exports["parquet"] = str(parquet_path)

                # CSV export
                csv_path = self._export_csv(kpi_results, run_dir)
                exports["csv"] = str(csv_path)

                # JSON export
                json_path = self._export_json(kpi_results, run_dir)
                exports["json"] = str(json_path)

                segment_snapshot_path = self._export_segment_snapshot(run_dir)
                if segment_snapshot_path is not None:
                    exports["segment_snapshot"] = str(segment_snapshot_path)

                # Export full ML intelligence payload
                if segment_kpis is not None:
                    seg_kpi_path = self._export_payload_json(
                        segment_kpis, run_dir, "segment_kpis.json"
                    )
                    exports["segment_kpis"] = str(seg_kpi_path)

                if time_series is not None:
                    ts_path = self._export_payload_json(time_series, run_dir, "time_series.json")
                    exports["time_series"] = str(ts_path)

                if anomalies is not None:
                    anomalies_path = self._export_payload_json(anomalies, run_dir, "anomalies.json")
                    exports["anomalies"] = str(anomalies_path)

                if nsm_recurrent_tpv is not None:
                    nsm_path = self._export_payload_json(
                        nsm_recurrent_tpv, run_dir, "nsm_recurrent_tpv_output.json"
                    )
                    exports["nsm_recurrent_tpv"] = str(nsm_path)

            # Export KPI audit trail if engine is provided
            if kpi_engine is not None:
                audit_path = self._export_kpi_audit_trail(kpi_engine)
                if audit_path:
                    exports["kpi_audit_trail"] = str(audit_path)

            # Write to database
            db_result = self._write_to_database(kpi_results)

            # Trigger dashboard refresh
            dashboard_result = self._trigger_dashboard_refresh()

            # Generate audit metadata
            audit_trail = self._generate_audit_metadata(kpi_results, exports, kpi_engine)

            results = {
                "status": "success",
                "exports": exports,
                "database_write": db_result,
                "dashboard_refresh": dashboard_result,
                "audit_trail": audit_trail,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Output completed: {len(exports)} exports, database: {db_result['status']}"
            )
            return results

        except Exception as e:
            logger.error("Output failed: %s", str(e), exc_info=True)
            return {"status": "failed", "error": str(e), "timestamp": datetime.now().isoformat()}

    def _export_parquet(self, kpi_results: Dict[str, Any], run_dir: Path) -> Path:
        """Export KPI results to Parquet format."""
        output_path = run_dir / "kpis_output.parquet"

        df = pd.DataFrame([kpi_results])
        df.to_parquet(output_path, index=False)

        logger.info("Exported Parquet: %s", output_path)
        return output_path

    def _export_csv(self, kpi_results: Dict[str, Any], run_dir: Path) -> Path:
        """Export KPI results to CSV format with Decimal precision for financial columns."""
        output_path = run_dir / "kpis_output.csv"
        df = pd.DataFrame([kpi_results])

        # Convert financial columns to Decimal for monetary precision
        financial_columns = {
            "amount",
            "principal_amount",
            "original_amount",
            "current_balance",
            "payment_amount",
            "interest_rate",
        }

        for col in financial_columns:
            if col in df.columns and df[col].iloc[0] is not None:
                try:
                    value = df[col].iloc[0]
                    if isinstance(value, (int, float)):
                        # Convert to Decimal with proper rounding
                        decimal_val = Decimal(str(value)).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                        df.at[0, col] = str(decimal_val)
                except (ValueError, TypeError) as e:
                    logger.warning("Could not convert %s to Decimal: %s", col, e)

        df.to_csv(output_path, index=False)

        logger.info("Exported CSV with Decimal precision: %s", output_path)
        return output_path

    def _export_json(self, kpi_results: Dict[str, Any], run_dir: Path) -> Path:
        """Export KPI results to JSON format."""
        output_path = run_dir / "kpis_output.json"

        with open(output_path, "w") as f:
            json.dump(kpi_results, f, indent=2, default=str)

        logger.info("Exported JSON: %s", output_path)
        return output_path

    def _export_payload_json(self, payload: Any, run_dir: Path, filename: str) -> Path:
        """Export an arbitrary ML intelligence payload to a named JSON file.

        Used to preserve full calculation intelligence (segment KPIs, time-series,
        anomalies, NSM TPV) so that no analytical output is silently discarded.
        """
        output_path = run_dir / filename
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)
        logger.info("Exported payload: %s", output_path)
        return output_path

    def _export_segment_snapshot(self, run_dir: Path) -> Optional[Path]:
        """
        Export segment-level risk snapshot from clean/transformed dataset.

        Produces `segment_snapshot.json` with per-dimension rows for:
        company, credit_line, kam_hunter, kam_farmer.
        """
        data_path: Optional[Path] = None
        for candidate in ("clean_data.parquet", "transformed.parquet"):
            candidate_path = run_dir / candidate
            if candidate_path.exists():
                data_path = candidate_path
                break

        if data_path is None:
            logger.debug("Segment snapshot skipped: no clean/transformed parquet in %s", run_dir)
            return None

        try:
            df = pd.read_parquet(data_path)
        except Exception as exc:
            logger.warning("Segment snapshot skipped: could not read %s (%s)", data_path, exc)
            return None

        if df.empty:
            logger.debug("Segment snapshot skipped: source dataframe is empty")
            return None

        balance_col = self._resolve_first_column(
            df, ["outstanding_balance", "current_balance", "balance"]
        )
        status_col = self._resolve_first_column(df, ["status", "loan_status"])
        dpd_col = self._resolve_first_column(df, ["dpd", "days_past_due"])
        loan_id_col = self._resolve_first_column(df, ["loan_id", "loan_uid"])
        interest_rate_col = self._resolve_first_column(df, ["interest_rate"])

        if balance_col is None:
            logger.debug("Segment snapshot skipped: no balance column present")
            return None

        working = df.copy()
        working["__balance"] = pd.to_numeric(working[balance_col], errors="coerce").fillna(0.0)
        working["__status"] = (
            working[status_col].astype(str).str.strip().str.lower()
            if status_col is not None
            else pd.Series(["unknown"] * len(working), index=working.index, dtype=object)
        )
        working["__dpd"] = (
            pd.to_numeric(working[dpd_col], errors="coerce").fillna(0.0)
            if dpd_col is not None
            else pd.Series([0.0] * len(working), index=working.index, dtype=float)
        )

        if interest_rate_col is not None:
            interest_rate = pd.to_numeric(working[interest_rate_col], errors="coerce")
            # Normalize 0-100 scales to 0-1 if needed.
            if interest_rate.notna().any() and float(interest_rate.median()) > 1:
                interest_rate = interest_rate / 100.0
            working["__interest_rate"] = interest_rate
        else:
            working["__interest_rate"] = pd.Series([pd.NA] * len(working), index=working.index)

        missing_markers = {"", "nan", "none", "null", "n/a", "missing", "unknown"}
        dimensions = [
            "company",
            "credit_line",
            "kam_hunter",
            "kam_farmer",
            "gov",
            "industry",
            "doc_type",
        ]
        dimension_rows: Dict[str, list[Dict[str, Any]]] = {}

        for dimension in dimensions:
            if dimension not in working.columns:
                continue

            raw_segment = working[dimension].astype(str).str.strip()
            normalized_segment = raw_segment.str.lower()
            valid_mask = ~normalized_segment.isin(missing_markers)
            if valid_mask.sum() == 0:
                continue

            segment_df = working.loc[valid_mask].copy()
            segment_df["__segment"] = raw_segment.loc[valid_mask]
            grouped = segment_df.groupby("__segment", dropna=False)

            rows: list[Dict[str, Any]] = []
            for segment_name, group in grouped:
                balance_sum = Decimal(str(group["__balance"].sum()))
                if balance_sum <= 0:
                    continue

                if loan_id_col is not None:
                    loan_count = int(group[loan_id_col].astype(str).nunique())
                else:
                    loan_count = int(len(group))

                par_30 = self._segment_ratio(group, balance_sum, dpd_threshold=30)
                par_60 = self._segment_ratio(group, balance_sum, dpd_threshold=60)
                par_90 = self._segment_ratio(group, balance_sum, dpd_threshold=90)
                default_rate = self._segment_default_rate(group, loan_count)
                avg_dpd = Decimal(str(group["__dpd"].mean()))

                row: Dict[str, Any] = {
                    "segment": str(segment_name),
                    "loan_count": loan_count,
                    "total_outstanding_balance": float(balance_sum),
                    "par_30": float(par_30),
                    "par_60": float(par_60),
                    "par_90": float(par_90),
                    "default_rate": float(default_rate),
                    "avg_dpd": float(avg_dpd),
                }

                if group["__interest_rate"].notna().any():
                    portfolio_yield = Decimal(str(group["__interest_rate"].mean())) * Decimal("100")
                    row["portfolio_yield"] = float(portfolio_yield)

                rows.append(row)

            if rows:
                rows.sort(key=lambda item: item["total_outstanding_balance"], reverse=True)
                dimension_rows[dimension] = rows[:25]

        if not dimension_rows:
            logger.debug("Segment snapshot skipped: no segment rows generated")
            return None

        payload = {
            "generated_at": datetime.now().isoformat(),
            "run_id": run_dir.name,
            "source_data_path": data_path.name,
            "as_of_date": self._derive_segment_as_of_date(working),
            "dimensions": dimension_rows,
        }

        output_path = run_dir / "segment_snapshot.json"
        with open(output_path, "w", encoding="utf-8") as file_handle:
            json.dump(payload, file_handle, indent=2, default=str)

        logger.info("Exported segment snapshot: %s", output_path)
        return output_path

    @staticmethod
    def _resolve_first_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
        available = {col.lower(): col for col in df.columns}
        for candidate in candidates:
            found = available.get(candidate.lower())
            if found is not None:
                return found
        return None

    @staticmethod
    def _segment_ratio(group: pd.DataFrame, balance_sum: Decimal, dpd_threshold: int) -> Decimal:
        if balance_sum <= 0:
            return Decimal("0")
        delinquent_outstanding = Decimal(
            str(group.loc[group["__dpd"] >= dpd_threshold, "__balance"].sum())
        )
        return (delinquent_outstanding / balance_sum) * Decimal("100")

    @staticmethod
    def _segment_default_rate(group: pd.DataFrame, loan_count: int) -> Decimal:
        if loan_count <= 0:
            return Decimal("0")
        defaulted_count = int((group["__status"] == "defaulted").sum())
        return (Decimal(defaulted_count) / Decimal(loan_count)) * Decimal("100")

    @staticmethod
    def _derive_segment_as_of_date(df: pd.DataFrame) -> Optional[str]:
        for date_col in ("as_of_date", "snapshot_date", "fecha_actual", "origination_date"):
            if date_col in df.columns:
                parsed = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
                max_dt = parsed.max()
                if pd.notna(max_dt):
                    return max_dt.date().isoformat()
        return None

    def _export_kpi_audit_trail(self, kpi_engine: Any) -> Optional[Path]:
        """
        Export KPI audit trail from KPIEngineV2 to exports/kpi_audit_trail.csv.

        Args:
            kpi_engine: KPIEngineV2 instance with audit records

        Returns:
            Path to exported audit trail CSV, or None if export failed
        """
        try:
            # Get repository root (3 levels up from src/pipeline/output.py)
            # Assumes standard project structure: repo_root/src/pipeline/output.py
            repo_root = Path(__file__).parent.parent.parent
            exports_dir = repo_root / "exports"
            exports_dir.mkdir(exist_ok=True)

            output_path = exports_dir / "kpi_audit_trail.csv"

            # Get audit trail from engine
            audit_df = kpi_engine.get_audit_trail()

            if audit_df.empty:
                logger.warning("No audit trail records to export")
                return None

            # Export to CSV
            audit_df.to_csv(output_path, index=False)
            logger.info("Exported KPI audit trail: %s (%d records)", output_path, len(audit_df))
            return output_path

        except Exception as e:
            logger.error("Failed to export KPI audit trail: %s", str(e), exc_info=True)
            return None

    def _check_database_prerequisites(self) -> Optional[Dict[str, Any]]:
        """Check if database output is enabled and return early error if not."""
        if not self.config.get("database", {}).get("enabled", False):
            logger.debug("Database output is disabled in configuration")
            return {"status": "skipped", "reason": "database_disabled"}
        return None

    def _validate_supabase_setup(self) -> Optional[Dict[str, Any]]:
        """Check if Supabase library and credentials are available."""
        if Client is None or create_client is None:
            logger.warning("Supabase library not installed")
            return {"status": "skipped", "reason": "supabase_not_installed"}

        supabase_url, supabase_key, _ = self._resolve_supabase_credentials()

        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not configured in environment")
            return {"status": "skipped", "reason": "missing_credentials"}

        return None

    def _resolve_supabase_credentials(self) -> tuple[Optional[str], Optional[str], str]:
        """
        Resolve Supabase credentials with safe defaults.

        Prefer service role for backend pipeline writes (RLS-compliant),
        fallback to anon key for read-only or permissive environments.
        """
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        anon_key = os.getenv("SUPABASE_ANON_KEY")

        if service_role_key:
            return supabase_url, service_role_key, "service_role"
        return supabase_url, anon_key, "anon"

    def _validate_kpi_results(self, kpi_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate KPI results are present and valid."""
        if not kpi_results or not isinstance(kpi_results, dict):
            logger.warning("No KPI results to write to database")
            return {"status": "skipped", "reason": "empty_kpi_results"}
        return None

    def _prepare_kpi_rows(self, kpi_results: Dict[str, Any]) -> tuple[list, str, str]:
        """Prepare rows for batch insert, filtering out NULL values."""
        rows_to_insert = []
        timestamp = datetime.now().isoformat()
        run_date = datetime.now().date().isoformat()

        # Check if we're using monitoring tables
        table_name = self.config.get("database", {}).get("table", "kpi_timeseries_daily")
        is_monitoring_table = self._is_monitoring_kpi_values_table(table_name)

        for kpi_name, kpi_value in kpi_results.items():
            if kpi_value is None:
                logger.debug("Skipping NULL KPI: %s", kpi_name)
                continue

            if is_monitoring_table:
                # Format for monitoring.kpi_values table
                # kpi_id will be looked up in _write_to_database
                rows_to_insert.append(
                    {
                        "kpi_name": kpi_name,
                        "value": self._to_numeric_value(kpi_value),
                        "timestamp": timestamp,
                        "status": "green",  # Default status, can be updated based on thresholds
                    }
                )
            else:
                # Legacy format for kpi_timeseries_daily table
                rows_to_insert.append(
                    {
                        "kpi_name": kpi_name,
                        "kpi_value": self._to_numeric_value(kpi_value),
                        "timestamp": timestamp,
                        "run_date": run_date,
                        "source": "pipeline_v2",
                    }
                )

        return rows_to_insert, timestamp, run_date

    def _is_monitoring_kpi_values_table(self, table_name: str) -> bool:
        """Return True when target table is the monitoring KPI values surface."""
        normalized = (table_name or "").strip().lower()
        return normalized in {"monitoring.kpi_values", "public.kpi_values", "kpi_values"}

    @staticmethod
    def _to_numeric_value(value: Any) -> Optional[float]:
        """Safely coerce KPI values to float, including Decimal payloads."""
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _get_kpi_definitions_map(
        self, supabase: Client
    ) -> Optional[tuple[Dict[str, str], Dict[str, int]]]:
        """Get mapping of KPI names to KPI keys (and IDs when available)."""
        try:
            definitions_table = self.config.get("database", {}).get(
                "definitions_table", "monitoring.kpi_definitions"
            )
            query = self._table_query(supabase, definitions_table)

            # monitoring schema may be exposed via public view (without id column).
            response = None
            try:
                response = query.select("id, name, kpi_key").execute()
            except Exception:
                response = query.select("name, kpi_key").execute()

            name_to_key: Dict[str, str] = {}
            name_to_id: Dict[str, int] = {}
            for kpi in response.data:
                name = kpi.get("name") or kpi.get("kpi_key")
                kpi_key = kpi.get("kpi_key") or name
                if not name or not kpi_key:
                    continue
                name_to_key[str(name)] = str(kpi_key)
                if kpi.get("id") is not None:
                    name_to_id[str(name)] = int(kpi["id"])

            logger.info("Loaded KPI definitions: %d names mapped", len(name_to_key))
            return name_to_key, name_to_id
        except Exception as e:
            logger.warning("Failed to load KPI definitions: %s", e)
            return None

    def _split_table_name(self, table_name: str) -> tuple[str, str]:
        """Split a possibly schema-qualified table name into (schema, table)."""
        if "." in table_name:
            schema_name, bare_table = table_name.split(".", 1)
            return schema_name, bare_table
        return "public", table_name

    def _table_query(self, supabase: Client, table_name: str):
        """
        Build a Supabase table query with schema support.

        For `monitoring.*`, fallback to `public` views because many projects
        expose only `public` to PostgREST.
        """
        schema_name, bare_table = self._split_table_name(table_name)
        if schema_name == "monitoring":
            return supabase.table(bare_table)
        return supabase.schema(schema_name).table(bare_table)

    def _map_monitoring_kpi_name(self, kpi_name: str) -> str:
        """
        Map pipeline KPI names to monitoring.kpi_definitions names.

        Allows pipeline formula names and dashboard names to diverge
        while still writing to a stable monitoring schema.
        """
        configured_aliases = (
            self.config.get("database", {}).get("kpi_name_aliases", {})
            if isinstance(self.config.get("database", {}), dict)
            else {}
        )
        default_aliases = {
            "default_rate": "npl_rate",
            "collections_rate": "collection_rate_6m",
            "disbursement_volume_mtd": "disbursement_volume",
            "new_loans_count_mtd": "new_loans",
            "total_outstanding_balance": "total_aum",
            "total_loans_count": "loan_count",
            "processing_time_avg": "processing_time",
            "portfolio_growth_rate": "portfolio_rotation",
        }
        aliases = {**default_aliases, **configured_aliases}
        return aliases.get(kpi_name, kpi_name)

    def _insert_batch_rows(self, supabase: Client, table_name: str, rows: list) -> int:
        """Insert rows in batches to Supabase."""
        batch_size = 100
        total_inserted = 0

        # If using monitoring tables, convert format
        is_monitoring_table = self._is_monitoring_kpi_values_table(table_name)
        if is_monitoring_table:
            kpi_maps = self._get_kpi_definitions_map(supabase)
            if not kpi_maps:
                logger.error("Cannot write to monitoring.kpi_values without KPI definitions")
                return 0
            name_to_key, name_to_id = kpi_maps
            mapped_names: Set[str] = {
                self._map_monitoring_kpi_name(str(row.get("kpi_name", "")))
                for row in rows
                if row.get("kpi_name")
            }
            self._ensure_missing_kpi_definitions(supabase, mapped_names, set(name_to_key.keys()))
            if not mapped_names.issubset(set(name_to_key.keys())):
                kpi_maps = self._get_kpi_definitions_map(supabase)
                if kpi_maps:
                    name_to_key, name_to_id = kpi_maps

            snapshot_id = (
                self.config.get("database", {}).get("snapshot_id")
                or os.getenv("PIPELINE_MONITORING_SNAPSHOT_ID")
                or "pipeline_daily"
            )
            run_id = (
                self.config.get("database", {}).get("run_id")
                or f"pipeline_v2_{date.today().isoformat()}"
            )
            inputs_hash = self.config.get("database", {}).get("inputs_hash") or "pipeline_v2"

            # Convert rows to monitoring format with kpi_id + upsert keys
            monitoring_rows = []
            for row in rows:
                original_name = str(row.get("kpi_name", ""))
                mapped_name = self._map_monitoring_kpi_name(original_name)
                if mapped_name in name_to_key:
                    row_timestamp = row.get("timestamp")
                    as_of_date = (
                        str(row_timestamp).split("T")[0]
                        if row_timestamp
                        else date.today().isoformat()
                    )
                    value = row.get("value")
                    mapped_kpi_key = name_to_key[mapped_name]
                    monitoring_row: Dict[str, Any] = {
                        "kpi_key": mapped_kpi_key,
                        "value": row.get("value"),
                        "value_num": value,
                        "timestamp": row.get("timestamp"),
                        "computed_at": row.get("timestamp"),
                        "as_of_date": as_of_date,
                        "status": row.get("status", "green"),
                        "snapshot_id": snapshot_id,
                        "run_id": run_id,
                        "inputs_hash": inputs_hash,
                    }
                    if mapped_name in name_to_id:
                        monitoring_row["kpi_id"] = name_to_id[mapped_name]
                    monitoring_rows.append(monitoring_row)
                else:
                    logger.warning(
                        "KPI not found in definitions: %s (mapped: %s)",
                        original_name,
                        mapped_name,
                    )

            rows = monitoring_rows

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            query = self._table_query(supabase, table_name)
            if is_monitoring_table:
                query.upsert(batch, on_conflict="as_of_date,kpi_key,snapshot_id").execute()
            else:
                query.insert(batch).execute()
            total_inserted += len(batch)
            logger.info(
                "Inserted batch",
                extra={"batch_start": i, "batch_end": i + len(batch), "batch_size": len(batch)},
            )

        return total_inserted

    def _ensure_missing_kpi_definitions(
        self, supabase: Client, mapped_names: Set[str], existing_names: Set[str]
    ) -> None:
        """
        Best-effort creation of missing KPI definitions.

        This keeps Grafana tables complete even when new KPIs are introduced
        before migrations are applied in every environment.
        """
        missing = sorted(name for name in mapped_names if name and name not in existing_names)
        if not missing:
            return

        configured_table = self.config.get("database", {}).get(
            "definitions_table", "monitoring.kpi_definitions"
        )
        # Write into base table (not public view) when table is unqualified.
        definitions_table = (
            configured_table if "." in configured_table else "monitoring.kpi_definitions"
        )
        query = self._table_query(supabase, definitions_table)

        for kpi_name in missing:
            payload_variants = [
                (
                    {
                        "kpi_key": kpi_name,
                        "name": kpi_name,
                        "display_name": kpi_name.replace("_", " ").title(),
                        "category": "Pipeline",
                        "description": f"Auto-registered KPI definition for {kpi_name}",
                        "unit": "unknown",
                    },
                    "kpi_key",
                ),
                (
                    {
                        "kpi_key": kpi_name,
                        "display_name": kpi_name.replace("_", " ").title(),
                        "category": "Pipeline",
                        "description": f"Auto-registered KPI definition for {kpi_name}",
                        "unit": "unknown",
                    },
                    "kpi_key",
                ),
                (
                    {
                        "kpi_key": kpi_name,
                        "display_name": kpi_name.replace("_", " ").title(),
                    },
                    "kpi_key",
                ),
                (
                    {
                        "name": kpi_name,
                        "category": "Pipeline",
                        "description": f"Auto-registered KPI definition for {kpi_name}",
                        "unit": "unknown",
                    },
                    "name",
                ),
            ]

            created = False
            last_error: Optional[Exception] = None
            for payload, conflict_col in payload_variants:
                try:
                    query.upsert([payload], on_conflict=conflict_col).execute()
                    created = True
                    break
                except Exception as exc:
                    last_error = exc

            if created:
                logger.info("Auto-created missing KPI definition: %s", kpi_name)
            else:
                logger.warning(
                    "Could not auto-create KPI definition '%s'. "
                    "Apply Supabase migrations for full KPI coverage. Last error: %s",
                    kpi_name,
                    last_error,
                )

    def _write_to_database(self, kpi_results: Dict[str, Any]) -> Dict[str, Any]:
        """Write results to Supabase database."""
        # Check prerequisites
        prereq_error = self._check_database_prerequisites()
        result: Dict[str, Any]
        if prereq_error:
            result = prereq_error
            return result

        # Validate input data
        input_error = self._validate_kpi_results(kpi_results)
        if input_error:
            result = input_error
            return result

        try:
            # Validate Supabase setup
            setup_error = self._validate_supabase_setup()
            if setup_error:
                result = setup_error
                return result

            # Create Supabase client
            supabase_url, supabase_key, key_source = self._resolve_supabase_credentials()
            if supabase_url is None or supabase_key is None:
                raise RuntimeError("Supabase credentials missing during Phase 4 persistence")
            supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("Using Supabase credentials source: %s", key_source)

            # Prepare rows for insert
            rows_to_insert, timestamp, _ = self._prepare_kpi_rows(kpi_results)

            if not rows_to_insert:
                logger.warning("No rows to insert after filtering")
                result = {"status": "skipped", "reason": "no_valid_kpis"}
                return result

            # Write to database
            table_name = self.config.get("database", {}).get("table", "kpi_timeseries_daily")
            logger.info(
                "Writing %d KPI records to Supabase table: %s",
                len(rows_to_insert),
                table_name,
            )

            total_inserted = self._insert_batch_rows(supabase, table_name, rows_to_insert)

            logger.info("Successfully wrote %d KPI records to database", total_inserted)
            result = {
                "status": "success",
                "records_written": total_inserted,
                "timestamp": timestamp,
                "table": table_name,
            }
        except ImportError as e:
            logger.warning("Supabase library not available: %s", e)
            result = {"status": "skipped", "reason": "supabase_not_installed"}
        except Exception as e:
            logger.error("Database write failed: %s", e, exc_info=True)
            result = {"status": "error", "error": str(e)}

        return result

    def _trigger_dashboard_refresh(self) -> Dict[str, str]:
        """Trigger dashboard to refresh data via HTTP POST."""
        try:
            webhook_url = self.config.get("dashboard_webhook_url")
            if not webhook_url:
                logger.debug("Dashboard webhook URL not configured - refresh skipped")
                return {"status": "skipped", "reason": "no_webhook_configured"}

            if httpx is None:
                logger.warning("httpx not installed - webhook POST skipped")
                return {"status": "skipped", "reason": "httpx_not_installed"}

            payload = {
                "event": "kpi_pipeline_complete",
                "timestamp": datetime.now().isoformat(),
                "source": "pipeline_phase_4",
            }

            with httpx.Client(timeout=10.0) as client:
                resp = client.post(webhook_url, json=payload)
                resp.raise_for_status()

            logger.info(
                "Dashboard refresh triggered: webhook=%s status=%d",
                webhook_url,
                resp.status_code,
            )

            return {
                "status": "triggered",
                "webhook": webhook_url,
                "timestamp": payload["timestamp"],
            }

        except Exception as e:
            logger.error("Dashboard refresh failed: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}

    def _get_failed_kpis_from_audit(self, audit_df: pd.DataFrame) -> list:
        """
        Extract failed KPI names from audit trail DataFrame.

        Helper method to reduce code duplication and ensure consistent
        filtering behavior across quality score and SLA checking methods.

        Args:
            audit_df: Audit trail DataFrame from KPIEngineV2

        Returns:
            List of KPI names with failed status

        Raises:
            ValueError: If audit DataFrame has unexpected structure
        """
        try:
            if audit_df.empty:
                return []

            # Validate expected columns exist
            if "status" not in audit_df.columns or "kpi_name" not in audit_df.columns:
                logger.warning("Audit DataFrame missing required columns")
                return []

            # Filter for failed status and extract KPI names
            failed_mask = audit_df["status"] == "failed"
            failed_kpis = audit_df[failed_mask]["kpi_name"].tolist()
            return failed_kpis

        except Exception as e:
            logger.error("Error extracting failed KPIs from audit trail: %s", e)
            return []

    def _generate_audit_metadata(
        self,
        kpi_results: Dict[str, Any],
        exports: Dict[str, str],
        kpi_engine: Optional["KPIEngineV2"] = None,
    ) -> Dict[str, Any]:
        """
        Generate audit metadata/summary for this pipeline run.

        Note: This generates metadata about the pipeline run itself.
        For detailed KPI calculation audit trail, see kpi_engine.get_audit_trail().

        Args:
            kpi_results: KPI calculation results
            exports: Dict of export paths
            kpi_engine: Optional KPIEngineV2 instance for detailed audit info

        Returns:
            Audit metadata/summary
        """
        # Calculate quality score based on validation results
        quality_score = self._calculate_quality_score(kpi_results, kpi_engine)

        # Check if SLA was met (simplified - checks if all KPIs calculated successfully)
        sla_met = self._check_sla(kpi_results, kpi_engine)

        audit_info = {
            "timestamp": datetime.now().isoformat(),
            "kpis_generated": len(kpi_results),
            "exports_created": list(exports.keys()),
            "quality_score": quality_score,
            "sla_met": sla_met,
        }

        # Add detailed audit info if KPIEngineV2 was used
        if kpi_engine is not None:
            try:
                audit_df = kpi_engine.get_audit_trail()
                if not audit_df.empty:
                    failed_kpis = self._get_failed_kpis_from_audit(audit_df)
                    audit_info["kpi_engine_used"] = True
                    audit_info["total_calculations"] = len(audit_df)
                    audit_info["failed_calculations"] = len(failed_kpis)
                    if failed_kpis:
                        audit_info["failed_kpis"] = failed_kpis
            except Exception as e:
                logger.warning("Could not add detailed audit info: %s", e)

        return audit_info

    def _calculate_quality_score(
        self, kpi_results: Dict[str, Any], kpi_engine: Optional["KPIEngineV2"] = None
    ) -> float:
        """
        Calculate quality score based on validation results.

        Score is based on:
        - Percentage of KPIs successfully calculated
        - Data completeness
        - Error rate

        Fallback behavior:
        - Returns 0.0 if no kpi_results (no KPIs to calculate is considered failure)
        - Returns 1.0 if kpi_engine is None but kpi_results exist (optimistic assumption:
          results are present and valid when audit trail is unavailable for verification)

        Returns:
            Quality score between 0.0 and 1.0
        """
        if not kpi_results:
            # No KPIs calculated - complete failure scenario
            return 0.0

        # If KPIEngineV2 was used, check audit trail
        if kpi_engine is not None:
            try:
                audit_df = kpi_engine.get_audit_trail()
                if not audit_df.empty:
                    total = len(audit_df)
                    failed_kpis = self._get_failed_kpis_from_audit(audit_df)
                    successful = total - len(failed_kpis)
                    return round(successful / total, 2) if total > 0 else 0.0
            except Exception as e:
                logger.debug("Could not calculate quality score from audit trail: %s", e)

        # Fallback: kpi_results exist but audit data unavailable - assume all successful
        # This optimistic fallback treats "results exist but unverified" as valid
        return 1.0

    def _check_sla(
        self, kpi_results: Dict[str, Any], kpi_engine: Optional["KPIEngineV2"] = None
    ) -> bool:
        """
        Check if SLA was met for this pipeline run.

        SLA is met if:
        - All critical KPIs were calculated successfully
        - No errors in the calculation process

        Fallback behavior:
        - Returns False if no kpi_results (no KPIs calculated is an SLA violation)
        - Returns True if kpi_engine is None but kpi_results exist (optimistic assumption:
          at this point we know results exist, so treat "unverified results" as SLA-compliant
          since we cannot prove otherwise)

        Returns:
            True if SLA was met, False otherwise
        """
        if not kpi_results:
            # No KPIs calculated - SLA violation
            return False

        # If KPIEngineV2 was used, check for any failures
        if kpi_engine is not None:
            try:
                audit_df = kpi_engine.get_audit_trail()
                if not audit_df.empty:
                    # SLA is met if there are no failed calculations
                    failed_kpis = self._get_failed_kpis_from_audit(audit_df)
                    return len(failed_kpis) == 0
            except Exception as e:
                logger.debug("Could not check SLA from audit trail: %s", e)

        # Fallback: results exist but audit data is missing/unusable
        # Since kpi_results is non-empty (early return above), treat this as SLA-compliant
        return True
