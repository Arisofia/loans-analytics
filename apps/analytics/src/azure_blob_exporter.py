# Azure Blob KPI Exporter module for publishing KPI payloads to Azure Blob Storage.

import json
import logging
from datetime import datetime, timezone
from numbers import Number
from typing import Dict, Optional

from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings


class AzureBlobKPIExporter:
    """Publishes KPI payloads to Azure Blob Storage with traceable metadata."""

    def __init__(
        self, container_name=None, account_url=None, connection_string=None,
        credential=None, blob_service_client=None, **kwargs
    ):
        # Support both legacy (test) and config dict signatures
        if container_name is None and isinstance(kwargs.get('config'), dict):
            config = kwargs['config']
            container_name = config.get("container_name")
            account_url = config.get("account_url")
            connection_string = config.get("connection_string")
            credential = config.get("credential")
            blob_service_client = config.get("blob_service_client")

        if not container_name or not str(container_name).strip():
            raise ValueError("A non-empty container_name is required.")

        if blob_service_client is not None:
            self.blob_service_client = blob_service_client
        else:
            if not connection_string and not account_url:
                raise ValueError(
                    "Either connection_string or account_url must be provided."
                )
            if connection_string:
                blob_service = BlobServiceClient.from_connection_string(
                    connection_string
                )
                self.blob_service_client = blob_service
            else:
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=credential or DefaultAzureCredential()
                )
        self.container_name = str(container_name).strip()

    def upload_metrics(
        self,
        metrics: Dict[str, float],
        blob_name: Optional[str] = None
    ) -> str:
        """Uploads KPI metrics as a JSON blob to Azure Blob Storage."""
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

        container_client = self.blob_service_client.get_container_client(
            self.container_name
        )
        try:
            container_client.create_container()
        except ResourceExistsError:
            logging.info(f"Container '{self.container_name}' already exists.")
        except Exception as e:
            logging.error(f"Failed to create container '{self.container_name}': {e}")
            raise

        timestamp = datetime.now(timezone.utc)
        blob_path = blob_name or (
            f"kpi-dashboard-{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
        )
        payload = {
            "generated_at": timestamp.isoformat(),
            "metrics": normalized_metrics,
        }

        container_client.upload_blob(
            name=blob_path,
            data=json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":")
            ),
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json"),
        )
        return f"{self.container_name}/{blob_path}"
