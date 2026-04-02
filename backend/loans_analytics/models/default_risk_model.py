from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
logger = logging.getLogger(__name__)

def _import_pandas() -> Any:
    import pandas as pd
    return pd
NUMERIC_FEATURES: List[str] = ['principal_amount', 'interest_rate', 'term_months', 'collateral_value', 'outstanding_balance', 'tpv', 'equifax_score', 'last_payment_amount', 'total_scheduled', 'origination_fee', 'days_past_due']
ENGINEERED_FEATURES: List[str] = ['ltv_ratio', 'payment_ratio']
ALL_FEATURES: List[str] = NUMERIC_FEATURES + ENGINEERED_FEATURES
TARGET_COL = 'is_default'
FEATURE_COLUMNS = ALL_FEATURES

class DefaultRiskModel:

    def __init__(self, model: Any=None) -> None:
        self.model = model
        self.feature_names: List[str] = list(ALL_FEATURES)
        self.metadata: Dict[str, Any] = {}

    @staticmethod
    def prepare_features(df: Any, payment_df: Optional[Any]=None, customer_df: Optional[Any]=None) -> Any:
        try:
            from backend.loans_analytics.features.feature_store import FeatureStore
            fs = FeatureStore()
            return fs.compute_features(df, payment_df, customer_df)
        except ImportError:
            import pandas as pd
            features = pd.DataFrame()
            for col in NUMERIC_FEATURES:
                if col in df.columns:
                    features[col] = pd.to_numeric(df[col], errors='coerce')
                else:
                    features[col] = 0.0
            features['ltv_ratio'] = np.where(features['collateral_value'] > 0, features['outstanding_balance'] / features['collateral_value'] * 100, 0.0)
            features['payment_ratio'] = np.where(features['total_scheduled'] > 0, features['last_payment_amount'] / features['total_scheduled'] * 100, 0.0)
            return features.fillna(0.0)

    @staticmethod
    def prepare_target(df: Any) -> Any:
        if 'is_default' in df.columns:
            return df['is_default'].astype(int)
        status_col = next((c for c in df.columns if c in ['status', 'current_status', 'estado']), None)
        if status_col is None:
            raise ValueError('No status column found in data')
        return df[status_col].str.strip().str.lower().isin(['default', 'defaulted', 'mora', 'en_mora', 'castigado']).astype(int)

    def train(self, df: Any, payment_df: Optional[Any]=None, customer_df: Optional[Any]=None, test_size: float=0.2, random_state: int=42, exclude_features: Optional[List[str]]=None, selected_features: Optional[List[str]]=None) -> Dict[str, Any]:
        import xgboost as xgb
        from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score, roc_auc_score
        from sklearn.model_selection import StratifiedKFold, train_test_split
        logger.info('Preparing features and target...')
        X = self.prepare_features(df, payment_df, customer_df)
        y = self.prepare_target(df)
        X = X.drop(columns=[c for c in ['loan_id', 'customer_id'] if c in X.columns])
        if selected_features:
            self.feature_names = [c for c in selected_features if c in X.columns]
            X = X[self.feature_names]
            logger.info('Using %d IV-selected features', len(self.feature_names))
        else:
            self.feature_names = list(X.columns)
        if exclude_features:
            X = X.drop(columns=[c for c in exclude_features if c in X.columns])
            self.feature_names = list(X.columns)
            logger.info('Dropped %d excluded features', len(exclude_features))
        n_neg = int((y == 0).sum())
        n_pos = int((y == 1).sum())
        scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0
        logger.info('Dataset: %d samples, %d defaults (%.2f%%), scale_pos_weight=%.1f', len(y), n_pos, n_pos / len(y) * 100, scale_pos_weight)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
        self.model = xgb.XGBClassifier(n_estimators=500, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, min_child_weight=10, gamma=1.0, reg_alpha=1.0, reg_lambda=5.0, scale_pos_weight=scale_pos_weight, eval_metric='auc', early_stopping_rounds=30, random_state=random_state, tree_method='hist')
        logger.info('Training XGBoost model (with early stopping)...')
        self.model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        logger.info('Stopped at %d / %d boosting rounds', self.model.best_iteration + 1 if hasattr(self.model, 'best_iteration') else '?', 500)
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_proba)
        gini = 2 * auc - 1
        from scipy.stats import ks_2samp
        pos_proba = y_proba[y_test == 1]
        neg_proba = y_proba[y_test == 0]
        ks_stat, _ = ks_2samp(pos_proba, neg_proba)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        used_features = list(X_train.columns)
        feat_importances = self.model.feature_importances_.tolist()
        importance = dict(zip(used_features, feat_importances))
        importance_sorted = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        cv_aucs: List[float] = []
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
        for train_idx, val_idx in skf.split(X, y):
            x_cv_train, x_cv_val = (X.iloc[train_idx], X.iloc[val_idx])
            y_cv_train, y_cv_val = (y.iloc[train_idx], y.iloc[val_idx])
            cv_model = xgb.XGBClassifier(n_estimators=500, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, min_child_weight=10, gamma=1.0, reg_alpha=1.0, reg_lambda=5.0, scale_pos_weight=scale_pos_weight, eval_metric='auc', early_stopping_rounds=30, random_state=random_state, tree_method='hist')
            cv_model.fit(x_cv_train, y_cv_train, eval_set=[(x_cv_val, y_cv_val)], verbose=False)
            cv_proba = cv_model.predict_proba(x_cv_val)[:, 1]
            cv_aucs.append(roc_auc_score(y_cv_val, cv_proba))
        metrics: Dict[str, Any] = {'auc_roc': round(auc, 4), 'gini_coefficient': round(gini, 4), 'ks_statistic': round(ks_stat, 4), 'cv_auc_mean': round(float(np.mean(cv_aucs)), 4), 'cv_auc_std': round(float(np.std(cv_aucs)), 4), 'accuracy': round(accuracy, 4), 'precision': round(precision, 4), 'recall': round(recall, 4), 'f1_score': round(f1, 4), 'train_size': len(X_train), 'test_size': len(X_test), 'n_defaults_train': int(y_train.sum()), 'n_defaults_test': int(y_test.sum()), 'feature_importance': importance_sorted, 'classification_report': classification_report(y_test, y_pred, output_dict=True)}
        self.metadata = {'model_type': 'XGBClassifier', 'n_estimators': self.model.best_iteration + 1 if hasattr(self.model, 'best_iteration') else 500, 'max_depth': 4, 'regularisation': {'reg_alpha': 1.0, 'reg_lambda': 5.0, 'gamma': 1.0, 'min_child_weight': 10}, 'features': list(self.feature_names), 'metrics': metrics}
        logger.info('Model trained: AUC=%.4f, CV AUC=%.4f +/- %.4f', auc, float(np.mean(cv_aucs)), float(np.std(cv_aucs)))
        return metrics

    @classmethod
    def load(cls, path: Union[str, Path]) -> 'DefaultRiskModel':
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f'Model file not found: {path}')
        try:
            import xgboost as xgb
        except ImportError as exc:
            raise ImportError('xgboost is required for the default risk model. Install it with: pip install xgboost') from exc
        model = xgb.XGBClassifier()
        model.load_model(str(path))
        instance = cls(model=model)
        meta_path = path.parent / 'default_risk_metadata.json'
        if meta_path.exists():
            with open(meta_path) as f:
                instance.metadata = json.load(f)
            if 'features' in instance.metadata:
                instance.feature_names = instance.metadata['features']
        logger.info('Loaded XGBoost model from %s', path)
        return instance

    def save(self, model_dir: str='models/risk') -> str:
        if self.model is None:
            raise RuntimeError('No model to save')
        path = Path(model_dir)
        path.mkdir(parents=True, exist_ok=True)
        model_path = path / 'default_risk_xgb.ubj'
        self.model.save_model(str(model_path))
        meta_path = path / 'default_risk_metadata.json'
        import math

        def _sanitize(obj: object) -> object:
            if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
                return None
            if isinstance(obj, dict):
                return {k: _sanitize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_sanitize(v) for v in obj]
            return obj

        with open(meta_path, 'w') as f:
            json.dump(_sanitize(self.metadata), f, indent=2, default=str)
        logger.info('Model saved to %s', model_path)
        return str(model_path)

    @staticmethod
    def _can_derive_feature(feature_name: str, loan_data: Dict[str, Any]) -> bool:
        if feature_name == 'ltv_ratio':
            return feature_name in loan_data or ('collateral_value' in loan_data and 'outstanding_balance' in loan_data)
        if feature_name == 'payment_ratio':
            return feature_name in loan_data or ('total_scheduled' in loan_data and 'last_payment_amount' in loan_data)
        return feature_name in loan_data

    def validate_features(self, loan_data: Dict[str, Any]) -> None:
        if (missing := [feature_name for feature_name in self.feature_names if not self._can_derive_feature(feature_name, loan_data)]):
            raise ValueError(f"Missing required features for inference: {', '.join(missing)}")

    def _engineer_features_dict(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        feat = {key: float(value) if value is not None else 0.0 for key, value in loan_data.items() if key in self.feature_names}
        if 'ltv_ratio' in self.feature_names and 'ltv_ratio' not in feat:
            collateral = float(loan_data.get('collateral_value', 0.0))
            balance = float(loan_data.get('outstanding_balance', 0.0))
            feat['ltv_ratio'] = balance / collateral * 100 if collateral > 0 else 0.0
        if 'payment_ratio' in self.feature_names and 'payment_ratio' not in feat:
            scheduled = float(loan_data.get('total_scheduled', 0.0))
            last_payment = float(loan_data.get('last_payment_amount', 0.0))
            feat['payment_ratio'] = last_payment / scheduled * 100 if scheduled > 0 else 0.0
        for col in self.feature_names:
            if col not in feat:
                feat[col] = 0.0
        return feat

    def _build_inference_array(self, loan_data: Dict[str, Any]) -> np.ndarray:
        self.validate_features(loan_data)
        feat = self._engineer_features_dict(loan_data)
        return np.array([[float(feat[col]) for col in self.feature_names]], dtype=np.float32)

    def predict_proba(self, loan_data: Dict[str, Any], payment_df: Optional[Any]=None, customer_df: Optional[Any]=None) -> float:
        if self.model is None:
            raise RuntimeError('Model not trained or loaded')
        _ = (payment_df, customer_df)
        features = self._build_inference_array(loan_data)
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(features)[:, 1]
            return float(proba[0])
        preds = self._predict_with_booster(features)
        return max(0.0, min(1.0, float(preds[0])))

    def _predict_with_booster(self, features: np.ndarray) -> np.ndarray:
        import xgboost as xgb
        dmatrix = xgb.DMatrix(features, feature_names=self.feature_names)
        return self.model.get_booster().predict(dmatrix)

    def _ensure_features_present(self, X: Any) -> Any:
        for f in self.feature_names:
            if f not in X.columns:
                X[f] = 0.0
        return X

    def _prepare_batch_features(self, loans: Union[List[Dict[str, Any]], Any], payment_df: Optional[Any]=None, customer_df: Optional[Any]=None) -> Any:
        pd = _import_pandas()
        if isinstance(loans, list):
            rows = []
            for loan_data in loans:
                self.validate_features(loan_data)
                feat = self._engineer_features_dict(loan_data)
                rows.append([float(feat[col]) for col in self.feature_names])
            X = pd.DataFrame(rows, columns=self.feature_names)
            df = pd.DataFrame(loans)
            return (X, df)
        df = pd.DataFrame(loans) if isinstance(loans, list) else loans
        X = self.prepare_features(df, payment_df, customer_df)
        X = self._ensure_features_present(X)
        return (X[self.feature_names], df)

    def _predict_batch_with_pandas(self, X: Any, df: Any) -> Any:
        pd = _import_pandas()
        return pd.Series(self.model.predict_proba(X)[:, 1], index=df.index)

    def _predict_batch_fallback(self, loans: Union[List[Dict[str, Any]], Any]) -> Any:
        rows = []
        for loan in loans:
            feat = self._engineer_features_dict(loan)
            rows.append([float(feat[col]) for col in self.feature_names])
        features = np.array(rows, dtype=np.float32)
        preds = self._predict_with_booster(features)
        return [max(0.0, min(1.0, float(p))) for p in preds]

    def predict_batch(self, loans: Union[List[Dict[str, Any]], Any], payment_df: Optional[Any]=None, customer_df: Optional[Any]=None) -> Any:
        if self.model is None:
            raise RuntimeError('Model not trained or loaded')
        try:
            X, df = self._prepare_batch_features(loans, payment_df, customer_df)
            return self._predict_batch_with_pandas(X, df)
        except ImportError:
            return self._predict_batch_fallback(loans)
