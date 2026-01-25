"""KPI calculation utilities with validation hooks."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, Iterable

import pandas as pd

from python.models.kpi_models import KpiDefinition


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(Decimal(numerator) / Decimal(denominator))


def compute_par90(loans: pd.DataFrame) -> float:
    """Compute PAR90 metric from a loans dataframe."""

    delinquent = loans[loans["dpd"] >= 90]["principal"].sum()
    total = loans["principal"].sum()
    return _safe_divide(delinquent, total)


def compute_collection_rate(collections: pd.DataFrame) -> float:
    """Compute collection rate over the provided window."""

    scheduled = collections["scheduled"].sum()
    collected = collections["collected"].sum()
    return _safe_divide(collected, scheduled)


def _round_value(value: float, precision: int) -> float:
    try:
        quantized = Decimal(str(value)).quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP)
        return float(quantized)
    except (InvalidOperation, ValueError):
        return value


def calculate_kpi(definition: KpiDefinition, frames: Dict[str, pd.DataFrame]) -> float:
    """Calculate a KPI based on its definition and available frames."""

    if definition.name.upper() == "PAR90":
        value = compute_par90(frames[definition.source_table])
    elif definition.name.upper() == "COLLECTION_RATE":
        value = compute_collection_rate(frames[definition.source_table])
    else:
        raise NotImplementedError(f"KPI {definition.name} is not yet implemented")

    lower, upper = (definition.validation.validation_range or (None, None))
    if lower is not None and value < lower:
        raise ValueError(f"KPI {definition.name} below minimum threshold: {value} < {lower}")
    if upper is not None and value > upper:
        raise ValueError(f"KPI {definition.name} above maximum threshold: {value} > {upper}")

    return _round_value(value, definition.validation.precision)


def calculate_all_kpis(definitions: Iterable[KpiDefinition], frames: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    """Calculate all KPIs from the provided definitions."""

    results: Dict[str, float] = {}
    for definition in definitions:
        results[definition.name] = calculate_kpi(definition, frames)
    return results
