import pytest
import requests
import os

sync_playwright = pytest.importorskip(
    "playwright.sync_api",
    reason="playwright is required only for optional e2e tests",
).sync_playwright

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:8501")
RUN_E2E = os.getenv("RUN_E2E", "0") == "1"

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not RUN_E2E, reason="Set RUN_E2E=1 to run E2E tests"),
]


def is_frontend_up() -> bool:
    try:
        response = requests.get(FRONTEND_BASE_URL, timeout=3)
        return response.status_code < 500
    except Exception:
        return False


@pytest.mark.skipif(not is_frontend_up(), reason="Streamlit frontend not running")
def test_frontend_home_loads():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(FRONTEND_BASE_URL, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_selector("#root", state="attached", timeout=20000)
        page.wait_for_function(
            "document.querySelector('#root') && document.querySelector('#root').children.length > 0",
            timeout=30000,
        )
        assert page.url.startswith(FRONTEND_BASE_URL)
        assert page.locator("#root").count() == 1
        browser.close()
