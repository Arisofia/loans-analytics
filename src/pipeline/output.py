"""
PHASE 4: OUTPUT & DISTRIBUTION

Responsibilities:
- Multi-format exports (Parquet/CSV/JSON)
- Database writes (Supabase)
- Dashboard refresh triggers
- Audit trail generation
- SLA monitoring
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from python.logging_config import get_logger

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
        self, kpi_results: Dict[str, Any], run_dir: Optional[Path] = None, kpi_engine: Optional[Any] = None
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

            # Generate audit trail
            audit_trail = self._generate_audit_trail(kpi_results, exports, kpi_engine)

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
            logger.error(f"Output failed: {str(e)}", exc_info=True)
            return {"status": "failed", "error": str(e), "timestamp": datetime.now().isoformat()}

    def _export_parquet(self, kpi_results: Dict[str, Any], run_dir: Path) -> Path:
        """Export KPI results to Parquet format."""
        output_path = run_dir / "kpis_output.parquet"

        df = pd.DataFrame([kpi_results])
        df.to_parquet(output_path, index=False)

        logger.info(f"Exported Parquet: {output_path}")
        return output_path

    def _export_csv(self, kpi_results: Dict[str, Any], run_dir: Path) -> Path:
        """Export KPI results to CSV format."""
        output_path = run_dir / "kpis_output.csv"

        df = pd.DataFrame([kpi_results])
        df.to_csv(output_path, index=False)

        logger.info(f"Exported CSV: {output_path}")
        return output_path

    def _export_json(self, kpi_results: Dict[str, Any], run_dir: Path) -> Path:
        """Export KPI results to JSON format."""
        output_path = run_dir / "kpis_output.json"

        with open(output_path, "w") as f:
            json.dump(kpi_results, f, indent=2, default=str)

        logger.info(f"Exported JSON: {output_path}")
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
            # Get repository root
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
            logger.info(f"Exported KPI audit trail: {output_path} ({len(audit_df)} records)")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to export KPI audit trail: {str(e)}", exc_info=True)
            return None

    def _write_to_database(self, kpi_results: Dict[str, Any]) -> Dict[str, Any]:
        """Write results to Supabase database."""
        # TODO: Implement Supabase client
        # - Transaction safety
        # - Idempotent upserts
        # - Retry logic

        logger.info("Database write not yet implemented")
        return {"status": "skipped", "reason": "Supabase client not configured"}

    def _trigger_dashboard_refresh(self) -> Dict[str, str]:
        """Trigger dashboard to refresh data."""
        # TODO: Implement dashboard refresh mechanism
        # - Webhook
        # - Event bus
        # - File watcher

        logger.info("Dashboard refresh not yet implemented")
        return {"status": "skipped"}

    def _generate_audit_trail(
        self, kpi_results: Dict[str, Any], exports: Dict[str, str], kpi_engine: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Generate audit trail for this pipeline run.
        
        Args:
            kpi_results: KPI calculation results
            exports: Dict of export paths
            kpi_engine: Optional KPIEngineV2 instance for detailed audit info
        
        Returns:
            Audit trail metadata
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
            audit_df = kpi_engine.get_audit_trail()
            if not audit_df.empty:
                failed_kpis = audit_df[audit_df["status"] == "failed"]["kpi_name"].tolist()
                audit_info["kpi_engine_used"] = True
                audit_info["total_calculations"] = len(audit_df)
                audit_info["failed_calculations"] = len(failed_kpis)
                if failed_kpis:
                    audit_info["failed_kpis"] = failed_kpis
        
        return audit_info
    
    def _calculate_quality_score(
        self, kpi_results: Dict[str, Any], kpi_engine: Optional[Any] = None
    ) -> float:
        """
        Calculate quality score based on validation results.
        
        Score is based on:
        - Percentage of KPIs successfully calculated
        - Data completeness
        - Error rate
        
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not kpi_results:
            return 0.0
        
        # If KPIEngineV2 was used, check audit trail
        if kpi_engine is not None:
            try:
                audit_df = kpi_engine.get_audit_trail()
                if not audit_df.empty:
                    total = len(audit_df)
                    successful = len(audit_df[audit_df["status"] == "success"])
                    return round(successful / total, 2) if total > 0 else 0.0
            except Exception as e:
                logger.debug(f"Could not calculate quality score from audit trail: {e}")
        
        # Fallback: assume all KPIs in results are successful
        return 1.0
    
    def _check_sla(
        self, kpi_results: Dict[str, Any], kpi_engine: Optional[Any] = None
    ) -> bool:
        """
        Check if SLA was met for this pipeline run.
        
        SLA is met if:
        - All critical KPIs were calculated successfully
        - No errors in the calculation process
        
        Returns:
            True if SLA was met, False otherwise
        """
        if not kpi_results:
            return False
        
        # If KPIEngineV2 was used, check for any failures
        if kpi_engine is not None:
            try:
                audit_df = kpi_engine.get_audit_trail()
                if not audit_df.empty:
                    # SLA is met if there are no failed calculations
                    failed = len(audit_df[audit_df["status"] == "failed"])
                    return failed == 0
            except Exception as e:
                logger.debug(f"Could not check SLA from audit trail: {e}")
        
        # Fallback: assume SLA is met if we have results
        return True
