"""
Historical Context Provider for Multi-Agent System.

Provides historical KPI data, trend analysis, and temporal context
to enhance agent decision-making with historical awareness.

Phase G4.1 Implementation
"""

# pylint: disable=too-many-lines

import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

import numpy as np
from pydantic import BaseModel, Field

# Constant for repeated literal
KPI_IDENTIFIER_DESC = "KPI identifier"


class TrendDirection(str, Enum):
    """Trend direction classification."""

    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class TrendStrength(str, Enum):
    """Trend strength classification."""

    STRONG = "strong"  # Clear, consistent trend
    MODERATE = "moderate"  # Noticeable but variable
    WEAK = "weak"  # Slight trend, high variance


@dataclass
class KpiHistoricalValue:
    """Historical KPI data point."""

    kpi_id: str
    date: date
    value: float
    timestamp: datetime


class TrendAnalysis(BaseModel):
    """
    Summary of a KPI's historical trend over a fixed analysis window.

    This model captures the result of a time-based trend analysis performed
    over historical KPI values, typically using a simple linear regression
    of value versus time. The regression produces a slope and r-squared
    statistic (`slope`, `r_squared`), which are then interpreted into a
    qualitative trend `direction` (e.g., increasing, decreasing, stable) and
    `strength` (e.g., strong, moderate, weak).

    In addition, the analysis records the time span covered (`period_days`),
    the starting and ending KPI values (`start_value`, `end_value`), and the
    overall `percent_change` across the period. The `calculated_at` field
    indicates when this analysis snapshot was generated.
    """

    kpi_id: str = Field(..., description=KPI_IDENTIFIER_DESC)
    direction: TrendDirection = Field(..., description="Trend direction")
    strength: TrendStrength = Field(..., description="Trend strength")
    slope: float = Field(..., description="Linear regression slope")
    r_squared: float = Field(..., description="R-squared value (0-1)")
    period_days: int = Field(..., description="Analysis period in days")
    start_value: float = Field(..., description="Starting value")
    end_value: float = Field(..., description="Ending value")
    percent_change: float = Field(..., description="Percentage change")
    calculated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Analysis timestamp (UTC)",
    )


class SeasonalityPattern(BaseModel):
    """Seasonality pattern detection result."""

    kpi_id: str = Field(..., description=KPI_IDENTIFIER_DESC)
    has_seasonality: bool = Field(..., description="Whether seasonality detected")
    cycle_length_months: Optional[int] = Field(None, description="Seasonal cycle length")
    peak_months: List[int] = Field(
        default_factory=list,
        description="Months with peak values (1-12)",
    )
    trough_months: List[int] = Field(
        default_factory=list, description="Months with trough values (1-12)"
    )
    seasonal_strength: float = Field(..., description="Strength of seasonality (0-1)")
    adjustment_factors: Dict[int, float] = Field(
        default_factory=dict, description="Monthly adjustment factors (month: factor)"
    )


class KpiProjection(BaseModel):
    """KPI forecast projection."""

    kpi_id: str = Field(..., description=KPI_IDENTIFIER_DESC)
    projection_date: date = Field(..., description="Future date")
    predicted_value: float = Field(..., description="Predicted value")
    lower_bound: float = Field(..., description="Lower confidence bound")
    upper_bound: float = Field(..., description="Upper confidence bound")
    confidence_level: float = Field(0.95, description="Confidence level (0-1)")
    method: str = Field(..., description="Forecasting method used")


@runtime_checkable
class HistoricalDataBackend(Protocol):
    """
    Protocol for historical KPI data backends.

    This defines the interface that any data source must implement
    to provide historical KPI data to the HistoricalContextProvider.

    Implementations:
        - MockHistoricalBackend: In-memory mock data (Phase G4.1, default)
        - SupabaseHistoricalBackend: Supabase-backed storage (Phase G4.2+)
        - FileHistoricalBackend: File-based storage (future)
    """

    def get_kpi_history(
        self,
        kpi_id: str,
        start_date: date,
        end_date: date,
    ) -> List[KpiHistoricalValue]:
        """
        Retrieve historical KPI values for the specified date range.

        Args:
            kpi_id: KPI identifier
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of KpiHistoricalValue objects sorted by date

        Raises:
            ValueError: If date range is invalid
            RuntimeError: If data source is unavailable
        """


class HistoricalContextProvider:
    """
    Provides historical context and trend analysis for KPIs.

    Phase G4.1 Implementation:
    - Historical KPI data retrieval
    - Trend analysis (direction, strength)
    - Moving averages
    - Basic caching for performance
    """

    def __init__(
        self,
        cache_ttl_seconds: int = 3600,
        mode: Optional[str] = None,
        backend: Optional[HistoricalDataBackend] = None,
        rule_hash: Optional[str] = None,
    ) -> None:
        """
        Initialize historical context provider with backend validation and mode selection.
        """
        self.cache_ttl_seconds: int = cache_ttl_seconds
        self._cache: Dict[str, tuple[datetime, Any]] = {}
        self._historical_data: Dict[str, List[KpiHistoricalValue]] = {}
        self.rule_hash: str = rule_hash or "default_v1"

        env_mode = os.getenv("HISTORICAL_CONTEXT_MODE", "REAL").upper()
        self.mode: str = (mode or env_mode).upper()
        self._backend: Optional[HistoricalDataBackend] = backend

        if self.mode not in ("MOCK", "REAL"):
            raise ValueError(f"Invalid mode '{self.mode}'. Must be 'MOCK' or 'REAL'.")
        if self.mode == "REAL":
            if self._backend is None:
                raise RuntimeError(
                    "HistoricalContextProvider in REAL mode requires a backend "
                    "implementing HistoricalDataBackend protocol."
                )
            # Validate backend interface at runtime
            if not isinstance(self._backend, HistoricalDataBackend):
                raise TypeError("Backend does not implement HistoricalDataBackend protocol.")

    def _load_historical_data(
        self, kpi_id: str, start_date: date, end_date: date
    ) -> List[KpiHistoricalValue]:
        """
        Load historical KPI data from configured data source.

        Phase G4.1:
            - Returns mock data used for tests and development
        Phase G4.2:
            - Adds REAL mode backed by external data source (e.g., Supabase)
            - MOCK remains the default and is NOT removed

        Current modes:
            - MOCK: Deterministic synthetic time series (fully test-covered)
            - REAL: Delegates to self._backend.get_kpi_history()

        Args:
            kpi_id: KPI identifier
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of historical KPI values sorted by date

        Raises:
            RuntimeError: If REAL mode is used without a configured backend
            ValueError: If backend returns invalid data

        Note:
            MOCK mode data generation is INTENTIONAL and should NOT be
            removed. It provides a stable, deterministic baseline for
            all unit tests and development environments.
        """
        # REAL mode: delegate to configured backend
        if self.mode == "REAL":
            if self._backend is None:
                raise RuntimeError(
                    "HistoricalContextProvider in REAL mode requires a backend "
                    "implementing HistoricalDataBackend protocol."
                )
            return self._backend.get_kpi_history(kpi_id, start_date, end_date)

        # ===================================================================
        # MOCK mode: Phase G4.1 synthetic data generation
        # This is the DEFAULT behavior to maintain backward compatibility
        # ===================================================================

        values = []
        current = start_date
        # Different KPIs get different base values to ensure distinction
        base_value = 100.0 + (abs(hash(kpi_id)) % 50)

        while current <= end_date:
            # Generate mock trend data
            days_diff = (current - start_date).days
            # Slight upward trend
            trend_value = base_value + (days_diff * 0.1)
            # ±5 variation with more diverse hashing to avoid collisions
            hash_seed = abs(hash(f"{kpi_id}|{current.isoformat()}|{len(kpi_id)}"))
            noise = (hash_seed % 100) / 10.0 - 5.0

            values.append(
                KpiHistoricalValue(
                    kpi_id=kpi_id,
                    date=current,
                    value=trend_value + noise,
                    timestamp=datetime.now(timezone.utc),
                )
            )
            current += timedelta(days=1)

        return values

    def get_kpi_history(
        self, kpi_id: str, start_date: date, end_date: date
    ) -> List[KpiHistoricalValue]:
        """
        Fetch historical KPI values for a time range.

        Args:
            kpi_id: KPI identifier
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of historical KPI values ordered by date
        """
        # Rule-hash cache invalidation: include rule_hash in cache key
        cache_key = f"{self.rule_hash}:{kpi_id}:{start_date}:{end_date}"

        # Check cache
        if cached_entry := self._cache.get(cache_key):
            cached_time, cached_data = cached_entry
            cache_age_seconds = (datetime.now(timezone.utc) - cached_time).total_seconds()
            cache_fresh = cache_age_seconds < self.cache_ttl_seconds
            if cache_fresh:
                return cached_data

        # Load data
        data = self._load_historical_data(kpi_id, start_date, end_date)

        # Cache result
        self._cache[cache_key] = (datetime.now(timezone.utc), data)

        return data

    def get_trend(self, kpi_id: str, periods: int = 12) -> TrendAnalysis:
        """
        Calculate trend for a KPI over the specified periods (months).
        Uses simple linear regression for clarity and auditability.
        """
        end_date: date = date.today()
        start_date: date = end_date - timedelta(days=periods * 30)
        history: List[KpiHistoricalValue] = self.get_kpi_history(kpi_id, start_date, end_date)
        if len(history) < 2:
            return self._empty_trend(kpi_id, start_date, end_date)

        n: int = len(history)
        x_values: List[float] = [float(i) for i in range(n)]
        y_values: List[float] = [h.value for h in history]

        x_mean: float = sum(x_values) / n
        y_mean: float = sum(y_values) / n
        numerator: float = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator: float = sum((x - x_mean) ** 2 for x in x_values)
        slope: float = numerator / denominator if denominator != 0 else 0.0
        y_pred: List[float] = [slope * (x - x_mean) + y_mean for x in x_values]
        ss_res: float = sum((y - yp) ** 2 for y, yp in zip(y_values, y_pred))
        ss_tot: float = sum((y - y_mean) ** 2 for y in y_values)
        r_squared: float = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        start_val: float = history[0].value
        end_val: float = history[-1].value
        percent_change: float = ((end_val - start_val) / start_val * 100) if start_val != 0 else 0.0

        if abs(slope) < 0.01:
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING

        if r_squared > 0.7:
            strength = TrendStrength.STRONG
        elif r_squared > 0.4:
            strength = TrendStrength.MODERATE
        else:
            strength = TrendStrength.WEAK

        return TrendAnalysis(
            kpi_id=kpi_id,
            direction=direction,
            strength=strength,
            slope=slope,
            r_squared=r_squared,
            period_days=(end_date - start_date).days,
            start_value=start_val,
            end_value=end_val,
            percent_change=percent_change,
        )

    def agent_summary(self, kpi_id: str, periods: int = 12) -> Dict[str, Any]:
        """
        Return a concise, agent-ready summary of historical context for a KPI.
        Includes trend, moving average, and recent change point if detected.
        """
        trend = self.get_trend(kpi_id, periods)
        moving_avg = self.get_moving_average(kpi_id, window_days=30)
        change_point = self.detect_change_point(kpi_id, window_size=14, periods=periods)
        return {
            "kpi_id": kpi_id,
            "trend": trend.model_dump(),
            "moving_average_30d": moving_avg,
            "recent_change_point": change_point,
        }

    def get_moving_average(self, kpi_id: str, window_days: int = 30) -> Optional[float]:
        """
        Calculate moving average for a KPI.

        Args:
            kpi_id: KPI identifier
            window_days: Window size in days (default 30)

        Returns:
            Moving average value or None if insufficient data
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=window_days)

        history = self.get_kpi_history(kpi_id, start_date, end_date)

        return sum(h.value for h in history) / len(history) if history else None

    def clear_cache(self) -> None:
        """Clear the historical data cache."""
        self._cache.clear()

    # =====================================================================
    # Phase G4.2: Advanced Trend Analysis Methods
    # =====================================================================

    def get_exponential_trend(
        self, kpi_id: str, alpha: float = 0.3, periods: int = 12
    ) -> TrendAnalysis:
        """
        Calculate exponential smoothing trend for a KPI.

        Uses exponential weighted moving average to emphasize recent values
        while still considering historical patterns.

        Args:
            kpi_id: KPI identifier
            alpha: Smoothing factor (0-1, higher = more recent weight)
            periods: Number of periods to analyze

        Returns:
            Trend analysis with exponential smoothing applied
        """
        if alpha < 0 or alpha > 1:
            raise ValueError("alpha must be between 0 and 1")

        end_date = date.today()
        start_date = end_date - timedelta(days=periods * 30)

        history = self.get_kpi_history(kpi_id, start_date, end_date)

        if len(history) < 2:
            return self._empty_trend(kpi_id, start_date, end_date)

        # Calculate exponential smoothing
        smoothed = [history[0].value]
        for i in range(1, len(history)):
            smoothed_val = alpha * history[i].value + (1 - alpha) * smoothed[i - 1]
            smoothed.append(smoothed_val)

        # Calculate trend from smoothed values
        return self._calculate_trend_from_values(
            kpi_id, history, smoothed, (end_date - start_date).days
        )

    def get_polynomial_trend(
        self, kpi_id: str, degree: int = 2, periods: int = 12
    ) -> TrendAnalysis:
        """
        Calculate polynomial trend fit for a KPI.

        Fits polynomial curve to historical data to capture non-linear trends.

        Args:
            kpi_id: KPI identifier
            degree: Polynomial degree (1=linear, 2=quadratic, 3=cubic)
            periods: Number of periods to analyze

        Returns:
            Trend analysis with polynomial fit
        """
        if degree < 1 or degree > 5:
            raise ValueError("degree must be between 1 and 5")

        end_date = date.today()
        start_date = end_date - timedelta(days=periods * 30)

        history = self.get_kpi_history(kpi_id, start_date, end_date)

        if len(history) < degree + 2:
            return self._empty_trend(kpi_id, start_date, end_date)

        x_vals = np.array([float(i) for i in range(len(history))])
        y_vals = np.array([h.value for h in history])

        # Polynomial fitting using numpy
        coeffs = np.polyfit(x_vals, y_vals, degree)
        p = np.poly1d(coeffs)
        y_pred = p(x_vals)

        # Calculate R-squared
        y_mean = np.mean(y_vals)
        ss_res = np.sum((y_vals - y_pred) ** 2)
        ss_tot = np.sum((y_vals - y_mean) ** 2)
        r_squared = max(0.0, 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0)

        # Determine strength
        if r_squared > 0.7:
            strength = TrendStrength.STRONG
        elif r_squared > 0.4:
            strength = TrendStrength.MODERATE
        else:
            strength = TrendStrength.WEAK

        # Polynomial direction based on predicted values
        start_val = history[0].value
        end_val = history[-1].value

        # Calculate percent change
        percent_change = 0.0
        has_nonzero_start = start_val != 0
        if has_nonzero_start:
            percent_change = (end_val - start_val) / start_val * 100

        # Determine direction based on predicted values
        is_increasing = y_pred[-1] > y_pred[0]
        is_decreasing = y_pred[-1] < y_pred[0]

        if is_increasing:
            direction = TrendDirection.INCREASING
        elif is_decreasing:
            direction = TrendDirection.DECREASING
        else:
            direction = TrendDirection.STABLE

        # Use the slope of the linear fit as a simplified 'slope'
        # for compatibility with TrendAnalysis model
        slope = (y_pred[-1] - y_pred[0]) / len(history) if len(history) > 1 else 0.0

        return TrendAnalysis(
            kpi_id=kpi_id,
            direction=direction,
            strength=strength,
            slope=slope,
            r_squared=r_squared,
            period_days=(end_date - start_date).days,
            start_value=start_val,
            end_value=end_val,
            percent_change=percent_change,
        )

    def get_standard_deviation_bands(
        self, kpi_id: str, window_days: int = 30, num_std: float = 2.0
    ) -> Dict[str, Any]:
        """
        Calculate standard deviation bands (Bollinger-style).

        Args:
            kpi_id: KPI identifier
            window_days: Window size for moving average
            num_std: Number of standard deviations for bands

        Returns:
            Dictionary with moving_average, upper_band, and lower_band
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=window_days)

        history = self.get_kpi_history(kpi_id, start_date, end_date)

        if not history:
            return {}

        values = np.array([h.value for h in history])
        mean = np.mean(values)
        std = np.std(values)

        return {
            "moving_average": mean,
            "upper_band": mean + (num_std * std),
            "lower_band": mean - (num_std * std),
            "std_dev": std,
            "num_std": num_std,
        }

    def get_weighted_moving_average(self, kpi_id: str, window_days: int = 30) -> Optional[float]:
        """
        Calculate weighted moving average (more recent values have higher weight).

        Args:
            kpi_id: KPI identifier
            window_days: Window size in days

        Returns:
            Weighted moving average value or None if insufficient data
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=window_days)

        history = self.get_kpi_history(kpi_id, start_date, end_date)

        if not history:
            return None

        # Linear weight: earlier values get lower weight
        n = len(history)
        weights = [(i + 1) / (n * (n + 1) / 2) for i in range(n)]

        weighted_sum = sum(h.value * w for h, w in zip(history, weights))
        total_weight = sum(weights)
        return (weighted_sum / total_weight) if total_weight > 0 else None

    def get_trend_for_period(self, kpi_id: str, days: int = 30) -> TrendAnalysis:
        """
        Calculate trend for a KPI over a specific number of days.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        history = self.get_kpi_history(kpi_id, start_date, end_date)

        if len(history) < 2:
            return self._empty_trend(kpi_id, start_date, end_date)

        values = [h.value for h in history]
        return self._calculate_trend_from_values(kpi_id, history, values, days)

    def get_multi_period_trends(self, kpi_id: str) -> Dict[str, TrendAnalysis]:
        """
        Calculate trends over multiple time periods.

        Returns trends for 7-day, 30-day, 90-day, and Year-over-Year periods.

        Args:
            kpi_id: KPI identifier

        Returns:
            Dictionary of period -> trend analysis
        """
        return {
            "7_day": self.get_trend_for_period(kpi_id, days=7),
            "30_day": self.get_trend_for_period(kpi_id, days=30),
            "90_day": self.get_trend_for_period(kpi_id, days=90),
            "yoy": self.get_trend_for_period(kpi_id, days=365),
        }

    def get_trend_confidence_interval(
        self, kpi_id: str, confidence: float = 0.95, periods: int = 12
    ) -> Dict[str, float]:
        """
        Calculate confidence interval for trend estimate.

        Args:
            kpi_id: KPI identifier
            confidence: Confidence level (0.90, 0.95, 0.99)
            periods: Number of periods to analyze

        Returns:
            Dictionary with trend, lower, upper, and confidence values
        """
        trend = self.get_trend(kpi_id, periods)

        # Simple confidence interval based on R-squared
        # Lower confidence = wider interval
        z_score = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}.get(confidence, 1.96)

        # Standard error approximation based on R-squared
        std_error = trend.slope * (1 - trend.r_squared) * z_score

        return {
            "trend_slope": trend.slope,
            "lower_bound": trend.slope - std_error,
            "upper_bound": trend.slope + std_error,
            "confidence_level": confidence,
        }

    def detect_change_point(
        self, kpi_id: str, window_size: int = 14, periods: int = 12
    ) -> Optional[Dict[str, Any]]:
        """
        Detect significant change points in historical data.

        Args:
            kpi_id: KPI identifier
            window_size: Window size for change detection
            periods: Number of periods to analyze

        Returns:
            Dictionary with change point info or None if no change detected
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=periods * 30)

        history = self.get_kpi_history(kpi_id, start_date, end_date)

        if len(history) < window_size * 2:
            return None

        # Calculate mean of first and second half
        mid = len(history) // 2
        first_half_mean = sum(h.value for h in history[:mid]) / mid
        second_half_mean = sum(h.value for h in history[mid:]) / (len(history) - mid)

        # Calculate relative change
        change_pct = 0.0
        has_nonzero_first_half = first_half_mean != 0
        if has_nonzero_first_half:
            change_pct = abs(second_half_mean - first_half_mean) / first_half_mean * 100

        # Detect if change is significant (>10%)
        if change_pct > 10:
            change_direction = "increase" if second_half_mean > first_half_mean else "decrease"

            return {
                "change_point_date": history[mid].date,
                "before_mean": first_half_mean,
                "after_mean": second_half_mean,
                "change_pct": change_pct,
                "direction": change_direction,
            }

        return None

    # =====================================================================
    # Helper Methods for Phase G4.2
    # =====================================================================

    def _empty_trend(self, kpi_id: str, start_date: date, end_date: date) -> TrendAnalysis:
        """Helper to create empty trend when insufficient data."""
        return TrendAnalysis(
            kpi_id=kpi_id,
            direction=TrendDirection.STABLE,
            strength=TrendStrength.WEAK,
            slope=0.0,
            r_squared=0.0,
            period_days=(end_date - start_date).days,
            start_value=0.0,
            end_value=0.0,
            percent_change=0.0,
        )

    def _calculate_trend_from_values(
        self,
        kpi_id: str,
        history: List[KpiHistoricalValue],
        values: List[float],
        period_days: int,
    ) -> TrendAnalysis:
        """Helper to calculate trend from value arrays."""
        n = len(values)
        x_values = list(range(n))
        y_mean = sum(values) / n

        numerator = sum((x - n / 2) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - n / 2) ** 2 for x in x_values)
        slope = numerator / denominator if denominator != 0 else 0.0

        # Calculate R-squared
        y_pred = [slope * (x - n / 2) + y_mean for x in x_values]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(values, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        start_val = history[0].value
        end_val = history[-1].value
        percent_change = 0.0
        has_nonzero_start = start_val != 0
        if has_nonzero_start:
            percent_change = (end_val - start_val) / start_val * 100

        if abs(slope) < 0.01:
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING

        if r_squared > 0.7:
            strength = TrendStrength.STRONG
        elif r_squared > 0.4:
            strength = TrendStrength.MODERATE
        else:
            strength = TrendStrength.WEAK

        return TrendAnalysis(
            kpi_id=kpi_id,
            direction=direction,
            strength=strength,
            slope=slope,
            r_squared=r_squared,
            period_days=period_days,
            start_value=start_val,
            end_value=end_val,
            percent_change=percent_change,
        )

    @staticmethod
    def _fit_linear(x_values: List[float], y_values: List[float]) -> tuple[float, float]:
        """Fit linear regression (slope, intercept)."""
        n = len(x_values)
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        slope = numerator / denominator if denominator != 0 else 0.0
        intercept = y_mean - slope * x_mean

        return slope, intercept

    @staticmethod
    def _fit_quadratic(x_values: List[float], y_values: List[float]) -> tuple[float, float, float]:
        """Fit quadratic regression (a, b, c for ax^2 + bx + c)."""
        n = len(x_values)

        # Using Cramer's rule for 3x3 system (simplified)
        sum_x = sum(x_values)
        sum_x2 = sum(x**2 for x in x_values)
        sum_x3 = sum(x**3 for x in x_values)
        sum_x4 = sum(x**4 for x in x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2y = sum((x**2) * y for x, y in zip(x_values, y_values))

        # Simplified quadratic fit (2nd order)
        # For production, use numpy.polyfit
        denom = (
            n * sum_x2 * sum_x4
            + sum_x * sum_x3 * sum_x2
            + sum_x2 * sum_x * sum_x3
            - sum_x2 * sum_x2 * sum_x2
            - n * sum_x3 * sum_x3
            - sum_x * sum_x * sum_x4
        )

        if abs(denom) < 1e-10:
            # Fallback to linear fit
            slope, intercept = HistoricalContextProvider._fit_linear(x_values, y_values)
            return 0.0, slope, intercept

        a = (
            sum_y * (sum_x2 * sum_x4 - sum_x3 * sum_x3)
            - sum_xy * (sum_x * sum_x4 - sum_x2 * sum_x3)
            + sum_x2y * (sum_x * sum_x3 - sum_x2 * sum_x2)
        ) / denom

        b = (
            n * (sum_xy * sum_x4 - sum_x2y * sum_x3)
            - sum_y * (sum_x * sum_x4 - sum_x2 * sum_x3)
            + sum_x2y * (sum_x * sum_x3 - sum_x2 * sum_x2)
        ) / denom

        c = (
            n * (sum_x2 * sum_x2y - sum_x * sum_xy)
            - sum_y * (sum_x2 * sum_x2 - sum_x * sum_x)
            + sum_xy * (sum_x * sum_x - sum_x2 * sum_x)
        ) / denom

        return a, b, c

    # =====================================================================
    # Phase G4.3: Seasonality Detection Methods
    # =====================================================================

    def get_seasonality(self, kpi_id: str, periods_years: int = 2) -> SeasonalityPattern:
        """
        Detect seasonality patterns in historical KPI data.

        Analyzes data over multiple years to identify recurring monthly patterns.

        Args:
            kpi_id: KPI identifier
            periods_years: Number of years to analyze

        Returns:
            SeasonalityPattern with detected cycles and factors
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=periods_years * 365)

        history = self.get_kpi_history(kpi_id, start_date, end_date)

        if len(history) < 12:
            return SeasonalityPattern(
                kpi_id=kpi_id,
                has_seasonality=False,
                cycle_length_months=None,
                seasonal_strength=0.0,
            )

        # Group by month
        monthly_values: Dict[int, List[float]] = {}
        for h in history:
            month = h.date.month
            if month not in monthly_values:
                monthly_values[month] = []
            monthly_values[month].append(h.value)

        # Calculate monthly means
        monthly_means = {m: sum(v) / len(v) for m, v in monthly_values.items()}
        overall_mean = sum(h.value for h in history) / len(history)

        # Calculate adjustment factors (ratio to mean)
        adjustment_factors = {m: val / overall_mean for m, val in monthly_means.items()}

        # Identify peaks and troughs
        sorted_months = sorted(monthly_means.items(), key=lambda x: x[1])
        trough_months = [m for m, v in sorted_months[:3]]
        peak_months = [m for m, v in sorted_months[-3:]]

        # Calculate seasonal strength (variance of factors)
        factors_list = list(adjustment_factors.values())
        seasonal_strength = float(np.std(factors_list)) if factors_list else 0.0
        # Normalize strength to 0-1 range (approximate)
        seasonal_strength = min(1.0, seasonal_strength * 2)

        has_seasonality = seasonal_strength > 0.1

        return SeasonalityPattern(
            kpi_id=kpi_id,
            has_seasonality=has_seasonality,
            cycle_length_months=12,
            peak_months=peak_months,
            trough_months=trough_months,
            seasonal_strength=seasonal_strength,
            adjustment_factors=adjustment_factors,
        )

    def deseasonalize(self, kpi_id: str, value: float, month: int) -> float:
        """
        Remove seasonal component from a KPI value.

        Args:
            kpi_id: KPI identifier
            value: Raw KPI value
            month: Month of the value (1-12)

        Returns:
            Deseasonalized value
        """
        seasonality = self.get_seasonality(kpi_id)
        seasonality_data = seasonality.model_dump()
        adjustment_factors = seasonality_data.get("adjustment_factors", {})
        factor = adjustment_factors.get(month, 1.0) if isinstance(adjustment_factors, dict) else 1.0
        return value / factor if factor != 0 else value

    def get_seasonal_decomposition(
        self, kpi_id: str, model: str = "additive"
    ) -> Dict[str, List[float]]:
        """
        Decompose KPI into trend, seasonal, and residual components.

        Args:
            kpi_id: KPI identifier
            model: "additive" or "multiplicative"

        Returns:
            Dictionary with trend, seasonal, and residual arrays
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        history = self.get_kpi_history(kpi_id, start_date, end_date)

        if not history:
            return {"trend": [], "seasonal": [], "residual": []}

        values = np.array([h.value for h in history])
        seasonality = self.get_seasonality(kpi_id)

        seasonal_component: List[float] = []
        for h in history:
            seasonality_data = seasonality.model_dump()
            adjustment_factors = seasonality_data.get("adjustment_factors", {})
            factor = (
                adjustment_factors.get(h.date.month, 1.0)
                if isinstance(adjustment_factors, dict)
                else 1.0
            )
            if model == "additive":
                # For additive, factor is difference from mean
                overall_mean = np.mean(values)
                seasonal_component.append((factor - 1.0) * overall_mean)
            else:
                seasonal_component.append(factor)

        seasonal_component_array = np.array(seasonal_component)

        # Simple trend (moving average)
        window = 30
        trend_component = np.convolve(values, np.ones(window) / window, mode="same")

        if model == "additive":
            residual = values - trend_component - seasonal_component_array
        else:
            residual = values / (trend_component * seasonal_component_array)

        return {
            "trend": trend_component.tolist(),
            "seasonal": seasonal_component_array.tolist(),
            "residual": residual.tolist(),
        }

    # =====================================================================
    # Phase G4.4: Forecasting Methods
    # =====================================================================

    def get_forecast(
        self,
        kpi_id: str,
        steps: int = 30,
        confidence_level: float = 0.95,
        method: str = "exponential_smoothing",
    ) -> List[KpiProjection]:
        """
        Generate future projections for a KPI.

        Args:
            kpi_id: KPI identifier
            steps: Number of days to forecast
            confidence_level: Confidence level (0-1)
            method: Forecasting method ("exponential_smoothing", "linear", "arima")

        Returns:
            List of KpiProjection objects
        """
        end_date = date.today()
        history = self.get_kpi_history(kpi_id, end_date - timedelta(days=90), end_date)

        if not history:
            return []

        values = np.array([h.value for h in history])
        last_val = values[-1]

        projections = []
        for i in range(1, steps + 1):
            target_date = end_date + timedelta(days=i)

            if method == "linear":
                trend = self.get_trend(kpi_id, periods=3)
                predicted = last_val + (trend.slope * i)
            elif method == "exponential_smoothing":
                # Simple exponential smoothing forecast (constant level)
                alpha = 0.3
                level = last_val
                for v in values:
                    level = alpha * v + (1 - alpha) * level
                predicted = level
            else:
                # Default to last value (naive)
                predicted = last_val

            # Confidence interval expands with time (square root of steps)
            std_dev = np.std(values) if len(values) > 1 else 1.0
            z_score = {0.80: 1.28, 0.90: 1.645, 0.95: 1.96}.get(confidence_level, 1.96)
            uncertainty = z_score * std_dev * np.sqrt(i)

            projections.append(
                KpiProjection(
                    kpi_id=kpi_id,
                    projection_date=target_date,
                    predicted_value=predicted,
                    lower_bound=predicted - uncertainty,
                    upper_bound=predicted + uncertainty,
                    confidence_level=confidence_level,
                    method=method,
                )
            )

        return projections

    def validate_forecast(self, kpi_id: str, projections: List[KpiProjection]) -> Dict[str, float]:
        """
        Validate forecast accuracy against actual historical data.

        Args:
            kpi_id: KPI identifier
            projections: Previously generated projections

        Returns:
            Dictionary with accuracy metrics (MAE, RMSE, MAPE)
        """
        if not projections:
            return {}

        start_date = projections[0].projection_date
        end_date = projections[-1].projection_date

        actuals = self.get_kpi_history(kpi_id, start_date, end_date)
        if not actuals:
            return {}

        actual_map = {a.date: a.value for a in actuals}
        errors = []
        pct_errors = []

        for p in projections:
            if p.projection_date in actual_map:
                actual = actual_map[p.projection_date]
                error = p.predicted_value - actual
                errors.append(error)
                if actual != 0:
                    pct_errors.append(abs(error / actual))

        if not errors:
            return {}

        errors_np = np.array(errors)
        return {
            "mae": float(np.mean(np.abs(errors_np))),
            "rmse": float(np.sqrt(np.mean(errors_np**2))),
            "mape": float(np.mean(pct_errors)) * 100 if pct_errors else 0.0,
            "bias": float(np.mean(errors_np)),
        }

    def get_scenario_projection(
        self, kpi_id: str, scenarios: Dict[str, float], steps: int = 30
    ) -> Dict[str, List[KpiProjection]]:
        """
        Generate multiple scenario-based projections.

        Args:
            kpi_id: KPI identifier
            scenarios: Map of scenario name to growth/adjustment factor
            steps: Number of days to forecast

        Returns:
            Dictionary mapping scenario name to its projection list
        """
        base_forecast = self.get_forecast(kpi_id, steps=steps)
        results = {"base": base_forecast}

        for name, factor in scenarios.items():
            scenario_projections = []
            for p in base_forecast:
                # Apply scenario factor (e.g., 1.1 for 10% growth)
                adjusted_val = p.predicted_value * factor
                scenario_projections.append(
                    KpiProjection(
                        kpi_id=kpi_id,
                        projection_date=p.projection_date,
                        predicted_value=adjusted_val,
                        lower_bound=p.lower_bound * factor,
                        upper_bound=p.upper_bound * factor,
                        confidence_level=p.confidence_level,
                        method=f"scenario_{name}",
                    )
                )
            results[name] = scenario_projections

        return results

    # =====================================================================
    # Phase G4.5: Benchmarking Methods
    # =====================================================================

    def get_benchmarks(self, kpi_id: str) -> Dict[str, float]:
        """
        Retrieve benchmark values for a KPI.

        Returns industry standards, peer medians, and regulatory thresholds.
        """
        # Centralized benchmark registry (mock data for now)
        registry = {
            "default_rate": {
                "industry_avg": 0.05,
                "peer_median": 0.045,
                "regulatory_max": 0.10,
                "basel_iii_threshold": 0.08,
            },
            "disbursements": {
                "industry_avg": 100.0,
                "industry_growth_avg": 0.12,
                "target_growth": 0.15,
            },
            "par_30": {
                "industry_avg": 0.03,
                "regulatory_limit": 0.05,
            },
            "npl_rate": {
                "industry_avg": 0.04,
                "regulatory_limit": 0.07,
            },
        }
        return registry.get(kpi_id, {"industry_avg": 0.0})

    def get_percentile_ranking(self, kpi_id: str, current_value: float) -> float:
        """
        Calculate percentile rank of current KPI value relative to peers.

        Args:
            kpi_id: KPI identifier
            current_value: Current value to rank

        Returns:
            Percentile rank (0.0 to 1.0)
        """
        # Simulate peer distribution for ranking
        benchmarks = self.get_benchmarks(kpi_id)
        median = benchmarks.get("peer_median", benchmarks.get("industry_avg", current_value))

        # Generate mock distribution centered around peer median
        rng = np.random.default_rng(abs(hash(kpi_id)) % 10000)
        peer_data = rng.normal(loc=median, scale=max(0.001, median * 0.2), size=100)

        # Percentile rank
        rank = float(np.sum(peer_data < current_value) / len(peer_data))

        # For some KPIs (like default_rate), lower is better, so we invert the rank
        if "rate" in kpi_id or "par" in kpi_id or "processing_time" in kpi_id:
            return 1.0 - rank

        return rank

    def get_z_score(self, kpi_id: str, current_value: float) -> float:
        """
        Calculate Z-score relative to industry distribution.

        Args:
            kpi_id: KPI identifier
            current_value: Current value

        Returns:
            Number of standard deviations from mean
        """
        benchmarks = self.get_benchmarks(kpi_id)
        avg = benchmarks.get("industry_avg", current_value)
        std = max(0.001, avg * 0.2)  # Mock standard deviation

        return (current_value - avg) / std

    def get_gap_analysis(
        self, kpi_id: str, current_value: float, target_key: str = "industry_avg"
    ) -> Dict[str, Any]:
        """
        Perform gap analysis against a specific benchmark target.

        Args:
            kpi_id: KPI identifier
            current_value: Current value
            target_key: Key in benchmark dict to compare against

        Returns:
            Dictionary with gap metrics and status
        """
        benchmarks = self.get_benchmarks(kpi_id)
        target = benchmarks.get(target_key)

        if target is None:
            return {"error": f"Target {target_key} not found for {kpi_id}"}

        gap = current_value - target
        gap_pct = (gap / target * 100) if target != 0 else 0.0

        # Determine status (depends on KPI direction)
        is_positive_kpi = "rate" not in kpi_id and "par" not in kpi_id
        status = "on_track"

        if is_positive_kpi and gap < -0.05 * target:
            status = "below_target"
        elif is_positive_kpi and gap > 0.05 * target:
            status = "above_target"
        elif not is_positive_kpi and gap > 0.05 * target:
            status = "at_risk"
        elif not is_positive_kpi and gap < -0.05 * target:
            status = "performing_well"

        return {
            "kpi_id": kpi_id,
            "current": current_value,
            "target": target,
            "target_type": target_key,
            "gap": gap,
            "gap_pct": gap_pct,
            "status": status,
        }

    def _is_regulatory_threshold_key(self, key: str) -> bool:
        """Return True when a benchmark key represents a regulatory threshold."""
        return any(word in key for word in ["regulatory", "threshold", "limit", "max"])

    def _classify_threshold_direction(self, kpi_id: str) -> Optional[str]:
        """Classify whether lower or higher values are preferable for a KPI."""
        if any(word in kpi_id for word in ["rate", "par", "dpd"]):
            return "lower_is_better"
        if any(word in kpi_id for word in ["ratio", "coverage", "liquidity"]):
            return "higher_is_better"
        return None

    def _get_threshold_severity(
        self, direction: str, current_value: float, threshold: float
    ) -> Optional[str]:
        """Determine severity for a threshold breach, or None if no breach."""
        if direction == "lower_is_better" and current_value > threshold:
            return "critical" if current_value > threshold * 1.2 else "warning"
        if direction == "higher_is_better" and current_value < threshold:
            return "critical" if current_value < threshold * 0.8 else "warning"
        return None

    def check_regulatory_thresholds(
        self, kpi_id: str, current_value: float
    ) -> List[Dict[str, Any]]:
        """
        Check KPI against known regulatory thresholds.

        Args:
            kpi_id: KPI identifier
            current_value: Current value

        Returns:
            List of detected violations or warnings
        """
        benchmarks = self.get_benchmarks(kpi_id)
        direction = self._classify_threshold_direction(kpi_id)
        if direction is None:
            return []

        results = []
        for key, threshold in benchmarks.items():
            if not self._is_regulatory_threshold_key(key):
                continue

            severity = self._get_threshold_severity(direction, current_value, threshold)
            if severity is None:
                continue

            results.append(
                {
                    "threshold_name": key,
                    "threshold_value": threshold,
                    "current_value": current_value,
                    "status": "violation",
                    "severity": severity,
                }
            )

        return results
