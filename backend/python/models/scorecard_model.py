from __future__ import annotations
from contextlib import suppress
import importlib.util
import json
import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
warnings.filterwarnings('ignore', category=UserWarning)
logger = logging.getLogger(__name__)
BASE_SCORE = 600
PDO = 20
BASE_ODDS = 50.0
IV_USELESS = 0.02
IV_WEAK = 0.1
IV_MEDIUM = 0.3

class ScorecardModel:

    def __init__(self) -> None:
        self.binning_map: Dict[str, Any] = {}
        self.iv_table: pd.DataFrame = pd.DataFrame()
        self.selected_features: List[str] = []
        self.lr_model: Optional[LogisticRegression] = None
        self.scorecard_table: pd.DataFrame = pd.DataFrame()
        self.metadata: Dict[str, Any] = {}
        self.feature_names_woe: List[str] = []

    @staticmethod
    def _normalize_columns(df: pd.DataFrame) -> None:
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]

    @staticmethod
    def _find_col(df: pd.DataFrame, *patterns: str) -> Optional[str]:
        for col in df.columns:
            for pat in patterns:
                if pat in col:
                    return col
        return None

    @staticmethod
    def _coerce_alias_column(loan_df: pd.DataFrame, source_col: Optional[str], target_col: str) -> None:
        if source_col and source_col != target_col:
            loan_df[target_col] = pd.to_numeric(loan_df[source_col], errors='coerce')

    @staticmethod
    def _add_core_loan_features(loan_df: pd.DataFrame) -> Optional[str]:
        status_col = ScorecardModel._find_col(loan_df, 'status', 'estado', 'estatus')
        if status_col is None:
            raise ValueError("No status column found in loan_df. Expected a column containing 'status' or 'estado'.")
        loan_df['is_default'] = loan_df[status_col].str.strip().str.lower().isin(['default', 'defaulted', 'mora', 'en_mora', 'castigado']).astype(int)
        dpd_col = ScorecardModel._find_col(loan_df, 'days_past_due', 'days_in_default', 'dpd', 'dias_mora', 'dias_en_mora')
        if dpd_col:
            loan_df['days_past_due'] = pd.to_numeric(loan_df[dpd_col], errors='coerce').fillna(0)
        else:
            loan_df['days_past_due'] = 0.0
        ScorecardModel._coerce_alias_column(loan_df, ScorecardModel._find_col(loan_df, 'outstanding'), 'outstanding_balance')
        ScorecardModel._coerce_alias_column(loan_df, ScorecardModel._find_col(loan_df, 'collateral', 'garantia', 'garantía'), 'collateral_value')
        ScorecardModel._coerce_alias_column(loan_df, ScorecardModel._find_col(loan_df, 'interest_rate', 'interest', 'tasa_interes', 'tasa', 'apr'), 'interest_rate')
        ScorecardModel._coerce_alias_column(loan_df, ScorecardModel._find_col(loan_df, 'principal_amount', 'principal', 'loan_amount', 'monto_prestamo', 'monto_desembolsado'), 'principal_amount')
        return ScorecardModel._find_col(loan_df, 'disburs', 'originat', 'fecha_desembolso')

    @staticmethod
    def _add_date_and_ratio_features(loan_df: pd.DataFrame, date_col: Optional[str]) -> None:
        if date_col:
            loan_df[date_col] = pd.to_datetime(loan_df[date_col], errors='coerce')
            loan_df['loan_age_days'] = (pd.Timestamp.today() - loan_df[date_col]).dt.days.clip(lower=0)
            loan_df['vintage_quarter'] = loan_df[date_col].dt.to_period('Q').astype(str)
        if 'outstanding_balance' in loan_df.columns and 'collateral_value' in loan_df.columns:
            loan_df['ltv_ratio'] = np.where(pd.to_numeric(loan_df['collateral_value'], errors='coerce').fillna(0) > 0, pd.to_numeric(loan_df['outstanding_balance'], errors='coerce').fillna(0) / pd.to_numeric(loan_df['collateral_value'], errors='coerce').fillna(1) * 100, np.nan)
        if 'last_payment_amount' in loan_df.columns and 'total_scheduled' in loan_df.columns:
            loan_df['payment_ratio'] = np.where(pd.to_numeric(loan_df['total_scheduled'], errors='coerce').fillna(0) > 0, pd.to_numeric(loan_df['last_payment_amount'], errors='coerce').fillna(0) / pd.to_numeric(loan_df['total_scheduled'], errors='coerce').fillna(1) * 100, np.nan)

    @staticmethod
    def _max_consecutive_lates(series: pd.Series) -> int:
        max_c = cur_c = 0
        for v in series:
            if v == 1:
                cur_c += 1
                max_c = max(max_c, cur_c)
            else:
                cur_c = 0
        return max_c

    @staticmethod
    def _merge_payment_behavior_features(loan_df: pd.DataFrame, payment_df: pd.DataFrame, date_col: Optional[str]) -> pd.DataFrame:
        loan_id_col_pay = ScorecardModel._find_col(payment_df, 'loan_id', 'prestamo_id', 'id_prestamo')
        loan_id_col_loan = ScorecardModel._find_col(loan_df, 'loan_id', 'id_prestamo', 'prestamo_id')
        if not (loan_id_col_pay and loan_id_col_loan):
            return loan_df
        status_pay_col = ScorecardModel._find_col(payment_df, 'status', 'estado', 'estatus')
        if not status_pay_col:
            return loan_df
        amount_pay_col = ScorecardModel._find_col(payment_df, 'total_payment', 'true_total', 'amount', 'monto', 'valor')
        date_pay_col = next((c for c in payment_df.columns if 'date' in c or 'fecha' in c), None)
        payment_df['_is_late'] = payment_df[status_pay_col].str.strip().str.lower().isin(['late', 'tardio', 'tardío', 'mora', 'atrasado']).astype(int)
        beh = payment_df.groupby(loan_id_col_pay).agg(n_payments=('_is_late', 'count'), n_late_payments=('_is_late', 'sum')).reset_index()
        beh.columns = [loan_id_col_loan, 'n_payments', 'n_late_payments']
        beh['late_payment_rate'] = np.where(beh['n_payments'] > 0, beh['n_late_payments'] / beh['n_payments'], 0.0)
        consec = payment_df.sort_values([loan_id_col_pay, date_pay_col] if date_pay_col else [loan_id_col_pay]).groupby(loan_id_col_pay)['_is_late'].apply(ScorecardModel._max_consecutive_lates).reset_index()
        consec.columns = [loan_id_col_loan, 'max_consecutive_late']
        beh = beh.merge(consec, on=loan_id_col_loan, how='left')
        if amount_pay_col:
            payment_df[amount_pay_col] = pd.to_numeric(payment_df[amount_pay_col], errors='coerce')
            vol = payment_df.groupby(loan_id_col_pay)[amount_pay_col].std().reset_index()
            vol.columns = [loan_id_col_loan, 'payment_amount_std']
            beh = beh.merge(vol, on=loan_id_col_loan, how='left')
        if date_pay_col and date_col:
            payment_df[date_pay_col] = pd.to_datetime(payment_df[date_pay_col], errors='coerce')
            first_late = payment_df[payment_df['_is_late'] == 1].sort_values(date_pay_col).groupby(loan_id_col_pay)[date_pay_col].first().reset_index()
            first_late.columns = [loan_id_col_loan, '_first_late_date']
            loan_df = loan_df.merge(first_late, on=loan_id_col_loan, how='left')
            loan_df['days_to_first_late'] = (loan_df['_first_late_date'] - loan_df[date_col]).dt.days
            loan_df.drop(columns=['_first_late_date'], inplace=True)
        loan_df = loan_df.merge(beh, on=loan_id_col_loan, how='left')
        logger.info('Behavioral features added: n_late_payments, late_payment_rate, max_consecutive_late, payment_amount_std')
        return loan_df

    @staticmethod
    def _merge_customer_features(loan_df: pd.DataFrame, customer_df: pd.DataFrame) -> pd.DataFrame:
        cust_id_col_cust = next((c for c in customer_df.columns if 'customer_id' in c or 'cliente_id' in c or 'borrower_id' in c), None)
        cust_id_col_loan = next((c for c in loan_df.columns if 'customer_id' in c or 'cliente_id' in c or 'borrower_id' in c), None)
        if not (cust_id_col_cust and cust_id_col_loan):
            return loan_df
        industry_col = next((c for c in customer_df.columns if 'industry' in c or 'sector' in c or 'giro' in c), None)
        score_col = next((c for c in customer_df.columns if 'equifax' in c or 'score' in c or 'buro' in c), None)
        keep_cols = [cust_id_col_cust]
        if industry_col:
            keep_cols.append(industry_col)
            customer_df[industry_col] = customer_df[industry_col].str.strip()
        if score_col:
            keep_cols.append(score_col)
            customer_df[score_col] = pd.to_numeric(customer_df[score_col], errors='coerce')
        loan_df = loan_df.merge(customer_df[keep_cols].rename(columns={cust_id_col_cust: cust_id_col_loan}), on=cust_id_col_loan, how='left')
        logger.info('Customer features merged: %s', keep_cols)
        return loan_df

    @staticmethod
    def build_model_dataset(loan_df: pd.DataFrame, payment_df: pd.DataFrame, customer_df: pd.DataFrame) -> pd.DataFrame:
        ScorecardModel._normalize_columns(loan_df)
        ScorecardModel._normalize_columns(payment_df)
        ScorecardModel._normalize_columns(customer_df)
        date_col = ScorecardModel._add_core_loan_features(loan_df)
        ScorecardModel._add_date_and_ratio_features(loan_df, date_col)
        loan_df = ScorecardModel._merge_payment_behavior_features(loan_df, payment_df, date_col)
        loan_df = ScorecardModel._merge_customer_features(loan_df, customer_df)
        logger.info('Model dataset: %d rows, %d defaults (%.2f%%), %d features', len(loan_df), loan_df['is_default'].sum(), loan_df['is_default'].mean() * 100, len(loan_df.columns))
        return loan_df

    @staticmethod
    def _predictive_power_label(iv_val: float) -> str:
        if iv_val < IV_USELESS:
            return 'Useless'
        if iv_val < IV_WEAK:
            return 'Weak'
        return 'Medium' if iv_val < IV_MEDIUM else 'Strong'

    def _build_iv_record(self, feat: str, iv_val: float, n_bins: int, woe_range: float, dtype: str) -> Dict[str, Any]:
        return {
            'feature': feat,
            'iv': round(iv_val, 4),
            'predictive_power': self._predictive_power_label(iv_val),
            'n_bins': n_bins,
            'woe_range': woe_range,
            'dtype': dtype,
        }

    @staticmethod
    def _has_sufficient_variation(values: np.ndarray) -> bool:
        return len(np.unique(values)) >= 2

    @staticmethod
    def _prepare_feature_target_arrays(df: pd.DataFrame, feat: str, target: str) -> Optional[Tuple[pd.Series, np.ndarray, np.ndarray]]:
        series = df[feat]
        y = df[target]
        mask = series.notna()
        x_clean = series[mask].values
        y_clean = y[mask].values
        if not ScorecardModel._has_sufficient_variation(x_clean):
            return None
        return (series, x_clean, y_clean)

    @staticmethod
    def _fit_and_build_binning(ob: Any, x_clean: np.ndarray, y_clean: np.ndarray) -> Any:
        ob.fit(x_clean, y_clean)
        return ob.binning_table.build()

    @staticmethod
    def _calculate_binning_metrics(bt: pd.DataFrame) -> Tuple[float, int, float]:
        iv_val = float(bt.loc[bt.index[:-1], 'IV'].sum())
        woe_vals = bt.loc[bt.index[:-1], 'WoE'].dropna()
        woe_range = round(float(woe_vals.max() - woe_vals.min()), 4) if len(woe_vals) > 0 else 0.0
        n_bins = len(bt) - 1
        return iv_val, n_bins, woe_range

    def _compute_binning_stats(self, feat: str, dtype: str, x_clean: np.ndarray, y_clean: np.ndarray) -> Tuple[Any, float, int, float]:
        ob = self._create_optimal_binning(feat, dtype)
        bt = self._fit_and_build_binning(ob, x_clean, y_clean)
        iv_val, n_bins, woe_range = self._calculate_binning_metrics(bt)
        return (ob, iv_val, n_bins, woe_range)

    def _compute_feature_iv_record(self, df: pd.DataFrame, feat: str, target: str) -> Optional[Tuple[Any, Dict[str, Any]]]:
        prepared = self._prepare_feature_target_arrays(df, feat, target)
        if prepared is None:
            return None
        series, x_clean, y_clean = prepared
        dtype = 'categorical' if series.dtype == object else 'numerical'
        try:
            ob, iv_val, n_bins, woe_range = self._compute_binning_stats(feat, dtype, x_clean, y_clean)
            record = self._build_iv_record(feat, iv_val, n_bins, woe_range, dtype)
            return (ob, record)
        except Exception as e:
            logger.warning('Binning failed for %s: %s', feat, e)
            return None

    @staticmethod
    def _ensure_optbinning_installed() -> None:
        if importlib.util.find_spec('optbinning') is None:
            raise ImportError('pip install optbinning')

    @staticmethod
    def _create_optimal_binning(feat: str, dtype: str) -> Any:
        from optbinning import OptimalBinning
        return OptimalBinning(name=feat, dtype=dtype, solver='cp', max_n_bins=8, min_bin_size=0.03)

    def _collect_iv_records(self, df: pd.DataFrame, candidate_features: List[str], target: str) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        self.binning_map = {}
        for feat in candidate_features:
            if feat not in df.columns:
                continue
            result = self._compute_feature_iv_record(df, feat, target)
            if result is None:
                continue
            ob, record = result
            self.binning_map[feat] = ob
            records.append(record)
        return records

    def compute_iv_table(self, df: pd.DataFrame, candidate_features: List[str], target: str='is_default') -> pd.DataFrame:
        self._ensure_optbinning_installed()
        records = self._collect_iv_records(df, candidate_features, target)
        iv_df = pd.DataFrame(records).sort_values('iv', ascending=False).reset_index(drop=True)
        self.iv_table = iv_df
        return iv_df

    def _transform_woe(self, df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
        woe_df = pd.DataFrame(index=df.index)
        for feat in features:
            if feat not in self.binning_map:
                continue
            ob = self.binning_map[feat]
            series = df[feat]
            mask = series.notna()
            woe_col = np.zeros(len(df))
            if mask.sum() > 0:
                with suppress(Exception):
                    woe_vals = ob.transform(series[mask].values, metric='woe')
                    woe_col[mask.values] = woe_vals
            woe_df[f'{feat}_woe'] = woe_col
        return woe_df

    @staticmethod
    def _scale_score(log_odds: np.ndarray) -> np.ndarray:
        factor = PDO / np.log(2)
        offset = BASE_SCORE + factor * np.log(BASE_ODDS)
        scores = offset - factor * log_odds
        return np.clip(scores, 300, 850).astype(int)

    def fit(self, loan_df: pd.DataFrame, payment_df: pd.DataFrame, customer_df: pd.DataFrame, iv_threshold: float=IV_USELESS, cv_folds: int=5) -> Dict[str, Any]:
        logger.info('Building model dataset...')
        model_df = self.build_model_dataset(loan_df, payment_df, customer_df)
        target = 'is_default'
        exclude = {target, 'loan_id', 'customer_id', 'borrower_id', 'id_prestamo', 'status', 'current_status', 'estado', '_first_late_date', 'vintage_quarter'}
        candidates = [c for c in model_df.columns if c not in exclude and (not c.startswith('_'))]
        logger.info('Computing IV for %d candidate features...', len(candidates))
        iv_table = self.compute_iv_table(model_df, candidates, target=target)
        selected = iv_table[iv_table['iv'] >= iv_threshold]['feature'].tolist()
        logger.info('Features selected (IV >= %.3f): %d / %d', iv_threshold, len(selected), len(candidates))
        if len(selected) == 0:
            raise ValueError(f'No features with IV >= {iv_threshold}. Check data quality or lower the threshold.')
        self.selected_features = selected
        logger.info('Transforming features to WoE space...')
        woe_df = self._transform_woe(model_df, selected)
        self.feature_names_woe = list(woe_df.columns)
        y = model_df[target].values
        x_woe = woe_df.values
        logger.info('Training Logistic Regression on WoE features...')
        self.lr_model = LogisticRegression(C=0.1, max_iter=1000, solver='lbfgs', class_weight='balanced', random_state=42)
        self.lr_model.fit(x_woe, y)
        skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        cv_aucs = cross_val_score(self.lr_model, x_woe, y, cv=skf, scoring='roc_auc')
        y_proba = self.lr_model.predict_proba(x_woe)[:, 1]
        auc = roc_auc_score(y, y_proba)
        gini = 2 * auc - 1
        from scipy.stats import ks_2samp
        ks_stat, _ = ks_2samp(y_proba[y == 1], y_proba[y == 0])
        log_odds = np.log(y_proba / (1 - y_proba + 1e-09))
        scores = self._scale_score(log_odds)
        model_df['predicted_score'] = scores
        model_df['predicted_pd'] = y_proba
        score_stats = {'defaults_mean_score': int(model_df[model_df[target] == 1]['predicted_score'].mean()), 'non_defaults_mean_score': int(model_df[model_df[target] == 0]['predicted_score'].mean()), 'score_p25': int(np.percentile(scores, 25)), 'score_p50': int(np.percentile(scores, 50)), 'score_p75': int(np.percentile(scores, 75))}
        self.scorecard_table = self._build_scorecard_table()
        metrics = {'auc_roc': round(auc, 4), 'gini_coefficient': round(gini, 4), 'ks_statistic': round(ks_stat, 4), 'cv_auc_mean': round(float(cv_aucs.mean()), 4), 'cv_auc_std': round(float(cv_aucs.std()), 4), 'n_features_selected': len(selected), 'n_samples': len(y), 'n_defaults': int(y.sum()), 'default_rate': round(float(y.mean()) * 100, 2), 'score_distribution': score_stats}
        self.metadata = {'model_type': 'WoE_LogisticRegression', 'features': selected, 'iv_threshold': iv_threshold, 'regularisation_C': 0.1, 'score_scale': {'base': BASE_SCORE, 'pdo': PDO, 'base_odds': BASE_ODDS}, 'metrics': metrics}
        logger.info('Scorecard trained: AUC=%.4f, KS=%.4f, Gini=%.4f, CV AUC=%.4f±%.4f', auc, ks_stat, gini, cv_aucs.mean(), cv_aucs.std())
        return metrics

    def _build_scorecard_table(self) -> pd.DataFrame:
        if self.lr_model is None:
            return pd.DataFrame()
        rows = []
        factor = PDO / np.log(2)
        n_features = len(self.selected_features)
        intercept_per_feature = self.lr_model.intercept_[0] / n_features if n_features > 0 else 0
        for i, feat in enumerate(self.selected_features):
            if feat not in self.binning_map:
                continue
            ob = self.binning_map[feat]
            coef = self.lr_model.coef_[0][i]
            bt = ob.binning_table.build()
            for _, row in bt.iloc[:-1].iterrows():
                woe_val = row.get('WoE', 0.0)
                if pd.isna(woe_val):
                    continue
                points = -(coef * woe_val + intercept_per_feature) * factor
                rows.append({'feature': feat, 'bin': str(row.get('Bin', '')), 'count': int(row.get('Count', 0)), 'event_rate': round(float(row.get('Event rate', 0)) * 100, 2), 'woe': round(float(woe_val), 4), 'iv_bin': round(float(row.get('IV', 0)), 4), 'points': round(float(points), 1)})
        return pd.DataFrame(rows)

    def predict_proba(self, loan_data: Dict[str, Any]) -> float:
        if self.lr_model is None:
            raise RuntimeError('Model not trained or loaded')
        row = pd.DataFrame([loan_data])
        woe_df = self._transform_woe(row, self.selected_features)
        for col in self.feature_names_woe:
            if col not in woe_df.columns:
                woe_df[col] = 0.0
        woe_df = woe_df[self.feature_names_woe]
        return float(self.lr_model.predict_proba(woe_df.values)[:, 1][0])

    def predict_score(self, loan_data: Dict[str, Any]) -> int:
        pd_prob = self.predict_proba(loan_data)
        pd_prob = max(1e-06, min(1 - 1e-06, pd_prob))
        log_odds = np.log(pd_prob / (1 - pd_prob))
        return int(self._scale_score(np.array([log_odds]))[0])

    def save(self, model_dir: str='models/scorecard') -> str:
        import pickle
        path = Path(model_dir)
        path.mkdir(parents=True, exist_ok=True)
        with open(path / 'lr_model.pkl', 'wb') as f:
            pickle.dump(self.lr_model, f)
        with open(path / 'binning_map.pkl', 'wb') as f:
            pickle.dump(self.binning_map, f)
        self.iv_table.to_csv(path / 'iv_table.csv', index=False)
        self.scorecard_table.to_csv(path / 'scorecard_table.csv', index=False)
        with open(path / 'metadata.json', 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
        logger.info('Scorecard saved to %s', path)
        return str(path)

    @classmethod
    def load(cls, model_dir: str='models/scorecard') -> 'ScorecardModel':
        import pickle
        path = Path(model_dir)
        if not path.exists():
            raise FileNotFoundError(f'Model directory not found: {path}')
        instance = cls()
        with open(path / 'lr_model.pkl', 'rb') as f:
            instance.lr_model = pickle.load(f)  # nosec B301
        with open(path / 'binning_map.pkl', 'rb') as f:
            instance.binning_map = pickle.load(f)  # nosec B301
        instance.iv_table = pd.read_csv(path / 'iv_table.csv')
        instance.scorecard_table = pd.read_csv(path / 'scorecard_table.csv')
        with open(path / 'metadata.json') as fj:
            instance.metadata = json.load(fj)
        instance.selected_features = instance.metadata.get('features', [])
        instance.feature_names_woe = [f'{f}_woe' for f in instance.selected_features]
        logger.info('Scorecard loaded from %s', path)
        return instance
