"""
Figma output integration for syncing KPI metrics and design updates.

Handles:
- KPI card updates in design system
- Dashboard metric visualizations
- Real-time KPI status badges
- Historical KPI charts (via embedded iframes or data bindings)
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


def _extract_file_key(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = value.strip()
    if "figma.com" in raw:
        match = re.search(r"/(file|design|proto)/([A-Za-z0-9_-]+)", raw)
        if match:
            return match.group(2)
        return None
    return raw.split("?")[0]


class FigmaClient:
    """Sync analytics metrics, KPI updates, and dashboard data to Figma designs."""

    def __init__(self, api_token: Optional[str] = None, file_key: Optional[str] = None):
        self.api_token = (
            api_token
            or os.getenv("FIGMA_TOKEN")
            or os.getenv("FIGMA_OAUTH_TOKEN")
            or os.getenv("FIGMA_API_TOKEN")
            or os.getenv("FIGMA_PERSONAL_ACCESS_TOKEN")
        )
        raw_file_key = (
            file_key
            or os.getenv("FIGMA_FILE_KEY")
            or os.getenv("FIGMA_FILE_URL")
            or os.getenv("FIGMA_FILE_LINK")
        )
        self.file_key = _extract_file_key(raw_file_key)
        self.base_url = "https://api.figma.com/v1"
        self.headers = {"Content-Type": "application/json"}
        if self.api_token:
            self.headers["X-Figma-Token"] = self.api_token

        if not self.api_token or not self.file_key:
            logger.warning("Figma credentials not configured. Figma export disabled.")

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make authenticated request to Figma API."""
        if not self.api_token:
            logger.warning("Figma credentials not configured. Figma export disabled.")
            return {}
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("headers", self.headers)

        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Figma API error: {e}")
            return {}

    def get_file_data(self) -> Dict[str, Any]:
        """Retrieve Figma file structure and components."""
        if not self.file_key:
            return {}
        return self._request("GET", f"/files/{self.file_key}")

    def update_text_node(self, node_id: str, new_text: str, run_id: str) -> bool:
        """Update a text node in Figma with new metric value."""
        if not self.file_key:
            return False

        payload = {
            "commits": [
                {
                    "message": f"KPI Update from Analytics Pipeline (run: {run_id})",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
            "edits": [
                {
                    "type": "SET",
                    "id": node_id,
                    "characters": new_text,
                }
            ],
        }

        result = self._request("POST", f"/files/{self.file_key}", json=payload)
        success = bool(result)

        if success:
            logger.info(f"Updated Figma node {node_id} with text: {new_text}")
        else:
            logger.error(f"Failed to update Figma node {node_id}")

        return success

    def update_kpi_cards(self, kpi_metrics: Dict[str, Any], run_id: str) -> Dict[str, bool]:
        """Update KPI card components in design system."""
        results = {}

        kpi_mapping = {
            "collection_rate": {
                "label_node": "label-collection-rate",
                "value_node": "value-collection-rate",
                "status_node": "status-collection-rate",
            },
            "par_30": {
                "label_node": "label-par-30",
                "value_node": "value-par-30",
                "status_node": "status-par-30",
            },
            "par_90": {
                "label_node": "label-par-90",
                "value_node": "value-par-90",
                "status_node": "status-par-90",
            },
            "dti": {
                "label_node": "label-dti",
                "value_node": "value-dti",
                "status_node": "status-dti",
            },
            "ltv": {
                "label_node": "label-ltv",
                "value_node": "value-ltv",
                "status_node": "status-ltv",
            },
        }

        for kpi_name, nodes in kpi_mapping.items():
            if kpi_name not in kpi_metrics:
                continue

            metric = kpi_metrics[kpi_name]
            current_value = metric.get("current_value")
            status = metric.get("status", "neutral")

            if current_value is not None:
                results[f"{kpi_name}_value"] = self.update_text_node(
                    nodes["value_node"], f"{current_value:.2f}", run_id
                )
                results[f"{kpi_name}_status"] = self.update_text_node(
                    nodes["status_node"], status.upper(), run_id
                )

        return results

    def create_dashboard_snapshot(
        self,
        dashboard_data: Dict[str, Any],
        run_id: str,
    ) -> Optional[str]:
        """Create or update a dashboard snapshot frame with current metrics."""
        if not self.file_key:
            return None

        snapshot_frame_id = os.getenv("FIGMA_DASHBOARD_FRAME_ID")
        if not snapshot_frame_id:
            logger.warning("FIGMA_DASHBOARD_FRAME_ID not configured")
            return None

        metadata = {
            "snapshot_type": "kpi_dashboard",
            "generated_at": datetime.utcnow().isoformat(),
            "run_id": run_id,
            "metrics": dashboard_data,
        }

        document_text = json.dumps(metadata, indent=2)
        self.update_text_node(snapshot_frame_id, document_text, run_id)

        logger.info(f"Created dashboard snapshot in Figma (frame: {snapshot_frame_id})")
        return snapshot_frame_id

    def sync_batch_export(self, export_data: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """
        Sync complete batch export (KPIs, metrics, summaries) to Figma.

        Args:
            export_data: Dict containing 'kpi_metrics', 'summary', 'metadata'
            run_id: Pipeline run identifier

        Returns:
            Dict with update results for each component
        """
        if not self.file_key:
            logger.warning("Figma sync skipped: credentials not configured")
            return {}

        results: Dict[str, Any] = {
            "kpi_cards": {},
            "dashboard_snapshot": None,
            "success": False,
        }

        try:
            if "kpi_metrics" in export_data:
                results["kpi_cards"] = self.update_kpi_cards(export_data["kpi_metrics"], run_id)

            if "summary" in export_data:
                results["dashboard_snapshot"] = self.create_dashboard_snapshot(
                    export_data["summary"], run_id
                )

            results["success"] = True
            logger.info(f"Figma batch sync completed (run: {run_id})")

        except Exception as e:
            logger.error(f"Figma batch sync failed: {e}")
            results["error"] = str(e)

        return results
