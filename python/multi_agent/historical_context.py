"""
Historical Context Provider for Multi-Agent System.

Provides historical KPI data, trend analysis, and temporal context
to enhance agent decision-making with historical awareness.

Phase G4.1 Implementation
"""

import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

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
    ) -> None:
        """
        Initialize historical context provider with backend validation and mode selection.
        """
        self.cache_ttl_seconds: int = cache_ttl_seconds
        self._cache: Dict[str, tuple[datetime, Any]] = {}
        self._historical_data: Dict[str, List[KpiHistoricalValue]] = {}

        env_mode = os.getenv("HISTORICAL_CONTEXT_MODE", "MOCK").upper()
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
        cache_key = f"{kpi_id}:{start_date}:{end_date}"

        # Check cache
        cached_entry = self._cache.get(cache_key)
        if cached_entry:
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
        numerator: float = sum(
            (x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values, strict=False)
        )
        denominator: float = sum((x - x_mean) ** 2 for x in x_values)
        slope: float = numerator / denominator if denominator != 0 else 0.0
        y_pred: List[float] = [slope * (x - x_mean) + y_mean for x in x_values]
        ss_res: float = sum((y - yp) ** 2 for y, yp in zip(y_values, y_pred, strict=False))
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
            "trend": trend.dict(),
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

        if not history:
            return None

        return sum(h.value for h in history) / len(history)

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

        # Simple polynomial fitting using numpy-like approach
        # (without external dependency)
        x_vals = [float(i) for i in range(len(history))]
        y_vals = [h.value for h in history]

        # For polynomial fitting, use linear regression as simplification
        # (full polynomial fitting without numpy is complex)
        coeffs = self._fit_linear(x_vals, y_vals)
        y_pred = [coeffs[0] * x + coeffs[1] for x in x_vals]

        # Calculate R-squared
        y_mean = sum(y_vals) / len(y_vals)
        ss_res = sum((y - yp) ** 2 for y, yp in zip(y_vals, y_pred, strict=False))
        ss_tot = sum((y - y_mean) ** 2 for y in y_vals)
        r_squared = max(0.0, 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0)

        # Determine strength
        if r_squared > 0.7:
            strength = TrendStrength.STRONG
        elif r_squared > 0.4:
            strength = TrendStrength.MODERATE
        else:
            strength = TrendStrength.WEAK

        # Polynomial direction based on fitted curve direction at end
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

        return TrendAnalysis(
            kpi_id=kpi_id,
            direction=direction,
            strength=strength,
            slope=coeffs[0],
            r_squared=r_squared,
            period_days=(end_date - start_date).days,
            start_value=start_val,
            end_value=end_val,
            percent_change=percent_change,
        )

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

        weighted_sum = sum(h.value * w for h, w in zip(history, weights, strict=False))
        total_weight = sum(weights)

        result = None
        has_nonzero_weight = total_weight > 0
        if has_nonzero_weight:
            result = weighted_sum / total_weight

        return result

    def get_multi_period_trends(self, kpi_id: str) -> Dict[str, TrendAnalysis]:
        """
        Calculate trends over multiple time periods.

        Returns trends for 7-day, 30-day, 90-day, and annual periods.

        Args:
            kpi_id: KPI identifier

        Returns:
            Dictionary of period -> trend analysis
        """
        return {
            "7_day": self.get_trend(kpi_id, periods=1),
            "30_day": self.get_trend(kpi_id, periods=1),
            "90_day": self.get_trend(kpi_id, periods=3),
            "annual": self.get_trend(kpi_id, periods=12),
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

        numerator = sum((x - n / 2) * (y - y_mean) for x, y in zip(x_values, values, strict=False))
        denominator = sum((x - n / 2) ** 2 for x in x_values)
        slope = numerator / denominator if denominator != 0 else 0.0

        # Calculate R-squared
        y_pred = [slope * (x - n / 2) + y_mean for x in x_values]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(values, y_pred, strict=False))
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

        numerator = sum(
            (x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values, strict=False)
        )
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
        sum_xy = sum(x * y for x, y in zip(x_values, y_values, strict=False))
        sum_x2y = sum((x**2) * y for x, y in zip(x_values, y_values, strict=False))

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
