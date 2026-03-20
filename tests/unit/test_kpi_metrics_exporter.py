"""Test KPI metrics exporter for AlertManager integration."""

import pytest
from backend.python.monitoring.kpi_metrics import KPIMetricsExporter


class TestKPIMetricsExporter:
    """Test KPI threshold metrics publishing for alerts."""

    def test_publish_kpi_result_normal_status(self):
        """Test publishing a KPI in normal status."""
        exporter = KPIMetricsExporter()
        
        kpi_result = {
            "value": 88.5,
            "threshold_status": "normal",
            "thresholds": {"critical": 85, "warning": 70},
            "unit": "percentage",
        }
        
        exporter.publish_kpi_result("collection_rate", kpi_result)
        
        # Check metrics were published
        assert len(exporter.metrics) > 0
        
        # Check status metric
        normal_metrics = [k for k in exporter.metrics if 'status="normal"' in k]
        assert len(normal_metrics) > 0
        assert exporter.metrics[normal_metrics[0]] == 1
        
        # Check that other statuses are 0
        warning_metrics = [k for k in exporter.metrics if 'status="warning"' in k]
        assert len(warning_metrics) > 0
        assert exporter.metrics[warning_metrics[0]] == 0

    def test_publish_kpi_result_warning_status(self):
        """Test publishing a KPI in warning status."""
        exporter = KPIMetricsExporter()
        
        kpi_result = {
            "value": 72.0,
            "threshold_status": "warning",
            "thresholds": {"critical": 85, "warning": 70},
            "unit": "percentage",
        }
        
        exporter.publish_kpi_result("par_30", kpi_result, category="asset_quality")
        
        # Check warning status metric is 1
        warning_metrics = [k for k in exporter.metrics if 'status="warning"' in k]
        assert len(warning_metrics) > 0
        assert exporter.metrics[warning_metrics[0]] == 1
        
        # Check critical status metric is 0
        critical_metrics = [k for k in exporter.metrics if 'status="critical"' in k]
        assert len(critical_metrics) > 0
        assert exporter.metrics[critical_metrics[0]] == 0

    def test_publish_kpi_result_critical_status(self):
        """Test publishing a KPI in critical status."""
        exporter = KPIMetricsExporter()
        
        kpi_result = {
            "value": 45.0,
            "threshold_status": "critical",
            "thresholds": {"critical": 85, "warning": 70},
            "unit": "percentage",
        }
        
        exporter.publish_kpi_result("collection_rate", kpi_result)
        
        # Check critical status metric is 1
        critical_metrics = [k for k in exporter.metrics if 'status="critical"' in k]
        assert len(critical_metrics) > 0
        assert exporter.metrics[critical_metrics[0]] == 1

    def test_threshold_values_published(self):
        """Test that threshold values are published as separate metrics."""
        exporter = KPIMetricsExporter()
        
        kpi_result = {
            "value": 80.0,
            "threshold_status": "warning",
            "thresholds": {"critical": 85, "warning": 70, "target": 95},
            "unit": "percentage",
        }
        
        exporter.publish_kpi_result("test_kpi", kpi_result)
        
        # Check threshold metrics
        warning_thresh = [v for k, v in exporter.metrics.items() if 'kpi_warning_threshold' in k]
        assert len(warning_thresh) > 0
        assert warning_thresh[0] == 70.0
        
        critical_thresh = [v for k, v in exporter.metrics.items() if 'kpi_critical_threshold' in k]
        assert len(critical_thresh) > 0
        assert critical_thresh[0] == 85.0

    def test_prometheus_metrics_text_format(self):
        """Test generating Prometheus text exposition format."""
        exporter = KPIMetricsExporter()
        
        kpi_result = {
            "value": 88.5,
            "threshold_status": "normal",
            "thresholds": {"critical": 85, "warning": 70},
            "unit": "percentage",
        }
        
        exporter.publish_kpi_result("collection_rate", kpi_result)
        metrics_text = exporter.generate_metrics_text()
        
        # Should have HELP and TYPE lines
        assert "# HELP" in metrics_text
        assert "# TYPE" in metrics_text
        
        # Should have metric values
        assert "kpi_value" in metrics_text
        assert "kpi_threshold_status" in metrics_text
        
        # Should end with newline
        assert metrics_text.endswith("\n")

    def test_get_critical_kpis(self):
        """Test retrieving list of critical KPIs."""
        exporter = KPIMetricsExporter()
        
        # Publish some KPIs in different states
        exporter.publish_kpi_result("kpi1", {
            "value": 50.0,
            "threshold_status": "critical",
            "thresholds": {"critical": 85},
            "unit": "pct",
        })
        
        exporter.publish_kpi_result("kpi2", {
            "value": 90.0,
            "threshold_status": "normal",
            "thresholds": {"critical": 85},
            "unit": "pct",
        })
        
        exporter.publish_kpi_result("kpi3", {
            "value": 60.0,
            "threshold_status": "critical",
            "thresholds": {"critical": 85},
            "unit": "pct",
        })
        
        critical = exporter.get_critical_kpis()
        assert "kpi1" in critical
        assert "kpi3" in critical
        assert "kpi2" not in critical

    def test_get_warning_kpis(self):
        """Test retrieving list of warning KPIs."""
        exporter = KPIMetricsExporter()
        
        exporter.publish_kpi_result("kpi1", {
            "value": 72.0,
            "threshold_status": "warning",
            "thresholds": {"critical": 85, "warning": 70},
            "unit": "pct",
        })
        
        exporter.publish_kpi_result("kpi2", {
            "value": 90.0,
            "threshold_status": "normal",
            "thresholds": {"critical": 85},
            "unit": "pct",
        })
        
        warning = exporter.get_warning_kpis()
        assert "kpi1" in warning
        assert "kpi2" not in warning

    def test_get_status_summary(self):
        """Test getting summary of all KPI statuses."""
        exporter = KPIMetricsExporter()
        
        exporter.publish_kpi_result("kpi1", {
            "value": 50.0,
            "threshold_status": "critical",
            "thresholds": {"critical": 85},
            "unit": "pct",
        })
        
        exporter.publish_kpi_result("kpi2", {
            "value": 72.0,
            "threshold_status": "warning",
            "thresholds": {"critical": 85, "warning": 70},
            "unit": "pct",
        })
        
        exporter.publish_kpi_result("kpi3", {
            "value": 95.0,
            "threshold_status": "normal",
            "thresholds": {"critical": 85},
            "unit": "pct",
        })
        
        summary = exporter.get_status_summary()
        assert summary["critical"] == 1
        assert summary["warning"] == 1
        assert summary["normal"] == 1
        assert summary["not_configured"] == 0

    def test_metadata_storage(self):
        """Test that metadata is stored for reference."""
        exporter = KPIMetricsExporter()
        
        kpi_result = {
            "value": 88.5,
            "threshold_status": "normal",
            "thresholds": {"critical": 85},
            "unit": "percentage",
        }
        
        exporter.publish_kpi_result(
            "collection_rate",
            kpi_result,
            category="collections",
            owner_email="ops@abaco.local"
        )
        
        # Check metadata was stored
        assert "collection_rate" in exporter.metric_metadata
        metadata = exporter.metric_metadata["collection_rate"]
        assert metadata["threshold_status"] == "normal"
        assert metadata["value"] == 88.5
        assert metadata["category"] == "collections"
        assert metadata["owner_email"] == "ops@abaco.local"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
