from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

def _make_mock_classifier(proba_values):
    mock = MagicMock()
    arr = np.array([[1 - p, p] for p in proba_values])
    mock.predict_proba.return_value = arr
    mock.get_booster.return_value = MagicMock()
    return mock

class TestDefaultRiskModel:

    def test_import(self):
        from backend.python.models.default_risk_model import FEATURE_COLUMNS, DefaultRiskModel
        assert len(FEATURE_COLUMNS) > 0

    def test_load_file_not_found(self):
        from backend.python.models.default_risk_model import DefaultRiskModel
        with pytest.raises(FileNotFoundError):
            DefaultRiskModel.load('/nonexistent/path/model.ubj')

    def test_predict_proba(self):
        from backend.python.models.default_risk_model import ALL_FEATURES, DefaultRiskModel
        mock_clf = _make_mock_classifier([0.42])
        model = DefaultRiskModel(model=mock_clf)
        loan = dict.fromkeys(ALL_FEATURES, 1.0)
        prob = model.predict_proba(loan)
        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0

    def test_predict_proba_high(self):
        from backend.python.models.default_risk_model import ALL_FEATURES, DefaultRiskModel
        mock_clf = _make_mock_classifier([0.95])
        model = DefaultRiskModel(model=mock_clf)
        loan = dict.fromkeys(ALL_FEATURES, 1.0)
        prob = model.predict_proba(loan)
        assert isinstance(prob, float)
        assert prob >= 0.9

    def test_predict_proba_low(self):
        from backend.python.models.default_risk_model import ALL_FEATURES, DefaultRiskModel
        mock_clf = _make_mock_classifier([0.01])
        model = DefaultRiskModel(model=mock_clf)
        loan = dict.fromkeys(ALL_FEATURES, 1.0)
        prob = model.predict_proba(loan)
        assert isinstance(prob, float)
        assert prob <= 0.05

    def test_predict_proba_not_loaded_raises(self):
        from backend.python.models.default_risk_model import ALL_FEATURES, DefaultRiskModel
        model = DefaultRiskModel(model=None)
        loan = dict.fromkeys(ALL_FEATURES, 1.0)
        with pytest.raises(RuntimeError, match='not trained or loaded'):
            model.predict_proba(loan)

    def test_predict_batch(self):
        from backend.python.models.default_risk_model import ALL_FEATURES, DefaultRiskModel
        mock_clf = _make_mock_classifier([0.3, 0.7])
        model = DefaultRiskModel(model=mock_clf)
        loans = [dict.fromkeys(ALL_FEATURES, 1.0), dict.fromkeys(ALL_FEATURES, 2.0)]
        probs = model.predict_batch(loans)
        assert len(probs) == 2

    def test_predict_proba_validates_features(self):
        from backend.python.models.default_risk_model import DefaultRiskModel
        model = DefaultRiskModel(model=_make_mock_classifier([0.5]))
        with pytest.raises(ValueError, match='Missing required features'):
            model.predict_proba({'principal_amount': 100})

    def test_feature_columns_alias(self):
        from backend.python.models.default_risk_model import ALL_FEATURES, FEATURE_COLUMNS
        assert FEATURE_COLUMNS == ALL_FEATURES

    def test_metadata_empty_on_init(self):
        from backend.python.models.default_risk_model import DefaultRiskModel
        model = DefaultRiskModel()
        assert model.metadata == {}
        assert model.model is None

class TestPredictionModels:

    def test_request_model(self):
        from backend.python.apps.analytics.api.models import DefaultPredictionRequest
        req = DefaultPredictionRequest(loan_amount=50000.0, interest_rate=12.5, term_months=24)
        assert req.loan_amount == pytest.approx(50000.0)
        assert req.ltv_ratio == pytest.approx(0.0)

    def test_response_model(self):
        from backend.python.apps.analytics.api.models import DefaultPredictionResponse
        resp = DefaultPredictionResponse(probability=0.42, risk_level='medium', model_version='xgb_v1')
        assert resp.probability == pytest.approx(0.42)
        assert resp.risk_level == 'medium'

class TestPredictEndpoint:

    def test_predict_default_no_model(self):
        try:
            from fastapi.testclient import TestClient
            from backend.python.apps.analytics.api.main import app
        except ImportError:
            pytest.skip('FastAPI not available')
        if app is None:
            pytest.skip('FastAPI app not initialized')
        client = TestClient(app)
        from backend.python.apps.analytics.api import main as main_mod
        if hasattr(main_mod, '_risk_model_cache'):
            main_mod._risk_model_cache.clear()
        with patch.object(Path, 'exists', return_value=False):
            resp = client.post('/predict/default', json={'loan_amount': 50000, 'interest_rate': 12.5, 'term_months': 24})
        assert resp.status_code == 503

    def test_predict_default_with_model(self):
        try:
            from fastapi.testclient import TestClient
            from backend.python.apps.analytics.api.main import app
        except ImportError:
            pytest.skip('FastAPI not available')
        if app is None:
            pytest.skip('FastAPI app not initialized')
        client = TestClient(app)
        from backend.python.apps.analytics.api import main as main_mod
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = 0.35
        main_mod._risk_model_cache['model'] = mock_model
        try:
            resp = client.post('/predict/default', json={'loan_amount': 50000, 'interest_rate': 12.5, 'term_months': 24, 'ltv_ratio': 75.0, 'dti_ratio': 40.0, 'credit_score': 650})
            assert resp.status_code == 200
            data = resp.json()
            assert 'probability' in data
            assert 'risk_level' in data
            assert data['risk_level'] == 'medium'
        finally:
            main_mod._risk_model_cache.clear()
