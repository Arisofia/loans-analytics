"""Logistic Scorecard Model using WoE transformation.

A stable, interpretable model for credit risk.
Transforms numeric features into Weight of Evidence (WoE) bins
and applies Logistic Regression.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, accuracy_score
from .woe_iv_engine import WoEIVEngine

logger = logging.getLogger(__name__)

class LogisticScorecardModel:
    """Logistic Regression model based on Weight of Evidence."""

    def __init__(self, target_col: str = "is_default"):
        self.target_col = target_col
        self.engine = WoEIVEngine(target_col=target_col)
        self.model = LogisticRegression()
        self.features: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def train(self, df: pd.DataFrame, features: List[str]) -> Dict[str, Any]:
        """Train the scorecard: calculate WoE and fit Logistic Regression."""
        self.features = features
        
        # 1. Calculate WoE for all selected features
        self.engine.analyze_all(df, features)
        
        # 2. Transform dataset to WoE values
        X_woe = self._transform_to_woe(df)
        y = df[self.target_col]
        
        # 3. Fit Model
        self.model.fit(X_woe, y)
        
        # 4. Evaluate
        y_proba = self.model.predict_proba(X_woe)[:, 1]
        auc = roc_auc_score(y, y_proba)
        gini = 2 * auc - 1
        
        self.metadata = {
            "model_type": "LogisticScorecard",
            "features": self.features,
            "iv_values": self.engine.iv_values,
            "coefficients": dict(zip(self.features, self.model.coef_[0].tolist())),
            "intercept": float(self.model.intercept_[0]),
            "metrics": {
                "auc_roc": round(auc, 4),
                "gini": round(gini, 4)
            }
        }
        
        return self.metadata["metrics"]

    def _transform_to_woe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Replace raw values with their corresponding WoE."""
        X_woe = pd.DataFrame(index=df.index)
        
        for feat in self.features:
            stats = self.engine.stats[feat]
            # Use binning logic to map
            # This is a simplified version: in production we'd use fixed bin boundaries
            # For now, we'll re-calculate bins to find the WoE
            try:
                # Re-apply the same binning logic used in training
                bins = pd.qcut(df[feat], 10, duplicates='drop')
                woe_map = dict(zip(stats['bin'], stats['woe']))
                X_woe[feat] = bins.map(woe_map).fillna(0.0).astype(float)
            except:
                X_woe[feat] = 0.0
                
        return X_woe

    def predict_proba(self, input_data: Dict[str, Any]) -> float:
        """Predict probability for a single loan."""
        # This requires a more robust mapping of raw values to fixed WoE bins
        # For simplicity in this initial implementation, we refer to the coefficients
        # In a real scorecard, we'd pre-calculate a 'Points Table'
        
        # Mocking for now - implementation of fixed bin lookup needed for true inference
        return 0.05 

    def save(self, model_dir: str = "models/risk") -> str:
        path = Path(model_dir)
        path.mkdir(parents=True, exist_ok=True)
        
        meta_path = path / "logistic_scorecard_metadata.json"
        with open(meta_path, "w") as f:
            # We need to handle the Interval objects in stats if we were to save them
            # For now, save just the key metadata
            json.dump(self.metadata, f, indent=2)
            
        return str(meta_path)
