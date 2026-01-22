"""
Notion output integration for documentation and report syncing.

Handles:
- Creating analytics reports in Notion
- Syncing KPI summaries to Notion databases
- Team documentation from pipeline results
- Audit logs and compliance records
"""

import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


def _normalize_notion_id(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = value.strip()
    match = re.search(r"[0-9a-fA-F]{32}", raw)
    if match:
        return match.group(0)
    match = re.search(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        raw,
    )
    if match:
        return match.group(0).replace("-", "")
    return raw


class NotionOutputClient:
    """Sync analytics data to Notion workspace."""

    def __init__(
        self,
        api_token: Optional[str] = None,
        database_id: Optional[str] = None,
    ):
        self.api_token = (
            api_token
            or os.getenv("NOTION_API_KEY")
            or os.getenv("NOTION_TOKEN")
            or os.getenv("NOTION_INTEGRATION_TOKEN")
        )
        raw_database_id = (
            database_id
            or os.getenv("NOTION_DATABASE_ID")
            or os.getenv("NOTION_DATABASE_URL")
            or os.getenv("NOTION_DATABASE")
        )
        self.database_id = _normalize_notion_id(raw_database_id)

        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        if not self.api_token:
            logger.warning("Notion credentials not configured. Notion export disabled.")

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make authenticated request to Notion API."""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("headers", self.headers)

        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Notion API error: {e}")
            return {}

    def create_report_page(
        self,
        parent_page_id: str,
        title: str,
        report_content: Dict[str, Any],
        run_id: str,
    ) -> Optional[str]:
        """Create a new Notion page for analytics report."""
        if not self.api_token:
            logger.warning("Notion credentials not configured")
            return None

        try:
            blocks = self._build_report_blocks(report_content)

            payload = {
                "parent": {"page_id": parent_page_id},
                "properties": {
                    "title": {
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": title},
                            }
                        ]
                    },
                    "Run ID": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": run_id},
                            }
                        ]
                    },
                    "Generated": {
                        "date": {
                            "start": datetime.utcnow().isoformat(),
                        }
                    },
                },
                "children": blocks,
            }

            response = self._request("POST", "/pages", json=payload)

            page_id = response.get("id")
            if page_id:
                logger.info(f"Created Notion report page: {title} ({page_id})")
            else:
                logger.warning(f"Failed to create Notion report page: {title}")

            return page_id

        except Exception as e:
            logger.error(f"Error creating Notion report page: {e}")
            return None

    def _build_report_blocks(self, report_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build Notion blocks for report content."""
        blocks = []

        if "summary" in report_content:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": report_content["summary"]},
                            }
                        ]
                    },
                }
            )

        if "kpi_metrics" in report_content:
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "KPI Metrics"},
                            }
                        ]
                    },
                }
            )

            for kpi_name, metric_data in report_content["kpi_metrics"].items():
                content = f"{kpi_name}: {metric_data.get('current_value', 'N/A')} {metric_data.get('unit', '')}"
                blocks.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": content},
                                }
                            ]
                        },
                    }
                )

        if "findings" in report_content:
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Key Findings"},
                            }
                        ]
                    },
                }
            )

            for finding in report_content["findings"]:
                blocks.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": finding},
                                }
                            ]
                        },
                    }
                )

        return blocks

    def add_database_item(
        self,
        database_id: str,
        properties: Dict[str, Any],
    ) -> Optional[str]:
        """Add item to Notion database."""
        if not self.api_token:
            logger.warning("Notion credentials not configured")
            return None

        try:
            payload = {
                "parent": {"database_id": database_id},
                "properties": properties,
            }

            response = self._request("POST", "/pages", json=payload)

            page_id = response.get("id")
            if page_id:
                logger.info(f"Added item to Notion database: {page_id}")
            else:
                logger.warning("Failed to add item to Notion database")

            return page_id

        except Exception as e:
            logger.error(f"Error adding item to Notion database: {e}")
            return None

    def log_kpi_metrics(
        self,
        kpi_metrics: Dict[str, Any],
        run_id: str,
    ) -> Dict[str, str]:
        """Log KPI metrics to Notion database."""
        if not self.database_id or not self.api_token:
            logger.warning("Notion database not configured")
            return {}

        results = {}

        try:
            for kpi_name, metric_data in kpi_metrics.items():
                properties = {
                    "Name": {
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": kpi_name},
                            }
                        ]
                    },
                    "Value": {"number": float(metric_data.get("current_value", 0))},
                    "Unit": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": metric_data.get("unit", "")},
                            }
                        ]
                    },
                    "Status": {
                        "select": {
                            "name": metric_data.get("status", "neutral"),
                        }
                    },
                    "Run ID": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": run_id},
                            }
                        ]
                    },
                    "Logged At": {
                        "date": {
                            "start": datetime.utcnow().isoformat(),
                        }
                    },
                }

                page_id = self.add_database_item(self.database_id, properties)
                if page_id:
                    results[kpi_name] = page_id

        except Exception as e:
            logger.error(f"Error logging KPI metrics to Notion: {e}")

        return results

    def sync_batch_export(
        self,
        export_data: Dict[str, Any],
        run_id: str,
        parent_page_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sync batch export to Notion.

        Args:
            export_data: Dict with 'kpi_metrics', 'summary', 'findings'
            run_id: Pipeline run ID
            parent_page_id: Parent page for report (if None, skips report creation)

        Returns:
            Dict with results from Notion sync operations
        """
        if not self.api_token:
            logger.warning("Notion export skipped: credentials not configured")
            return {}

        results: Dict[str, Any] = {
            "report_created": None,
            "kpi_metrics_logged": {},
            "success": False,
        }

        try:
            raw_parent_page = parent_page_id or os.getenv("NOTION_REPORTS_PAGE_ID")
            parent_page_id = _normalize_notion_id(raw_parent_page)

            if parent_page_id:
                report_title = f"Analytics Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
                page_id = self.create_report_page(
                    parent_page_id=parent_page_id,
                    title=report_title,
                    report_content=export_data,
                    run_id=run_id,
                )
                results["report_created"] = page_id

            if self.database_id and "kpi_metrics" in export_data:
                results["kpi_metrics_logged"] = self.log_kpi_metrics(
                    export_data["kpi_metrics"], run_id
                )

            results["success"] = True
            logger.info(f"Notion batch sync completed (run: {run_id})")

        except Exception as e:
            logger.error(f"Notion batch sync failed: {e}")
            results["error"] = str(e)

        return results
