"""Credit Scorecard Model using WoE (Weight of Evidence) / IV (Information Value).

Architecture:
  1. Optimal binning per variable (OptBinning) - finds statistically optimal
     bin boundaries that maximize WoE separation between defaults/non-defaults.
  2. IV filter - removes features with IV < 0.02 (no predictive power).
  3. Logistic Regression on WoE-transformed features - produces calibrated
     probability estimates and interpretable scorecard points.
  4. Score scaling - maps probabilities to a 300-850 point scale (credit
     bureau convention: higher = lower risk).

Why scorecard first (over XGBoost alone):
  - 301 defaults / 18k+ loans (~1.7% default rate) - low volume for
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

from contextlib import suppress
import json
import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score

warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)

# Score scaling parameters
# Maps ln(odds) to 300-850 scale (standard credit bureau convention)
# PDO = 20 (Points to Double Odds), Base score = 600 at odds 50:1
BASE_SCORE = 600
PDO = 20
BASE_ODDS = 50.0

# IV thresholds
IV_USELESS = 0.02
IV_WEAK = 0.1
IV_MEDIUM = 0.3


class ScorecardModel:
    """WoE/IV logistic regression scorecard for credit default prediction."""

    def __init__(self) -> None:
        self.binning_map: Dict[str, Any] = {}
        self.iv_table: pd.DataFrame = pd.DataFrame()
        self.selected_features: List[str] = []
        self.lr_model: Optional[LogisticRegression] = None
        self.scorecard_table: pd.DataFrame = pd.DataFrame()
        self.metadata: Dict[str, Any] = {}
        self.feature_names_woe: List[str] = []

    @staticmethod
    def _normalize_columns(df: pd.DataFrame) -> None:  # NOSONAR
        df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]

    @staticmethod
    def _find_column(df: pd.DataFrame, *patterns: str) -> Optional[str]:
        for col in df.columns:
            for pat in patterns:
                if pat in col:
                    return col
        return None

    @classmethod
    def _coerce_alias_numeric(
        cls, df: pd.DataFrame, target_col: str, *patterns: str
    ) -> None:
        source_col = cls._find_column(df, *patterns)
        if source_col and source_col != target_col:
            df[target_col] = pd.to_numeric(df[source_col], errors="coerce")

    @classmethod
    def _add_target_and_core_features(cls, loan_df: pd.DataFrame) -> Optional[str]:
        status_col = cls._find_column(loan_df, "status", "estado", "estatus")
        if status_col is None:
            raise ValueError(
                "No status column found in loan_df. "
                "Expected a column containing 'status' or 'estado'."
            )

        loan_df["is_default"] = (
            loan_df[status_col]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["default", "defaulted", "mora", "en_mora", "castigado"])
            .astype(int)
        )

        dpd_col = cls._find_column(
            loan_df, "days_past_due", "days_in_default", "dpd", "dias_mora", "dias_en_mora"
        )
        loan_df["days_past_due"] = (
            pd.to_numeric(loan_df[dpd_col], errors="coerce").fillna(0) if dpd_col else 0.0
        )

        cls._coerce_alias_numeric(loan_df, "outstanding_balance", "outstanding")
        cls._coerce_alias_numeric(loan_df, "collateral_value", "collateral", "garantia", "garantía")
        cls._coerce_alias_numeric(
            loan_df,
            "interest_rate",
            "interest_rate",
            "interest",
            "tasa_interes",
            "tasa",
            "apr",
        )
        cls._coerce_alias_numeric(
            loan_df,
            "principal_amount",
            "principal_amount",
            "principal",
            "loan_amount",
            "monto_prestamo",
            "monto_desembolsado",
        )

        date_col = cls._find_column(loan_df, "disburs", "originat", "fecha_desembolso")
        if date_col:
            loan_df[date_col] = pd.to_datetime(loan_df[date_col], errors="coerce")
            loan_df["loan_age_days"] = (pd.Timestamp.today() - loan_df[date_col]).dt.days.clip(lower=0)
            loan_df["vintage_quarter"] = loan_df[date_col].dt.to_period("Q").astype(str)

        return date_col

    @staticmethod
    def _add_ratio_features(loan_df: pd.DataFrame) -> None:
        if "outstanding_balance" in loan_df.columns and "collateral_value" in loan_df.columns:
            loan_df["ltv_ratio"] = np.where(
                pd.to_numeric(loan_df["collateral_value"], errors="coerce").fillna(0) > 0,
                pd.to_numeric(loan_df["outstanding_balance"], errors="coerce").fillna(0)
                / pd.to_numeric(loan_df["collateral_value"], errors="coerce").fillna(1)
                * 100,
                np.nan,
            )

        if "last_payment_amount" in loan_df.columns and "total_scheduled" in loan_df.columns:
            loan_df["payment_ratio"] = np.where(
                pd.to_numeric(loan_df["total_scheduled"], errors="coerce").fillna(0) > 0,
                pd.to_numeric(loan_df["last_payment_amount"], errors="coerce").fillna(0)
                / pd.to_numeric(loan_df["total_scheduled"], errors="coerce").fillna(1)
                * 100,
                np.nan,
            )

    @staticmethod
    def _max_consecutive_late(series: pd.Series) -> int:
        max_c = 0
        cur_c = 0
        for val in series:
            if val == 1:
                cur_c += 1
                max_c = max(max_c, cur_c)
            else:
                cur_c = 0
        return max_c

    @classmethod
    def _merge_payment_behavior_features(
        cls,
        loan_df: pd.DataFrame,
        payment_df: pd.DataFrame,
        date_col: Optional[str],
    ) -> pd.DataFrame:
        loan_id_col_pay = cls._find_column(payment_df, "loan_id", "prestamo_id", "id_prestamo")
        loan_id_col_loan = cls._find_column(loan_df, "loan_id", "id_prestamo", "prestamo_id")
        status_pay_col = cls._find_column(payment_df, "status", "estado", "estatus")

        if not (loan_id_col_pay and loan_id_col_loan and status_pay_col):
            return loan_df

        amount_pay_col = cls._find_column(
            payment_df, "total_payment", "true_total", "amount", "monto", "valor"
        )
        date_pay_col = next((c for c in payment_df.columns if "date" in c or "fecha" in c), None)

        payment_df["_is_late"] = (
            payment_df[status_pay_col]
            .astype(str)
            .str.strip()
            .str.lower()
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

        sort_cols = [loan_id_col_pay, date_pay_col] if date_pay_col else [loan_id_col_pay]
        consec = (
            payment_df.sort_values(sort_cols)
            .groupby(loan_id_col_pay)["_is_late"]
            .apply(cls._max_consecutive_late)
            .reset_index()
        )
        consec.columns = [loan_id_col_loan, "max_consecutive_late"]
        beh = beh.merge(consec, on=loan_id_col_loan, how="left")

        if amount_pay_col:
            payment_df[amount_pay_col] = pd.to_numeric(payment_df[amount_pay_col], errors="coerce")
            vol = payment_df.groupby(loan_id_col_pay)[amount_pay_col].std().reset_index()
            vol.columns = [loan_id_col_loan, "payment_amount_std"]
            beh = beh.merge(vol, on=loan_id_col_loan, how="left")

        if date_pay_col and date_col:
            payment_df[date_pay_col] = pd.to_datetime(payment_df[date_pay_col], errors="coerce")
            first_late = (
                payment_df[payment_df["_is_late"] == 1]
                .sort_values(date_pay_col)
                .groupby(loan_id_col_pay)[date_pay_col]
                .first()
                .reset_index()
            )
            first_late.columns = [loan_id_col_loan, "_first_late_date"]
            loan_df = loan_df.merge(first_late, on=loan_id_col_loan, how="left")
            loan_df["days_to_first_late"] = (loan_df["_first_late_date"] - loan_df[date_col]).dt.days
            loan_df.drop(columns=["_first_late_date"], inplace=True)

        return loan_df.merge(beh, on=loan_id_col_loan, how="left")

    @staticmethod
    def _find_customer_id_column(df: pd.DataFrame) -> Optional[str]:
        return next(
            (c for c in df.columns if "customer_id" in c or "cliente_id" in c or "borrower_id" in c),
            None,
        )

    @classmethod
    def _merge_customer_features(
        cls,
        loan_df: pd.DataFrame,
        customer_df: pd.DataFrame,
    ) -> pd.DataFrame:
        cust_id_col_cust = cls._find_customer_id_column(customer_df)
        cust_id_col_loan = cls._find_customer_id_column(loan_df)
        if not (cust_id_col_cust and cust_id_col_loan):
            return loan_df

        industry_col = next(
            (c for c in customer_df.columns if "industry" in c or "sector" in c or "giro" in c),
            None,
        )
        score_col = next(
            (c for c in customer_df.columns if "equifax" in c or "score" in c or "buro" in c),
            None,
        )

        keep_cols = [cust_id_col_cust]
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

    @classmethod
    def build_model_dataset(
        cls,
        loan_df: pd.DataFrame,
        payment_df: pd.DataFrame,
        customer_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Merge loan, payment history, and customer data into a flat model table."""
        cls._normalize_columns(loan_df)
        cls._normalize_columns(payment_df)
        cls._normalize_columns(customer_df)

        date_col = cls._add_target_and_core_features(loan_df)
        cls._add_ratio_features(loan_df)
        loan_df = cls._merge_payment_behavior_features(loan_df, payment_df, date_col)
        loan_df = cls._merge_customer_features(loan_df, customer_df)

        logger.info(
            "Model dataset: %d rows, %d defaults (%.2f%%), %d features",
            len(loan_df),
            int(loan_df["is_default"].sum()),
            float(loan_df["is_default"].mean()) * 100.0,
            len(loan_df.columns),
        )
        return loan_df

    @staticmethod
    def _iv_predictive_power(iv_value: float) -> str:
        return (
            "Useless"
            if iv_value < IV_USELESS
            else "Weak"
            if iv_value < IV_WEAK
            else "Medium"
            if iv_value < IV_MEDIUM
            else "Strong"
        )

    @staticmethod
    def _iv_feature_dtype(series: pd.Series) -> str:
        return "categorical" if series.dtype == object else "numerical"

    def _compute_single_feature_iv(
        self,
        feat: str,
        series: pd.Series,
        y: pd.Series,
        optimal_binning_cls: Any,
    ) -> Dict[str, Any] | None:
        mask = series.notna()
        x_clean = series[mask].values
        y_clean = y[mask].values

        if len(np.unique(x_clean)) < 2:
            return None

        dtype = self._iv_feature_dtype(series)

        try:
            ob = optimal_binning_cls(
                name=feat,
                dtype=dtype,
                solver="cp",
                max_n_bins=8,
                min_bin_size=0.03,
            )
            ob.fit(x_clean, y_clean)
            bt = ob.binning_table.build()
        except Exception as err:
            logger.warning("Binning failed for %s: %s", feat, err)
            return None

        iv_val = float(bt.loc[bt.index[:-1], "IV"].sum())
        woe_vals = bt.loc[bt.index[:-1], "WoE"].dropna()
        woe_range = round(float(woe_vals.max() - woe_vals.min()), 4) if len(woe_vals) > 0 else 0.0
        n_bins = len(bt) - 1

        self.binning_map[feat] = ob

        return {
            "feature": feat,
            "iv": round(iv_val, 4),
            "predictive_power": self._iv_predictive_power(iv_val),
            "n_bins": n_bins,
            "woe_range": woe_range,
            "dtype": dtype,
        }

    def compute_iv_table(
        self,
        df: pd.DataFrame,
        candidate_features: List[str],
        target: str = "is_default",
    ) -> pd.DataFrame:  # NOSONAR - stepwise IV pipeline retained for model governance
        """Compute WoE and IV for each candidate feature using OptimalBinning."""
        try:
            from optbinning import OptimalBinning
        except ImportError as exc:
            raise ImportError("pip install optbinning") from exc

        records = []
        self.binning_map = {}
        y = df[target]

        for feat in candidate_features:
            if feat not in df.columns:
                continue
            record = self._compute_single_feature_iv(
                feat=feat,
                series=df[feat],
                y=y,
                optimal_binning_cls=OptimalBinning,
            )
            if record is not None:
                records.append(record)

        iv_df = pd.DataFrame(records).sort_values("iv", ascending=False).reset_index(drop=True)
        self.iv_table = iv_df
        return iv_df

    def _transform_woe(self, df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
        """Transform features to WoE values using fitted OptimalBinning objects."""
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
                    woe_vals = ob.transform(series[mask].values, metric="woe")
                    woe_col[mask.values] = woe_vals

            woe_df[f"{feat}_woe"] = woe_col

        return woe_df

    @staticmethod
    def _scale_score(log_odds: np.ndarray) -> np.ndarray:
        """Map log-odds to 300-850 scale."""
        factor = PDO / np.log(2)
        offset = BASE_SCORE + factor * np.log(BASE_ODDS)
        scores = offset - factor * log_odds
        return np.clip(scores, 300, 850).astype(int)

    def fit(
        self,
        loan_df: pd.DataFrame,
        payment_df: pd.DataFrame,
        customer_df: pd.DataFrame,
        iv_threshold: float = IV_USELESS,
        cv_folds: int = 5,
    ) -> Dict[str, Any]:
        """Full training pipeline: merge -> feature engineering -> IV -> LR -> scorecard."""
        model_df = self.build_model_dataset(loan_df, payment_df, customer_df)
        target = "is_default"

        exclude = {
            target,
            "loan_id",
            "customer_id",
            "borrower_id",
            "id_prestamo",
            "status",
            "current_status",
            "estado",
            "_first_late_date",
            "vintage_quarter",
        }
        candidates = [c for c in model_df.columns if c not in exclude and not c.startswith("_")]

        iv_table = self.compute_iv_table(model_df, candidates, target=target)

        selected = iv_table[iv_table["iv"] >= iv_threshold]["feature"].tolist()
        if len(selected) == 0:
            raise ValueError(
                f"No features with IV >= {iv_threshold}. "
                "Check data quality or lower the threshold."
            )

        self.selected_features = selected

        woe_df = self._transform_woe(model_df, selected)
        self.feature_names_woe = list(woe_df.columns)

        y = model_df[target].values
        x_woe = woe_df.values

        self.lr_model = LogisticRegression(
            C=0.1,
            max_iter=1000,
            solver="lbfgs",
            class_weight="balanced",
            random_state=42,
        )
        self.lr_model.fit(x_woe, y)

        skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        cv_aucs = cross_val_score(self.lr_model, x_woe, y, cv=skf, scoring="roc_auc")

        y_proba = self.lr_model.predict_proba(x_woe)[:, 1]
        auc = roc_auc_score(y, y_proba)
        gini = 2 * auc - 1

        from scipy.stats import ks_2samp

        ks_stat, _ = ks_2samp(y_proba[y == 1], y_proba[y == 0])

        log_odds = np.log(y_proba / (1 - y_proba + 1e-9))
        scores = self._scale_score(log_odds)
        model_df["predicted_score"] = scores
        model_df["predicted_pd"] = y_proba

        score_stats = {
            "defaults_mean_score": int(model_df[model_df[target] == 1]["predicted_score"].mean()),
            "non_defaults_mean_score": int(model_df[model_df[target] == 0]["predicted_score"].mean()),
            "score_p25": int(np.percentile(scores, 25)),
            "score_p50": int(np.percentile(scores, 50)),
            "score_p75": int(np.percentile(scores, 75)),
        }

        self.scorecard_table = self._build_scorecard_table()

        metrics = {
            "auc_roc": round(float(auc), 4),
            "gini_coefficient": round(float(gini), 4),
            "ks_statistic": round(float(ks_stat), 4),
            "cv_auc_mean": round(float(cv_aucs.mean()), 4),
            "cv_auc_std": round(float(cv_aucs.std()), 4),
            "n_features_selected": len(selected),
            "n_samples": len(y),
            "n_defaults": int(y.sum()),
            "default_rate": round(float(y.mean()) * 100, 2),
            "score_distribution": score_stats,
        }

        self.metadata = {
            "model_type": "WoE_LogisticRegression",
            "features": selected,
            "iv_threshold": iv_threshold,
            "regularisation_C": 0.1,
            "score_scale": {"base": BASE_SCORE, "pdo": PDO, "base_odds": BASE_ODDS},
            "metrics": metrics,
        }

        return metrics

    def _build_scorecard_table(self) -> pd.DataFrame:
        """Build human-readable scorecard: feature | bin | woe | points."""
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
                woe_val = row.get("WoE", 0.0)
                if pd.isna(woe_val):
                    continue
                points = -(coef * float(woe_val) + intercept_per_feature) * factor
                rows.append(
                    {
                        "feature": feat,
                        "bin": str(row.get("Bin", "")),
                        "count": int(row.get("Count", 0)),
                        "event_rate": round(float(row.get("Event rate", 0)) * 100, 2),
                        "woe": round(float(woe_val), 4),
                        "iv_bin": round(float(row.get("IV", 0)), 4),
                        "points": round(float(points), 1),
                    }
                )

        return pd.DataFrame(rows)

    def predict_proba(self, loan_data: Dict[str, Any]) -> float:
        """Return probability of default for a single loan."""
        if self.lr_model is None:
            raise RuntimeError("Model not trained or loaded")

        row = pd.DataFrame([loan_data])
        woe_df = self._transform_woe(row, self.selected_features)
        for col in self.feature_names_woe:
            if col not in woe_df.columns:
                woe_df[col] = 0.0
        woe_df = woe_df[self.feature_names_woe]
        return float(self.lr_model.predict_proba(woe_df.values)[:, 1][0])

    def predict_score(self, loan_data: Dict[str, Any]) -> int:
        """Return 300-850 credit score (higher = lower risk)."""
        pd_prob = self.predict_proba(loan_data)
        pd_prob = max(1e-6, min(1 - 1e-6, pd_prob))
        log_odds = np.log(pd_prob / (1 - pd_prob))
        return int(self._scale_score(np.array([log_odds]))[0])

    def save(self, model_dir: str = "models/scorecard") -> str:
        """Persist model, binning objects, scorecard table, and metadata."""
        import pickle

        path = Path(model_dir)
        path.mkdir(parents=True, exist_ok=True)

        with open(path / "lr_model.pkl", "wb") as handle:
            pickle.dump(self.lr_model, handle)

        with open(path / "binning_map.pkl", "wb") as handle:
            pickle.dump(self.binning_map, handle)

        self.iv_table.to_csv(path / "iv_table.csv", index=False)
        self.scorecard_table.to_csv(path / "scorecard_table.csv", index=False)

        with open(path / "metadata.json", "w", encoding="utf-8") as handle:
            json.dump(self.metadata, handle, indent=2, default=str)

        logger.info("Scorecard saved to %s", path)
        return str(path)

    @classmethod
    def load(cls, model_dir: str = "models/scorecard") -> "ScorecardModel":
        """Load a saved scorecard model."""
        import pickle

        path = Path(model_dir)
        if not path.exists():
            raise FileNotFoundError(f"Model directory not found: {path}")

        instance = cls()

        with open(path / "lr_model.pkl", "rb") as handle:
            instance.lr_model = pickle.load(handle)

        with open(path / "binning_map.pkl", "rb") as handle:
            instance.binning_map = pickle.load(handle)

        instance.iv_table = pd.read_csv(path / "iv_table.csv")
        instance.scorecard_table = pd.read_csv(path / "scorecard_table.csv")

        with open(path / "metadata.json", encoding="utf-8") as handle:
            instance.metadata = json.load(handle)

        instance.selected_features = instance.metadata.get("features", [])
        instance.feature_names_woe = [f"{feature}_woe" for feature in instance.selected_features]

        logger.info("Scorecard loaded from %s", path)
        return instance
