"""Tests for the DefaultRiskModel and /predict/default endpoint."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


def _make_mock_classifier(proba_values):
    """Create a mock XGBClassifier whose predict_proba returns *proba_values*.

    Parameters
    ----------
    proba_values : list[float]
        Default probabilities (column-1) for each sample.
    """
    mock = MagicMock()
    arr = np.array([[1 - p, p] for p in proba_values])
    mock.predict_proba.return_value = arr
    mock.get_booster.return_value = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# Unit tests for DefaultRiskModel
# ---------------------------------------------------------------------------
class TestDefaultRiskModel:
    """Tests for python.models.default_risk_model.DefaultRiskModel."""

    def test_import(self):
        """Module is importable."""
        from backend.python.models.default_risk_model import FEATURE_COLUMNS, DefaultRiskModel

        assert DefaultRiskModel is not None
        assert len(FEATURE_COLUMNS) > 0

    def test_load_file_not_found(self):
        """Raises FileNotFoundError when model file is missing."""
        from backend.python.models.default_risk_model import DefaultRiskModel

        with pytest.raises(FileNotFoundError):
            DefaultRiskModel.load("/nonexistent/path/model.ubj")

    def test_predict_proba(self):
        """predict_proba returns a float in [0, 1]."""
        from backend.python.models.default_risk_model import ALL_FEATURES, DefaultRiskModel

        mock_clf = _make_mock_classifier([0.42])
        model = DefaultRiskModel(model=mock_clf)
        loan = {col: 1.0 for col in ALL_FEATURES}

        prob = model.predict_proba(loan)

        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0

    def test_predict_proba_high(self):
        """High probability returned correctly."""
        from backend.python.models.default_risk_model import DefaultRiskModel

        mock_clf = _make_mock_classifier([0.95])
        model = DefaultRiskModel(model=mock_clf)

        prob = model.predict_proba({"principal_amount": 100})
        assert isinstance(prob, float)
        assert prob >= 0.9

    def test_predict_proba_low(self):
        """Low probability returned correctly."""
        from backend.python.models.default_risk_model import DefaultRiskModel

        mock_clf = _make_mock_classifier([0.01])
        model = DefaultRiskModel(model=mock_clf)

        prob = model.predict_proba({"principal_amount": 100})
        assert isinstance(prob, float)
        assert prob <= 0.05

    def test_predict_proba_not_loaded_raises(self):
        """predict_proba raises RuntimeError when model is None."""
        from backend.python.models.default_risk_model import DefaultRiskModel

        model = DefaultRiskModel(model=None)

        with pytest.raises(RuntimeError, match="not trained or loaded"):
            model.predict_proba({"principal_amount": 100})

    def test_predict_batch(self):
        """predict_batch returns predictions for multiple loans."""
        from backend.python.models.default_risk_model import DefaultRiskModel

        mock_clf = _make_mock_classifier([0.3, 0.7])
        model = DefaultRiskModel(model=mock_clf)
        loans = [{"principal_amount": 100}, {"principal_amount": 200}]

        probs = model.predict_batch(loans)
        assert len(probs) == 2

    def test_feature_columns_alias(self):
        """FEATURE_COLUMNS is an alias for ALL_FEATURES."""
        from backend.python.models.default_risk_model import ALL_FEATURES, FEATURE_COLUMNS

        assert FEATURE_COLUMNS == ALL_FEATURES

    def test_metadata_empty_on_init(self):
        """Model starts with empty metadata."""
        from backend.python.models.default_risk_model import DefaultRiskModel

        model = DefaultRiskModel()
        assert model.metadata == {}
        assert model.model is None


# ---------------------------------------------------------------------------
# Tests for API models
# ---------------------------------------------------------------------------
class TestPredictionModels:
    """Tests for DefaultPredictionRequest/Response Pydantic models."""

    def test_request_model(self):
        from backend.python.apps.analytics.api.models import DefaultPredictionRequest

        req = DefaultPredictionRequest(
            loan_amount=50000.0,
            interest_rate=12.5,
            term_months=24,
        )
        assert req.loan_amount == 50000.0
        assert req.ltv_ratio == 0.0  # default

    def test_response_model(self):
        from backend.python.apps.analytics.api.models import DefaultPredictionResponse

        resp = DefaultPredictionResponse(
            probability=0.42,
            risk_level="medium",
            model_version="xgb_v1",
        )
        assert resp.probability == 0.42
        assert resp.risk_level == "medium"


# ---------------------------------------------------------------------------
# Tests for /predict/default endpoint
# ---------------------------------------------------------------------------
class TestPredictEndpoint:
    """Tests for the /predict/default API endpoint."""

    def test_predict_default_no_model(self):
        """Returns 503 when model is not loaded."""
        try:
            from fastapi.testclient import TestClient

            from backend.python.apps.analytics.api.main import app

            if app is None:
                pytest.skip("FastAPI app not initialized")

            client = TestClient(app)
        except ImportError:
            pytest.skip("FastAPI not available")

        # Clear model cache to force reload
        from backend.python.apps.analytics.api import main as main_mod

        if hasattr(main_mod, "_risk_model_cache"):
            main_mod._risk_model_cache.clear()

        with patch.object(Path, "exists", return_value=False):
            resp = client.post(
                "/predict/default",
                json={
                    "loan_amount": 50000,
                    "interest_rate": 12.5,
                    "term_months": 24,
                },
            )
        assert resp.status_code == 503

    def test_predict_default_with_model(self):
        """Returns 200 with valid prediction when model is loaded."""
        try:
            from fastapi.testclient import TestClient

            from backend.python.apps.analytics.api.main import app

            if app is None:
                pytest.skip("FastAPI app not initialized")

            client = TestClient(app)
        except ImportError:
            pytest.skip("FastAPI not available")

        from backend.python.apps.analytics.api import main as main_mod

        mock_model = MagicMock()
        mock_model.predict_proba.return_value = 0.35

        main_mod._risk_model_cache["model"] = mock_model

        try:
            resp = client.post(
                "/predict/default",
                json={
                    "loan_amount": 50000,
                    "interest_rate": 12.5,
                    "term_months": 24,
                    "ltv_ratio": 75.0,
                    "dti_ratio": 40.0,
                    "credit_score": 650,
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "probability" in data
            assert "risk_level" in data
            assert data["risk_level"] == "medium"
        finally:
            main_mod._risk_model_cache.clear()
