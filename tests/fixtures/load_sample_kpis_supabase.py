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

    def __init__(self, seed: int | None=None) -> None:
        self._seed = seed
        if seed is not None:
            random.seed(seed)

    def generate_kpi_series(self, kpi_id: str, start_date: date, *, days: int, base_value: float=100.0, trend: float=0.001, noise: float=5.0, unit: str='EUR') -> List[KpiRecord]:
        if self._seed is not None:
            random.seed(self._seed)
        records: List[KpiRecord] = []
        current_value = base_value
        for offset in range(days):
            current_date = date.fromordinal(start_date.toordinal() + offset)
            drift = base_value * trend
            volatility = random.uniform(-noise, noise)
            current_value = max(0.0, current_value + drift + volatility)
            records.append(KpiRecord(kpi_name=kpi_id, kpi_date=current_date, value=Decimal(str(round(current_value, 2))), unit=unit))
        return records

    def load_to_supabase_mock(self, records: Iterable[KpiRecord]) -> int:
        return sum((1 for _ in records))
