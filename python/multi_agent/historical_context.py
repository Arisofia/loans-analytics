"""
Historical Context Provider for Multi-Agent System.

Provides historical KPI data, trend analysis, and temporal context
to enhance agent decision-making with historical awareness.

Phase G4.1 Implementation
"""

import os
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Protocol, runtime_checkable

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
        default_factory=lambda: datetime.now(UTC), description="Analysis timestamp (UTC)"
    )


class SeasonalityPattern(BaseModel):
    """Seasonality pattern detection result."""

    kpi_id: str = Field(..., description=KPI_IDENTIFIER_DESC)
    has_seasonality: bool = Field(..., description="Whether seasonality detected")
    cycle_length_months: Optional[int] = Field(None, description="Seasonal cycle length")
    peak_months: List[int] = Field(
        default_factory=list, description="Months with peak values (1-12)"
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
        ...


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
    ):
        """
        Initialize historical context provider.

        Args:
            cache_ttl_seconds: Time-to-live for cached data (default 1 hour)
            mode: Data source mode - "MOCK" (default) or "REAL".
                  Can also be set via HISTORICAL_CONTEXT_MODE env var.
            backend: Optional backend implementation for REAL mode.
                     Required if mode="REAL".

        Phase G4.1 Compatibility:
            Calling HistoricalContextProvider() without arguments works
            exactly as before - uses MOCK mode with synthetic data.

        Phase G4.2 Usage:
            provider = HistoricalContextProvider(
                mode="REAL",
                backend=SupabaseHistoricalBackend()
            )

        Raises:
            ValueError: If mode is not "MOCK" or "REAL"
            RuntimeError: If mode="REAL" but backend is None
        """
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, tuple[datetime, any]] = {}
        self._historical_data: Dict[str, List[KpiHistoricalValue]] = {}

        # Mode selection: default to MOCK for G4.1 backward compatibility
        env_mode = os.getenv("HISTORICAL_CONTEXT_MODE", "MOCK").upper()
        self.mode = (mode or env_mode).upper()

        if self.mode not in ("MOCK", "REAL"):
            raise ValueError(f"Invalid mode '{self.mode}'. Must be 'MOCK' or 'REAL'.")

        self._backend = backend

        # Validate REAL mode configuration
        if self.mode == "REAL" and self._backend is None:
            raise RuntimeError(
                "HistoricalContextProvider in REAL mode requires a backend "
                "implementing HistoricalDataBackend protocol. "
                "Pass backend=YourBackend() to __init__."
            )

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
        base_value = 100.0

        while current <= end_date:
            # Generate mock trend data
            days_diff = (current - start_date).days
            # Slight upward trend
            trend_value = base_value + (days_diff * 0.1)
            # ±5 variation
            noise = (hash(f"{kpi_id}{current}") % 100) / 10.0 - 5.0

            values.append(
                KpiHistoricalValue(
                    kpi_id=kpi_id,
                    date=current,
                    value=trend_value + noise,
                    timestamp=datetime.now(UTC),
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
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if (datetime.now(UTC) - cached_time).seconds < self.cache_ttl_seconds:
                return cached_data

        # Load data
        data = self._load_historical_data(kpi_id, start_date, end_date)

        # Cache result
        self._cache[cache_key] = (datetime.now(UTC), data)

        return data

    def get_trend(self, kpi_id: str, periods: int = 12) -> TrendAnalysis:
        """
        Calculate trend for a KPI over the specified periods.

        Args:
            kpi_id: KPI identifier
            periods: Number of periods to analyze (default 12 months)

        Returns:
            Trend analysis result
        """
        # Get historical data for trend analysis
        end_date = date.today()
        start_date = end_date - timedelta(days=periods * 30)  # Approximate months

        history = self.get_kpi_history(kpi_id, start_date, end_date)

        if len(history) < 2:
            # Not enough data for trend
            return TrendAnalysis(
                kpi_id=kpi_id,
                direction=TrendDirection.STABLE,
                strength=TrendStrength.WEAK,
                slope=0.0,
                r_squared=0.0,
                period_days=(end_date - start_date).days,
                start_value=history[0].value if history else 0.0,
                end_value=history[-1].value if history else 0.0,
                percent_change=0.0,
            )

        # Simple linear regression
        n = len(history)
        x_values = list(range(n))
        y_values = [h.value for h in history]

        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        slope = numerator / denominator if denominator != 0 else 0.0

        # Calculate R-squared
        y_pred = [slope * (x - x_mean) + y_mean for x in x_values]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(y_values, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        # Determine direction and strength
        start_val = history[0].value
        end_val = history[-1].value
        percent_change = ((end_val - start_val) / start_val * 100) if start_val != 0 else 0.0

        # Direction
        if abs(slope) < 0.01:
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING

        # Strength based on R-squared
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
