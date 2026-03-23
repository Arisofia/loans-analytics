import pytest
from backend.python.kpis.threshold_enrichment import get_threshold_status, load_kpi_thresholds, enrich_kpis_with_thresholds

class TestThresholdEnrichmentIntegration:

    def test_load_kpi_registry_thresholds(self):
        thresholds_map = load_kpi_thresholds()
        assert isinstance(thresholds_map, dict)
        assert len(thresholds_map) > 0, 'Should have loaded thresholds from registry'
        assert any((k in thresholds_map for k in ['total_outstanding_balance', 'portfolio_yield', 'par_30', 'net_interest_margin'])), 'Expected portfolio KPI thresholds in registry'

    def test_threshold_determination_high_is_good(self):
        thresholds = {'critical': 85, 'warning': 70}
        assert get_threshold_status(95, thresholds) == 'normal'
        assert get_threshold_status(78, thresholds) == 'warning'
        assert get_threshold_status(60, thresholds) == 'critical'

    def test_threshold_determination_low_is_good(self):
        thresholds = {'critical': 5, 'warning': 10}
        assert get_threshold_status(2, thresholds) == 'normal'
        assert get_threshold_status(7, thresholds) == 'warning'
        assert get_threshold_status(15, thresholds) == 'critical'

    def test_enrich_kpis_for_dashboard(self):
        kpi_snapshot = {'total_outstanding_balance': 50000000, 'par_30': 3.5, 'collection_rate': 88.2, 'total_loans': 250}
        thresholds_map = {'total_outstanding_balance': {'warning': 10000000, 'critical': 50000000}, 'par_30': {'critical': 5, 'warning': 10}, 'collection_rate': {'critical': 85, 'warning': 70}}
        enriched = enrich_kpis_with_thresholds(kpi_snapshot, thresholds_map)
        assert len(enriched) == len(kpi_snapshot)
        assert 'total_outstanding_balance' in enriched
        assert enriched['total_outstanding_balance']['value'] == 50000000
        assert enriched['total_outstanding_balance']['threshold_status'] == 'normal'
        assert enriched['par_30']['threshold_status'] == 'normal'
        assert enriched['collection_rate']['threshold_status'] == 'normal'
        assert enriched['total_loans']['threshold_status'] == 'not_configured'

    def test_dashboard_badge_rendering_status_values(self):
        valid_statuses = {'normal', 'warning', 'critical', 'not_configured'}
        test_values = [(100, {'critical': 85, 'warning': 70}), (75, {'critical': 85, 'warning': 70}), (50, {'critical': 85, 'warning': 70}), (0, None), (100, {})]
        for value, thresholds in test_values:
            status = get_threshold_status(value, thresholds)
            assert status in valid_statuses, f"Status '{status}' not in {valid_statuses}"

    def test_enriched_kpi_structure_for_streamlit_rendering(self):
        kpi_snapshot = {'collection_rate': 88.5}
        thresholds_map = {'collection_rate': {'critical': 85, 'warning': 70}}
        enriched = enrich_kpis_with_thresholds(kpi_snapshot, thresholds_map)
        assert 'collection_rate' in enriched
        kpi_data = enriched['collection_rate']
        assert 'value' in kpi_data
        assert 'threshold_status' in kpi_data
        assert 'thresholds' in kpi_data
        assert kpi_data['value'] == pytest.approx(88.5)
        assert kpi_data['threshold_status'] in {'normal', 'warning', 'critical', 'not_configured'}
if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
