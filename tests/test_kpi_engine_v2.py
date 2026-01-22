import pandas as pd
import pytest

from src.kpi_engine_v2 import KPIEngineV2


class TestKPIEngineV2:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame(
            {
                "dpd_30_60_usd": [100, 200, 0],
                "dpd_60_90_usd": [50, 100, 0],
                "dpd_90_plus_usd": [25, 50, 0],
                "total_receivable_usd": [1000, 2000, 500],
                "cash_available_usd": [100, 200, 50],
                "total_eligible_usd": [1000, 2000, 500],
            }
        )

    def test_kpi_engine_initialization(self, sample_df):
        engine = KPIEngineV2(sample_df)
        assert engine.df is not None
        assert engine.actor == "system"
        assert engine.action == "kpi"

    def test_calculate_all(self, sample_df):
        engine = KPIEngineV2(sample_df)
        metrics = engine.calculate_all(include_composite=True)

        assert "PAR30" in metrics
        assert "PAR90" in metrics
        assert "CollectionRate" in metrics
        assert "PortfolioHealth" in metrics

        for key, metric_data in metrics.items():
            assert "value" in metric_data
            if "error" not in metric_data:
                assert metric_data["value"] is not None

    def test_individual_calculations(self, sample_df):
        engine = KPIEngineV2(sample_df)

        par30_val, par30_ctx = engine.calculate_par_30()
        assert isinstance(par30_val, float)
        assert "formula" in par30_ctx

        par90_val, par90_ctx = engine.calculate_par_90()
        assert isinstance(par90_val, float)

        coll_val, coll_ctx = engine.calculate_collection_rate()
        assert isinstance(coll_val, float)

    def test_audit_trail(self, sample_df):
        engine = KPIEngineV2(sample_df)
        engine.calculate_all()
        audit_df = engine.get_audit_trail()

        assert len(audit_df) > 0
        assert "event" in audit_df.columns
        assert "status" in audit_df.columns
        assert "timestamp" in audit_df.columns

    def test_empty_dataframe(self):
        engine = KPIEngineV2(pd.DataFrame())
        metrics = engine.calculate_all()
        assert len(metrics) == 4  # All KPIs return with Empty DataFrame reason
        for key, metric_data in metrics.items():
            if key != "PortfolioHealth":  # Composite KPI has different structure
                assert metric_data.get("reason") == "Empty DataFrame"
