from typing import Any, Dict, Tuple

from src.kpis.base import KPIMetadata, create_context


class PortfolioHealthCalculator:
    """Portfolio Health Score - Composite KPI (not derived from DataFrame)."""

    METADATA = KPIMetadata(
        name="PortfolioHealth",
        description="Composite score (0-10) reflecting portfolio quality",
        formula="(10 - PAR30/10) * (CollectionRate/10)",
        unit="score",
        data_sources=["computed"],
        threshold_warning=5.0,
        threshold_critical=3.0,
        owner="CRO",
    )

    def calculate(self, par_30: float, collection_rate: float) -> Tuple[float, Dict[str, Any]]:
        par_component = max(0.0, 10.0 - (float(par_30) / 10.0))
        coll_component = float(collection_rate) / 10.0

        value = float(min(10.0, max(0.0, par_component * coll_component)))
        return value, create_context(
            self.METADATA.formula,
            rows_processed=2,
            par_30_input=float(par_30),
            collection_rate_input=float(collection_rate),
            par_component=float(par_component),
            coll_component=float(coll_component),
        )


def calculate_portfolio_health(
    par_30: float, collection_rate: float
) -> Tuple[float, Dict[str, Any]]:
    """Legacy interface for portfolio health calculation."""
    calculator = PortfolioHealthCalculator()
    return calculator.calculate(par_30, collection_rate)
