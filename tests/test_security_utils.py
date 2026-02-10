import os

from streamlit_app.utils.security import sanitize_api_base


def test_sanitize_valid_host():
    assert sanitize_api_base("http://example.com") == "http://example.com"
    assert sanitize_api_base("https://example.com") == "https://example.com"
    assert sanitize_api_base("https://example.com/path?q=1") == "https://example.com"


def test_sanitize_invalid_scheme():
    assert sanitize_api_base("ftp://example.com") is None


def test_sanitize_invalid_netloc():
    assert sanitize_api_base("http:///nohost") is None


def test_private_blocked_by_default(monkeypatch):
    # Point to an IP in private range - use string '10.0.0.1' to simulate
    assert sanitize_api_base("http://10.0.0.1") is None


def test_private_allowed_via_env(monkeypatch):
    monkeypatch.setenv("ALLOW_PRIVATE_API_BASE", "1")
    try:
        assert sanitize_api_base("http://10.0.0.1") == "http://10.0.0.1"
    finally:
        monkeypatch.delenv("ALLOW_PRIVATE_API_BASE", raising=False)
