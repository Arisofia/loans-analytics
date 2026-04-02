import unittest
import numpy as np
import pandas as pd
from backend.loans_analytics.models.segmentation_model import (
    SEGMENT_HIGH_VELOCITY,
    SEGMENT_SEASONAL,
    SEGMENT_STRUGGLING,
    SEGMENT_UNKNOWN,
    SegmentationModel,
)


def _make_loan_df(n: int = 40) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        'loan_id': [f'L{i:03d}' for i in range(n)],
        'days_past_due': rng.integers(0, 120, n).astype(float),
        'total_scheduled': rng.uniform(500, 5000, n),
    })


def _make_payment_df(loan_df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = []
    for _, loan in loan_df.iterrows():
        n_pay = int(rng.integers(2, 7))
        for _ in range(n_pay):
            is_late = rng.random() < 0.3
            rows.append({
                'loan_id': loan['loan_id'],
                'status': 'late' if is_late else 'current',
                'amount': float(rng.uniform(100, 1000)),
                'fecha': f'2025-{int(rng.integers(1, 13)):02d}-15',
            })
    return pd.DataFrame(rows)


class TestSegmentationModelInit(unittest.TestCase):

    def test_default_params(self):
        model = SegmentationModel()
        self.assertEqual(model.n_clusters, 3)
        self.assertEqual(model.algorithm, 'kmeans')
        self.assertIsNone(model.cluster_model)
        self.assertIsNone(model.scaler)

    def test_invalid_algorithm_raises(self):
        with self.assertRaises(ValueError):
            SegmentationModel(algorithm='unknown')

    def test_custom_params_stored(self):
        model = SegmentationModel(n_clusters=4, algorithm='dbscan', random_state=7)
        self.assertEqual(model.n_clusters, 4)
        self.assertEqual(model.algorithm, 'dbscan')
        self.assertEqual(model.random_state, 7)


class TestNormalizeColumns(unittest.TestCase):

    def test_strips_spaces_and_lowercases(self):
        df = pd.DataFrame({'Loan ID': [1], ' Status ': [2], 'MONTO TOTAL': [3]})
        SegmentationModel._normalize_columns(df)
        self.assertIn('loan_id', df.columns)
        self.assertIn('status', df.columns)
        self.assertIn('monto_total', df.columns)


class TestFindCol(unittest.TestCase):

    def test_finds_by_partial_match(self):
        df = pd.DataFrame({'loan_id': [], 'prestamo_monto': []})
        self.assertEqual(SegmentationModel._find_col(df, 'loan_id'), 'loan_id')
        self.assertEqual(SegmentationModel._find_col(df, 'monto'), 'prestamo_monto')

    def test_returns_none_when_not_found(self):
        df = pd.DataFrame({'a': [], 'b': []})
        self.assertIsNone(SegmentationModel._find_col(df, 'loan_id'))


class TestBuildBehavioralFeatures(unittest.TestCase):

    def setUp(self):
        self.loan_df = _make_loan_df(20)
        self.payment_df = _make_payment_df(self.loan_df)
        self.model = SegmentationModel()

    def test_returns_one_row_per_loan(self):
        feat = self.model.build_behavioral_features(
            self.loan_df.copy(), self.payment_df.copy()
        )
        self.assertEqual(len(feat), len(self.loan_df))

    def test_loan_id_column_present(self):
        feat = self.model.build_behavioral_features(
            self.loan_df.copy(), self.payment_df.copy()
        )
        self.assertIn('loan_id', feat.columns)

    def test_expected_columns_present(self):
        feat = self.model.build_behavioral_features(
            self.loan_df.copy(), self.payment_df.copy()
        )
        for col in ['tpv', 'days_past_due', 'late_payment_rate']:
            self.assertIn(col, feat.columns, f'Missing expected column: {col}')

    def test_missing_loan_id_raises(self):
        bad_loan = self.loan_df.rename(columns={'loan_id': 'nope'})
        with self.assertRaises(ValueError):
            self.model.build_behavioral_features(bad_loan, self.payment_df.copy())

    def test_tpv_non_negative(self):
        feat = self.model.build_behavioral_features(
            self.loan_df.copy(), self.payment_df.copy()
        )
        self.assertTrue((feat['tpv'].fillna(0) >= 0).all())

    def test_late_payment_rate_between_0_and_1(self):
        feat = self.model.build_behavioral_features(
            self.loan_df.copy(), self.payment_df.copy()
        )
        rate = feat['late_payment_rate'].dropna()
        self.assertTrue((rate >= 0).all())
        self.assertTrue((rate <= 1).all())

    def test_column_normalisation_accepted(self):
        loan_df = self.loan_df.copy()
        payment_df = self.payment_df.copy()
        loan_df.columns = [c.upper() for c in loan_df.columns]
        payment_df.columns = [c.upper() for c in payment_df.columns]
        feat = self.model.build_behavioral_features(loan_df, payment_df)
        self.assertEqual(len(feat), len(self.loan_df))


class TestSegmentationModelFit(unittest.TestCase):

    def setUp(self):
        self.loan_df = _make_loan_df(60)
        self.payment_df = _make_payment_df(self.loan_df)

    def test_fit_returns_metadata_dict(self):
        model = SegmentationModel(n_clusters=3)
        meta = model.fit(self.loan_df.copy(), self.payment_df.copy())
        self.assertIsInstance(meta, dict)

    def test_metadata_contains_required_keys(self):
        model = SegmentationModel(n_clusters=3)
        meta = model.fit(self.loan_df.copy(), self.payment_df.copy())
        for key in ('algorithm', 'n_clusters_found', 'segment_distribution', 'feature_columns'):
            self.assertIn(key, meta)

    def test_algorithm_recorded(self):
        model = SegmentationModel(n_clusters=3)
        meta = model.fit(self.loan_df.copy(), self.payment_df.copy())
        self.assertEqual(meta['algorithm'], 'kmeans')

    def test_fit_with_dbscan(self):
        model = SegmentationModel(algorithm='dbscan')
        meta = model.fit(self.loan_df.copy(), self.payment_df.copy())
        self.assertIn('n_noise', meta)

    def test_segment_map_uses_valid_business_labels(self):
        model = SegmentationModel(n_clusters=3)
        model.fit(self.loan_df.copy(), self.payment_df.copy())
        valid = {SEGMENT_HIGH_VELOCITY, SEGMENT_SEASONAL, SEGMENT_STRUGGLING, SEGMENT_UNKNOWN}
        self.assertTrue(set(model.segment_map.values()).issubset(valid))

    def test_cluster_profiles_populated(self):
        model = SegmentationModel(n_clusters=3)
        model.fit(self.loan_df.copy(), self.payment_df.copy())
        self.assertGreater(len(model.cluster_profiles), 0)
        for profile in model.cluster_profiles.values():
            self.assertIn('segment', profile)
            self.assertIn('n_members', profile)

    def test_scaler_and_model_set_after_fit(self):
        model = SegmentationModel(n_clusters=3)
        model.fit(self.loan_df.copy(), self.payment_df.copy())
        self.assertIsNotNone(model.scaler)
        self.assertIsNotNone(model.cluster_model)

    def test_insufficient_data_raises(self):
        model = SegmentationModel(n_clusters=5)
        small_loan = _make_loan_df(2)
        small_pay = _make_payment_df(small_loan)
        with self.assertRaises(ValueError):
            model.fit(small_loan, small_pay)

    def test_segment_distribution_sums_to_n_observations(self):
        model = SegmentationModel(n_clusters=3)
        meta = model.fit(self.loan_df.copy(), self.payment_df.copy())
        total_assigned = sum(meta['segment_distribution'].values())
        n_opaque = meta['n_opaque_excluded']
        self.assertEqual(total_assigned + n_opaque, len(self.loan_df))


class TestSegmentationModelPredict(unittest.TestCase):

    def setUp(self):
        self.loan_df = _make_loan_df(60)
        self.payment_df = _make_payment_df(self.loan_df)
        self.model = SegmentationModel(n_clusters=3)
        self.model.fit(self.loan_df.copy(), self.payment_df.copy())

    def test_predict_returns_series(self):
        result = self.model.predict(self.loan_df.copy(), self.payment_df.copy())
        self.assertIsInstance(result, pd.Series)

    def test_predict_indexed_by_loan_id(self):
        result = self.model.predict(self.loan_df.copy(), self.payment_df.copy())
        self.assertEqual(result.index.name, 'loan_id')

    def test_all_labels_are_valid(self):
        result = self.model.predict(self.loan_df.copy(), self.payment_df.copy())
        valid = {SEGMENT_HIGH_VELOCITY, SEGMENT_SEASONAL, SEGMENT_STRUGGLING, SEGMENT_UNKNOWN}
        self.assertTrue(set(result.unique()).issubset(valid))

    def test_predict_before_fit_raises(self):
        model = SegmentationModel()
        with self.assertRaises(RuntimeError):
            model.predict(self.loan_df.copy(), self.payment_df.copy())

    def test_predict_length_matches_input(self):
        result = self.model.predict(self.loan_df.copy(), self.payment_df.copy())
        self.assertEqual(len(result), len(self.loan_df))


class TestBusinessLabelAssignment(unittest.TestCase):

    def test_single_cluster_assigned_high_velocity(self):
        model = SegmentationModel()
        profiles = {
            0: {'tpv': 5000.0, 'days_past_due': 0.0, 'mora_month_concentration': 0.1, 'n_members': 10}
        }
        seg_map = model._assign_business_labels(profiles)
        self.assertEqual(seg_map[0], SEGMENT_HIGH_VELOCITY)

    def test_empty_profiles_returns_empty(self):
        model = SegmentationModel()
        self.assertEqual(model._assign_business_labels({}), {})

    def test_two_clusters_best_risk_gets_high_velocity(self):
        model = SegmentationModel()
        profiles = {
            0: {'tpv': 5000.0, 'days_past_due': 0.0, 'mora_month_concentration': 0.2, 'n_members': 10},
            1: {'tpv': 500.0, 'days_past_due': 90.0, 'mora_month_concentration': 0.9, 'n_members': 5},
        }
        seg_map = model._assign_business_labels(profiles)
        self.assertEqual(seg_map[0], SEGMENT_HIGH_VELOCITY)

    def test_three_clusters_all_different_labels(self):
        model = SegmentationModel()
        profiles = {
            0: {'tpv': 8000.0, 'days_past_due': 0.0, 'mora_month_concentration': 0.1, 'n_members': 20},
            1: {'tpv': 2000.0, 'days_past_due': 30.0, 'mora_month_concentration': 0.9, 'n_members': 15},
            2: {'tpv': 1000.0, 'days_past_due': 60.0, 'mora_month_concentration': 0.3, 'n_members': 10},
        }
        seg_map = model._assign_business_labels(profiles)
        self.assertEqual(seg_map[0], SEGMENT_HIGH_VELOCITY)
        self.assertEqual(seg_map[1], SEGMENT_SEASONAL)
        self.assertEqual(seg_map[2], SEGMENT_STRUGGLING)

    def test_seasonal_cluster_has_highest_mora_concentration(self):
        model = SegmentationModel()
        profiles = {
            0: {'tpv': 9000.0, 'days_past_due': 0.0, 'mora_month_concentration': 0.05, 'n_members': 30},
            1: {'tpv': 500.0, 'days_past_due': 45.0, 'mora_month_concentration': 0.95, 'n_members': 10},
            2: {'tpv': 300.0, 'days_past_due': 80.0, 'mora_month_concentration': 0.40, 'n_members': 8},
        }
        seg_map = model._assign_business_labels(profiles)
        self.assertEqual(seg_map[1], SEGMENT_SEASONAL)


if __name__ == '__main__':
    unittest.main()
