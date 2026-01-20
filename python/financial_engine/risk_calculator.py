import polars as pl
from abc import ABC, abstractmethod
from typing import Dict, Any

class RiskStrategy(ABC):
    @abstractmethod
    def process_expression(self) -> pl.Expr:
        """Return a Polars expression for the risk action."""
        pass

class RecourseStrategy(RiskStrategy):
    def process_expression(self) -> pl.Expr:
        # If overdue >90, chargeback
        return pl.when(pl.col("days_overdue") > 90) \
                 .then(pl.lit("chargeback")) \
                 .otherwise(pl.lit("ok"))

class NonRecourseStrategy(RiskStrategy):
    def process_expression(self) -> pl.Expr:
        # If overdue >90 and insolvency, insurance claim
        return pl.when((pl.col("days_overdue") > 90) & (pl.col("reason") == "insolvency")) \
                 .then(pl.lit("insurance_claim")) \
                 .otherwise(pl.lit("ok"))

class HybridStrategy(RiskStrategy):
    def process_expression(self) -> pl.Expr:
        # Hybrid logic: could be a mix, here we combine both for demonstration
        return pl.when((pl.col("days_overdue") > 90) & (pl.col("reason") == "insolvency")) \
                 .then(pl.lit("insurance_claim")) \
                 .when(pl.col("days_overdue") > 90) \
                 .then(pl.lit("chargeback")) \
                 .otherwise(pl.lit("ok"))

class RiskCalculator:
    """
    Polars-native Risk Calculator using Strategy Pattern.
    """
    @staticmethod
    def get_strategy(recourse_type: str) -> RiskStrategy:
        strategies = {
            "recourse": RecourseStrategy(),
            "non-recourse": NonRecourseStrategy(),
            "hybrid": HybridStrategy()
        }
        strategy = strategies.get(recourse_type.lower())
        if not strategy:
            raise ValueError(f"Unknown recourse type: {recourse_type}")
        return strategy

    def calculate_risk_actions(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Applies risk strategies to the dataframe.
        Supports mixed recourse types in the same dataframe by partitioning.
        """
        if "recourse_type" not in df.columns:
            raise ValueError("DataFrame must contain 'recourse_type' column")

        # Get unique recourse types present in the data
        recourse_types = df.select("recourse_type").unique().to_series().to_list()
        
        # We can use a vectorized when/then chain if we have few types,
        # or partition and apply strategy-specific expressions.
        
        # Vectorized approach:
        expr = pl.lit("unknown")
        for rt in recourse_types:
            try:
                strategy = self.get_strategy(rt)
                expr = pl.when(pl.col("recourse_type") == rt) \
                         .then(strategy.process_expression()) \
                         .otherwise(expr)
            except ValueError:
                continue
                
        return df.with_columns([
            expr.alias("recourse_action")
        ])
