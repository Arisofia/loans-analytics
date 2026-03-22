"""Credit Scorecard Model using WoE (Weight of Evidence) / IV (Information Value).

Architecture:
  1. Optimal binning per variable (OptBinning) — finds statistically optimal
     bin boundaries that maximize WoE separation between defaults/non-defaults.
  2. IV filter — removes features with IV < 0.02 (no predictive power).
  3. Logistic Regression on WoE-transformed features — produces calibrated
     probability estimates and interpretable scorecard points.
  4. Score scaling — maps probabilities to a 300-850 point scale (credit
     bureau convention: higher = lower risk).

Why scorecard first (over XGBoost alone):
  - 301 defaults / 18k+ loans (~1.7% default rate) — low volume for
    ensemble methods; LR is more stable at this sample size.
  - WoE transformation handles non-linearity + outliers without feature
    engineering assumptions.
  - Output is directly interpretable by credit committees (points per bin).
  - IV table is the definitive feature selection input for the XGBoost
    model in Phase 2.

Usage:
    # Training
    model = ScorecardModel()
    result = model.fit(loan_df, payment_df, customer_df)
    model.save("models/scorecard")

    # Inference
    model = ScorecardModel.load("models/scorecard")
    score = model.predict_score(loan_features_dict)
    pd_prob = model.predict_proba(loan_features_dict)
"""

from __future__ import annotations

import json
import logging
import pickle
import re
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from scipy.stats import ks_2samp

warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)

# ── Score scaling parameters ────────────────────────────────────────────────
# Maps ln(odds) to 300–850 scale (standard credit bureau convention)
# PDO = 20 (Points to Double Odds), Base score = 600 at odds 50:1
BASE_SCORE = 600
PDO = 20
BASE_ODDS = 50.0

# ── IV thresholds ────────────────────────────────────────────────────────────
IV_USELESS = 0.02
IV_WEAK = 0.1
IV_MEDIUM = 0.3


class ScorecardModel:
    """WoE/IV logistic regression scorecard for credit default prediction."""

    _NOT_FITTED_MSG = "Model must be fitted before prediction."

    def __init__(self) -> None:
        self.binning_map: Dict[str, Any] = {}      # feature -> OptimalBinning object
        self.iv_table: pd.DataFrame = pd.DataFrame()
        self.selected_features: List[str] = []
        self.lr_model: Optional[LogisticRegression] = None
        self.scorecard_table: pd.DataFrame = pd.DataFrame()
        self.metadata: Dict[str, Any] = {}
        self.feature_names_woe: List[str] = []     # WoE column names

    @staticmethod
    def _normalize_column_name(column_name: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "_", str(column_name).strip().lower())
        return normalized.strip("_")

    @classmethod
    def _normalize_dataframe_columns(cls, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [cls._normalize_column_name(column_name) for column_name in df.columns]
        return df

    @classmethod
    def _find_column(
        cls,
        columns: Sequence[str],
        aliases: Sequence[str],
    ) -> Optional[str]:
        normalized_map = {column: cls._normalize_column_name(column) for column in columns}
        normalized_aliases = [cls._normalize_column_name(alias) for alias in aliases]

        for alias in normalized_aliases:
            for column, normalized_column in normalized_map.items():
                if normalized_column == alias:
                    return column

        for alias in normalized_aliases:
            for column, normalized_column in normalized_map.items():
                if alias and (alias in normalized_column or normalized_column in alias):
                    return column

        return None

    # ── Data preparation ────────────────────────────────────────────────────

    @staticmethod
    def build_model_dataset(
        loan_df: pd.DataFrame,
        payment_df: pd.DataFrame,
        customer_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Merge loan, payment history, and customer data into a flat model table."""
        loan_df = ScorecardModel._normalize_dataframe_columns(loan_df)
        payment_df = ScorecardModel._normalize_dataframe_columns(payment_df)
        customer_df = ScorecardModel._normalize_dataframe_columns(customer_df)

        loan_df = ScorecardModel._add_target_variable(loan_df)
        loan_df = ScorecardModel._add_derived_loan_features(loan_df)
        loan_df = ScorecardModel._add_behavioral_features(loan_df, payment_df)
        loan_df = ScorecardModel._add_customer_features(loan_df, customer_df)

        return loan_df

    @staticmethod
    def _add_target_variable(df: pd.DataFrame) -> pd.DataFrame:
        status_col = ScorecardModel._find_column(
            df.columns,
            ["status", "current_status", "estado", "loan_status", "application_status"],
        )
        if status_col is None:
            raise ValueError("No status column found. Expected: status/current_status/estado/loan_status")

        df["is_default"] = (
            df[status_col].str.strip().str.lower()
            .isin(["default", "defaulted", "mora", "en_mora", "castigado", "loss"])
            .astype(int)
        )
        return df

    @staticmethod
    def _add_derived_loan_features(df: pd.DataFrame) -> pd.DataFrame:
        # Origination date
        date_col = ScorecardModel._find_column(
            df.columns,
            ["disbursement_date", "origination_date", "fecha_desembolso", "loan_date"],
        )
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df["loan_age_days"] = (
                pd.Timestamp.today() - df[date_col]
            ).dt.days.clip(lower=0)

        # LTV ratio
        if "outstanding_balance" in df.columns and "collateral_value" in df.columns:
            df["ltv_ratio"] = np.where(
                df["collateral_value"] > 0,
                df["outstanding_balance"] / df["collateral_value"] * 100,
                np.nan,
            )

        # Payment ratio
        if "last_payment_amount" in df.columns and "total_scheduled" in df.columns:
            df["payment_ratio"] = np.where(
                df["total_scheduled"] > 0,
                df["last_payment_amount"] / df["total_scheduled"] * 100,
                np.nan,
            )
        return df

    @staticmethod
    def _add_behavioral_features(loan_df: pd.DataFrame, payment_df: pd.DataFrame) -> pd.DataFrame:
        loan_id_col_pay = ScorecardModel._find_column(
            payment_df.columns,
            ["loan_id", "prestamo_id", "id_prestamo", "new_loan_id", "old_loan_id"],
        )
        loan_id_col_loan = ScorecardModel._find_column(
            loan_df.columns,
            ["loan_id", "id_prestamo", "prestamo_id", "new_loan_id", "old_loan_id"],
        )

        if not (loan_id_col_pay and loan_id_col_loan):
            return loan_df

        status_pay_col = ScorecardModel._find_column(
            payment_df.columns,
            ["payment_status", "true_payment_status", "status", "estado"],
        )
        if not status_pay_col:
            return loan_df

        payment_df = payment_df.copy()
        payment_df["_is_late"] = (
            payment_df[status_pay_col].astype(str).str.strip().str.lower()
            .isin(["late", "tardio", "tardío", "mora", "atrasado"])
            .astype(int)
        )

        beh = payment_df.groupby(loan_id_col_pay).agg(
            n_payments=("_is_late", "count"),
            n_late_payments=("_is_late", "sum"),
        ).reset_index()
        beh.columns = [loan_id_col_loan, "n_payments", "n_late_payments"]
        beh["late_payment_rate"] = np.where(
            beh["n_payments"] > 0,
            beh["n_late_payments"] / beh["n_payments"],
            0.0,
        )

        # Max consecutive late
        date_pay_col = ScorecardModel._find_column(
            payment_df.columns,
            ["true_payment_date", "payment_date", "date", "fecha"],
        )
        
        def max_consecutive(series: pd.Series) -> int:
            max_c = cur_c = 0
            for v in series:
                if v == 1:
                    cur_c += 1
                    max_c = max(max_c, cur_c)
                else:
                    cur_c = 0
            return max_c

        consec = (
            payment_df.sort_values([loan_id_col_pay, date_pay_col] if date_pay_col else [loan_id_col_pay])
            .groupby(loan_id_col_pay)["_is_late"]
            .apply(max_consecutive)
            .reset_index()
        )
        consec.columns = [loan_id_col_loan, "max_consecutive_late"]
        beh = beh.merge(consec, on=loan_id_col_loan, how="left")

        # Payment amount volatility
        amount_pay_col = ScorecardModel._find_column(
            payment_df.columns,
            ["true_total_payment", "total_payment", "payment_amount", "last_payment_amount", "amount"],
        )
        if amount_pay_col:
            payment_df[amount_pay_col] = pd.to_numeric(payment_df[amount_pay_col], errors="coerce")
            vol = payment_df.groupby(loan_id_col_pay)[amount_pay_col].std().reset_index()
            vol.columns = [loan_id_col_loan, "payment_amount_std"]
            beh = beh.merge(vol, on=loan_id_col_loan, how="left")

        return loan_df.merge(beh, on=loan_id_col_loan, how="left")

    @staticmethod
    def _add_customer_features(loan_df: pd.DataFrame, customer_df: pd.DataFrame) -> pd.DataFrame:
        cust_id_col_cust = ScorecardModel._find_column(
            customer_df.columns, ["customer_id", "cliente_id", "borrower_id"],
        )
        cust_id_col_loan = ScorecardModel._find_column(
            loan_df.columns, ["customer_id", "cliente_id", "borrower_id"],
        )

        if not (cust_id_col_cust and cust_id_col_loan):
            return loan_df

        industry_col = ScorecardModel._find_column(
            customer_df.columns, ["industry", "sector", "giro"],
        )
        score_col = ScorecardModel._find_column(
            customer_df.columns, ["equifax_score", "external_credit_score", "internal_credit_score", "score"],
        )

        keep_cols = [cust_id_col_cust]
        customer_df = customer_df.copy()
        if industry_col:
            keep_cols.append(industry_col)
            customer_df[industry_col] = customer_df[industry_col].astype(str).str.strip()
        if score_col:
            keep_cols.append(score_col)
            customer_df[score_col] = pd.to_numeric(customer_df[score_col], errors="coerce")

        return loan_df.merge(
            customer_df[keep_cols].rename(columns={cust_id_col_cust: cust_id_col_loan}),
            on=cust_id_col_loan,
            how="left",
        )

    # ── WoE / IV ────────────────────────────────────────────────────────────

    def compute_iv_table(
        self,
        df: pd.DataFrame,
        candidate_features: List[str],
        target: str = "is_default",
    ) -> pd.DataFrame:
        """Compute WoE and IV for each candidate feature using OptimalBinning."""
        records = []
        self.binning_map = {}

        for feat in candidate_features:
            if feat not in df.columns or feat == target:
                continue
            
            record = self._compute_feature_binning(df, feat, target)
            if record:
                records.append(record)

        iv_df = pd.DataFrame(records).sort_values("iv", ascending=False).reset_index(drop=True)
        self.iv_table = iv_df
        return iv_df

    def _compute_feature_binning(self, df: pd.DataFrame, feat: str, target: str) -> Optional[Dict[str, Any]]:
        """Compute Optimal Binning for a single feature."""
        try:
            from optbinning import OptimalBinning
        except ImportError as exc:
            raise ImportError("pip install optbinning") from exc

        series = df[feat]
        y = df[target]

        mask = series.notna()
        if mask.sum() < 10:
            return None
            
        x_clean = series[mask].values
        y_clean = y[mask].values

        if len(np.unique(x_clean)) < 2:
            return None

        dtype = "categorical" if series.dtype == object or series.dtype == bool else "numerical"

        try:
            ob = OptimalBinning(
                name=feat,
                dtype=dtype,
                solver="cp",
                max_n_bins=8,
                min_bin_size=0.03,
            )
            ob.fit(x_clean, y_clean)
            bt = ob.binning_table.build()

            iv_val = float(bt.loc[bt.index[:-1], "IV"].sum())
            woe_vals = bt.loc[bt.index[:-1], "WoE"].dropna()
            woe_range = round(float(woe_vals.max() - woe_vals.min()), 4) if len(woe_vals) > 0 else 0.0
            n_bins = len(bt) - 1

            self.binning_map[feat] = ob

            if iv_val < IV_USELESS:
                power = "Useless"
            elif iv_val < IV_WEAK:
                power = "Weak"
            elif iv_val < IV_MEDIUM:
                power = "Medium"
            else:
                power = "Strong"

            return {
                "feature": feat,
                "iv": round(iv_val, 4),
                "predictive_power": power,
                "n_bins": n_bins,
                "woe_range": woe_range,
                "dtype": dtype,
            }

        except Exception as e:
            logger.warning("Binning failed for %s: %s", feat, e)
            return None

    def _transform_woe(self, df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
        """Transform features to WoE values."""
        woe_df = pd.DataFrame(index=df.index)
        for feat in features:
            if feat not in self.binning_map:
                continue
            ob = self.binning_map[feat]
            series = df[feat]
            mask = series.notna()
            woe_col = np.zeros(len(df))

            if mask.sum() > 0:
                try:
                    woe_vals = ob.transform(series[mask].values, metric="woe")
                    woe_col[mask.values] = woe_vals
                except Exception:
                    pass

            woe_df[f"{feat}_woe"] = woe_col
        return woe_df

    # ── Score scaling ────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_scaling_params(base_score: float, base_odds: float, pdo: int) -> Tuple[float, float]:
        factor = pdo / np.log(2)
        offset = base_score - (factor * np.log(base_odds))
        return offset, factor

    def _scale_score(self, log_odds: np.ndarray) -> np.ndarray:
        """Map log-odds to 300–850 scale. Score = offset - factor * log_odds."""
        offset, factor = self._calculate_scaling_params(BASE_SCORE, BASE_ODDS, PDO)
        return np.round(offset - factor * log_odds).astype(int)

    # ── Main API ─────────────────────────────────────────────────────────────

    def fit(
        self,
        loan_df: pd.DataFrame,
        payment_df: pd.DataFrame,
        customer_df: pd.DataFrame,
        iv_threshold: float = 0.02,
        cv_folds: int = 5,
    ) -> Dict[str, Any]:
        """Full pipeline: prepare data, select features, train, and scale."""
        df = self.build_model_dataset(loan_df, payment_df, customer_df)
        
        candidate_features = [
            c for c in df.columns 
            if c not in ["is_default", "loan_id", "customer_id", "disbursement_date", "status"]
        ]
        
        self.compute_iv_table(df, candidate_features)
        self.selected_features = self.iv_table[self.iv_table["iv"] >= iv_threshold]["feature"].tolist()
        
        if not self.selected_features:
            raise ValueError(f"No features met IV threshold of {iv_threshold}")

        woe_df = self._transform_woe(df, self.selected_features)
        self.feature_names_woe = woe_df.columns.tolist()
        
        X = woe_df.values
        y = df["is_default"].values
        
        self.lr_model = LogisticRegression(C=0.1, solver="lbfgs")
        self.lr_model.fit(X, y)
        
        # Metrics
        y_proba = self.lr_model.predict_proba(X)[:, 1]
        auc = roc_auc_score(y, y_proba)
        
        # KS
        defaults = y_proba[y == 1]
        non_defaults = y_proba[y == 0]
        ks_stat = ks_2samp(defaults, non_defaults).statistic
        
        # CV
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        cv_scores = cross_val_score(self.lr_model, X, y, cv=cv, scoring="roc_auc")
        
        # Scorecard table
        self._build_scorecard_table()
        
        # Score distribution
        scores = self.predict_score_batch(df)
        sd = {
            "defaults_mean_score": float(scores[y == 1].mean()),
            "non_defaults_mean_score": float(scores[y == 0].mean()),
            "score_p25": float(np.percentile(scores, 25)),
            "score_p50": float(np.percentile(scores, 50)),
            "score_p75": float(np.percentile(scores, 75)),
        }
        
        self.metadata = {
            "model_type": "WoE_Logistic_Scorecard",
            "n_samples": len(df),
            "n_defaults": int(y.sum()),
            "default_rate": float(y.mean() * 100),
            "n_features_selected": len(self.selected_features),
            "metrics": {
                "auc_roc": float(auc),
                "gini_coefficient": float(2 * auc - 1),
                "ks_statistic": float(ks_stat),
                "cv_auc_mean": float(cv_scores.mean()),
                "cv_auc_std": float(cv_scores.std()),
            },
            "score_distribution": sd,
            "features": self.selected_features
        }
        
        return self.metadata

    def _build_scorecard_table(self) -> None:
        """Create a human-readable table of points per bin."""
        if self.lr_model is None:
            raise ValueError(self._NOT_FITTED_MSG)
            
        offset, factor = self._calculate_scaling_params(BASE_SCORE, BASE_ODDS, PDO)
        n_feats = len(self.selected_features)
        intercept = self.lr_model.intercept_[0]
        
        base_points = offset - factor * intercept
        
        records = []
        for i, feat in enumerate(self.selected_features):
            ob = self.binning_map[feat]
            bt = ob.binning_table.build()
            coef = self.lr_model.coef_[0][i]
            
            # Use binning table rows except 'Totals'
            for idx, row in bt.iterrows():
                if idx == bt.index[-1]:
                    continue
                
                woe = row["WoE"]
                event_rate = row["Event rate"]
                points = -(woe * coef * factor) + (base_points / n_feats)
                
                records.append({
                    "feature": feat,
                    "bin": row["Bin"],
                    "woe": woe,
                    "event_rate": event_rate,
                    "points": round(float(points), 1)
                })
        
        self.scorecard_table = pd.DataFrame(records)

    def predict_score(self, loan_features: Dict[str, Any]) -> int:
        """Predict score for a single loan."""
        if self.lr_model is None:
            raise ValueError(self._NOT_FITTED_MSG)
            
        df = pd.DataFrame([loan_features])
        woe_df = self._transform_woe(df, self.selected_features)
        log_odds = self.lr_model.decision_function(woe_df.values)
        return int(self._scale_score(log_odds)[0])

    def predict_score_batch(self, df: pd.DataFrame) -> np.ndarray:
        if self.lr_model is None:
            raise ValueError(self._NOT_FITTED_MSG)
            
        woe_df = self._transform_woe(df, self.selected_features)
        log_odds = self.lr_model.decision_function(woe_df.values)
        return self._scale_score(log_odds)

    def predict_proba(self, loan_features: Dict[str, Any]) -> float:
        if self.lr_model is None:
            raise ValueError(self._NOT_FITTED_MSG)
            
        df = pd.DataFrame([loan_features])
        woe_df = self._transform_woe(df, self.selected_features)
        return float(self.lr_model.predict_proba(woe_df.values)[0, 1])

    def save(self, path: str) -> str:
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        
        with open(p / "binning_map.pkl", "wb") as f:
            pickle.dump(self.binning_map, f)
            
        with open(p / "lr_model.pkl", "wb") as f:
            pickle.dump(self.lr_model, f)
            
        self.iv_table.to_csv(p / "iv_table.csv", index=False)
        self.scorecard_table.to_csv(p / "scorecard_table.csv", index=False)
        
        with open(p / "metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2)
            
        return str(p)

    @classmethod
    def load(cls, path: str) -> ScorecardModel:
        p = Path(path)
        model = cls()
        
        with open(p / "binning_map.pkl", "rb") as f:
            model.binning_map = pickle.load(f)
            
        with open(p / "lr_model.pkl", "rb") as f:
            model.lr_model = pickle.load(f)
            
        model.iv_table = pd.read_csv(p / "iv_table.csv")
        model.scorecard_table = pd.read_csv(p / "scorecard_table.csv")
        model.selected_features = model.iv_table[model.iv_table["iv"] >= 0.02]["feature"].tolist()
        
        with open(p / "metadata.json", "r") as f:
            model.metadata = json.load(f)
            
        return model
