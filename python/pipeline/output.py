import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import ResourceExistsError

logger = logging.getLogger(__name__)

class UnifiedOutput:
    """Phase 4: Output Persistence, Azure Export, and Manifest Generation."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("pipeline", {}).get("phases", {}).get("outputs", {})
        self.azure_config = self.config.get("azure", {})
        self.run_id = f"out_{uuid.uuid4().hex[:12]}"
        self.audit_log: List[Dict[str, Any]] = []

    def _log_event(self, event: str, status: str, **details: Any) -> None:
        entry = {
            "run_id": self.run_id,
            "event": event,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        }
        self.audit_log.append(entry)
        logger.info(f"[Output:{event}] {status} | {details}")

    def _guess_content_type(self, path: Path) -> str:
        mapping = {".csv": "text/csv", ".json": "application/json", ".parquet": "application/octet-stream"}
        return mapping.get(path.suffix.lower(), "application/octet-stream")

    def upload_to_azure(self, file_paths: List[Path], run_id: str) -> Dict[str, str]:
        """Upload a set of files to Azure Blob Storage."""
        if not self.azure_config.get("enabled"):
            return {}

        import os
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

        for path in file_paths:
            if not path.exists():
                continue
            
            blob_name = f"{prefix}/{path.name}"
            with path.open("rb") as data:
                container_client.upload_blob(
                    name=blob_name,
                    data=data,
                    overwrite=True,
                    content_settings=ContentSettings(content_type=self._guess_content_type(path))
                )
            uploaded[path.name] = f"{container_name}/{blob_name}"
        
        self._log_event("azure_upload", "success", uploaded_count=len(uploaded))
        return uploaded

    def persist(
        self, 
        df: pd.DataFrame, 
        metrics: Dict[str, Any], 
        metadata: Dict[str, Any], 
        run_ids: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute the output phase: write files, generate manifest, and upload to cloud."""
        self._log_event("start", "initiated", run_ids=run_ids)
        
        base_dir = Path(self.config.get("storage", {}).get("local_dir", "data/metrics"))
        base_dir.mkdir(parents=True, exist_ok=True)
        
        master_run_id = run_ids.get("ingest", "unknown")
        metrics_path = base_dir / f"{master_run_id}.parquet"
        csv_path = base_dir / f"{master_run_id}.csv"
        manifest_path = base_dir / f"{master_run_id}_manifest.json"

        # 1. Write Data Files
        df.to_parquet(metrics_path, index=False)
        df.to_csv(csv_path, index=False)
        self._log_event("persistence", "success", parquet=str(metrics_path), csv=str(csv_path))

        # 2. Build Manifest
        manifest = {
            "run_id": master_run_id,
            "sub_runs": run_ids,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "metadata": metadata,
            "files": {
                "parquet": str(metrics_path),
                "csv": str(csv_path)
            }
        }

        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, default=str)
        
        # 3. Azure Export
        azure_blobs = self.upload_to_azure([metrics_path, csv_path, manifest_path], master_run_id)
        if azure_blobs:
            manifest["azure_blobs"] = azure_blobs
            # Re-write manifest with azure links
            with manifest_path.open("w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, default=str)

        self._log_event("complete", "success", manifest=str(manifest_path))
        return manifest
