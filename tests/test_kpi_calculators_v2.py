import pytest
import pandas as pd
import numpy as np
from python.kpis.par_30 import PAR30Calculator, calculate_par_30
from python.kpis.par_90 import PAR90Calculator, calculate_par_90
from python.kpis.collection_rate import CollectionRateCalculator, calculate_collection_rate
from python.kpis.portfolio_health import PortfolioHealthCalculator, calculate_portfolio_health


class TestPAR30Calculator:
    def test_par30_valid_calculation(self):
        df = pd.DataFrame({
            "dpd_30_60_usd": [100, 200],
            "dpd_60_90_usd": [50, 100],
            "dpd_90_plus_usd": [25, 50],
            "total_receivable_usd": [1000, 2000],
        })
        value, context = calculate_par_30(df)
        assert isinstance(value, float)
        assert value == 17.5
        assert context["rows_processed"] == 2
        assert "formula" in context

    def test_par30_zero_receivable(self):
        df = pd.DataFrame({
            "dpd_30_60_usd": [100],
            "dpd_60_90_usd": [50],
            "dpd_90_plus_usd": [25],
            "total_receivable_usd": [0],
        })
        value, context = calculate_par_30(df)
        assert value == 0.0
        assert context["reason"] == "Zero total receivable"

    def test_par30_empty_dataframe(self):
        df = pd.DataFrame()
        value, context = calculate_par_30(df)
        assert value == 0.0
        assert context["rows_processed"] == 0

    def test_par30_missing_columns(self):
        df = pd.DataFrame({"dpd_30_60_usd": [100]})
        with pytest.raises(ValueError, match="Missing required columns"):
            calculate_par_30(df)


class TestPAR90Calculator:
    def test_par90_valid_calculation(self):
        df = pd.DataFrame({
            "dpd_90_plus_usd": [100, 200],
            "total_receivable_usd": [1000, 2000],
        })
        value, context = calculate_par_90(df)
        assert value == 10.0
        assert context["rows_processed"] == 2

    def test_par90_zero_receivable(self):
        df = pd.DataFrame({
            "dpd_90_plus_usd": [100],
            "total_receivable_usd": [0],
        })
        value, context = calculate_par_90(df)
        assert value == 0.0


class TestCollectionRateCalculator:
    def test_collection_rate_valid(self):
        df = pd.DataFrame({
            "cash_available_usd": [100, 200],
            "total_eligible_usd": [1000, 2000],
        })
        value, context = calculate_collection_rate(df)
        assert value == 10.0
        assert context["rows_processed"] == 2

    def test_collection_rate_with_nulls(self):
        df = pd.DataFrame({
            "cash_available_usd": [100, None, 200],
            "total_eligible_usd": [1000, 2000, 2000],
        })
        value, context = calculate_collection_rate(df)
        assert context["null_count"] > 0


class TestPortfolioHealthCalculator:
    def test_portfolio_health_valid(self):
        value, context = calculate_portfolio_health(5.0, 10.0)
        assert 0.0 <= value <= 10.0
        assert context["par_30_input"] == 5.0
        assert context["collection_rate_input"] == 10.0

    def test_portfolio_health_bounds(self):
        value, _ = calculate_portfolio_health(0.0, 100.0)
        assert value <= 10.0
        assert value >= 0.0
