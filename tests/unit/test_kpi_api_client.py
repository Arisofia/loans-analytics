"""
Unit tests for KPI API Client library.

Tests cover:
- HTTP request/response handling
- Cache validation and expiration
- Error handling and fallbacks
- KPI response parsing
- Singleton pattern
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
import time

# Mock httpx if needed
try:
    import httpx
except ImportError:
    httpx = None


@pytest.fixture
def mock_httpx():
    """Create mock httpx module."""
    if httpx is not None:
        return httpx
    
    mock_module = Mock()
    mock_module.Client = Mock
    mock_module.HTTPError = Exception
    return mock_module


@pytest.fixture
def api_client():
    """Create test API client with mocked httpx."""
    from frontend.streamlit_app.kpi_api_client import KPIAPIClient
    
    client = KPIAPIClient(
        api_url="http://test.local:8000",
        timeout=10,
        cache_ttl=5,
    )
    yield client
    client.close()


@pytest.fixture
def sample_kpi_response():
    """Sample API response with KPI data."""
    return {
        "kpis": [
            {
                "id": "avg_apr",
                "name": "Average APR",
                "value": 12.5,
                "unit": "%",
                "threshold_status": "normal",
                "thresholds": {
                    "warning": 14.0,
                    "critical": 16.0,
                },
                "updated_at": "2025-02-26T10:00:00Z",
            },
            {
                "id": "par_30",
                "name": "PAR 30",
                "value": 8.2,
                "unit": "%",
                "threshold_status": "critical",
                "thresholds": {
                    "warning": 5.0,
                    "critical": 7.0,
                },
                "updated_at": "2025-02-26T10:00:00Z",
            },
            {
                "id": "cac_usd",
                "name": "CAC",
                "value": 45.0,
                "unit": "USD",
                "threshold_status": "not_configured",
                "thresholds": {},
                "updated_at": "2025-02-26T10:00:00Z",
            },
        ],
        "timestamp": "2025-02-26T10:00:00Z",
        "metrics_published": True,
    }


class TestKPIAPIClient:
    """Test suite for KPI API Client."""
    
    def test_client_initialization(self, api_client):
        """Test client creation with custom settings."""
        assert api_client.api_url == "http://test.local:8000"
        assert api_client.timeout == 10
        assert api_client.cache_ttl == 5
        assert api_client._cache == {}
    
    def test_default_api_url_from_env(self, monkeypatch):
        """Test API URL from environment variable."""
        from frontend.streamlit_app.kpi_api_client import KPIAPIClient
        
        monkeypatch.setenv("KPI_API_URL", "http://prod.api:8000")
        client = KPIAPIClient()
        assert client.api_url == "http://prod.api:8000"
        client.close()
    
    def test_default_api_url_fallback(self, monkeypatch):
        """Test fallback API URL when env var not set."""
        from frontend.streamlit_app.kpi_api_client import KPIAPIClient
        
        monkeypatch.delenv("KPI_API_URL", raising=False)
        client = KPIAPIClient()
        assert client.api_url == "http://localhost:8000"
        client.close()
    
    @patch("frontend.streamlit_app.kpi_api_client.httpx")
    def test_get_latest_kpis_success(
        self, mock_httpx, api_client, sample_kpi_response
    ):
        """Test successful KPI fetch."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = sample_kpi_response
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        api_client._httpx_client = mock_client
        
        # Fetch KPIs
        result = api_client.get_latest_kpis()
        
        # Verify
        assert len(result["kpis"]) == 3
        assert result["kpis"][0].name == "Average APR"
        assert result["kpis"][0].value == pytest.approx(12.5)
        assert result["kpis"][0].threshold_status == "normal"
        assert result["metrics_published"] is True
    
    @patch("frontend.streamlit_app.kpi_api_client.httpx")
    def test_get_latest_kpis_with_filter(
        self, mock_httpx, api_client, sample_kpi_response
    ):
        """Test KPI fetch with key filtering."""
        mock_response = Mock()
        mock_response.json.return_value = sample_kpi_response
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        api_client._httpx_client = mock_client
        
        # Fetch with filter
        api_client.get_latest_kpis(
            kpi_keys=["avg_apr", "par_30"],
            portfolio_id="test-portfolio"
        )
        
        # Verify request parameters
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        # Check that params dict contains the expected values
        assert call_args.kwargs["params"]["kpi_keys"] == "avg_apr,par_30"
        assert call_args.kwargs["params"]["portfolio_id"] == "test-portfolio"
    
    @patch("frontend.streamlit_app.kpi_api_client.httpx")
    def test_cache_hit(self, mock_httpx, api_client, sample_kpi_response):
        """Test that cached results are reused."""
        mock_response = Mock()
        mock_response.json.return_value = sample_kpi_response
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        api_client._httpx_client = mock_client
        
        # First fetch
        result1 = api_client.get_latest_kpis()
        assert mock_client.get.call_count == 1
        
        # Second fetch should use cache
        result2 = api_client.get_latest_kpis(use_cache=True)
        assert mock_client.get.call_count == 1  # No additional call
        assert result1 == result2
    
    @patch("frontend.streamlit_app.kpi_api_client.httpx")
    def test_cache_expiration(
        self, mock_httpx, api_client, sample_kpi_response
    ):
        """Test that cache expires after TTL."""
        mock_response = Mock()
        mock_response.json.return_value = sample_kpi_response
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        api_client._httpx_client = mock_client
        api_client.cache_ttl = 1  # 1 second TTL
        
        # First fetch
        api_client.get_latest_kpis()
        assert mock_client.get.call_count == 1
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Second fetch should make new request
        api_client.get_latest_kpis()
        assert mock_client.get.call_count == 2
    
    @patch("frontend.streamlit_app.kpi_api_client.httpx")
    def test_bypass_cache(self, mock_httpx, api_client, sample_kpi_response):
        """Test bypassing cache with use_cache=False."""
        mock_response = Mock()
        mock_response.json.return_value = sample_kpi_response
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        api_client._httpx_client = mock_client
        
        # First fetch
        api_client.get_latest_kpis()
        assert mock_client.get.call_count == 1
        
        # Second fetch with cache disabled
        api_client.get_latest_kpis(use_cache=False)
        assert mock_client.get.call_count == 2
    
    @patch("frontend.streamlit_app.kpi_api_client.httpx")
    def test_critical_kpis_filter(self, mock_httpx, api_client, sample_kpi_response):
        """Test filtering for critical KPIs."""
        mock_response = Mock()
        mock_response.json.return_value = sample_kpi_response
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        api_client._httpx_client = mock_client
        
        critical = api_client.get_critical_kpis()
        assert len(critical) == 1
        assert critical[0].name == "PAR 30"
        assert critical[0].is_critical() is True
    
    @patch("frontend.streamlit_app.kpi_api_client.httpx")
    def test_warning_kpis_filter(self, mock_httpx, api_client, sample_kpi_response):
        """Test filtering for warning KPIs."""
        # Modify sample to have warning KPI
        sample = sample_kpi_response.copy()
        sample["kpis"][0]["threshold_status"] = "warning"
        
        mock_response = Mock()
        mock_response.json.return_value = sample
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        api_client._httpx_client = mock_client
        
        warning = api_client.get_warning_kpis()
        assert len(warning) == 1
        assert warning[0].is_warning() is True
    
    @patch("frontend.streamlit_app.kpi_api_client.httpx")
    def test_kpi_summary(self, mock_httpx, api_client, sample_kpi_response):
        """Test KPI status summary."""
        mock_response = Mock()
        mock_response.json.return_value = sample_kpi_response
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        api_client._httpx_client = mock_client
        
        summary = api_client.get_kpi_summary()
        assert summary["normal"] == 1
        assert summary["critical"] == 1
        assert summary["not_configured"] == 1
        assert summary["warning"] == 0
    
    @patch("frontend.streamlit_app.kpi_api_client.httpx")
    def test_get_single_kpi(self, mock_httpx, api_client):
        """Test fetching single KPI."""
        kpi_response = {
            "id": "avg_apr",
            "name": "Average APR",
            "value": 12.5,
            "unit": "%",
            "threshold_status": "normal",
            "thresholds": {"warning": 14.0, "critical": 16.0},
            "updated_at": "2025-02-26T10:00:00Z",
        }
        
        mock_response = Mock()
        mock_response.json.return_value = kpi_response
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        api_client._httpx_client = mock_client
        
        kpi = api_client.get_kpi_value("avg_apr")
        assert kpi.name == "Average APR"
        assert kpi.is_normal() is True
        assert kpi.is_configured() is True
    
    @patch("frontend.streamlit_app.kpi_api_client.httpx")
    def test_error_handling_connection(self, mock_httpx, api_client):
        """Test connection error handling."""
        # Create a mock HTTPError
        mock_httpx.HTTPError = Exception  # Use Exception as HTTPError
        http_error = Exception("Connection refused")
        
        mock_client = Mock()
        mock_client.get.side_effect = http_error
        api_client._httpx_client = mock_client
        
        with pytest.raises(ConnectionError):
            api_client.get_latest_kpis()
    
    @patch("frontend.streamlit_app.kpi_api_client.httpx")
    def test_error_handling_invalid_response(self, mock_httpx, api_client):
        """Test invalid response handling."""
        # Create a mock HTTPError
        mock_httpx.HTTPError = Exception
        
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        api_client._httpx_client = mock_client
        
        with pytest.raises(ValueError):
            api_client.get_latest_kpis()
    
    def test_clear_cache(self, api_client):
        """Test cache clearing."""
        # Manually add cache entry
        api_client._cache["test_key"] = ("test_value", time.time())
        assert len(api_client._cache) == 1
        
        api_client.clear_cache()
        assert len(api_client._cache) == 0
    
    def test_context_manager(self):
        """Test context manager support."""
        from frontend.streamlit_app.kpi_api_client import KPIAPIClient
        
        with KPIAPIClient() as client:
            assert client is not None
            assert client.api_url == "http://localhost:8000"


class TestKPIResponse:
    """Test suite for KPI response dataclass."""
    
    def test_status_checks_normal(self):
        """Test status checking methods."""
        from frontend.streamlit_app.kpi_api_client import KPIResponse
        
        kpi = KPIResponse(
            id="test",
            name="Test KPI",
            value=50.0,
            unit="unit",
            threshold_status="normal",
        )
        
        assert kpi.is_normal() is True
        assert kpi.is_warning() is False
        assert kpi.is_critical() is False
        assert kpi.is_configured() is True
    
    def test_status_checks_critical(self):
        """Test critical status check."""
        from frontend.streamlit_app.kpi_api_client import KPIResponse
        
        kpi = KPIResponse(
            id="test",
            name="Test KPI",
            value=99.0,
            unit="unit",
            threshold_status="critical",
        )
        
        assert kpi.is_critical() is True
        assert kpi.is_normal() is False
        assert kpi.is_configured() is True
    
    def test_status_checks_not_configured(self):
        """Test not configured status."""
        from frontend.streamlit_app.kpi_api_client import KPIResponse
        
        kpi = KPIResponse(
            id="test",
            name="Test KPI",
            value=50.0,
            unit="unit",
            threshold_status="not_configured",
        )
        
        assert kpi.is_configured() is False
        assert kpi.is_normal() is False
        assert kpi.is_critical() is False


class TestSingletonPattern:
    """Test singleton pattern for client."""
    
    def test_singleton_instance(self):
        """Test that get_client returns same instance."""
        from frontend.streamlit_app.kpi_api_client import get_client
        
        client1 = get_client()
        client2 = get_client()
        assert client1 is client2
    
    def test_singleton_with_parameters(self):
        """Test singleton parameter handling."""
        from frontend.streamlit_app.kpi_api_client import (
            get_client,
            _client_instance,
        )
        
        # Reset singleton
        import frontend.streamlit_app.kpi_api_client as client_module
        client_module._client_instance = None
        
        client = get_client(api_url="http://custom:8000")
        assert client.api_url == "http://custom:8000"
