import pytest
import requests


def is_backend_up():
    try:
        requests.get("http://localhost:8000/users", timeout=2)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not is_backend_up(), reason="Backend API not running")
def test_get_users():
    response = requests.get("http://localhost:8000/users")
    assert response.status_code == 200
    assert len(response.json()) > 0
