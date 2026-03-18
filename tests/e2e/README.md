# End-to-End (E2E) Testing

This directory contains E2E tests for both the backend (FastAPI) and frontend (Streamlit) components of the Abaco Loans Analytics platform.

## Purpose
- Ensure robust, high-coverage testing of mission-critical finance workflows
- Validate integration between backend and frontend
- Automate user flows and API interactions

## Structure
- `test_backend_api.py`: Backend integration tests using pytest and requests
- `test_frontend_playwright.py`: Frontend E2E tests using Playwright
- `test_csv_kpi_agent_flow.py`: Real business flow (CSV upload -> KPI cards -> Agent Analysis outputs)

## Setup
1. Install development dependencies:
   ```sh
   python3 -m pip install -r requirements-dev.txt --break-system-packages
   ```
2. Install Playwright browsers:
   ```sh
   python3 -m playwright install
   ```
3. Ensure backend (FastAPI) is running at `http://localhost:8000`
4. Ensure frontend is reachable:
   - Local Docker/dashboard default: `http://localhost:8501`
   - Azure startup default: `http://localhost:8000`
5. Export E2E flags (tests are opt-in):
   ```sh
   export RUN_E2E=1
   # Optional overrides:
   export BACKEND_BASE_URL=http://localhost:8000
   export FRONTEND_BASE_URL=http://localhost:8501
   ```

## Running Tests
To run all E2E tests:
```sh
pytest tests/e2e -m e2e --cov=.
```

## Real Business E2E Flow (Upload CSV -> KPI Calculation -> Agent Analysis + Outputs)
```sh
set -euo pipefail

# 1) Dependencies + browser
python3 -m pip install -r requirements-dev.txt
python3 -m playwright install chromium

# 2) Optional: use real LLM analysis if key is available
# export OPENAI_API_KEY="sk-..."

# 3) Start dashboard page that includes upload + KPI cards + agent analysis
export FRONTEND_BASE_URL="http://127.0.0.1:8501"
export PYTHONPATH=.
export CSV_PATH="data/samples/abaco_sample_data_20260202.csv"
mkdir -p data/agent_outputs
BEFORE_COUNT="$(find data/agent_outputs -maxdepth 1 -type f -name '*_response.json' | wc -l | tr -d ' ')"

nohup streamlit run streamlit_app/pages/3_Portfolio_Dashboard.py \
  --server.port=8501 \
  --server.address=127.0.0.1 \
  > /tmp/abaco_e2e_dashboard.log 2>&1 &
DASH_PID=$!
trap 'kill ${DASH_PID} >/dev/null 2>&1 || true' EXIT

for i in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:8501/_stcore/health" >/dev/null; then
    break
  fi
  sleep 2
done

# 4) Browser E2E: upload CSV -> verify KPIs rendered -> run agent analysis
python3 - <<'PY'
import os
import re
from playwright.sync_api import sync_playwright

url = os.environ["FRONTEND_BASE_URL"]
csv_path = os.environ["CSV_PATH"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60000)

    # Upload CSV
    page.get_by_test_id("stFileUploaderDropzone").locator("input").set_input_files(csv_path)
    page.get_by_text("Data uploaded and validated successfully", exact=False).wait_for(timeout=180000)

    # KPI section visible after load/validation
    page.get_by_text(re.compile("Key Portfolio Metrics", re.I)).first.wait_for(timeout=120000)

    # Run multi-agent analysis (real if OPENAI_API_KEY is set, deterministic fallback otherwise)
    page.get_by_role("button", name=re.compile("Run Agent Analysis", re.I)).click()
    page.get_by_text(re.compile("AI Analysis Results", re.I)).first.wait_for(timeout=240000)
    page.get_by_text(re.compile("Risk Analysis", re.I)).first.wait_for(timeout=240000)

    browser.close()
PY

# 5) Assert outputs were generated and print the latest ones
AFTER_COUNT="$(find data/agent_outputs -maxdepth 1 -type f -name '*_response.json' | wc -l | tr -d ' ')"
test "${AFTER_COUNT}" -gt "${BEFORE_COUNT}"

ls -1t data/agent_outputs/*_response.json | head -n 3
python3 - <<'PY'
import glob
import json
for path in sorted(glob.glob("data/agent_outputs/*_response.json"))[-3:]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print(path, data.get("scenario_name"), data.get("output_key"), data.get("status"))
PY
```

To run the executable business flow test directly:
```sh
RUN_E2E=1 pytest tests/e2e/test_csv_kpi_agent_flow.py -m e2e -v --tb=short
```

## Coverage
- Target: 95%+ code coverage
- Coverage reports generated with pytest-cov

## Notes
- Use fixtures and mocking to isolate tests from external dependencies
- Expand test cases to cover edge cases and critical user flows

## References
- [pytest](https://docs.pytest.org/)
- [pytest-playwright](https://github.com/microsoft/playwright-pytest)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

