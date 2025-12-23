import json
import logging
from datetime import datetime, timezone
from numbers import Number
from typing import Any, Dict, Optional

from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings


class AzureBlobKPIExporter:
    """Publishes KPI payloads to Azure Blob Storage with traceable metadata."""

    def __init__(
        self,
        *,
        container_name: Optional[str] = None,
        account_url: Optional[str] = None,
        connection_string: Optional[str] = None,
        credential: Optional[Any] = None,
        blob_service_client: Optional[BlobServiceClient] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        incoming_config = config or kwargs.get("config")
        if container_name is None and isinstance(incoming_config, dict):
            container_name = container_name or incoming_config.get("container_name")
            account_url = account_url or incoming_config.get("account_url")
            connection_string = connection_string or incoming_config.get("connection_string")
            credential = credential or incoming_config.get("credential")
            blob_service_client = blob_service_client or incoming_config.get("blob_service_client")

        if not container_name or not str(container_name).strip():
            raise ValueError("A non-empty container_name is required.")

        if blob_service_client is not None:
            self.blob_service_client = blob_service_client
        else:
            if not connection_string and not account_url:
                raise ValueError("Either connection_string or account_url must be provided.")
            if connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            else:
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url, credential=credential or DefaultAzureCredential()
                )
        self.container_name = str(container_name).strip()

    def upload_metrics(self, metrics: Dict[str, float], blob_name: Optional[str] = None) -> str:
        if not isinstance(metrics, dict) or not metrics:
            raise ValueError("Metrics payload must be a non-empty dictionary.")

        if blob_name is not None and not isinstance(blob_name, str):
            raise ValueError("blob_name must be a string if provided.")

        normalized_metrics: Dict[str, float] = {}
        for key, value in metrics.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("Metric keys must be non-empty strings.")
            if not isinstance(value, Number) or isinstance(value, bool):
                raise ValueError("Metric values must be numeric.")
            normalized_metrics[key] = float(value)

        container_client = self.blob_service_client.get_container_client(self.container_name)
        try:
            container_client.create_container()
        except ResourceExistsError:
            logging.info("Container '%s' already exists.", self.container_name)
        except Exception as exc:  # pragma: no cover - difficult to trigger reliably in unit tests
            logging.error("Failed to create container '%s': %s", self.container_name, exc)
            raise

        timestamp = datetime.now(timezone.utc)
        blob_path = blob_name or f"kpi-dashboard-{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
        payload = {
            "generated_at": timestamp.isoformat(),
            "metrics": normalized_metrics,
        }

        container_client.upload_blob(
            name=blob_path,
            data=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json"),
        )
        return f"{self.container_name}/{blob_path}"
