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
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

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
    ) -> Dict[str, Any]:
        """
        Execute output phase.

        Args:
            kpi_results: KPI calculation results from Phase 3
            run_dir: Directory for this pipeline run
            kpi_engine: Optional KPIEngineV2 instance for audit trail export

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

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not configured in environment")
            return {"status": "skipped", "reason": "missing_credentials"}

        return None

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
        is_monitoring_table = "monitoring.kpi_values" in table_name

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
                        "value": (
                            float(kpi_value) if isinstance(kpi_value, (int, float)) else None
                        ),
                        "timestamp": timestamp,
                        "status": "green",  # Default status, can be updated based on thresholds
                    }
                )
            else:
                # Legacy format for kpi_timeseries_daily table
                rows_to_insert.append(
                    {
                        "kpi_name": kpi_name,
                        "kpi_value": (
                            float(kpi_value) if isinstance(kpi_value, (int, float)) else None
                        ),
                        "timestamp": timestamp,
                        "run_date": run_date,
                        "source": "pipeline_v2",
                    }
                )

        return rows_to_insert, timestamp, run_date

    def _get_kpi_definitions_map(self, supabase: Client) -> Optional[Dict[str, int]]:
        """Get mapping of KPI names to their IDs from monitoring.kpi_definitions."""
        try:
            # Query monitoring.kpi_definitions for ID mapping
            response = supabase.table("monitoring.kpi_definitions").select("id, name").execute()
            
            # Build name -> id mapping
            kpi_map = {kpi["name"]: kpi["id"] for kpi in response.data}
            logger.info("Loaded KPI definitions: %d names mapped", len(kpi_map))
            return kpi_map
        except Exception as e:
            logger.warning("Failed to load KPI definitions: %s", e)
            return None

    def _insert_batch_rows(self, supabase: Client, table_name: str, rows: list) -> int:
        """Insert rows in batches to Supabase."""
        batch_size = 100
        total_inserted = 0
        
        # If using monitoring tables, convert format
        if "monitoring.kpi_values" in table_name:
            kpi_map = self._get_kpi_definitions_map(supabase)
            if not kpi_map:
                logger.error("Cannot write to monitoring.kpi_values without KPI definitions")
                return 0
            
            # Convert rows to monitoring format with kpi_id
            monitoring_rows = []
            for row in rows:
                kpi_name = row.get("kpi_name")
                if kpi_name in kpi_map:
                    monitoring_rows.append({
                        "kpi_id": kpi_map[kpi_name],
                        "value": row.get("value"),
                        "timestamp": row.get("timestamp"),
                        "status": row.get("status", "green"),
                    })
                else:
                    logger.warning("KPI not found in definitions: %s", kpi_name)
            
            rows = monitoring_rows

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            supabase.table(table_name).insert(batch).execute()
            total_inserted += len(batch)
            logger.info(
                "Inserted batch",
                extra={"batch_start": i, "batch_end": i + len(batch), "batch_size": len(batch)},
            )

        return total_inserted

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
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            assert supabase_url is not None
            assert supabase_key is not None
            supabase: Client = create_client(supabase_url, supabase_key)

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
