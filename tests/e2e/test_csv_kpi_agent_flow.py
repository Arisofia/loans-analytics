"""Business E2E flow: CSV upload -> KPI render -> Agent analysis + outputs."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
import requests


sync_playwright = pytest.importorskip(
    "playwright.sync_api",
    reason="playwright is required only for optional e2e tests",
).sync_playwright

RUN_E2E = os.getenv("RUN_E2E", "0") == "1"
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not RUN_E2E, reason="Set RUN_E2E=1 to run E2E tests"),
]


def _frontend_ready() -> bool:
    url = os.getenv("FRONTEND_BASE_URL", "http://localhost:8501")
    try:
        return requests.get(url, timeout=3).status_code < 500
    except Exception:
        return False


@pytest.mark.skipif(
    not _frontend_ready(),
    reason="Frontend dashboard is not ready",
)
def test_csv_upload_kpi_agent_flow(
    frontend_base_url: str,
    csv_path: Path,
    clean_agent_outputs: dict[str, set[Path]],
    agent_outputs_dir: Path,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(frontend_base_url, wait_until="domcontentloaded", timeout=60000)

        # Streamlit uploader file input is nested inside stFileUploaderDropzone.
        page.get_by_test_id("stFileUploaderDropzone").locator("input").set_input_files(str(csv_path))
        page.get_by_text(
            re.compile("Data uploaded and validated successfully", re.IGNORECASE)
        ).first.wait_for(timeout=180000)

        # KPI cards should be visible after upload.
        page.get_by_text(re.compile("Key Portfolio Metrics", re.IGNORECASE)).first.wait_for(
            timeout=120000
        )
        page.get_by_text(re.compile("Total Portfolio Value", re.IGNORECASE)).first.wait_for(
            timeout=120000
        )

        # Execute agent analysis.
        page.get_by_role("button", name=re.compile("Run Agent Analysis", re.IGNORECASE)).click()
        page.get_by_text(re.compile("AI Analysis Results", re.IGNORECASE)).first.wait_for(
            timeout=240000
        )
        page.get_by_text(re.compile("Risk Analysis", re.IGNORECASE)).first.wait_for(timeout=240000)
        browser.close()

    after = set(agent_outputs_dir.glob("*_response.json"))
    created = sorted(after - clean_agent_outputs["before"])
    assert created, "Expected new agent output files after running agent analysis"

    latest_payloads = []
    for path in created[-3:]:
        with open(path, encoding="utf-8") as f:
            latest_payloads.append((path, json.load(f)))

    for path, payload in latest_payloads:
        assert payload.get("status") == "success", f"Unexpected status in {path}"
        assert payload.get("scenario_name") == "loan_risk_review", f"Scenario missing in {path}"
        assert payload.get("output_key"), f"output_key missing in {path}"
        assert payload.get("response"), f"response missing in {path}"

    expect_fallback = os.getenv("EXPECT_FALLBACK_MODE", "0") == "1"
    if expect_fallback:
        for path, payload in latest_payloads:
            assert payload.get("analysis_mode") in {
                "local_fallback",
                "local_fallback_after_error",
            }, f"Expected fallback mode in {path}, got {payload.get('analysis_mode')}"
