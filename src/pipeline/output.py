import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.config.paths import Paths
from src.pipeline.utils import ensure_dir, hash_file, utc_now, write_json

logger = logging.getLogger(__name__)


@dataclass
class OutputResult:
    manifest: Dict[str, Any]
    manifest_path: Path
    output_paths: Dict[str, str]


@dataclass
class PersistContext:
    """Context for output persistence including quality checks and reports."""

    quality_checks: Optional[Dict[str, Any]] = None
    compliance_report_path: Optional[Path] = None
    timeseries: Optional[Dict[str, pd.DataFrame]] = None


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

    def _guess_content_type(self, path: Path) -> str:
        mapping = {
            ".csv": "text/csv",
            ".json": "application/json",
            ".parquet": "application/octet-stream",
        }
        return mapping.get(path.suffix.lower(), "application/octet-stream")

    def upload_to_azure(self, file_paths: List[Path], run_id: str) -> Dict[str, str]:
        if not self.azure_config.get("enabled"):
            return {}

        import os
        from concurrent.futures import ThreadPoolExecutor

        from azure.core.exceptions import ResourceExistsError
        from azure.storage.blob import BlobServiceClient, ContentSettings

        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            self._log_event("azure_upload", "skipped", reason="No connection string found")
            return {}

        container_name = self.azure_config.get("container", "pipeline-runs")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        try:
            container_client.create_container()
        except ResourceExistsError:
            pass

        prefix = f"{self.azure_config.get('prefix', 'analytics')}/{run_id}"
        uploaded: Dict[str, str] = {}

        def _upload_single_file(path: Path):
            if not path.exists():
                return None
            blob_name = f"{prefix}/{path.name}"
            with path.open("rb") as data:
                container_client.upload_blob(
                    name=blob_name,
                    data=data,
                    overwrite=True,
                    content_settings=ContentSettings(content_type=self._guess_content_type(path)),
                )
            return path.name, f"{container_name}/{blob_name}"

        with ThreadPoolExecutor(max_workers=min(len(file_paths), 10)) as executor:
            results = list(executor.map(_upload_single_file, file_paths))

        for res in results:
            if res:
                uploaded[res[0]] = res[1]

        self._log_event("azure_upload", "success", uploaded_count=len(uploaded))
        return uploaded

    def persist(
        self,
        df: pd.DataFrame,
        metrics: Dict[str, Any],
        metadata: Dict[str, Any],
        run_ids: Dict[str, str],
        context: Optional[PersistContext] = None,
        **kwargs: Any,
    ) -> OutputResult:
        self._log_event("start", "initiated", run_ids=run_ids)

        # Backward compatibility for positional or keyword arguments
        quality_checks = kwargs.get("quality_checks")
        compliance_report_path = kwargs.get("compliance_report_path")
        timeseries = kwargs.get("timeseries")

        if context:
            quality_checks = quality_checks or context.quality_checks
            compliance_report_path = compliance_report_path or context.compliance_report_path
            timeseries = timeseries or context.timeseries

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
            write_json(metrics_path, metrics)
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

        manifest = {
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

        self._log_event("complete", "success", manifest=str(manifest_path))

        return OutputResult(
            manifest=manifest, manifest_path=manifest_path, output_paths=output_paths
        )
