from __future__ import annotations
import json
import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import RobustScaler

warnings.filterwarnings("ignore", category=UserWarning)
logger = logging.getLogger(__name__)

SEGMENT_HIGH_VELOCITY = "High Velocity / Low Risk"
SEGMENT_SEASONAL = "Seasonal Transactors"
SEGMENT_STRUGGLING = "Struggling Survivors"
SEGMENT_UNKNOWN = "Unclassified"

_BEHAVIORAL_FEATURES = [
    "tpv",
    "days_past_due",
    "late_payment_rate",
    "payment_ratio",
    "mora_months",
    "mora_month_concentration",
    "payment_volatility",
]


class SegmentationModel:
    """
    Unsupervised K-Means (or DBSCAN) behavioral segmentation model for Loans
    loan portfolios.

    Clusters clients into three business-meaningful profiles drawn from the
    Google Control-de-Mora export:

    - High Velocity / Low Risk  : high TPV, near-zero DPD
    - Seasonal Transactors      : mora concentrated in specific calendar months
    - Struggling Survivors      : recurring partial payments with persistent mora

    Column names in both input DataFrames are normalized (stripped, lower-cased,
    spaces → underscores) before any processing, so CSV exports from Google
    Sheets are accepted as-is.

    Usage::

        model = SegmentationModel(n_clusters=3, algorithm='kmeans')
        metrics = model.fit(loan_df, payment_df)
        model.save('models/segmentation')

        # later
        model2 = SegmentationModel.load('models/segmentation')
        segments = model2.predict(new_loan_df, new_payment_df)
    """

    def __init__(
        self,
        n_clusters: int = 3,
        algorithm: str = "kmeans",
        random_state: int = 42,
    ) -> None:
        if algorithm not in ("kmeans", "dbscan"):
            raise ValueError(f"algorithm must be 'kmeans' or 'dbscan', got: {algorithm!r}")
        self.n_clusters = n_clusters
        self.algorithm = algorithm
        self.random_state = random_state
        self.scaler: Optional[RobustScaler] = None
        self.cluster_model: Any = None
        self.feature_columns: List[str] = []
        self.segment_map: Dict[int, str] = {}
        self.cluster_profiles: Dict[int, Dict[str, Any]] = {}
        self.metadata: Dict[str, Any] = {}
        self._train_scaled: Optional[np.ndarray] = None

    @staticmethod
    def _normalize_columns(df: pd.DataFrame) -> None:
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    @staticmethod
    def _find_col(df: pd.DataFrame, *patterns: str) -> Optional[str]:
        for col in df.columns:
            for pat in patterns:
                if pat in col:
                    return col
        return None

    @staticmethod
    def _extract_tpv(payment_df: pd.DataFrame, loan_id_col: str) -> pd.Series:
        """Total payment volume (sum of all payment amounts) per loan."""
        amount_col = SegmentationModel._find_col(
            payment_df, "monto", "amount", "valor", "total_payment", "true_total"
        )
        if amount_col is None:
            return pd.Series(dtype=float, name="tpv")
        payment_df[amount_col] = pd.to_numeric(payment_df[amount_col], errors="coerce")
        return payment_df.groupby(loan_id_col)[amount_col].sum().rename("tpv")

    @staticmethod
    def _extract_late_flags(payment_df: pd.DataFrame, loan_id_col: str) -> pd.DataFrame:
        """
        Compute late payment rate, mora_months, and mora_month_concentration.

        mora_month_concentration is a Herfindahl index (0–1).  A value near 1
        means all late payments fall in a single calendar month (seasonal pattern).
        """
        status_col = SegmentationModel._find_col(payment_df, "status", "estado", "estatus")
        if status_col is None:
            empty_idx = payment_df[loan_id_col].unique()
            return pd.DataFrame(
                {
                    "late_payment_rate": np.nan,
                    "mora_months": np.nan,
                    "mora_month_concentration": np.nan,
                },
                index=empty_idx,
            )

        payment_df["_is_late"] = (
            payment_df[status_col]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["late", "tardio", "tardío", "mora", "atrasado", "en_mora"])
            .astype(int)
        )

        date_col = next((c for c in payment_df.columns if "date" in c or "fecha" in c), None)
        if date_col:
            payment_df[date_col] = pd.to_datetime(payment_df[date_col], errors="coerce", format="mixed")
            payment_df["_month"] = payment_df[date_col].dt.month

        beh = payment_df.groupby(loan_id_col).agg(
            n_payments=("_is_late", "count"),
            n_late=("_is_late", "sum"),
        )
        beh["late_payment_rate"] = np.where(
            beh["n_payments"] > 0,
            beh["n_late"] / beh["n_payments"],
            0.0,
        )

        if "_month" in payment_df.columns:
            late_by_month = (
                payment_df[payment_df["_is_late"] == 1]
                .groupby([loan_id_col, "_month"])
                .size()
                .reset_index(name="cnt")
            )
            if late_by_month.empty:
                beh["mora_months"] = np.nan
                beh["mora_month_concentration"] = np.nan
            else:
                mora_months = (
                    late_by_month.groupby(loan_id_col)["_month"].nunique().rename("mora_months")
                )

                def _herfindahl(grp: pd.DataFrame) -> float:
                    cnt = grp["cnt"]
                    shares = cnt / cnt.sum()
                    return float((shares**2).sum())

                concentration = (
                    late_by_month.groupby(loan_id_col)
                    .apply(_herfindahl, include_groups=False)
                    .rename("mora_month_concentration")
                )
                beh = beh.join(mora_months, how="left").join(concentration, how="left")
        else:
            beh["mora_months"] = np.nan
            beh["mora_month_concentration"] = np.nan

        return beh[["late_payment_rate", "mora_months", "mora_month_concentration"]]

    @staticmethod
    def _extract_payment_volatility(payment_df: pd.DataFrame, loan_id_col: str) -> pd.Series:
        """Standard deviation of payment amounts — proxy for payment irregularity."""
        amount_col = SegmentationModel._find_col(
            payment_df, "monto", "amount", "valor", "total_payment", "true_total"
        )
        if amount_col is None:
            return pd.Series(dtype=float, name="payment_volatility")
        payment_df[amount_col] = pd.to_numeric(payment_df[amount_col], errors="coerce")
        return payment_df.groupby(loan_id_col)[amount_col].std().rename("payment_volatility")

    @staticmethod
    def _extract_payment_ratio(
        payment_df: pd.DataFrame,
        loan_df: pd.DataFrame,
        loan_id_pay: str,
        loan_id_loan: str,
    ) -> pd.Series:
        """Ratio of total actual payments to total scheduled amount per loan."""
        amount_col = SegmentationModel._find_col(
            payment_df, "monto", "amount", "valor", "total_payment", "true_total"
        )
        sched_col = SegmentationModel._find_col(
            loan_df, "total_scheduled", "scheduled", "cuota", "installment"
        )
        if amount_col is None or sched_col is None:
            return pd.Series(dtype=float, name="payment_ratio")

        payment_df[amount_col] = pd.to_numeric(payment_df[amount_col], errors="coerce")
        total_paid = payment_df.groupby(loan_id_pay)[amount_col].sum().rename("_total_paid")
        sched = pd.to_numeric(loan_df.set_index(loan_id_loan)[sched_col], errors="coerce").rename(
            "_scheduled"
        )
        combined = total_paid.to_frame().join(sched, how="left")
        ratio = np.where(
            combined["_scheduled"].fillna(0) > 0,
            combined["_total_paid"] / combined["_scheduled"],
            np.nan,
        )
        return pd.Series(ratio, index=combined.index, name="payment_ratio")

    def build_behavioral_features(
        self,
        loan_df: pd.DataFrame,
        payment_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Merge loan and payment tables into a single behavioral feature DataFrame.

        One row per loan.  Columns produced (subset depends on available input):
          tpv, days_past_due, late_payment_rate, payment_ratio,
          mora_months, mora_month_concentration, payment_volatility

        Both DataFrames are normalized in-place (column names stripped/lowercased).
        """
        self._normalize_columns(loan_df)
        self._normalize_columns(payment_df)

        loan_id_pay = self._find_col(
            payment_df, "loan_id", "prestamo_id", "id_prestamo", "codprestamo"
        )
        loan_id_loan = self._find_col(
            loan_df, "loan_id", "id_prestamo", "prestamo_id", "codprestamo"
        )
        if not (loan_id_pay and loan_id_loan):
            raise ValueError(
                "Cannot identify loan ID column in loan_df or payment_df. "
                "Expected a column containing: loan_id, prestamo_id, id_prestamo, codprestamo"
            )

        dpd_col = self._find_col(
            loan_df,
            "days_past_due",
            "dpd",
            "dias_mora",
            "dias_en_mora",
            "days_in_default",
        )
        feat = loan_df[[loan_id_loan]].copy().rename(columns={loan_id_loan: "loan_id"})
        feat = feat.set_index("loan_id")

        payment_df_copy = payment_df.copy()
        feat["days_past_due"] = (
            pd.to_numeric(loan_df.set_index(loan_id_loan)[dpd_col], errors="coerce").clip(lower=0)
            if dpd_col
            else 0.0
        )

        tpv = self._extract_tpv(payment_df_copy, loan_id_pay)
        tpv.index.name = "loan_id"
        feat = feat.join(tpv, how="left")

        late_feats = self._extract_late_flags(payment_df_copy, loan_id_pay)
        late_feats.index.name = "loan_id"
        feat = feat.join(late_feats, how="left")

        volatility = self._extract_payment_volatility(payment_df_copy, loan_id_pay)
        volatility.index.name = "loan_id"
        feat = feat.join(volatility, how="left")

        pay_ratio = self._extract_payment_ratio(
            payment_df_copy, loan_df.copy(), loan_id_pay, loan_id_loan
        )
        pay_ratio.index.name = "loan_id"
        feat = feat.join(pay_ratio, how="left")

        logger.info(
            "Behavioral features built: %d loans, columns: %s",
            len(feat),
            list(feat.columns),
        )
        return feat.reset_index()

    def _select_available_features(self, feat_df: pd.DataFrame) -> List[str]:
        return [c for c in _BEHAVIORAL_FEATURES if c in feat_df.columns]

    def _build_cluster_profile(
        self, feat_df: pd.DataFrame, labels: np.ndarray
    ) -> Dict[int, Dict[str, Any]]:
        profiles: Dict[int, Dict[str, Any]] = {}
        for lbl in sorted(set(labels)):
            if lbl == -1:
                continue  # DBSCAN noise points
            mask = labels == lbl
            group = feat_df[mask]
            profile: Dict[str, Any] = {}
            for col in self.feature_columns:
                vals = pd.to_numeric(group[col], errors="coerce").dropna()
                profile[col] = round(float(vals.mean()), 6) if len(vals) > 0 else 0.0
            profile["n_members"] = int(mask.sum())
            profiles[lbl] = profile
        return profiles

    def _assign_business_labels(self, profiles: Dict[int, Dict[str, Any]]) -> Dict[int, str]:
        """
        Map cluster IDs to business segment names based on centroid characteristics.

        Assignment order (greedy, applied once each):
          1. Cluster with lowest composite risk (low DPD, high TPV)
             → High Velocity / Low Risk
          2. Among the rest: cluster with highest mora_month_concentration
             → Seasonal Transactors
          3. All remaining clusters → Struggling Survivors
        """
        if not profiles:
            return {}

        cluster_ids = list(profiles.keys())

        def _get(profile: Dict[str, Any], key: str, default: float = 0.0) -> float:
            return float(profile.get(key, default) or default)

        def _risk_score(cid: int) -> float:
            p = profiles[cid]
            return _get(p, "days_past_due") - _get(p, "tpv") * 0.001

        sorted_by_risk = sorted(cluster_ids, key=_risk_score)
        segment_map: Dict[int, str] = {}

        if len(cluster_ids) == 1:
            segment_map[sorted_by_risk[0]] = SEGMENT_HIGH_VELOCITY
            return segment_map

        hvlr_id = sorted_by_risk[0]
        segment_map[hvlr_id] = SEGMENT_HIGH_VELOCITY
        remaining = sorted_by_risk[1:]

        if len(remaining) == 1:
            segment_map[remaining[0]] = SEGMENT_SEASONAL
            return segment_map

        seasonal_id = max(
            remaining,
            key=lambda cid: _get(profiles[cid], "mora_month_concentration"),
        )
        segment_map[seasonal_id] = SEGMENT_SEASONAL
        for cid in remaining:
            if cid != seasonal_id:
                segment_map[cid] = SEGMENT_STRUGGLING

        return segment_map

    def fit(
        self,
        loan_df: pd.DataFrame,
        payment_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Train the segmentation model on loan and payment data.

        Parameters
        ----------
        loan_df:
            Loan-level DataFrame (Google Control-de-Mora or Loans loan export).
        payment_df:
            Payment-level DataFrame (one row per payment event).

        Returns
        -------
        dict
            Training metadata including segment_distribution and cluster profiles.
        """
        logger.info("Building behavioral features...")
        feat_df = self.build_behavioral_features(loan_df.copy(), payment_df.copy())

        available = self._select_available_features(feat_df)
        if not available:
            raise ValueError(
                f"No behavioral features found in built dataset. "
                f"Expected columns: {_BEHAVIORAL_FEATURES}"
            )
        self.feature_columns = available

        feat_matrix = feat_df[available].copy()
        non_null_mask = feat_matrix.notna().all(axis=1)
        n_opaque = int((~non_null_mask).sum())
        feat_matrix = feat_matrix.loc[non_null_mask]

        min_required = max(self.n_clusters, 3)
        if len(feat_matrix) < min_required:
            raise ValueError(
                f"Insufficient non-null observations for clustering: "
                f"{len(feat_matrix)} rows after dropping NaNs (need >= {min_required})"
            )

        logger.info("Scaling %d observations with %d features...", len(feat_matrix), len(available))
        self.scaler = RobustScaler()
        x_scaled = self.scaler.fit_transform(feat_matrix.values)
        self._train_scaled = None  # stored for DBSCAN predict

        if self.algorithm == "kmeans":
            self.cluster_model = KMeans(
                n_clusters=self.n_clusters,
                random_state=self.random_state,
                n_init="auto",
            )
            labels = self.cluster_model.fit_predict(x_scaled)
            n_clusters = self.n_clusters
            n_noise = 0
        else:
            from sklearn.neighbors import NearestNeighbors

            n_neighbors = min(5, len(feat_matrix) - 1)
            nn = NearestNeighbors(n_neighbors=n_neighbors)
            nn.fit(x_scaled)
            distances, _ = nn.kneighbors(x_scaled)
            eps = float(np.percentile(distances[:, -1], 90))
            self.cluster_model = DBSCAN(
                eps=max(eps, 0.1),
                min_samples=max(3, len(feat_matrix) // 20),
            )
            labels = self.cluster_model.fit_predict(x_scaled)
            self._train_scaled = x_scaled  # needed for nearest-neighbor predict
            n_clusters = int(len(set(labels)) - (1 if -1 in labels else 0))
            n_noise = int((labels == -1).sum())

        self.cluster_profiles = self._build_cluster_profile(feat_matrix, labels)
        self.segment_map = self._assign_business_labels(self.cluster_profiles)

        for cid, profile in self.cluster_profiles.items():
            profile["segment"] = self.segment_map.get(cid, SEGMENT_UNKNOWN)

        distribution = {
            self.segment_map.get(cid, SEGMENT_UNKNOWN): int(profile["n_members"])
            for cid, profile in self.cluster_profiles.items()
        }
        self.metadata = {
            "algorithm": self.algorithm,
            "n_clusters_requested": self.n_clusters,
            "n_clusters_found": n_clusters,
            "n_noise": n_noise,
            "n_opaque_excluded": n_opaque,
            "feature_columns": self.feature_columns,
            "segment_distribution": distribution,
        }
        logger.info("Segmentation complete: %s", distribution)
        return self.metadata

    def predict(self, loan_df: pd.DataFrame, payment_df: pd.DataFrame) -> pd.Series:
        """
        Assign business segment labels to new loan/payment data.

        For K-Means, uses the trained model's ``predict()`` directly.
        For DBSCAN, assigns each new point to the nearest training core sample
        using a k-nearest-neighbor lookup to preserve consistency with the
        original cluster boundaries.

        Returns a Series indexed by loan_id with segment label strings.
        Rows with missing feature values are labelled 'Unclassified'.
        """
        if self.cluster_model is None or self.scaler is None:
            raise RuntimeError("Model not trained or loaded. Call fit() or load() first.")

        feat_df = self.build_behavioral_features(loan_df.copy(), payment_df.copy())
        feat_matrix = feat_df.set_index("loan_id")[self.feature_columns].copy()
        null_mask = feat_matrix.isna().any(axis=1)

        result = pd.Series(SEGMENT_UNKNOWN, index=feat_matrix.index, name="segment")

        clean_idx = feat_matrix.index[~null_mask]
        if len(clean_idx) > 0:
            x_scaled = self.scaler.transform(feat_matrix.loc[clean_idx].values)
            if self.algorithm == "kmeans":
                raw_labels = self.cluster_model.predict(x_scaled)
            else:
                from sklearn.neighbors import NearestNeighbors

                core_sample_indices = self.cluster_model.core_sample_indices_
                training_labels = self.cluster_model.labels_
                core_labels = training_labels[core_sample_indices]
                train_scaled = getattr(self, "_train_scaled", None)
                if train_scaled is None or len(core_sample_indices) == 0:
                    raw_labels = np.full(len(x_scaled), -1, dtype=int)
                else:
                    core_samples = train_scaled[core_sample_indices]
                    nn = NearestNeighbors(n_neighbors=1)
                    nn.fit(core_samples)
                    _, indices = nn.kneighbors(x_scaled)
                    raw_labels = core_labels[indices.ravel()]
            result.loc[clean_idx] = [
                self.segment_map.get(int(lbl), SEGMENT_UNKNOWN) for lbl in raw_labels
            ]

        return result

    def save(self, model_dir: str = "models/segmentation") -> str:
        import joblib

        path = Path(model_dir)
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.scaler, path / "scaler.joblib")
        joblib.dump(self.cluster_model, path / "cluster_model.joblib")
        with open(path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, default=str)
        with open(path / "cluster_profiles.json", "w", encoding="utf-8") as f:
            json.dump(self.cluster_profiles, f, indent=2, default=str)
        with open(path / "segment_map.json", "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in self.segment_map.items()}, f, indent=2)
        if self._train_scaled is not None:
            np.save(path / "train_scaled.npy", self._train_scaled)
        logger.info("Segmentation model saved to %s", path)
        return str(path)

    @classmethod
    def load(cls, model_dir: str = "models/segmentation") -> "SegmentationModel":
        import joblib

        path = Path(model_dir)
        if not path.exists():
            raise FileNotFoundError(f"Model directory not found: {path}")
        instance = cls()
        instance.scaler = joblib.load(path / "scaler.joblib")
        instance.cluster_model = joblib.load(path / "cluster_model.joblib")
        with open(path / "metadata.json", encoding="utf-8") as f:
            instance.metadata = json.load(f)
        with open(path / "cluster_profiles.json", encoding="utf-8") as f:
            instance.cluster_profiles = {int(k): v for k, v in json.load(f).items()}
        with open(path / "segment_map.json", encoding="utf-8") as f:
            instance.segment_map = {int(k): v for k, v in json.load(f).items()}
        instance.feature_columns = instance.metadata.get("feature_columns", [])
        raw_algo = instance.metadata.get("algorithm", "kmeans")
        if raw_algo not in ("kmeans", "dbscan"):
            raise ValueError(
                f"Invalid algorithm in saved metadata: {raw_algo!r}. "
                "Expected 'kmeans' or 'dbscan'."
            )
        instance.algorithm = raw_algo
        raw_n = instance.metadata.get("n_clusters_requested", 3)
        instance.n_clusters = int(raw_n) if isinstance(raw_n, (int, float)) and raw_n >= 1 else 3
        train_scaled_path = path / "train_scaled.npy"
        if train_scaled_path.exists():
            instance._train_scaled = np.load(train_scaled_path)
        logger.info("Segmentation model loaded from %s", path)
        return instance
