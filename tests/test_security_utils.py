from frontend.streamlit_app.utils.security import sanitize_api_base

def test_sanitize_valid_host(monkeypatch):
    monkeypatch.setattr('socket.getaddrinfo', lambda *args, **kwargs: [(2, 1, 6, '', ('93.184.216.34', 0))])
    assert sanitize_api_base('http://example.com') == 'http://example.com'
    assert sanitize_api_base('https://example.com') == 'https://example.com'
    assert sanitize_api_base('https://example.com/path?q=1') == 'https://example.com'

def test_sanitize_invalid_scheme():
    assert sanitize_api_base('ftp://example.com') is None

def test_sanitize_invalid_netloc():
    assert sanitize_api_base('http:///nohost') is None

def test_sanitize_invalid_input_type():
    assert sanitize_api_base(None) is None

def test_private_blocked_by_default(monkeypatch):
    assert sanitize_api_base('http://10.0.0.1') is None

def test_private_allowed_via_env(monkeypatch):
    monkeypatch.setenv('ALLOW_PRIVATE_API_BASE', '1')
    try:
        assert sanitize_api_base('http://10.0.0.1') == 'http://10.0.0.1'
    finally:
        monkeypatch.delenv('ALLOW_PRIVATE_API_BASE', raising=False)

def test_link_local_blocked_by_default():
    assert sanitize_api_base('http://169.254.169.254') is None

def test_loopback_blocked_by_default():
    assert sanitize_api_base('http://127.0.0.1') is None

def test_loopback_allowed_via_env(monkeypatch):
    monkeypatch.setenv('ALLOW_PRIVATE_API_BASE', '1')
    try:
        assert sanitize_api_base('http://127.0.0.1') == 'http://127.0.0.1'
    finally:
        monkeypatch.delenv('ALLOW_PRIVATE_API_BASE', raising=False)
