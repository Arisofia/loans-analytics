"""Cascade-specific helpers for fetching exports via Playwright."""

import logging
from typing import Optional

import backoff
from playwright.sync_api import TimeoutError, sync_playwright

LOG = logging.getLogger("cascade_client")


class CascadeClient:
    def __init__(self, session_cookie: str, cookie_name: str = "session", user_agent: Optional[str] = None):
        self.session_cookie = session_cookie
        self.cookie_name = cookie_name
        self.user_agent = user_agent
        self.domain = ".cascadedebt.com"

    def _context_args(self):
        args = {"locale": "en-US"}
        if self.user_agent:
            args["user_agent"] = self.user_agent
        return args

    @backoff.on_exception(backoff.expo, (TimeoutError, Exception), max_time=60)
    def _fetch_once(self, page, export_url: str) -> str:
        responses = []

        def capture_response(resp):
            responses.append(resp)

        page.on("response", capture_response)
        page.goto(export_url, wait_until="networkidle")
        page.wait_for_timeout(1000)

        for response in reversed(responses):
            content_type = (response.headers.get("content-type") or "").lower()
            if "csv" in content_type or "octet-stream" in content_type:
                try:
                    text = response.text()
                    if text and len(text) > 100:
                        return text
                except TimeoutError:
                    LOG.warning("Timeout reading CSV response %s", response.url)

        try:
            csv_text = page.evaluate("""() => {
                const pre = document.querySelector('pre');
                if (pre) return pre.innerText;
                return document.body ? document.body.innerText : '';
            }""")
        except Exception as exc:
            LOG.warning("Fallback evaluation failed: %s", exc)
            csv_text = ""

        if not csv_text or len(csv_text) < 100:
            raise RuntimeError("Unable to extract CSV payload")

        return csv_text

    def fetch_csv(self, export_url: str) -> str:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(**self._context_args())
            cookie = {
                "name": self.cookie_name,
                "value": self.session_cookie,
                "domain": self.domain,
                "path": "/",
                "httpOnly": True,
                "secure": True,
            }
            try:
                context.add_cookies([cookie])
            except Exception as exc:
                LOG.warning("Failed to add Cascade session cookie: %s", exc)
            page = context.new_page()
            page.set_default_timeout(60_000)
            try:
                return self._fetch_once(page, export_url)
            finally:
                page.close()
                context.close()
                browser.close()
