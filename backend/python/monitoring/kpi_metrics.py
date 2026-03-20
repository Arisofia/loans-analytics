"""
KPI Threshold Metrics Exporter for Prometheus and AlertManager Integration.

Exposes KPI threshold status and values as Prometheus metrics for alerting.
Integrates with the KPI formula engine to publish real-time threshold states.

Metrics exposed:
  - kpi_threshold_status{kpi_name, status, category, owner_email} = 1
  - kpi_value{kpi_name, unit} = <value>
  - kpi_warning_threshold{kpi_name} = <threshold>
  - kpi_critical_threshold{kpi_name} = <threshold>
  - kpi_last_update_timestamp{kpi_name} = <unix_timestamp>

Usage:
    from backend.python.monitoring.kpi_metrics import KPIMetricsExporter
    
    exporter = KPIMetricsExporter()
    exporter.publish_kpi_result(kpi_name, kpi_result)
    metrics_text = exporter.generate_metrics_text()
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ThresholdMetricLabels:
    """Labels for threshold metrics."""
    kpi_name: str
    threshold_status: str  # normal, warning, critical, not_configured
    category: str = "general"
    severity: str = "info"  # info, warning, critical
    owner_email: str = "ops-team@abaco.local"
    unit: str = "unknown"


class KPIMetricsExporter:
    """Publishes KPI threshold status as Prometheus metrics for AlertManager."""

    def __init__(self):
        """Initialize the KPI metrics exporter."""
        self.metrics: Dict[str, float] = {}
        self.metric_metadata: Dict[str, Dict[str, Any]] = {}

    def publish_kpi_result(
        self,
        kpi_name: str,
        kpi_result: dict,
        category: str = "general",
        owner_email: str = "ops-team@abaco.local",
    ) -> None:
        """
        Publish a KPI calculation result as Prometheus metrics.

        Args:
            kpi_name: Name of the KPI (from registry)
            kpi_result: Result dict from KPIFormulaEngine.calculate_kpi()
                       Must contain: value, threshold_status, thresholds, unit
            category: KPI category for routing alerts (portfolio, asset_quality, etc.)
            owner_email: Email of KPI owner for alerts
        """
        if not isinstance(kpi_result, dict):
            logger.warning(f"Invalid KPI result type for {kpi_name}: {type(kpi_result)}")
            return

        try:
            # Extract fields from result
            value = float(kpi_result.get("value", 0))
            threshold_status = str(kpi_result.get("threshold_status", "not_configured"))
            thresholds = kpi_result.get("thresholds", {})
            unit = str(kpi_result.get("unit", "unknown"))
            timestamp = datetime.now(timezone.utc).timestamp()

            # Map threshold status to severity for alerting
            status_to_severity = {
                "normal": "info",
                "warning": "warning",
                "critical": "critical",
                "not_configured": "info",
            }
            severity = status_to_severity.get(threshold_status, "info")

            # Publish KPI value metric
            self._publish_gauge(
                f'kpi_value{{kpi_name="{kpi_name}",unit="{unit}"}}',
                value,
            )

            # Publish threshold status metric (1 when in this state, 0 otherwise)
            for status in ["normal", "warning", "critical", "not_configured"]:
                is_in_state = 1 if status == threshold_status else 0
                self._publish_gauge(
                    f'kpi_threshold_status{{kpi_name="{kpi_name}",status="{status}",'
                    f'category="{category}",severity="{severity}",owner_email="{owner_email}"}}',
                    is_in_state,
                )

            # Publish threshold values
            if thresholds:
                if "warning" in thresholds:
                    warning_thresh = float(thresholds["warning"])
                    self._publish_gauge(
                        f'kpi_warning_threshold{{kpi_name="{kpi_name}"}}',
                        warning_thresh,
                    )
                if "critical" in thresholds:
                    critical_thresh = float(thresholds["critical"])
                    self._publish_gauge(
                        f'kpi_critical_threshold{{kpi_name="{kpi_name}"}}',
                        critical_thresh,
                    )

            # Publish last update timestamp
            self._publish_gauge(
                f'kpi_last_update_timestamp{{kpi_name="{kpi_name}"}}',
                timestamp,
            )

            # Store metadata for reference
            self.metric_metadata[kpi_name] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "threshold_status": threshold_status,
                "value": value,
                "category": category,
                "owner_email": owner_email,
            }

            logger.info(
                f"Published KPI metrics: {kpi_name}={value} status={threshold_status}"
            )

        except Exception as e:
            logger.error(f"Error publishing KPI metrics for {kpi_name}: {e}", exc_info=True)

    def _publish_gauge(self, metric_key: str, value: float) -> None:
        """Store a gauge metric."""
        self.metrics[metric_key] = value

    def generate_metrics_text(self) -> str:
        """
        Generate Prometheus text format metrics for scraping.

        Returns:
            Metrics in Prometheus text exposition format
        """
        lines = []

        # Add HELP and TYPE lines for each unique metric
        metric_types = {}
        for key in self.metrics:
            metric_name = key.split("{")[0]
            if metric_name not in metric_types:
                metric_types[metric_name] = "gauge"

        # Output HELP and TYPE declarations
        for metric_name, metric_type in sorted(metric_types.items()):
            lines.append(f"# HELP {metric_name} KPI threshold status metric")
            lines.append(f"# TYPE {metric_name} {metric_type}")

        # Output metric values
        for metric_key, value in sorted(self.metrics.items()):
            lines.append(f"{metric_key} {value}")

        return "\n".join(lines) + "\n" if lines else ""

    def get_kpi_by_status(self, status: str) -> list[str]:
        """Get all KPIs currently in a given threshold status."""
        kpis = []
        status_key = f'status="{status}"'
        for metric_key in self.metrics:
            if status_key in metric_key and self.metrics[metric_key] == 1:
                # Extract KPI name from metric key
                start = metric_key.find('kpi_name="') + len('kpi_name="')
                end = metric_key.find('"', start)
                if start > len('kpi_name="') - 1 and end > start:
                    kpi_name = metric_key[start:end]
                    kpis.append(kpi_name)
        return kpis

    def get_critical_kpis(self) -> list[str]:
        """Get all KPIs currently in critical status."""
        return self.get_kpi_by_status("critical")

    def get_warning_kpis(self) -> list[str]:
        """Get all KPIs currently in warning status."""
        return self.get_kpi_by_status("warning")

    def get_status_summary(self) -> dict[str, int]:
        """Get summary of KPI statuses across all KPIs."""
        summary = {
            "normal": 0,
            "warning": 0,
            "critical": 0,
            "not_configured": 0,
        }
        for status in summary:
            summary[status] = len(self.get_kpi_by_status(status))
        return summary


# Global exporter instance (used by Flask app)
_kpi_metrics_exporter: Optional[KPIMetricsExporter] = None


def get_kpi_metrics_exporter() -> KPIMetricsExporter:
    """Get or create the global KPI metrics exporter."""
    global _kpi_metrics_exporter
    if _kpi_metrics_exporter is None:
        _kpi_metrics_exporter = KPIMetricsExporter()
    return _kpi_metrics_exporter
