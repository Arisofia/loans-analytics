import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.config.paths import Paths
from src.pipeline.models import OutputResult, PersistContext
from src.pipeline.utils import ensure_dir, hash_file, utc_now, write_json

logger = logging.getLogger(__name__)


class UnifiedOutput:
    """Phase 4: Output persistence, optional cloud export, and manifest generation."""

    def __init__(self, config: Dict[str, Any], run_id: Optional[str] = None):
        self.config = config.get("pipeline", {}).get("phases", {}).get("outputs", {})
        self.azure_config = self.config.get("azure", {})
        self.run_id = run_id or f"out_{uuid.uuid4().hex[:12]}"
        self.audit_log: List[Dict[str, Any]] = []

    def _log_event(self, event: str, status: str, **details: Any) -> None:
        entry = {
            "run_id": self.run_id,
            "event": event,
            "status": status,
            "timestamp": utc_now(),
            **details,
        }
        self.audit_log.append(entry)
        logger.info("[Output:%s] %s | %s", event, status, details)

    def upload_to_azure(self, file_paths: List[Path], run_id: str) -> Dict[str, str]:
        if not self.azure_config.get("enabled"):
            return {}

        from src.integrations.azure_outputs import AzureStorageClient
        
        connection_string = self.azure_config.get("storage_connection_string")
        client = AzureStorageClient(connection_string=connection_string)
        
        if not client.client:
            self._log_event("azure_upload", "skipped", reason="Client not initialized (check credentials)")
            return {}

        prefix = f"{self.azure_config.get('prefix', 'analytics')}/{run_id}"
        uploaded = client.upload_files(file_paths, prefix)

        self._log_event("azure_upload", "success", uploaded_count=len(uploaded))
        return uploaded

    def upload_to_supabase(self, df: pd.DataFrame, metrics: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        supabase_cfg = self.config.get("supabase", {})
        if not supabase_cfg.get("enabled"):
            return {}

        from src.integrations.supabase_client import SupabaseOutputClient
        
        client = SupabaseOutputClient()
        if not client.client:
            self._log_event("supabase_upload", "skipped", reason="Client not initialized (check credentials)")
            return {}

        results = {}
        
        # 1. Insert metrics
        kpi_results = client.insert_kpi_metrics(metrics, run_id)
        results["kpi_metrics"] = kpi_results
        
        # 2. Insert raw data if configured
        tables = supabase_cfg.get("tables", [])
        if "fact_loans" in tables:
            inserted_count = client.insert_raw_data(df, "fact_loans", run_id)
            results["fact_loans_inserted"] = inserted_count

        self._log_event("supabase_upload", "success", results=results)
        return results

    def persist(
        self,
        df: pd.DataFrame,
        metrics: Dict[str, Any],
        metadata: Dict[str, Any],
        run_ids: Dict[str, str],
        context: Optional[PersistContext] = None,
    ) -> OutputResult:
        self._log_event("start", "initiated", run_ids=run_ids)

        ctx = context or PersistContext()
        quality_checks = ctx.quality_checks
        compliance_report_path = ctx.compliance_report_path
        timeseries = ctx.timeseries

        storage_cfg = self.config.get("storage", {})
        base_dir = ensure_dir(Path(storage_cfg.get("local_dir", str(Paths.metrics_dir()))))
        manifest_dir = ensure_dir(
            Path(storage_cfg.get("manifest_dir", str(Paths.runs_artifacts_dir())))
        )

        master_run_id = run_ids.get("pipeline", run_ids.get("ingest", "unknown"))
        parquet_path = base_dir / f"{master_run_id}.parquet"
        csv_path = base_dir / f"{master_run_id}.csv"
        metrics_path = base_dir / f"{master_run_id}_metrics.json"
        manifest_path = manifest_dir / master_run_id / f"{master_run_id}_manifest.json"

        output_paths: Dict[str, str] = {}
        formats = set(self.config.get("formats", ["parquet", "csv", "json"]))
        if "parquet" in formats:
            df.to_parquet(parquet_path, index=False)
            output_paths["parquet"] = str(parquet_path)
        if "csv" in formats:
            df.to_csv(csv_path, index=False)
            output_paths["csv"] = str(csv_path)
        if "json" in formats:
            # Include metadata for legacy compatibility and self-documentation
            metrics_to_write = {
                **metrics,
                "run_id": master_run_id,
                "timestamp": utc_now(),
                "pipeline_status": "success",
            }
            write_json(metrics_path, metrics_to_write)
            output_paths["metrics_json"] = str(metrics_path)

        timeseries_paths: Dict[str, str] = {}
        if timeseries:
            ts_dir = ensure_dir(base_dir / "timeseries")
            for rollup, frame in timeseries.items():
                ts_path = ts_dir / f"{master_run_id}_{rollup}.parquet"
                frame.to_parquet(ts_path, index=False)
                timeseries_paths[rollup] = str(ts_path)

        file_hashes: Dict[str, str] = {}
        for key, path_str in output_paths.items():
            path_obj = Path(path_str)
            if path_obj.exists():
                file_hashes[key] = hash_file(path_obj)
        for key, path_str in timeseries_paths.items():
            path_obj = Path(path_str)
            if path_obj.exists():
                file_hashes[f"timeseries_{key}"] = hash_file(path_obj)

        manifest: Dict[str, Any] = {
            "run_id": master_run_id,
            "sub_runs": run_ids,
            "generated_at": utc_now(),
            "metrics": metrics,
            "metadata": metadata,
            "quality_checks": quality_checks or {},
            "files": output_paths,
            "timeseries": timeseries_paths,
            "compliance_report": str(compliance_report_path) if compliance_report_path else None,
            "file_hashes": file_hashes,
        }

        write_json(manifest_path, manifest)

        azure_blobs = self.upload_to_azure(
            [parquet_path, csv_path, metrics_path, manifest_path], master_run_id
        )
        if azure_blobs:
            manifest["azure_blobs"] = azure_blobs
            write_json(manifest_path, manifest)

        supabase_results = self.upload_to_supabase(df, metrics, master_run_id)
        if supabase_results:
            manifest["supabase"] = supabase_results
            write_json(manifest_path, manifest)

        # If configured, trigger dashboard/export notifications to external platforms
        triggers_cfg = self.config.get("dashboard_triggers", {})
        if triggers_cfg.get("enabled"):
            try:
                # Lazy import to avoid pulling integration deps unless needed
                from src.integrations.unified_output_manager import \
                    UnifiedOutputManager

                outputs = triggers_cfg.get("outputs", ["figma", "azure"])
                manager = UnifiedOutputManager()
                # Allow basic client configuration via triggers cfg if provided
                manager.configure_clients(triggers_cfg.get("clients", {}))

                # Use a lightweight export that only pushes KPI metrics by default
                trigger_results = manager.export_kpi_metrics_only(
                    metrics, master_run_id, enabled_outputs=outputs
                )

                # Record trigger results in manifest and persist
                if "triggers" not in manifest:
                    manifest["triggers"] = {}

                # Check for dictionary type for mypy safety
                manifest_triggers = manifest["triggers"]
                if isinstance(manifest_triggers, dict):
                    manifest_triggers["dashboard_trigger"] = trigger_results

                write_json(manifest_path, manifest)

                self._log_event("dashboard_trigger", "success", result_summary=str(trigger_results))
            except Exception as exc:  # pragma: no cover - defensive logging
                self._log_event("dashboard_trigger", "failed", error=str(exc))

        self._log_event("complete", "success", manifest=str(manifest_path))

        return OutputResult(
            manifest=manifest, manifest_path=manifest_path, output_paths=output_paths
        )
