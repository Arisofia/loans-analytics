"""Weight of Evidence (WoE) and Information Value (IV) Engine.

Used for feature selection and building interpretable logistic scorecards.
Provides automated binning and IV calculation to identify predictive power.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class WoEIVEngine:
    """Calculates WoE and IV for features against a binary target."""

    def __init__(self, target_col: str = "is_default"):
        self.target_col = target_col
        self.stats: Dict[str, pd.DataFrame] = {}
        self.iv_values: Dict[str, float] = {}

    def calculate_iv(self, df: pd.DataFrame, feature: str, bins: int = 10) -> Tuple[pd.DataFrame, float]:
        """Calculate WoE and IV for a specific feature.
        
        Uses qcut for automatic equal-frequency binning of numeric features.
        """
        # Ensure we work with a copy and drop NaNs for stats
        data = df[[feature, self.target_col]].copy()
        
        # Numeric binning
        try:
            data['bin'] = pd.qcut(data[feature], bins, duplicates='drop')
        except (ValueError, TypeError):
            # Fallback for categorical or sparse numeric
            data['bin'] = data[feature].astype(str)

        # Group by bin
        stats = data.groupby('bin', observed=True).agg(
            total_count=(self.target_col, 'count'),
            bad_count=(self.target_col, 'sum')
        ).reset_index()

        stats['good_count'] = stats['total_count'] - stats['bad_count']
        
        # Distribution
        total_bad = stats['bad_count'].sum()
        total_good = stats['good_count'].sum()
        
        if total_bad == 0 or total_good == 0:
            logger.warning("Feature %s has no target variance. IV will be 0.", feature)
            return stats, 0.0

        stats['dist_bad'] = stats['bad_count'] / total_bad
        stats['dist_good'] = stats['good_count'] / total_good
        
        # WoE calculation (add small epsilon to avoid log(0))
        eps = 1e-9
        stats['woe'] = np.log((stats['dist_good'] + eps) / (stats['dist_bad'] + eps))
        
        # IV contribution
        stats['iv_contrib'] = (stats['dist_good'] - stats['dist_bad']) * stats['woe']
        
        total_iv = stats['iv_contrib'].sum()
        
        self.stats[feature] = stats
        self.iv_values[feature] = total_iv
        
        return stats, total_iv

    def analyze_all(self, df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
        """Calculate IV for a list of features and rank them."""
        for feat in features:
            if feat in df.columns:
                _, iv = self.calculate_iv(df, feat)
                logger.info("Feature: %s | IV: %.4f", feat, iv)
        
        # Sort by IV descending
        return dict(sorted(self.iv_values.items(), key=lambda item: item[1], reverse=True))

    @staticmethod
    def interpret_iv(iv: float) -> str:
        """Standard IV power interpretation."""
        if iv < 0.02: return "Sin poder predictivo"
        if iv < 0.1:  return "Débil"
        if iv < 0.3:  return "Medio"
        return "Fuerte"
