"""Default risk prediction model using XGBoost.

This module provides a wrapper around a trained XGBoost model for
predicting loan default probability. The model file is expected at
``models/risk/default_risk_xgb.ubj``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

logger = logging.getLogger(__name__)

# Feature columns expected by the trained model (order matters)
FEATURE_COLUMNS: List[str] = [
    "loan_amount",
    "interest_rate",
    "term_months",
    "ltv_ratio",
    "dti_ratio",
    "credit_score",
    "days_past_due",
    "monthly_income",
    "employment_length_years",
    "num_open_accounts",
]


class DefaultRiskModel:
    """Thin wrapper around a serialised XGBoost booster for default prediction."""

    def __init__(self, booster: Any) -> None:
        self._booster = booster

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    @classmethod
    def load(cls, path: Union[str, Path]) -> "DefaultRiskModel":
        """Load a saved XGBoost model from *path*.

        Raises ``FileNotFoundError`` if the file does not exist and
        ``ImportError`` if xgboost is not installed.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError("Model file not found: %s" % path)

        try:
            import xgboost as xgb
        except ImportError as exc:
            raise ImportError(
                "xgboost is required for the default risk model. "
                "Install it with: pip install xgboost"
            ) from exc

        booster = xgb.Booster()
        booster.load_model(str(path))
        logger.info("Loaded XGBoost model from %s", path)
        return cls(booster)

    def save(self, path: Union[str, Path]) -> None:
        """Persist the booster to *path* (UBJ format)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._booster.save_model(str(path))
        logger.info("Saved XGBoost model to %s", path)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def predict_proba(self, loan_data: Dict[str, Any]) -> float:
        """Return the default probability for a single loan.

        Parameters
        ----------
        loan_data:
            Dictionary whose keys are a superset of ``FEATURE_COLUMNS``.
            Missing features default to ``0.0``.

        Returns
        -------
        float
            Probability in [0, 1].
        """
        try:
            import xgboost as xgb
        except ImportError as exc:
            raise ImportError(
                "xgboost is required for prediction. " "Install it with: pip install xgboost"
            ) from exc

        features = np.array(
            [[float(loan_data.get(col, 0.0)) for col in FEATURE_COLUMNS]],
            dtype=np.float32,
        )
        dmatrix = xgb.DMatrix(features, feature_names=FEATURE_COLUMNS)
        preds = self._booster.predict(dmatrix)
        probability = float(preds[0])
        # Clamp to [0, 1] for safety
        return max(0.0, min(1.0, probability))

    def predict_batch(self, loans: List[Dict[str, Any]]) -> List[float]:
        """Return default probabilities for a batch of loans."""
        try:
            import xgboost as xgb
        except ImportError as exc:
            raise ImportError(
                "xgboost is required for prediction. " "Install it with: pip install xgboost"
            ) from exc

        rows = [[float(loan.get(col, 0.0)) for col in FEATURE_COLUMNS] for loan in loans]
        features = np.array(rows, dtype=np.float32)
        dmatrix = xgb.DMatrix(features, feature_names=FEATURE_COLUMNS)
        preds = self._booster.predict(dmatrix)
        return [max(0.0, min(1.0, float(p))) for p in preds]
