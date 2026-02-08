"""Tests for the DefaultRiskModel and /predict/default endpoint."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Unit tests for DefaultRiskModel
# ---------------------------------------------------------------------------
class TestDefaultRiskModel:
    """Tests for python.models.default_risk_model.DefaultRiskModel."""

    def test_import(self):
        """Module is importable."""
        from python.models.default_risk_model import FEATURE_COLUMNS, DefaultRiskModel

        assert DefaultRiskModel is not None
        assert len(FEATURE_COLUMNS) > 0

    def test_load_file_not_found(self):
        """Raises FileNotFoundError when model file is missing."""
        from python.models.default_risk_model import DefaultRiskModel

        with pytest.raises(FileNotFoundError):
            DefaultRiskModel.load("/nonexistent/path/model.ubj")

    @patch("python.models.default_risk_model.xgb", create=True)
    def test_predict_proba(self):
        """predict_proba returns a float in [0, 1]."""
        from python.models.default_risk_model import FEATURE_COLUMNS, DefaultRiskModel

        mock_booster = MagicMock()
        mock_booster.predict.return_value = np.array([0.42])

        model = DefaultRiskModel(booster=mock_booster)

        loan = {col: 1.0 for col in FEATURE_COLUMNS}

        with patch("python.models.default_risk_model.xgb", create=True) as mock_xgb:
            mock_xgb.DMatrix.return_value = MagicMock()
            mock_booster.predict.return_value = np.array([0.42])

            prob = model.predict_proba(loan)

        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0

    def test_predict_proba_clamps_high(self):
        """Values above 1.0 are clamped to 1.0."""
        from python.models.default_risk_model import DefaultRiskModel

        mock_booster = MagicMock()

        model = DefaultRiskModel(booster=mock_booster)

        with patch("python.models.default_risk_model.xgb", create=True) as mock_xgb:
            mock_xgb.DMatrix.return_value = MagicMock()
            mock_booster.predict.return_value = np.array([1.5])

            prob = model.predict_proba({"loan_amount": 100})

        assert prob == 1.0

    def test_predict_proba_clamps_low(self):
        """Values below 0.0 are clamped to 0.0."""
        from python.models.default_risk_model import DefaultRiskModel

        mock_booster = MagicMock()

        model = DefaultRiskModel(booster=mock_booster)

        with patch("python.models.default_risk_model.xgb", create=True) as mock_xgb:
            mock_xgb.DMatrix.return_value = MagicMock()
            mock_booster.predict.return_value = np.array([-0.1])

            prob = model.predict_proba({"loan_amount": 100})

        assert prob == 0.0

    def test_predict_batch(self):
        """predict_batch returns a list of floats."""
        from python.models.default_risk_model import DefaultRiskModel

        mock_booster = MagicMock()

        model = DefaultRiskModel(booster=mock_booster)

        loans = [{"loan_amount": 100}, {"loan_amount": 200}]

        with patch("python.models.default_risk_model.xgb", create=True) as mock_xgb:
            mock_xgb.DMatrix.return_value = MagicMock()
            mock_booster.predict.return_value = np.array([0.3, 0.7])

            probs = model.predict_batch(loans)

        assert len(probs) == 2
        assert all(isinstance(p, float) for p in probs)
        assert all(0.0 <= p <= 1.0 for p in probs)


# ---------------------------------------------------------------------------
# Tests for API models
# ---------------------------------------------------------------------------
class TestPredictionModels:
    """Tests for DefaultPredictionRequest/Response Pydantic models."""

    def test_request_model(self):
        from python.apps.analytics.api.models import DefaultPredictionRequest

        req = DefaultPredictionRequest(
            loan_amount=50000.0,
            interest_rate=12.5,
            term_months=24,
        )
        assert req.loan_amount == 50000.0
        assert req.ltv_ratio == 0.0  # default

    def test_response_model(self):
        from python.apps.analytics.api.models import DefaultPredictionResponse

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

            from python.apps.analytics.api.main import app

            if app is None:
                pytest.skip("FastAPI app not initialized")

            client = TestClient(app)
        except ImportError:
            pytest.skip("FastAPI not available")

        # Clear model cache to force reload
        from python.apps.analytics.api import main as main_mod

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

            from python.apps.analytics.api.main import app

            if app is None:
                pytest.skip("FastAPI app not initialized")

            client = TestClient(app)
        except ImportError:
            pytest.skip("FastAPI not available")

        from python.apps.analytics.api import main as main_mod

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
