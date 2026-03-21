"""
Test dashboard KPI enrichment with threshold status integration.

This test demonstrates the end-to-end flow:
1. KPI values are computed (from KPICatalogProcessor or backend)
2. Values are enriched with threshold_status from SSOT registry
3. Dashboard renders KPIs with visual threshold badges
"""

import pytest

from backend.python.kpis.threshold_enrichment import (
    get_threshold_status,
    load_kpi_thresholds,
    enrich_kpis_with_thresholds,
)


class TestThresholdEnrichmentIntegration:
    """Test threshold enrichment for dashboard KPI visualization."""

    def test_load_kpi_registry_thresholds(self):
        """Verify we can load thresholds from SSOT registry."""
        thresholds_map = load_kpi_thresholds()

        # Should load some thresholds from registry
        assert isinstance(thresholds_map, dict)
        assert len(thresholds_map) > 0, "Should have loaded thresholds from registry"

        # Portfolio KPIs should be present
        assert any(
            k in thresholds_map
            for k in [
                "total_outstanding_balance",
                "portfolio_yield",
                "par_30",
                "net_interest_margin",
            ]
        ), "Expected portfolio KPI thresholds in registry"

    def test_threshold_determination_high_is_good(self):
        """Test threshold status for metrics where higher is better."""
        # Collection rate: higher is better
        thresholds = {"critical": 85, "warning": 70}

        assert get_threshold_status(95, thresholds) == "normal"
        assert get_threshold_status(78, thresholds) == "warning"
        assert get_threshold_status(60, thresholds) == "critical"

    def test_threshold_determination_low_is_good(self):
        """Test threshold status for metrics where lower is better."""
        # PAR/DPD: lower is better
        thresholds = {"critical": 5, "warning": 10}

        assert get_threshold_status(2, thresholds) == "normal"
        assert get_threshold_status(7, thresholds) == "warning"
        assert get_threshold_status(15, thresholds) == "critical"

    def test_enrich_kpis_for_dashboard(self):
        """Test enriching KPI snapshot with threshold metadata."""
        # Simulate KPIs computed by KPICatalogProcessor
        kpi_snapshot = {
            "total_outstanding_balance": 50000000,  # $50M
            "par_30": 3.5,  # 3.5% of portfolio
            "collection_rate": 88.2,  # 88.2%
            "total_loans": 250,  # 250 loans
        }

        # Custom thresholds for test
        thresholds_map = {
            "total_outstanding_balance": {"warning": 10000000, "critical": 50000000},
            "par_30": {"critical": 5, "warning": 10},
            "collection_rate": {"critical": 85, "warning": 70},
            # total_loans has no thresholds
        }

        enriched = enrich_kpis_with_thresholds(kpi_snapshot, thresholds_map)

        # Verify all KPIs are enriched
        assert len(enriched) == len(kpi_snapshot)

        # Check enriched structure
        assert "total_outstanding_balance" in enriched
        assert enriched["total_outstanding_balance"]["value"] == 50000000

        # Verify threshold status calculations
        # $50M at critical threshold (50M), so should be normal (meets critical)
        assert enriched["total_outstanding_balance"]["threshold_status"] == "normal"

        # PAR 3.5% is below critical 5%, so normal
        assert enriched["par_30"]["threshold_status"] == "normal"

        # Collection rate 88.2% is above critical 85%, so normal
        assert enriched["collection_rate"]["threshold_status"] == "normal"

        # No thresholds for total_loans
        assert enriched["total_loans"]["threshold_status"] == "not_configured"

    def test_dashboard_badge_rendering_status_values(self):
        """Test that threshold status values are valid for display."""
        valid_statuses = {"normal", "warning", "critical", "not_configured"}

        test_values = [
            (100, {"critical": 85, "warning": 70}),
            (75, {"critical": 85, "warning": 70}),
            (50, {"critical": 85, "warning": 70}),
            (0, None),
            (100, {}),
        ]

        for value, thresholds in test_values:
            status = get_threshold_status(value, thresholds)
            assert status in valid_statuses, f"Status '{status}' not in {valid_statuses}"

    def test_enriched_kpi_structure_for_streamlit_rendering(self):
        """Test that enriched KPIs have the right structure for Streamlit display."""
        kpi_snapshot = {"collection_rate": 88.5}
        thresholds_map = {"collection_rate": {"critical": 85, "warning": 70}}

        enriched = enrich_kpis_with_thresholds(kpi_snapshot, thresholds_map)

        # Should have required fields for rendering
        assert "collection_rate" in enriched
        kpi_data = enriched["collection_rate"]

        # Structure expected by updated render_kpi_snapshot
        assert "value" in kpi_data
        assert "threshold_status" in kpi_data
        assert "thresholds" in kpi_data

        # Value should be unchanged
        assert kpi_data["value"] == pytest.approx(88.5)

        # Status should be one of the valid values
        assert kpi_data["threshold_status"] in {"normal", "warning", "critical", "not_configured"}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
