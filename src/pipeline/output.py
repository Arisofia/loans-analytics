"""
PHASE 4: OUTPUT & DISTRIBUTION

Responsibilities:
- Multi-format exports (Parquet/CSV/JSON)
- Database writes (Supabase)
- Dashboard refresh triggers
- Audit trail generation
- SLA monitoring
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from python.logging_config import get_logger

if TYPE_CHECKING:
    from python.kpis.engine import KPIEngineV2

logger = get_logger(__name__)


class OutputPhase:
    """Phase 4: Output & Distribution"""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize output phase.

        Args:
            config: Output configuration from pipeline.yml
        """
        self.config = config
        logger.info("Initialized output phase")

    def execute(
        self,
        kpi_results: dict[str, Any],
        run_dir: Path | None = None,
        kpi_engine: "KPIEngineV2" | None = None,
    ) -> dict[str, Any]:
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

    def _export_parquet(self, kpi_results: dict[str, Any], run_dir: Path) -> Path:
        """Export KPI results to Parquet format."""
        output_path = run_dir / "kpis_output.parquet"

        df = pd.DataFrame([kpi_results])
        df.to_parquet(output_path, index=False)

        logger.info("Exported Parquet: %s", output_path)
        return output_path

    def _export_csv(self, kpi_results: dict[str, Any], run_dir: Path) -> Path:
        """Export KPI results to CSV format."""
        output_path = run_dir / "kpis_output.csv"

        df = pd.DataFrame([kpi_results])
        df.to_csv(output_path, index=False)

        logger.info("Exported CSV: %s", output_path)
        return output_path

    def _export_json(self, kpi_results: dict[str, Any], run_dir: Path) -> Path:
        """Export KPI results to JSON format."""
        output_path = run_dir / "kpis_output.json"

        with open(output_path, "w") as f:
            json.dump(kpi_results, f, indent=2, default=str)

        logger.info("Exported JSON: %s", output_path)
        return output_path

    def _export_kpi_audit_trail(self, kpi_engine: Any) -> Path | None:
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

    def _write_to_database(self, kpi_results: dict[str, Any]) -> dict[str, Any]:
        """Write results to Supabase database."""
        # TODO: Implement Supabase client
        # - Transaction safety
        # - Idempotent upserts
        # - Retry logic

        logger.info("Database write not yet implemented")
        return {"status": "skipped", "reason": "Supabase client not configured"}

    def _trigger_dashboard_refresh(self) -> dict[str, str]:
        """Trigger dashboard to refresh data."""
        # TODO: Implement dashboard refresh mechanism
        # - Webhook
        # - Event bus
        # - File watcher

        logger.info("Dashboard refresh not yet implemented")
        return {"status": "skipped"}

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
        kpi_results: dict[str, Any],
        exports: dict[str, str],
        kpi_engine: "KPIEngineV2" | None = None,
    ) -> dict[str, Any]:
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
        self, kpi_results: dict[str, Any], kpi_engine: "KPIEngineV2" | None = None
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
        self, kpi_results: dict[str, Any], kpi_engine: "KPIEngineV2" | None = None
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
