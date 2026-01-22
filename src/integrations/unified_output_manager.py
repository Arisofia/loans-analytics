"""
Unified output manager that orchestrates batch exports to all platforms.

This module provides a factory for coordinating outputs to:
- Figma (design/metrics sync)
- Azure (dashboards, blob storage)
- Supabase (data persistence)
- Meta (pixel events, ads insights)
- Notion (documentation, reports)
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.integrations.azure_outputs import AzureDashboardClient, AzureStorageClient
from src.integrations.figma_client import FigmaClient
from src.integrations.meta_client import MetaOutputClient
from src.integrations.notion_client import NotionOutputClient
from src.integrations.supabase_client import SupabaseOutputClient

logger = logging.getLogger(__name__)


class UnifiedOutputManager:
    """
    Orchestrate batch exports to all output platforms.

    Provides a single interface for scheduling and managing outputs with
    optional filtering, retry logic, and result aggregation.
    """

    def __init__(self):
        self.figma_client = FigmaClient()
        self.azure_storage_client = AzureStorageClient()
        self.azure_dashboard_client = AzureDashboardClient()
        self.supabase_client = SupabaseOutputClient()
        self.meta_client = MetaOutputClient()
        self.notion_client = NotionOutputClient()

        self.results = {}

    def configure_clients(self, config: Dict[str, Any]) -> None:
        """Configure output clients from config dict."""
        figma_cfg = config.get("figma", {})
        if figma_cfg.get("enabled"):
            self.figma_client = FigmaClient(
                api_token=figma_cfg.get("token"),
                file_key=figma_cfg.get("file_key"),
            )

        azure_cfg = config.get("azure", {})
        if azure_cfg.get("enabled"):
            self.azure_storage_client = AzureStorageClient(
                connection_string=azure_cfg.get("storage_connection_string")
            )
            self.azure_dashboard_client = AzureDashboardClient(
                subscription_id=azure_cfg.get("subscription_id")
            )

        supabase_cfg = config.get("supabase", {})
        if supabase_cfg.get("enabled"):
            self.supabase_client = SupabaseOutputClient(
                url=supabase_cfg.get("url"),
                service_role_key=supabase_cfg.get("service_role_key"),
            )

        meta_cfg = config.get("meta", {})
        if meta_cfg.get("enabled"):
            self.meta_client = MetaOutputClient(
                pixel_id=meta_cfg.get("pixel_id"),
                access_token=meta_cfg.get("access_token"),
                ad_account_id=meta_cfg.get("ad_account_id"),
            )

        notion_cfg = config.get("notion", {})
        if notion_cfg.get("enabled"):
            self.notion_client = NotionOutputClient(
                api_token=notion_cfg.get("api_token"),
                database_id=notion_cfg.get("database_id"),
            )

    def export_batch(
        self,
        export_data: Dict[str, Any],
        run_id: str,
        enabled_outputs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Export batch data to all enabled output platforms.

        Args:
            export_data: Dict with 'kpi_metrics', 'raw_data_df', 'summary', 'findings', etc.
            run_id: Pipeline run ID
            enabled_outputs: List of output names to enable (None = all enabled outputs)
                           Valid values: ['figma', 'azure', 'supabase', 'meta', 'notion']

        Returns:
            Dict with results from each output platform
        """
        results = {
            "run_id": run_id,
            "timestamp": pd.Timestamp.now().isoformat(),
            "outputs": {},
        }

        enabled_outputs = enabled_outputs or [
            "figma",
            "azure",
            "supabase",
            "meta",
            "notion",
        ]

        if "figma" in enabled_outputs:
            logger.info("Exporting to Figma...")
            results["outputs"]["figma"] = self.figma_client.sync_batch_export(export_data, run_id)

        if "azure" in enabled_outputs:
            logger.info("Exporting to Azure...")
            azure_results = {
                "storage": self.azure_storage_client.upload_batch_exports(
                    export_data.get("export_dir", Path("data/exports")),
                    run_id,
                ),
                "dashboard": self.azure_dashboard_client.sync_batch_export(export_data),
            }
            results["outputs"]["azure"] = azure_results

        if "supabase" in enabled_outputs:
            logger.info("Exporting to Supabase...")
            results["outputs"]["supabase"] = self.supabase_client.sync_batch_export(
                export_data, run_id
            )

        if "meta" in enabled_outputs:
            logger.info("Exporting to Meta...")
            results["outputs"]["meta"] = self.meta_client.sync_batch_export(export_data)

        if "notion" in enabled_outputs:
            logger.info("Exporting to Notion...")
            results["outputs"]["notion"] = self.notion_client.sync_batch_export(export_data, run_id)

        success_flags = [
            output.get("success")
            for output in results["outputs"].values()
            if isinstance(output, dict) and "success" in output
        ]
        results["success"] = all(success_flags) if success_flags else True

        self._log_results(results)
        return results

    def export_kpi_metrics_only(
        self,
        kpi_metrics: Dict[str, Any],
        run_id: str,
        enabled_outputs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Quick export of just KPI metrics to all platforms."""
        export_data = {
            "kpi_metrics": kpi_metrics,
        }
        return self.export_batch(export_data, run_id, enabled_outputs)

    def export_dashboard_data(
        self,
        kpi_metrics: Dict[str, Any],
        summary: Dict[str, Any],
        run_id: str,
        enabled_outputs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Export dashboard summary data for visualization."""
        export_data = {
            "kpi_metrics": kpi_metrics,
            "summary": summary,
        }
        return self.export_batch(export_data, run_id, enabled_outputs)

    def export_complete_report(
        self,
        df: pd.DataFrame,
        kpi_metrics: Dict[str, Any],
        summary: Dict[str, Any],
        findings: List[str],
        run_id: str,
        timeseries: Optional[Dict[str, pd.DataFrame]] = None,
        enabled_outputs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Export complete analytics report across all platforms."""
        export_data = {
            "raw_data_df": df,
            "kpi_metrics": kpi_metrics,
            "summary": summary,
            "findings": findings,
            "timeseries": timeseries or {},
        }
        return self.export_batch(export_data, run_id, enabled_outputs)

    def _log_results(self, results: Dict[str, Any]) -> None:
        """Log summary of export results."""
        logger.info("=" * 60)
        logger.info("UNIFIED OUTPUT EXPORT RESULTS")
        logger.info("=" * 60)

        for platform, platform_results in results.get("outputs", {}).items():
            if isinstance(platform_results, dict):
                success = platform_results.get("success", True)
                status = "✓ SUCCESS" if success else "✗ FAILED"
                logger.info(f"{platform.upper()}: {status}")

                for key, value in platform_results.items():
                    if key != "success" and value:
                        logger.info(f"  - {key}: {value}")
            else:
                logger.info(f"{platform.upper()}: {platform_results}")

        logger.info("=" * 60)

    def health_check(self) -> Dict[str, bool]:
        """Check health of all output clients."""
        checks = {
            "figma": bool(self.figma_client.api_token),
            "azure": bool(self.azure_storage_client.client),
            "supabase": bool(self.supabase_client.client),
            "meta": bool(self.meta_client.access_token),
            "notion": bool(self.notion_client.api_token),
        }

        logger.info("Output Client Health Check:")
        for platform, healthy in checks.items():
            status = "✓" if healthy else "✗"
            logger.info(f"  {status} {platform}")

        return checks
