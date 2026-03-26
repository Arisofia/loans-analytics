"""Unit tests for TargetLoader and 2026 targets system."""

import pytest
from decimal import Decimal
from backend.python.kpis.target_loader import TargetLoader, get_2026_targets
import pandas as pd


class TestTargetLoaderBasics:
    """Test basic target retrieval."""
    
    def test_get_2026_targets_dict(self):
        """Verify hardcoded 2026 targets dict."""
        targets = get_2026_targets()
        assert len(targets) == 12
        assert targets["Jan"] == 8500000
        assert targets["Dec"] == 12000000
        assert targets["Jul"] == 10500000
    
    def test_loader_get_target_by_month_number(self):
        """Test retrieving target by month number (1-12)."""
        loader = TargetLoader()
        
        assert loader.get_target(1) == Decimal("8500000")
        assert loader.get_target(12) == Decimal("12000000")
        assert loader.get_target(6) == Decimal("10200000")
        assert loader.get_target(7) == Decimal("10500000")
    
    def test_loader_get_target_by_month_name(self):
        """Test retrieving target by month name (Jan-Dec, case-insensitive)."""
        loader = TargetLoader()
        
        assert loader.get_target("Jan") == Decimal("8500000")
        assert loader.get_target("DEC") == Decimal("12000000")  # Case insensitive
        assert loader.get_target("Jun") == Decimal("10200000")  # Note: capitalized for month lookup
        assert loader.get_target("JUL") == Decimal("10500000")  # Case insensitive
    
    def test_loader_get_target_invalid(self):
        """Test that invalid month raises ValueError."""
        loader = TargetLoader()
        
        with pytest.raises(ValueError):
            loader.get_target(13)
        
        with pytest.raises(ValueError):
            loader.get_target(0)
        
        with pytest.raises(ValueError):
            loader.get_target("Xxx")


class TestVarianceCalculation:
    """Test variance calculation and status assignment."""
    
    def test_variance_on_track_positive(self):
        """Positive variance (actual > target) within ON_TRACK band."""
        loader = TargetLoader()
        actual = Decimal("8700000")
        target = Decimal("8500000")
        result = loader.calculate_variance(actual, target)
        assert result["status"] == "ON_TRACK"
        assert result["variance_amount"] == Decimal("200000")
        assert result["variance_pct"] == Decimal("2.35")
    
    def test_variance_on_track_negative(self):
        """Negative variance (actual < target) within ON_TRACK band."""
        loader = TargetLoader()
        actual = Decimal("8300000")
        target = Decimal("8500000")
        result = loader.calculate_variance(actual, target)
        assert result["status"] == "ON_TRACK"
        assert result["variance_amount"] == Decimal("-200000")
        assert result["variance_pct"] == Decimal("-2.35")
    
    def test_variance_monitor(self):
        """Variance at boundary of AT_RISK (90-95% band)."""
        loader = TargetLoader()
        actual = Decimal("8075000")
        target = Decimal("8500000")
        result = loader.calculate_variance(actual, target)
        assert result["status"] == "ON_TRACK"
        assert result["variance_pct"] == Decimal("-5.00")
    
    def test_variance_at_risk(self):
        """Negative variance below -5% threshold."""
        loader = TargetLoader()
        actual = Decimal("8000000")  # -500k = -5.88%
        target = Decimal("8500000")
        
        result = loader.calculate_variance(actual, target)
        
        assert result["status"] == "AT_RISK"
        assert result["variance_pct"] == Decimal("-5.88")
    
    def test_variance_exceeded_5pct(self):
        """Positive variance exceeding +5% threshold."""
        loader = TargetLoader()
        actual = Decimal("9000000")  # +500k = +5.88%
        target = Decimal("8500000")
        
        result = loader.calculate_variance(actual, target)
        
        assert result["status"] == "EXCEEDED"
        assert result["variance_pct"] == Decimal("5.88")
    
    def test_variance_exact_match(self):
        """Zero variance (actual = target)."""
        loader = TargetLoader()
        actual = Decimal("8500000")
        target = Decimal("8500000")
        
        result = loader.calculate_variance(actual, target)
        
        assert result["status"] == "ON_TRACK"
        assert result["variance_amount"] == Decimal("0")
        assert result["variance_pct"] == Decimal("0.00")
    
    def test_variance_precision_decimals(self):
        """Verify Decimal precision is maintained."""
        loader = TargetLoader()
        actual = Decimal("8500001") 
        target = Decimal("8500000")
        
        result = loader.calculate_variance(actual, target)
        
        # Should maintain precision
        assert isinstance(result["variance_amount"], Decimal)
        assert isinstance(result["variance_pct"], Decimal)


class TestDataFrameOperations:
    """Test DataFrame loading and comparison."""
    
    def test_export_targets_table(self):
        """Test exporting targets as DataFrame."""
        loader = TargetLoader()
        df = loader.export_targets_table()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12
        assert "month_name" in df.columns
        assert "portfolio_target" in df.columns
        assert df.loc[df["month_name"] == "Jan", "portfolio_target"].values[0] == Decimal("8500000")
        assert df.loc[df["month_name"] == "Dec", "portfolio_target"].values[0] == Decimal("12000000")
    
    def test_load_from_dataframe(self):
        """Test loading targets from DataFrame (simulating Google Sheets export)."""
        loader = TargetLoader()
        df = pd.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "Portfolio_Target": [8500000, 9000000, 9300000, 9600000, 9900000, 10200000, 10500000, 10800000, 11100000, 11400000, 11700000, 12000000],
            "NPL_Target": [2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4],
            "Default_Rate_Target": [1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
        })
        result = loader.load_from_dataframe(df)
        assert result.get("status") == "success"
        assert result.get("rows_loaded") == 12
        assert len(result.get("months_loaded", [])) == 12
    
    def test_compare_actuals_vs_targets(self):
        """Test comparing actual values against targets."""
        loader = TargetLoader()
        actuals = {
            1: Decimal("8700000"),
            2: Decimal("8900000"),
            3: Decimal("9400000"),
        }
        comparison = loader.compare_actuals_vs_targets(actuals)
        assert isinstance(comparison, pd.DataFrame)
        assert len(comparison) == 12
        jan_row = comparison[comparison["month"] == "Jan"].iloc[0]
        assert jan_row["actual_portfolio"] == Decimal("8700000")
        assert jan_row["target"] == 8.5e6
        assert abs(jan_row["variance_pct"] - 2.35) < 0.01


class TestTargetSequence:
    """Test that 2026 target sequence is correct."""
    
    def test_monthly_growth_consistent(self):
        """Verify monthly growth is consistent ($300k/month after Feb)."""
        loader = TargetLoader()
        assert loader.get_target(2) - loader.get_target(1) == Decimal("500000")
        for month in range(3, 13):
            prev_target = loader.get_target(month - 1)
            curr_target = loader.get_target(month)
            growth = curr_target - prev_target
            assert growth == Decimal("300000"), f"Month {month} growth is {growth}, expected 300000"
    
    def test_year_growth_target(self):
        """Verify total year growth is $3.5M."""
        loader = TargetLoader()
        
        jan_target = loader.get_target(1)
        dec_target = loader.get_target(12)
        total_growth = dec_target - jan_target
        
        assert total_growth == Decimal("3500000")
        assert dec_target == Decimal("12000000")
    
    def test_all_months_positive(self):
        """Verify all targets are positive."""
        loader = TargetLoader()
        
        for month in range(1, 13):
            target = loader.get_target(month)
            assert target > 0, f"Month {month} has non-positive target: {target}"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_variance_with_zero_target(self):
        """Test variance calculation doesn't divide by zero."""
        loader = TargetLoader()
        result = loader.calculate_variance(Decimal("1000"), Decimal("0"))
        assert result["status"] == "INVALID_TARGET"
    
    def test_large_variance(self):
        """Test variance for very large positive/negative swings."""
        loader = TargetLoader()
        result = loader.calculate_variance(Decimal("17000000"), Decimal("8500000"))
        assert result["variance_pct"] == Decimal("100.00")
        assert result["status"] == "EXCEEDED"
        result = loader.calculate_variance(Decimal("4250000"), Decimal("8500000"))
        assert result["variance_pct"] == Decimal("-50.00")
        assert result["status"] == "AT_RISK"
    
    def test_very_small_actual(self):
        """Test variance when actual is very small."""
        loader = TargetLoader()
        
        result = loader.calculate_variance(Decimal("1000"), Decimal("8500000"))
        assert result["status"] == "AT_RISK"
        assert result["variance_pct"] < Decimal("-99")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
