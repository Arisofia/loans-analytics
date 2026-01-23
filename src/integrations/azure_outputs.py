"""
Azure output integrations for dashboards, storage, and monitoring.

Handles:
- Azure Blob Storage for raw data and reports
- Azure Dashboards for metric visualizations
- Azure Monitor for alerting and observability
- Azure Cosmos DB for time-series data (optional)
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

try:
    from azure.core.credentials import AzureNamedKeyCredential, AzureSasCredential
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient, ContentSettings

    HAS_AZURE = True
except ImportError:
    AzureNamedKeyCredential = None
    AzureSasCredential = None
    DefaultAzureCredential = None
    BlobServiceClient = None
    ContentSettings = None
    HAS_AZURE = False


def _extract_account_name(account_url: Optional[str]) -> Optional[str]:
    if not account_url:
        return None
    parsed = urlparse(account_url)
    host = parsed.netloc or parsed.path
    if not host:
        return None
    return host.split(".")[0]


def _normalize_account_url(raw_url: Optional[str], account_name: Optional[str]) -> Optional[str]:
    if raw_url:
        if raw_url.startswith("http://") or raw_url.startswith("https://"):
            return raw_url
        return f"https://{raw_url}"
    if account_name:
        return f"https://{account_name}.blob.core.windows.net"
    return None


class AzureStorageClient:
    """Handle uploading analytics data to Azure Blob Storage."""

    def __init__(self, connection_string: Optional[str] = None):
        if not HAS_AZURE:
            logger.warning("Azure SDK not installed. Azure Storage disabled.")
            self.client = None
            return

        self.connection_string = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER", "analytics-exports")

        account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME") or os.getenv("AZURE_STORAGE_ACCOUNT")
        account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        sas_token = os.getenv("AZURE_STORAGE_SAS_TOKEN")
        raw_account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL")

        if raw_account_url and not raw_account_url.startswith("http") and "." not in raw_account_url:
            account_name = account_name or raw_account_url
            raw_account_url = None

        account_url = _normalize_account_url(raw_account_url, account_name)
        if not account_name and account_url:
            account_name = _extract_account_name(account_url)

        if not self.connection_string and account_name and account_key:
            self.connection_string = (
                f"DefaultEndpointsProtocol=https;AccountName={account_name};"
                f"AccountKey={account_key};EndpointSuffix=core.windows.net"
            )

        if self.connection_string:
            self.client = BlobServiceClient.from_connection_string(self.connection_string)
        elif account_url and account_key and AzureNamedKeyCredential and account_name:
            credential = AzureNamedKeyCredential(account_name, account_key)
            self.client = BlobServiceClient(account_url=account_url, credential=credential)
        elif account_url and sas_token and AzureSasCredential:
            self.client = BlobServiceClient(
                account_url=account_url, credential=AzureSasCredential(sas_token)
            )
        elif account_url and DefaultAzureCredential:
            self.client = BlobServiceClient(
                account_url=account_url, credential=DefaultAzureCredential()
            )
        else:
            logger.warning("Azure Storage credentials not configured")
            self.client = None

    def upload_file(
        self,
        file_path: Path,
        blob_name: str,
        overwrite: bool = True,
    ) -> Optional[str]:
        """Upload a single file to Azure Blob Storage."""
        if not self.client:
            logger.warning("Azure Storage client not initialized")
            return None

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        try:
            container_client = self.client.get_container_client(self.container_name)

            content_type = self._guess_content_type(file_path)

            with file_path.open("rb") as data:
                container_client.upload_blob(
                    name=blob_name,
                    data=data,
                    overwrite=overwrite,
                    content_settings=ContentSettings(content_type=content_type),
                )

            blob_url = f"https://{self.client.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
            logger.info(f"Uploaded {file_path.name} to Azure: {blob_url}")
            return blob_url

        except Exception as e:
            logger.error(f"Failed to upload {file_path.name} to Azure: {e}")
            return None

    def upload_dataframe_csv(
        self,
        df,
        blob_name: str,
        overwrite: bool = True,
    ) -> Optional[str]:
        """Upload pandas DataFrame as CSV to Azure Blob Storage."""
        if not self.client:
            logger.warning("Azure Storage client not initialized")
            return None

        try:
            container_client = self.client.get_container_client(self.container_name)

            csv_content = df.to_csv(index=False)

            container_client.upload_blob(
                name=blob_name,
                data=csv_content,
                overwrite=overwrite,
                content_settings=ContentSettings(content_type="text/csv"),
            )

            blob_url = f"https://{self.client.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
            logger.info(f"Uploaded DataFrame to Azure: {blob_url}")
            return blob_url

        except Exception as e:
            logger.error(f"Failed to upload DataFrame to Azure: {e}")
            return None

    def upload_batch_exports(
        self,
        export_dir: Path,
        run_id: str,
        patterns: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Upload all exported files matching patterns to Azure Blob Storage."""
        if not self.client:
            logger.warning("Azure Storage client not initialized")
            return {}

        patterns = patterns or ["*.csv", "*.json", "*.parquet"]
        uploaded = {}

        for pattern in patterns:
            for file_path in export_dir.glob(pattern):
                blob_name = f"exports/{run_id}/{file_path.name}"
                url = self.upload_file(file_path, blob_name)
                if url:
                    uploaded[file_path.name] = url

        return uploaded

    @staticmethod
    def _guess_content_type(file_path: Path) -> str:
        """Guess MIME type based on file extension."""
        mapping = {
            ".csv": "text/csv",
            ".json": "application/json",
            ".parquet": "application/octet-stream",
            ".txt": "text/plain",
            ".html": "text/html",
        }
        return mapping.get(file_path.suffix.lower(), "application/octet-stream")


class AzureDashboardClient:
    """Create and update Azure Monitor Dashboards with KPI metrics."""

    def __init__(self, subscription_id: Optional[str] = None):
        self.subscription_id = (
            subscription_id
            or os.getenv("AZURE_SUBSCRIPTION_ID")
            or os.getenv("AZURE_SUBSCRIPTION")
        )
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP") or os.getenv(
            "AZURE_RESOURCE_GROUP_NAME"
        )
        self.dashboard_name = os.getenv("AZURE_DASHBOARD_NAME", "abaco-analytics-dashboard")

        if not HAS_AZURE or DefaultAzureCredential is None:
            logger.warning("Azure SDK not installed. Azure Dashboard disabled.")
            self.credential = None
        elif self.subscription_id:
            self.credential = DefaultAzureCredential()
        else:
            self.credential = None

    def create_kpi_tile(
        self,
        kpi_name: str,
        current_value: float,
        previous_value: float,
        unit: str = "%",
    ) -> Dict[str, Any]:
        """Create a dashboard tile for a KPI metric."""
        change = current_value - previous_value
        change_pct = (change / previous_value * 100) if previous_value != 0 else 0

        return {
            "properties": {
                "markdown": {
                    "content": f"""
### {kpi_name}
**Current**: {current_value:.2f}{unit}
**Previous**: {previous_value:.2f}{unit}
**Change**: {change:+.2f}{unit} ({change_pct:+.1f}%)
**Updated**: {datetime.utcnow().isoformat()}
"""
                }
            },
            "position": {"x": 0, "y": 0, "width": 3, "height": 2},
        }

    def create_metric_chart_tile(
        self,
        metric_name: str,
        metric_id: str,
    ) -> Dict[str, Any]:
        """Create a dashboard tile for metric time-series chart."""
        return {
            "properties": {
                "metrics": {
                    "resourceMetadata": {"id": metric_id},
                    "metrics": [{"name": metric_name, "resourceId": metric_id}],
                    "title": f"{metric_name} - Last 24 Hours",
                    "timespan": "PT24H",
                    "visualization": {"chartType": 2},
                }
            },
            "position": {"x": 0, "y": 0, "width": 6, "height": 3},
        }

    def build_dashboard_payload(self, kpi_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Build complete dashboard JSON payload with KPI tiles."""
        tiles = []

        for idx, (kpi_name, metric_data) in enumerate(kpi_metrics.items()):
            tile = self.create_kpi_tile(
                kpi_name=kpi_name,
                current_value=metric_data.get("current_value", 0),
                previous_value=metric_data.get("previous_value", 0),
                unit=metric_data.get("unit", ""),
            )
            tile["position"]["y"] = (idx % 3) * 3
            tile["position"]["x"] = (idx // 3) * 3
            tiles.append(tile)

        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.Portal/dashboards/{self.dashboard_name}",
            "name": self.dashboard_name,
            "type": "Microsoft.Portal/dashboards",
            "location": "eastus",
            "properties": {
                "lenses": {
                    "0": {
                        "order": 0,
                        "parts": {f"part{i}": tile for i, tile in enumerate(tiles)},
                    }
                },
                "metadata": {
                    "model": {
                        "timeRange": {"value": "P1D", "type": 1},
                        "filterLocale": {"value": "en-us"},
                        "filters": {},
                    }
                },
            },
        }

    def update_dashboard(self, kpi_metrics: Dict[str, Any]) -> bool:
        """Update or create Azure Dashboard with KPI metrics."""
        if not self.credential or not self.subscription_id:
            logger.warning("Azure credentials not configured for dashboards")
            return False
        if not self.resource_group:
            logger.warning("Azure resource group not configured for dashboards")
            return False

        try:
            from azure.mgmt.portal import Portal

            client = Portal(self.credential, self.subscription_id)

            payload = self.build_dashboard_payload(kpi_metrics)

            dashboard = client.dashboards.create_or_update(
                resource_group_name=self.resource_group,
                dashboard_name=self.dashboard_name,
                dashboard=payload,
            )

            logger.info(f"Updated Azure Dashboard: {dashboard.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update Azure Dashboard: {e}")
            return False

    def sync_batch_export(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync batch export data to Azure (storage + dashboards)."""
        results = {
            "storage_uploaded": {},
            "dashboard_updated": False,
            "success": False,
        }

        try:
            export_dir = export_data.get("export_dir", Path("data/exports"))
            if isinstance(export_dir, str):
                export_dir = Path(export_dir)

            storage_client = AzureStorageClient()
            if storage_client.client:
                run_id = export_data.get("run_id", "unknown")
                results["storage_uploaded"] = storage_client.upload_batch_exports(
                    export_dir, run_id
                )

            if "kpi_metrics" in export_data:
                self.update_dashboard(export_data["kpi_metrics"])
                results["dashboard_updated"] = True

            results["success"] = True

        except Exception as e:
            logger.error(f"Azure batch sync failed: {e}")
            results["error"] = str(e)

        return results
