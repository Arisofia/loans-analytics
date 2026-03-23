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
    from backend.python.models.default_risk_model import DefaultRiskModel
    model = DefaultRiskModel()
    metrics = model.train(training_dataframe)
    model.save("models/risk")

    # Inference (API serving)
    from backend.python.models.default_risk_model import DefaultRiskModel
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


def _import_pandas() -> Any:
    """Lazy import pandas, required for DataFrame operations."""
    import pandas as pd
    return pd


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
    def prepare_features(
        df: Any,
        payment_df: Optional[Any] = None,
        customer_df: Optional[Any] = None,
    ) -> Any:
        """Prepare and engineer features from raw loan data.

        Parameters
        ----------
        df : pandas.DataFrame
            Raw loan data.
        payment_df : pandas.DataFrame, optional
            Payment history data.
        customer_df : pandas.DataFrame, optional
            Customer profile data.

        Returns
        -------
        pandas.DataFrame
            Engineered features ready for model input.
        """
        try:
            from backend.python.features.feature_store import FeatureStore
            fs = FeatureStore()
            # If df is already engineered (from FeatureStore), this will just ensure consistency
            # If not, it will compute everything from build_model_dataset logic
            return fs.compute_features(df, payment_df, customer_df)
        except ImportError:
            # Fallback to legacy logic if FeatureStore cannot be imported
            import pandas as pd
            features = pd.DataFrame()
            for col in NUMERIC_FEATURES:
                if col in df.columns:
                    features[col] = pd.to_numeric(df[col], errors="coerce")
                else:
                    features[col] = 0.0

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
            return features.fillna(0.0)

    @staticmethod
    def prepare_target(df: Any) -> Any:
        """Prepare binary target: 1 = Default, 0 = Not Default.
        
        Matches ScorecardModel.build_model_dataset logic for consistency.
        """
        if "is_default" in df.columns:
            return df["is_default"].astype(int)

        status_col = next(
            (c for c in df.columns if c in ["status", "current_status", "estado"]),
            None,
        )
        if status_col is None:
            raise ValueError("No status column found in data")

        return (
            df[status_col].str.strip().str.lower()
            .isin(["default", "defaulted", "mora", "en_mora", "castigado"])
            .astype(int)
        )

    def train(
        self,
        df: Any,
        payment_df: Optional[Any] = None,
        customer_df: Optional[Any] = None,
        test_size: float = 0.2,
        random_state: int = 42,
        exclude_features: Optional[List[str]] = None,
        selected_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Train the model on loan data and return evaluation metrics.

        Parameters
        ----------
        df : pandas.DataFrame
            Raw loan data.
        payment_df : pandas.DataFrame, optional
            Payment history data.
        customer_df : pandas.DataFrame, optional
            Customer profile data.
        test_size : float
            Proportion of dataset to include in the test split.
        random_state : int
            Random seed for reproducibility.
        exclude_features : list of str, optional
            Features to explicitly remove from training.
        selected_features : list of str, optional
            Explicit list of features to use (e.g. from IV table).
            If provided, this overrides ALL_FEATURES but still respects exclude_features.

        **Overfitting mitigation** (vs. original implementation):
        ...
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
        X = self.prepare_features(df, payment_df, customer_df)
        y = self.prepare_target(df)

        # Drop ID columns that might have been preserved by FeatureStore
        X = X.drop(columns=[c for c in ["loan_id", "customer_id"] if c in X.columns])

        # ── Feature selection ─────────────────────────────────────────────
        if selected_features:
            # Only keep columns that were selected AND exist in X
            self.feature_names = [c for c in selected_features if c in X.columns]
            X = X[self.feature_names]
            logger.info("Using %d IV-selected features", len(self.feature_names))
        else:
            self.feature_names = list(X.columns)

        # Drop excluded features (e.g. days_past_due for origination model)
        if exclude_features:
            X = X.drop(columns=[c for c in exclude_features if c in X.columns])
            self.feature_names = list(X.columns)
            logger.info("Dropped %d excluded features", len(exclude_features))

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
        gini = 2 * auc - 1

        # KS Statistic
        from scipy.stats import ks_2samp

        pos_proba = y_proba[y_test == 1]
        neg_proba = y_proba[y_test == 0]
        ks_stat, _ = ks_2samp(pos_proba, neg_proba)

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        # Feature importance
        used_features = list(X_train.columns)
        feat_importances = self.model.feature_importances_.tolist()
        importance = dict(zip(used_features, feat_importances))  # updated
        importance_sorted = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

        # Cross-validation AUC
        cv_aucs: List[float] = []
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
        for train_idx, val_idx in skf.split(X, y):
            x_cv_train, x_cv_val = X.iloc[train_idx], X.iloc[val_idx]
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
                x_cv_train,
                y_cv_train,
                eval_set=[(x_cv_val, y_cv_val)],
                verbose=False,
            )
            cv_proba = cv_model.predict_proba(x_cv_val)[:, 1]
            cv_aucs.append(roc_auc_score(y_cv_val, cv_proba))

        metrics: Dict[str, Any] = {
            "auc_roc": round(auc, 4),
            "gini_coefficient": round(gini, 4),
            "ks_statistic": round(ks_stat, 4),
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
    # Validation
    # ------------------------------------------------------------------
    def validate_features(self, loan_data: Dict[str, Any]) -> None:
        """Verify all required features are present in the input dictionary.

        Raises
        ------
        ValueError
            If one or more required features are missing.
        """
        if missing := [f for f in self.feature_names if f not in loan_data]:
            raise ValueError(f"Missing required features for inference: {', '.join(missing)}")

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def _engineer_features_dict(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simple feature engineering for a single dictionary (numpy fallback)."""
        # Create a copy with base features
        feat = {k: float(v) if v is not None else 0.0 for k, v in loan_data.items() if k in self.feature_names}
        
        # Engineer features (only if they are required by the model)
        if "ltv_ratio" in self.feature_names and "ltv_ratio" not in feat:
            collateral = float(loan_data.get("collateral_value", 0.0))
            balance = float(loan_data.get("outstanding_balance", 0.0))
            feat["ltv_ratio"] = (balance / collateral * 100) if collateral > 0 else 0.0

        if "payment_ratio" in self.feature_names and "payment_ratio" not in feat:
            scheduled = float(loan_data.get("total_scheduled", 0.0))
            last_payment = float(loan_data.get("last_payment_amount", 0.0))
            feat["payment_ratio"] = (last_payment / scheduled * 100) if scheduled > 0 else 0.0
            
        # Fill any remaining missing features from self.feature_names with 0.0
        for col in self.feature_names:
            if col not in feat:
                feat[col] = 0.0
                
        return feat

    def predict_proba(
        self,
        loan_data: Dict[str, Any],
        payment_df: Optional[Any] = None,
        customer_df: Optional[Any] = None,
    ) -> float:
        """Return the default probability for a single loan.

        Parameters
        ----------
        loan_data:
            Dictionary whose keys are a superset of ``FEATURE_COLUMNS``.
        payment_df: pandas.DataFrame, optional
            Payment history data for behavioral features.
        customer_df: pandas.DataFrame, optional
            Customer profile data.

        Returns
        -------
        float
            Probability in [0, 1].
        """
        if self.model is None:
            raise RuntimeError("Model not trained or loaded")

        try:
            pd = _import_pandas()

            df = pd.DataFrame([loan_data])
            X = self.prepare_features(df, payment_df, customer_df)
            
            # Drop IDs
            X = X.drop(columns=[c for c in ["loan_id", "customer_id"] if c in X.columns])

            X = self._ensure_features_present(X)
            X = X[self.feature_names]
            proba = self.model.predict_proba(X)[:, 1]
            return float(proba[0])
        except ImportError:
            # Fallback: numpy-only path (no pandas available)
            import xgboost as xgb

            # Apply simple feature engineering
            feat = self._engineer_features_dict(loan_data)

            features = np.array(
                [[float(feat[col]) for col in self.feature_names]],
                dtype=np.float32,
            )
            preds = self._predict_with_booster(features)
            return max(0.0, min(1.0, float(preds[0])))

    def _predict_with_booster(self, features: np.ndarray) -> np.ndarray:
        """Low-level prediction using the underlying XGBoost booster."""
        import xgboost as xgb
        dmatrix = xgb.DMatrix(features, feature_names=self.feature_names)
        return self.model.get_booster().predict(dmatrix)

    def _ensure_features_present(self, X: Any) -> Any:
        """Ensure all required features are present in the feature matrix."""
        for f in self.feature_names:
            if f not in X.columns:
                X[f] = 0.0
        return X

    def _prepare_batch_features(
        self,
        loans: Union[List[Dict[str, Any]], Any],
        payment_df: Optional[Any] = None,
        customer_df: Optional[Any] = None,
    ) -> Any:
        """Prepare and validate features for batch prediction."""
        pd = _import_pandas()

        df = pd.DataFrame(loans) if isinstance(loans, list) else loans
        X = self.prepare_features(df, payment_df, customer_df)
        X = self._ensure_features_present(X)
        return X[self.feature_names], df

    def _predict_batch_with_pandas(self, X: Any, df: Any) -> Any:
        """Helper to return predictions as pandas Series."""
        pd = _import_pandas()
        return pd.Series(self.model.predict_proba(X)[:, 1], index=df.index)

    def _predict_batch_fallback(self, loans: Union[List[Dict[str, Any]], Any]) -> Any:
        """Fallback batch prediction without pandas (numpy + xgboost only)."""
        rows = []
        for loan in loans:
            feat = self._engineer_features_dict(loan)
            rows.append([float(feat[col]) for col in self.feature_names])

        features = np.array(rows, dtype=np.float32)
        preds = self._predict_with_booster(features)
        return [max(0.0, min(1.0, float(p))) for p in preds]

    def predict_batch(
        self,
        loans: Union[List[Dict[str, Any]], Any],
        payment_df: Optional[Any] = None,
        customer_df: Optional[Any] = None,
    ) -> Any:
        """Return default probabilities for a batch of loans.

        Parameters
        ----------
        loans:
            Either a list of dicts or a pandas DataFrame.
        payment_df: pandas.DataFrame, optional
            Payment history data.
        customer_df: pandas.DataFrame, optional
            Customer profile data.
        """
        if self.model is None:
            raise RuntimeError("Model not trained or loaded")

        try:
            X, df = self._prepare_batch_features(loans, payment_df, customer_df)
            return self._predict_batch_with_pandas(X, df)
        except ImportError:
            return self._predict_batch_fallback(loans)
