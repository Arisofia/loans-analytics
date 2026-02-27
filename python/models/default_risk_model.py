"""Default Risk Prediction Model using XGBoost.

Predicts the probability of loan default based on loan and borrower features.
Target: current_status == 'Default' (binary classification).

Features used (post-engineering):
  - principal_amount, interest_rate, term_months, collateral_value
  - outstanding_balance, tpv, equifax_score
  - last_payment_amount, total_scheduled, origination_fee
  - ltv_ratio (outstanding_balance / collateral_value)
  - payment_ratio (last_payment_amount / total_scheduled)
  - days_past_due (real-time risk signal)

Usage:
    # Training
    from python.models.default_risk_model import DefaultRiskModel
    model = DefaultRiskModel()
    metrics = model.train(training_dataframe)
    model.save("models/risk")

    # Inference (API serving)
    from python.models.default_risk_model import DefaultRiskModel
    model = DefaultRiskModel.load("models/risk/default_risk_xgb.ubj")
    prob = model.predict_proba(loan_features_dict)

Note: xgboost, pandas, and sklearn are imported lazily so the module can
be imported in CI environments where only inference (or mocking) is needed.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

logger = logging.getLogger(__name__)

# Features used for model training and inference
NUMERIC_FEATURES: List[str] = [
    "principal_amount",
    "interest_rate",
    "term_months",
    "collateral_value",
    "outstanding_balance",
    "tpv",
    "equifax_score",
    "last_payment_amount",
    "total_scheduled",
    "origination_fee",
    "days_past_due",
]

ENGINEERED_FEATURES: List[str] = [
    "ltv_ratio",
    "payment_ratio",
]

ALL_FEATURES: List[str] = NUMERIC_FEATURES + ENGINEERED_FEATURES

TARGET_COL = "is_default"

# Legacy alias kept for backward-compat with the inference-only API endpoint
FEATURE_COLUMNS = ALL_FEATURES


class DefaultRiskModel:
    """XGBoost-based default risk prediction model.

    Supports two operating modes:

    * **Training** – call :meth:`train` with a pandas ``DataFrame``.
      Requires ``xgboost``, ``pandas``, and ``scikit-learn``.
    * **Inference** – call :meth:`predict_proba` / :meth:`predict_batch`.
      Requires ``xgboost`` and ``numpy`` only.
    """

    def __init__(self, model: Any = None) -> None:
        self.model = model
        self.feature_names: List[str] = list(ALL_FEATURES)
        self.metadata: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Feature engineering (requires pandas)
    # ------------------------------------------------------------------
    @staticmethod
    def prepare_features(df: Any) -> Any:
        """Prepare and engineer features from raw loan data.

        Parameters
        ----------
        df : pandas.DataFrame
            Raw loan data with columns matching ``NUMERIC_FEATURES``.

        Returns
        -------
        pandas.DataFrame
            Engineered features ready for model input.
        """

        import pandas as pd  # noqa: F811 – lazy import

        features = pd.DataFrame()

        col_map = {
            "Equifax Score": "equifax_score",
            "equifax_score": "equifax_score",
        }

        for col in NUMERIC_FEATURES:
            source_col = col_map.get(col, col)
            if source_col in df.columns:
                features[col] = pd.to_numeric(df[source_col], errors="coerce")
            elif col in df.columns:
                features[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                features[col] = 0.0

        # Engineered features
        features["ltv_ratio"] = np.where(
            features["collateral_value"] > 0,
            features["outstanding_balance"] / features["collateral_value"] * 100,
            0.0,
        )
        features["payment_ratio"] = np.where(
            features["total_scheduled"] > 0,
            features["last_payment_amount"] / features["total_scheduled"] * 100,
            0.0,
        )

        # Fill NaN with median (robust to outliers)
        for col in ALL_FEATURES:
            if features[col].isna().any():
                median_val = features[col].median()
                features[col] = features[col].fillna(
                    median_val if not np.isnan(median_val) else 0.0
                )

        return features[ALL_FEATURES]

    @staticmethod
    def prepare_target(df: Any) -> Any:
        """Prepare binary target: 1 = Default, 0 = Not Default."""
        status_col = None
        for col in ["current_status", "status"]:
            if col in df.columns:
                status_col = col
                break

        if status_col is None:
            raise ValueError("No status column found in data")

        return (df[status_col].str.strip().str.lower() == "default").astype(int)

    def train(
        self,
        df: Any,
        test_size: float = 0.2,
        random_state: int = 42,
        exclude_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Train the model on loan data and return evaluation metrics.

        **Overfitting mitigation** (vs. original implementation):

        * ``early_stopping_rounds=30`` halts training when validation AUC
          stops improving, preventing the model from memorising noise.
        * ``reg_alpha=1.0`` (L1) and ``reg_lambda=5.0`` (L2) shrink leaf
          weights and encourage sparsity.
        * ``min_child_weight=10`` requires each leaf to represent at least
          10 samples, reducing sensitivity to individual records.
        * ``max_depth=4`` (reduced from 5) limits tree complexity.
        * ``gamma=1.0`` adds a minimum loss reduction for further splits.
        """
        import xgboost as xgb  # lazy
        from sklearn.metrics import (
            accuracy_score,
            classification_report,
            f1_score,
            precision_score,
            recall_score,
            roc_auc_score,
        )
        from sklearn.model_selection import StratifiedKFold, train_test_split

        logger.info("Preparing features and target...")
        X = self.prepare_features(df)
        y = self.prepare_target(df)

        # Drop excluded features (e.g. days_past_due for origination model)
        if exclude_features:
            X = X.drop(columns=[c for c in exclude_features if c in X.columns])
            self.feature_names = list(X.columns)

        # Class imbalance ratio for scale_pos_weight
        n_neg = int((y == 0).sum())
        n_pos = int((y == 1).sum())
        scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0

        logger.info(
            "Dataset: %d samples, %d defaults (%.2f%%), scale_pos_weight=%.1f",
            len(y),
            n_pos,
            n_pos / len(y) * 100,
            scale_pos_weight,
        )

        # Stratified train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=y,
        )

        # -----------------------------------------------------------
        # XGBoost classifier — regularised to prevent overfitting
        # -----------------------------------------------------------
        self.model = xgb.XGBClassifier(
            n_estimators=500,  # higher ceiling; early stopping trims
            max_depth=4,  # reduced from 5
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=10,  # NEW — prevents tiny leaves
            gamma=1.0,  # NEW — min split loss
            reg_alpha=1.0,  # NEW — L1 regularisation
            reg_lambda=5.0,  # NEW — L2 regularisation
            scale_pos_weight=scale_pos_weight,
            eval_metric="auc",
            early_stopping_rounds=30,  # NEW — halts when val AUC stalls
            random_state=random_state,
            tree_method="hist",
        )

        logger.info("Training XGBoost model (with early stopping)...")
        self.model.fit(
            X_train,
            y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )
        logger.info(
            "Stopped at %d / %d boosting rounds",
            self.model.best_iteration + 1 if hasattr(self.model, "best_iteration") else "?",
            500,
        )

        # Evaluate
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]

        auc = roc_auc_score(y_test, y_proba)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        # Feature importance
        used_features = list(X_train.columns)
        feat_importances = self.model.feature_importances_.tolist()
        importance = dict(zip(used_features, feat_importances, strict=False))
        importance_sorted = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

        # Cross-validation AUC
        cv_aucs: List[float] = []
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
        for train_idx, val_idx in skf.split(X, y):
            X_cv_train, X_cv_val = X.iloc[train_idx], X.iloc[val_idx]
            y_cv_train, y_cv_val = y.iloc[train_idx], y.iloc[val_idx]

            cv_model = xgb.XGBClassifier(
                n_estimators=500,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=10,
                gamma=1.0,
                reg_alpha=1.0,
                reg_lambda=5.0,
                scale_pos_weight=scale_pos_weight,
                eval_metric="auc",
                early_stopping_rounds=30,
                random_state=random_state,
                tree_method="hist",
            )
            cv_model.fit(
                X_cv_train,
                y_cv_train,
                eval_set=[(X_cv_val, y_cv_val)],
                verbose=False,
            )
            cv_proba = cv_model.predict_proba(X_cv_val)[:, 1]
            cv_aucs.append(roc_auc_score(y_cv_val, cv_proba))

        metrics: Dict[str, Any] = {
            "auc_roc": round(auc, 4),
            "cv_auc_mean": round(float(np.mean(cv_aucs)), 4),
            "cv_auc_std": round(float(np.std(cv_aucs)), 4),
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "n_defaults_train": int(y_train.sum()),
            "n_defaults_test": int(y_test.sum()),
            "feature_importance": importance_sorted,
            "classification_report": classification_report(y_test, y_pred, output_dict=True),
        }

        self.metadata = {
            "model_type": "XGBClassifier",
            "n_estimators": (
                self.model.best_iteration + 1 if hasattr(self.model, "best_iteration") else 500
            ),
            "max_depth": 4,
            "regularisation": {
                "reg_alpha": 1.0,
                "reg_lambda": 5.0,
                "gamma": 1.0,
                "min_child_weight": 10,
            },
            "features": list(self.feature_names),
            "metrics": metrics,
        }

        logger.info(
            "Model trained: AUC=%.4f, CV AUC=%.4f +/- %.4f",
            auc,
            float(np.mean(cv_aucs)),
            float(np.std(cv_aucs)),
        )
        return metrics

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    @classmethod
    def load(cls, path: Union[str, Path]) -> "DefaultRiskModel":
        """Load a saved XGBoost model from *path* (UBJ or JSON format).

        Raises ``FileNotFoundError`` if the file does not exist and
        ``ImportError`` if xgboost is not installed.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        try:
            import xgboost as xgb
        except ImportError as exc:
            raise ImportError(
                "xgboost is required for the default risk model. "
                "Install it with: pip install xgboost"
            ) from exc

        model = xgb.XGBClassifier()
        model.load_model(str(path))

        instance = cls(model=model)

        meta_path = path.parent / "default_risk_metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                instance.metadata = json.load(f)
            # Restore feature_names from metadata if available
            if "features" in instance.metadata:
                instance.feature_names = instance.metadata["features"]

        logger.info("Loaded XGBoost model from %s", path)
        return instance

    def save(self, model_dir: str = "models/risk") -> str:
        """Save model and metadata to disk (UBJ format)."""
        if self.model is None:
            raise RuntimeError("No model to save")

        path = Path(model_dir)
        path.mkdir(parents=True, exist_ok=True)

        model_path = path / "default_risk_xgb.ubj"
        self.model.save_model(str(model_path))

        meta_path = path / "default_risk_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(self.metadata, f, indent=2, default=str)

        logger.info("Model saved to %s", model_path)
        return str(model_path)

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
        if self.model is None:
            raise RuntimeError("Model not trained or loaded")

        try:
            import pandas as pd  # noqa: F811

            df = pd.DataFrame([loan_data])
            X = self.prepare_features(df)
            X = X[[c for c in self.feature_names if c in X.columns]]
            proba = self.model.predict_proba(X)[:, 1]
            return float(proba[0])
        except ImportError:
            # Fallback: numpy-only path (no pandas available)
            import xgboost as xgb

            features = np.array(
                [[float(loan_data.get(col, 0.0)) for col in self.feature_names]],
                dtype=np.float32,
            )
            dmatrix = xgb.DMatrix(features, feature_names=self.feature_names)
            preds = self.model.get_booster().predict(dmatrix)
            return max(0.0, min(1.0, float(preds[0])))

    def predict_batch(self, loans: Union[List[Dict[str, Any]], Any]) -> Any:
        """Return default probabilities for a batch of loans.

        Parameters
        ----------
        loans:
            Either a list of dicts or a pandas DataFrame.
        """
        if self.model is None:
            raise RuntimeError("Model not trained or loaded")

        try:
            import pandas as pd  # noqa: F811

            df = pd.DataFrame(loans) if isinstance(loans, list) else loans
            X = self.prepare_features(df)
            X = X[[c for c in self.feature_names if c in X.columns]]
            return pd.Series(self.model.predict_proba(X)[:, 1], index=df.index)
        except ImportError:
            # Fallback: list-of-dicts only
            import xgboost as xgb

            rows = [[float(loan.get(col, 0.0)) for col in self.feature_names] for loan in loans]
            features = np.array(rows, dtype=np.float32)
            dmatrix = xgb.DMatrix(features, feature_names=self.feature_names)
            preds = self.model.get_booster().predict(dmatrix)
            return [max(0.0, min(1.0, float(p))) for p in preds]
