"""
Synthetic KPI data loader for testing (no Supabase connectivity).

Security: Uses `random` with seed for reproducible synthetic KPI sequences.
No real customer, portfolio, or credential data is handled here.

Follows python:S2245 guidelines: synthetic metrics don't require cryptographic RNG.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable, List


@dataclass
class KpiRecord:
    kpi_name: str
    kpi_date: date
    value: Decimal
    unit: str


class KpiDataLoader:
    """
    Synthetic KPI data loader used only for tests.

    Security note:
    - Uses random with seed for reproducible synthetic KPI sequences.
    - No real customer, portfolio, or credential data is handled here.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._seed = seed
        if seed is not None:
            random.seed(seed)

    def generate_kpi_series(
        self,
        kpi_id: str,
        start_date: date,
        *,
        days: int,
        base_value: float = 100.0,
        trend: float = 0.001,
        noise: float = 5.0,
        unit: str = "EUR",
    ) -> List[KpiRecord]:
        """
        Generate reproducible synthetic KPI time series.

        Args:
            kpi_id: Unique KPI identifier (also used as seed differentiator)
            start_date: First date in series
            days: Number of days to generate
            base_value: Starting value
            trend: Daily trend (e.g., 0.001 = 0.1% growth per day)
            noise: Random volatility magnitude
            unit: Measurement unit (e.g., "EUR")

        Returns:
            List of synthetic KPI records
        """
        # Re-seed if same KPI ID is used again (ensures reproducibility)
        if self._seed is not None:
            random.seed(self._seed)

        records: List[KpiRecord] = []
        current_value = base_value

        for offset in range(days):
            current_date = date.fromordinal(start_date.toordinal() + offset)
            # Simple random walk with drift
                            drift = base_value * trend
                            volatility = random.uniform(-noise, noise)  # nosec
                            current_value = max(0.0, current_value + drift + volatility)
            records.append(
                KpiRecord(
                    kpi_name=kpi_id,
                    kpi_date=current_date,
                    value=Decimal(str(round(current_value, 2))),
                    unit=unit,
                )
            )

        return records

    def load_to_supabase_mock(self, records: Iterable[KpiRecord]) -> int:
        """
        Fake persistence method for tests that need a 'loader' interface.

        Returns the number of records 'loaded'. No external I/O is performed.
        """
        return sum(1 for _ in records)
