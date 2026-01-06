from typing import Any, Dict, Tuple

from src.kpis.base import KPIMetadata, create_context


class PortfolioHealthCalculator:
    """Portfolio Health Score - Composite KPI (not derived from DataFrame)."""

    METADATA = KPIMetadata(
        name="PortfolioHealth",
        description="Composite score (0-100) reflecting portfolio quality",
        formula="(100 - PAR30) * (CollectionRate / 100)",
        unit="score",
        data_sources=["computed"],
        threshold_warning=70.0,
        threshold_critical=50.0,
        owner="CRO",
    )

    def calculate(self, par_30: float, collection_rate: float) -> Tuple[float, Dict[str, Any]]:
        # Snippet formula: (100 - PAR30) * (collection_rate / 100)
        par_factor = 100.0 - float(par_30)
        coll_factor = float(collection_rate) / 100.0

        # Cap the score at a 0-10 range for downstream UX/consistency.
        raw_value = max(0.0, par_factor * coll_factor)
        value = float(min(10.0, raw_value))
        return value, create_context(
            self.METADATA.formula,
            rows_processed=2,
            par_30_input=float(par_30),
            collection_rate_input=float(collection_rate),
            par_factor=float(par_factor),
            coll_factor=float(coll_factor),
        )


def calculate_portfolio_health(
    par_30: float, collection_rate: float
) -> Tuple[float, Dict[str, Any]]:
    """Legacy interface for portfolio health calculation."""
    calculator = PortfolioHealthCalculator()
    return calculator.calculate(par_30, collection_rate)
