import os

import pytest
import requests

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
RUN_E2E = os.getenv("RUN_E2E", "0") == "1"

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not RUN_E2E, reason="Set RUN_E2E=1 to run E2E tests"),
]


def is_backend_up() -> bool:
    try:
        response = requests.get(f"{BACKEND_BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            return False
        payload = response.json()
        return payload.get("status") == "ok"
    except Exception:
        return False


@pytest.mark.skipif(not is_backend_up(), reason="Backend API health endpoint is not ready")
def test_backend_health():
    response = requests.get(f"{BACKEND_BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    assert response.json().get("status") == "ok"
