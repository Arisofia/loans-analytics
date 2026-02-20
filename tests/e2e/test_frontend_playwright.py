import pytest
from playwright.sync_api import sync_playwright
import socket


def is_frontend_up():
    s = socket.socket()
    try:
        s.connect(("localhost", 8501))
        s.close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not is_frontend_up(), reason="Streamlit frontend not running")
def test_login():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto("http://localhost:8501/")
        page.fill("input[name=username]", "testuser")
        page.fill("input[name=password]", "testpassword")
        page.click("button[type=submit]")
        assert page.url == "http://localhost:8501/dashboard"
        browser.close()
