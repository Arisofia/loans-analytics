from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging
logger = logging.getLogger(__name__)
_KPI_NAME_LABEL = 'kpi_name="'

@dataclass
class ThresholdMetricLabels:
    kpi_name: str
    threshold_status: str
    category: str = 'general'
    severity: str = 'info'
    owner_email: str = 'ops-team@abaco.local'
    unit: str = 'unknown'

class KPIMetricsExporter:

    def __init__(self):
        self.metrics: Dict[str, float] = {}
        self.metric_metadata: Dict[str, Dict[str, Any]] = {}

    def publish_kpi_result(self, kpi_name: str, kpi_result: dict, category: str='general', owner_email: str='ops-team@abaco.local') -> None:
        if not isinstance(kpi_result, dict):
            logger.warning(f'Invalid KPI result type for {kpi_name}: {type(kpi_result)}')
            return
        try:
            value = float(kpi_result.get('value', 0))
            threshold_status = str(kpi_result.get('threshold_status', 'not_configured'))
            thresholds = kpi_result.get('thresholds', {})
            unit = str(kpi_result.get('unit', 'unknown'))
            timestamp = datetime.now(timezone.utc).timestamp()
            status_to_severity = {'normal': 'info', 'warning': 'warning', 'critical': 'critical', 'not_configured': 'info'}
            severity = status_to_severity.get(threshold_status, 'info')
            self._publish_gauge(f'kpi_value{{kpi_name="{kpi_name}",unit="{unit}"}}', value)
            for status in ['normal', 'warning', 'critical', 'not_configured']:
                is_in_state = 1 if status == threshold_status else 0
                self._publish_gauge(f'kpi_threshold_status{{kpi_name="{kpi_name}",status="{status}",category="{category}",severity="{severity}",owner_email="{owner_email}"}}', is_in_state)
            if thresholds:
                if 'warning' in thresholds:
                    warning_thresh = float(thresholds['warning'])
                    self._publish_gauge(f'kpi_warning_threshold{{kpi_name="{kpi_name}"}}', warning_thresh)
                if 'critical' in thresholds:
                    critical_thresh = float(thresholds['critical'])
                    self._publish_gauge(f'kpi_critical_threshold{{kpi_name="{kpi_name}"}}', critical_thresh)
            self._publish_gauge(f'kpi_last_update_timestamp{{kpi_name="{kpi_name}"}}', timestamp)
            self.metric_metadata[kpi_name] = {'timestamp': datetime.now(timezone.utc).isoformat(), 'threshold_status': threshold_status, 'value': value, 'category': category, 'owner_email': owner_email}
            logger.info(f'Published KPI metrics: {kpi_name}={value} status={threshold_status}')
        except Exception as e:
            logger.error(f'Error publishing KPI metrics for {kpi_name}: {e}', exc_info=True)

    def _publish_gauge(self, metric_key: str, value: float) -> None:
        self.metrics[metric_key] = value

    def generate_metrics_text(self) -> str:
        lines = []
        metric_types = {}
        for key in self.metrics:
            metric_name = key.split('{')[0]
            if metric_name not in metric_types:
                metric_types[metric_name] = 'gauge'
        for metric_name, metric_type in sorted(metric_types.items()):
            lines.append(f'# HELP {metric_name} KPI threshold status metric')
            lines.append(f'# TYPE {metric_name} {metric_type}')
        for metric_key, value in sorted(self.metrics.items()):
            lines.append(f'{metric_key} {value}')
        return '\n'.join(lines) + '\n' if lines else ''

    def get_kpi_by_status(self, status: str) -> list[str]:
        kpis = []
        status_key = f'status="{status}"'
        for metric_key in self.metrics:
            if status_key in metric_key and self.metrics[metric_key] == 1:
                start = metric_key.find(_KPI_NAME_LABEL) + len(_KPI_NAME_LABEL)
                end = metric_key.find('"', start)
                if start > len(_KPI_NAME_LABEL) - 1 and end > start:
                    kpi_name = metric_key[start:end]
                    kpis.append(kpi_name)
        return kpis

    def get_critical_kpis(self) -> list[str]:
        return self.get_kpi_by_status('critical')

    def get_warning_kpis(self) -> list[str]:
        return self.get_kpi_by_status('warning')

    def get_status_summary(self) -> dict[str, int]:
        summary = {'normal': 0, 'warning': 0, 'critical': 0, 'not_configured': 0}
        for status in summary:
            summary[status] = len(self.get_kpi_by_status(status))
        return summary
_kpi_metrics_exporter: Optional[KPIMetricsExporter] = None

def get_kpi_metrics_exporter() -> KPIMetricsExporter:
    global _kpi_metrics_exporter
    if _kpi_metrics_exporter is None:
        _kpi_metrics_exporter = KPIMetricsExporter()
    return _kpi_metrics_exporter
