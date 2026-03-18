from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


def _load_portfolio_dashboard_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "frontend"
        / "streamlit_app"
        / "pages"
        / "3_Portfolio_Dashboard.py"
    )
    spec = importlib.util.spec_from_file_location("portfolio_dashboard_page", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def dashboard():
    return _load_portfolio_dashboard_module()


def test_canonicalize_status_aliases(dashboard):
    assert dashboard._canonicalize_status("current") == "active"
    assert dashboard._canonicalize_status("paid_off") == "closed"
    assert dashboard._canonicalize_status("mora") == "delinquent"
    assert dashboard._canonicalize_status("charged_off") == "defaulted"
    assert dashboard._canonicalize_status("weird_status") == "unknown"


def test_get_exposure_series_priority(dashboard):
    df = pd.DataFrame(
        {
            "outstanding_balance": [100.0, None, None],
            "current_balance": [90.0, 70.0, None],
            "principal_amount": [80.0, 60.0, 50.0],
        }
    )
    exposure = dashboard._get_exposure_series(df)
    assert exposure.tolist() == [100.0, 70.0, 50.0]


def test_calculate_portfolio_metrics_with_active_exposure_split(dashboard):
    df = pd.DataFrame(
        {
            "loan_id": ["L1", "L2", "L3", "L4"],
            "principal_amount": [120.0, 220.0, 80.0, 150.0],
            "outstanding_balance": [100.0, 200.0, None, None],
            "current_balance": [90.0, 190.0, 50.0, None],
            "interest_rate": [0.10, 0.25, 0.20, 0.30],
            "term_months": [12, 12, 12, 12],
            "origination_date": pd.to_datetime(
                ["2025-01-01", "2025-01-01", "2025-01-01", "2025-01-01"]
            ),
            "current_status": ["active", "closed", "delinquent", "defaulted"],
            "risk_score": [0.10, 0.00, 0.50, 0.90],
            "days_past_due": [0, 0, 40, 120],
            "last_payment_amount": [90.0, 0.0, 30.0, 20.0],
            "total_scheduled": [100.0, 0.0, 80.0, 70.0],
            "borrower_id_number": ["A", "X", "A", "B"],
            "payment_history_json": ["[]", "[]", "[]", "[]"],
        }
    )

    metrics = dashboard.calculate_portfolio_metrics(df)

    assert metrics["total_loans_all"] == 4
    assert metrics["total_loans"] == 3
    assert metrics["closed_loans"] == 1
    assert metrics["total_portfolio"] == pytest.approx(300.0)
    assert metrics["weighted_avg_rate"] == pytest.approx(65.0 / 300.0)
    assert metrics["par_30_rate"] == pytest.approx((200.0 / 300.0) * 100.0)
    assert metrics["par_90_rate"] == pytest.approx((150.0 / 300.0) * 100.0)
    assert metrics["default_count"] == 1
    assert metrics["default_rate"] == pytest.approx((1.0 / 3.0) * 100.0)
    assert metrics["loss_rate"] == pytest.approx((150.0 / 300.0) * 100.0)
    assert metrics["collections_rate"] == pytest.approx((140.0 / 250.0) * 100.0)
    assert metrics["recovery_rate"] == pytest.approx((20.0 / 150.0) * 100.0)
    assert metrics["cash_on_hand"] == pytest.approx(140.0)
    assert metrics["active_borrowers"] == 2
    assert metrics["repeat_borrower_rate"] == pytest.approx(50.0)
    assert metrics["status_distribution"] == {"active": 1, "delinquent": 1, "defaulted": 1}


def test_kpi_methodology_rows_include_new_metrics(dashboard):
    metrics = {
        "total_portfolio": 1_000.0,
        "weighted_avg_rate": 0.12,
        "risk_score_sum": 0.9,
        "total_loans": 10,
        "dpd_30_count": 2,
        "dpd_60_count": 1,
        "dpd_90_count": 1,
        "par_30_amount": 150.0,
        "par_30_rate": 15.0,
        "par_90_amount": 80.0,
        "par_90_rate": 8.0,
        "default_count": 1,
        "default_rate": 10.0,
        "default_exposure": 70.0,
        "collections_received": 90.0,
        "collections_scheduled": 120.0,
        "collections_rate": 75.0,
        "default_collections": 20.0,
        "recovery_rate": 28.57,
        "expected_loss": 110.0,
        "expected_loss_rate": 11.0,
    }
    rows = dashboard._kpi_methodology_rows(metrics)
    labels = {row["KPI"] for row in rows}
    assert {"PAR 90", "Default Rate", "Collections Rate", "Recovery Rate"}.issubset(labels)


# ---------------------------------------------------------------------------
# _fetch_nsm_data – SSRF guard: unsafe URLs must be blocked without HTTP call
# ---------------------------------------------------------------------------


class TestFetchNsmDataSsrfGuard:
    """Verify that _fetch_nsm_data blocks unsafe URLs before issuing HTTP requests."""

    @pytest.fixture(scope="class")
    def dash(self):
        return _load_portfolio_dashboard_module()

    def test_private_ip_blocked_without_http_call(self, dash):
        """A private-range IP URL must be rejected and requests.get must not be called."""
        with patch.object(dash.requests, "get") as mock_get:
            result = dash._fetch_nsm_data("http://192.168.1.1/analytics/nsm")
        assert result is None
        mock_get.assert_not_called()

    def test_localhost_blocked_without_http_call(self, dash):
        """localhost resolves to a private address and must be blocked."""
        with patch.object(dash.requests, "get") as mock_get:
            result = dash._fetch_nsm_data("http://127.0.0.1/analytics/nsm")
        assert result is None
        mock_get.assert_not_called()

    def test_invalid_scheme_blocked_without_http_call(self, dash):
        """A URL with an unsupported scheme (ftp://) must be rejected."""
        with patch.object(dash.requests, "get") as mock_get:
            result = dash._fetch_nsm_data("ftp://example.com/analytics/nsm")
        assert result is None
        mock_get.assert_not_called()

    def test_valid_public_url_passes_through(self, dash):
        """A publicly-routable HTTPS URL must be allowed through to requests.get."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"latest_period": None}
        mock_response.raise_for_status = MagicMock()
        with patch.object(dash.requests, "get", return_value=mock_response) as mock_get:
            result = dash._fetch_nsm_data("https://api.example.com/analytics/nsm")
        mock_get.assert_called_once()
        assert result == {"latest_period": None}
