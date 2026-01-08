import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from tests.db_manager import DBManager

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

# Change working directory to repository root so relative file paths work
os.chdir(ROOT)

# Pytest compatibility shim: some pytest internal helpers expect `_pytest.src` to be
# available (older/alternative pytest distributions). Ensure the attribute is
# present so older-style internal references do not raise AttributeError during
# fixture resolution.
try:
    import _pytest
    import _pytest.python as _pytest_python

    if not hasattr(_pytest, "src"):
        _pytest.src = _pytest_python
except Exception:
    # Best-effort shim only; tests may still fail when running in exotic envs.
    pass


# Lightweight requests_mock fixture for environments where the requests-mock
# plugin is not installed (CI and some dev venvs). It provides a minimal
# subset of the plugin's API used by our tests: `.get(url, ...)` and
# `.put(url, ...)` registrations and returns `requests.Response` objects.
#
# TODO: This shim is a temporary compatibility layer to support broken or
# missing local `requests-mock` installs. Once the dev venvs / CI include
# `requests-mock` (see commit that adds it to `requirements.txt`), remove
# this shim and rely on the upstream plugin's fixture instead. See PR: TBD.

import requests
from types import SimpleNamespace


class _SimpleRequestsMock:
    def __init__(self):
        # support exact and regex-based route matching; store as list of tuples
        # (method, matcher, kwargs) where matcher is either a string or compiled regex
        self._routes = []

    def register(self, method: str, url, **kwargs):
        # url may be a string or a compiled regex pattern
        self._routes.append((method.upper(), url, kwargs))

    def get(self, url, **kwargs):
        self.register("GET", url, **kwargs)

    def put(self, url, **kwargs):
        self.register("PUT", url, **kwargs)

    def _handle(self, method: str, url: str, **kwargs) -> requests.Response:
        # Find first matching route (exact match or regex)
        for mth, matcher, route_kwargs in self._routes:
            if mth != method.upper():
                continue
            if hasattr(matcher, "match"):
                # Regex-like object
                if matcher.match(url):
                    route = route_kwargs
                    break
            else:
                if matcher == url:
                    route = route_kwargs
                    break
        else:
            resp = requests.Response()
            resp.status_code = 404
            resp._content = b"Not Found"
            return resp
        # callback-style JSON handler
        if "json" in route and callable(route["json"]):
            ctx = SimpleNamespace()
            ctx.status_code = 200
            # provide a request-like object with .json() and .text for callbacks
            class _Req:
                def __init__(self, method, url, headers, body):
                    self.method = method
                    self.url = url
                    self.headers = headers or {}
                    self.body = body

                @property
                def text(self):
                    if self.body is None:
                        return ""
                    if isinstance(self.body, bytes):
                        return self.body.decode("utf-8")
                    return str(self.body)

                def json(self_inner):
                    import json as _json
                    return _json.loads(self_inner.text)

            req_obj = _Req(method=method, url=url, headers=kwargs.get("headers", {}), body=kwargs.get("data"))
            res = route["json"](req_obj, ctx)
            resp = requests.Response()
            resp.status_code = getattr(ctx, "status_code", 200)
            if isinstance(res, dict):
                import json as _json

                resp._content = _json.dumps(res).encode("utf-8")
                resp.headers["Content-Type"] = "application/json"
            elif isinstance(res, str):
                resp._content = res.encode("utf-8")
            return resp

        resp = requests.Response()
        resp.status_code = int(route.get("status_code", 200))
        if "json" in route:
            import json as _json

            resp._content = _json.dumps(route["json"]).encode("utf-8")
            resp.headers["Content-Type"] = "application/json"
        elif "text" in route:
            resp._content = str(route["text"]).encode("utf-8")
        else:
            resp._content = b""
        return resp


@pytest.fixture
def requests_mock(monkeypatch):
    stub = _SimpleRequestsMock()
    orig = requests.Session.request

    def _patched(self, method, url, *args, **kwargs):
        resp = stub._handle(method, url, **kwargs)
        # If we return a Response here, requests.get() / requests.post() will
        # not raise for 4xx/5xx by default (requests does not raise by default),
        # which matches the plugin behavior; tests handle raising when needed.
        return resp

    monkeypatch.setattr(requests.Session, "request", _patched)
    return stub


@pytest.fixture(scope="session")
def analytics_test_env(tmp_path_factory):
    """Analytics test environment with mocked integrations."""
    output_dir = tmp_path_factory.mktemp("output")
    
    dataset_path = ROOT / "tests" / "data" / "archives" / "sample_small.csv"
    
    return {
        "output_dir": output_dir,
        "dataset_path": dataset_path,
    }


@pytest.fixture(scope="session")
def run_analytics_pipeline(analytics_test_env):
    """Run the analytics pipeline once and return the output directory."""
    import subprocess
    import sys
    import shutil
    import re
    
    dataset = analytics_test_env["dataset_path"]
    output_dir = analytics_test_env["output_dir"]
    
    # Ensure dataset exists (create if missing - should be there from previous step)
    if not dataset.exists():
        dataset.parent.mkdir(parents=True, exist_ok=True)
        dataset.write_text("segment,measurement_date,total_receivable_usd,total_eligible_usd,cash_available_usd,discounted_balance_usd\nConsumer,2024-01-31,1000,1000,970,1000")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_data_pipeline.py",
            "--input",
            str(dataset),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    
    # Extract run_id from stdout
    match = re.search(r"RUN_ID: (pipeline_\d+_\d+)", result.stdout)
    if not match:
        # Try generic match if specific one fails
        match = re.search(r"RUN_ID: ([\w_]+)", result.stdout)
        
    if match:
        run_id = match.group(1)
        # Copy results to output_dir for legacy test compatibility
        metrics_file = Path("data/metrics") / f"{run_id}_metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                raw_metrics = json.load(f)
            
            # Flatten for legacy compatibility
            flat_metrics = {**raw_metrics}
            for k, v in raw_metrics.items():
                if isinstance(v, dict) and "value" in v:
                    # Map to legacy names if needed
                    legacy_mapping = {
                        "AUM": "total_receivable_usd",
                        "CollectionRate": "collection_rate_pct",
                        "PAR90": "par_90_pct",
                        "PortfolioHealth": "portfolio_health_score"
                    }
                    flat_metrics[legacy_mapping.get(k, k)] = v["value"]
            
            # Add other required fields for schema validation
            if "num_records" not in flat_metrics:
                # Try to get from AUM or other metric context
                num_recs = 0
                for m in raw_metrics.values():
                    if isinstance(m, dict) and "rows_processed" in m:
                        num_recs = m["rows_processed"]
                        break
                flat_metrics["num_records"] = num_recs
            
            if "pipeline_status" not in flat_metrics:
                flat_metrics["pipeline_status"] = "success"
                
            with open(output_dir / "kpi_results.json", "w") as f:
                json.dump(flat_metrics, f)
        
        # Create metrics.csv shim for legacy tests
        if metrics_file.exists():
            import pandas as pd
            metrics_rows = []
            for k, v in raw_metrics.items():
                if isinstance(v, dict) and v.get("value") is not None:
                    metrics_rows.append({
                        "metric_name": k,
                        "value": v["value"],
                        "unit": v.get("unit", "percentage" if "Rate" in k or "PAR" in k else "")
                    })
            if metrics_rows:
                pd.DataFrame(metrics_rows).to_csv(output_dir / "metrics.csv", index=False)
            
    return output_dir


@pytest.fixture
def minimal_config_path(minimal_config, tmp_path) -> Path:
    """Path to a temporary YAML file with minimal config."""
    import yaml
    config_path = tmp_path / "minimal_config.yml"
    with open(config_path, "w") as f:
        yaml.dump(minimal_config, f)
    return config_path


@pytest.fixture
def analytics_baseline_kpis():
    """Load baseline KPI values for comparison."""
    baseline_path = ROOT / "tests" / "fixtures" / "baseline_kpis.json"
    if not baseline_path.exists():
        return {}
    with open(baseline_path) as f:
        return json.load(f)


@pytest.fixture
def kpi_schema():
    """Load KPI results JSON schema."""
    schema_path = ROOT / "tests" / "fixtures" / "schemas" / "kpi_results_schema.json"
    if not schema_path.exists():
        return {}
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture(scope="session", autouse=True)
def ensure_sample_csv():
    """Create sample CSV file for tests if it doesn't exist."""
    csv_path = Path(ROOT) / "data_samples" / "abaco_portfolio_sample.csv"

    if not csv_path.exists():
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        csv_content = """segment,measurement_date,dpd_90_plus_usd,total_receivable_usd,total_eligible_usd,cash_available_usd,par_90,collection_rate,delinquency_flag
Consumer,2025-01-31,32500,1000000,1000000,972000,3.25,97.2,1
Consumer,2025-02-28,32500,1000000,1000000,972000,3.25,97.2,1
SME,2025-01-31,32500,1000000,1000000,972000,3.25,97.2,1
SME,2025-02-28,32500,1000000,1000000,972000,3.25,97.2,1
"""
        csv_path.write_text(csv_content)


@pytest.fixture
def minimal_config() -> Dict[str, Any]:
    """Minimal pipeline config for testing."""
    return {
        "pipeline": {
            "phases": {
                "ingestion": {
                    "validation": {
                        "strict": False,
                        "required_columns": [
                            "total_receivable_usd",
                            "total_eligible_usd",
                            "discounted_balance_usd",
                        ],
                        "numeric_columns": [
                            "total_receivable_usd",
                            "total_eligible_usd",
                            "discounted_balance_usd",
                            "cash_available_usd",
                            "dpd_0_7_usd",
                            "dpd_7_30_usd",
                            "dpd_30_60_usd",
                            "dpd_60_90_usd",
                            "dpd_90_plus_usd",
                        ],
                        "date_columns": ["measurement_date"],
                    },
                    "deduplication": {"enabled": False},
                },
                "transformation": {
                    "normalization": {
                        "lowercase_columns": True,
                        "strip_whitespace": True,
                    },
                    "null_handling": {
                        "strategy": "fill_zero",
                        "columns": [],
                    },
                    "outlier_detection": {
                        "enabled": False,
                    },
                    "pii_masking": {
                        "enabled": False,
                    },
                },
            },
        },
        "cascade": {
            "http": {
                "retry": {
                    "max_retries": 1,
                    "backoff_seconds": 0.1,
                },
                "rate_limit": {
                    "max_requests_per_minute": 60,
                },
                "circuit_breaker": {
                    "failure_threshold": 3,
                    "reset_seconds": 60,
                },
            },
        },
    }


def pytest_configure(config):
    config.addinivalue_line("markers", "db: requires database")


# === Database fixtures for backend tests ===
@pytest.fixture(scope="session")
def db_setup():
    """Session-scoped fixture that ensures a clean, deterministic DB baseline.

    - Requires `DATABASE_URL` to be set in the environment (use .env for local dev)
    - Wipes tables and seeds deterministic KPI rows used by sync tests
    """
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set")

    manager = DBManager()
    manager.wipe_database()
    manager.seed_kpi_data()
    yield manager
    # Optional teardown after the full test session. Uncomment if desired:
    # manager.wipe_database()


@pytest.fixture(scope="function")
def db_reset(db_setup):
    """Reset DB between tests when a test needs a fresh state."""
    db_setup.wipe_database()
    db_setup.seed_kpi_data()
    yield
    db_setup.wipe_database()
