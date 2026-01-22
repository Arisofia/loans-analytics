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

logger = logging.getLogger(__name__)

try:
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient, ContentSettings

    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False


class AzureStorageClient:
    """Handle uploading analytics data to Azure Blob Storage."""

    def __init__(self, connection_string: Optional[str] = None):
        if not HAS_AZURE:
            logger.warning("Azure SDK not installed. Azure Storage disabled.")
            self.client = None
            return

        self.connection_string = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER", "analytics-exports")

        if self.connection_string:
            self.client = BlobServiceClient.from_connection_string(self.connection_string)
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
        self.subscription_id = subscription_id or os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP")
        self.dashboard_name = os.getenv("AZURE_DASHBOARD_NAME", "abaco-analytics-dashboard")

        self.credential = DefaultAzureCredential() if self.subscription_id else None

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
