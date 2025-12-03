import pandas as pd
import numpy as np

class FeatureEngineer:
    """A class for performing feature engineering on financial data."""

    @staticmethod
    def segment_by_revenue(revenue: pd.Series) -> pd.Series:
        """Segments customers into tiers based on revenue."""
        bins = [-np.inf, 50000, 100000, np.inf]
        labels = ['Bronze', 'Silver', 'Gold']
        return pd.cut(revenue, bins=bins, labels=labels, right=False)

    @classmethod
    def enrich_portfolio(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enriches a portfolio dataframe with utilization, DPD buckets, and revenue-based segments.
        This method operates on a copy to prevent mutation of the original dataframe.

        Args:
            df (pd.DataFrame): The input portfolio dataframe.

        Returns:
            pd.DataFrame: The enriched dataframe with new feature columns.
        """
        enriched_df = df.copy()

        # Conditionally compute utilization if balance and limit columns exist
        if 'balance' in enriched_df.columns and 'limit' in enriched_df.columns:
            enriched_df['utilization'] = np.where(
                enriched_df['limit'] > 0,
                enriched_df['balance'] / enriched_df['limit'],
                0
            )

        # Conditionally create DPD buckets if dpd column exists
        if 'dpd' in enriched_df.columns:
            bins = [-np.inf, 0, 30, 60, 90, np.inf]
            labels = ['Current', '1-30 DPD', '31-60 DPD', '61-90 DPD', '90+ DPD']
            enriched_df['dpd_bucket'] = pd.cut(enriched_df['dpd'], bins=bins, labels=labels, right=True)

        # Always derive segment from revenue if revenue column exists
        if 'revenue' in enriched_df.columns:
            enriched_df['segment'] = cls.segment_by_revenue(enriched_df['revenue'])

        return enriched_df
