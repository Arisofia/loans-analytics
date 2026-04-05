from __future__ import annotations

import importlib
from decimal import ROUND_HALF_UP, getcontext
from pathlib import Path

import pytest
import toml


@pytest.fixture()
def _clear_api_main_module():
    import sys

    sys.modules.pop("backend.loans_analytics.apps.analytics.api.main", None)
    yield
    sys.modules.pop("backend.loans_analytics.apps.analytics.api.main", None)


def _import_api_main():
    getcontext().rounding = ROUND_HALF_UP
    return importlib.import_module("backend.loans_analytics.apps.analytics.api.main")


def test_production_environment_guard_rejects_mock(monkeypatch, _clear_api_main_module):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("MOCK", "true")
    monkeypatch.setenv("HISTORICAL_CONTEXT_MODE", "REAL")
    monkeypatch.setenv("API_RELOAD", "false")

    with pytest.raises(RuntimeError, match="MOCK=true is not permitted"):
        _import_api_main()


def test_production_environment_guard_rejects_mock_historical_context(
    monkeypatch, _clear_api_main_module
):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("MOCK", "false")
    monkeypatch.setenv("HISTORICAL_CONTEXT_MODE", "MOCK")
    monkeypatch.setenv("API_RELOAD", "false")

    with pytest.raises(RuntimeError, match="HISTORICAL_CONTEXT_MODE must be REAL"):
        _import_api_main()


def test_staging_environment_allows_docs(monkeypatch, _clear_api_main_module):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("MOCK", "false")
    monkeypatch.setenv("HISTORICAL_CONTEXT_MODE", "REAL")
    monkeypatch.setenv("API_RELOAD", "false")

    m = _import_api_main()
    assert m.app.docs_url == "/docs"


def test_production_api_docs_disabled(monkeypatch, _clear_api_main_module):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("MOCK", "false")
    monkeypatch.setenv("HISTORICAL_CONTEXT_MODE", "REAL")
    monkeypatch.setenv("API_RELOAD", "false")
    monkeypatch.setenv("API_JWT_ENABLED", "1")
    monkeypatch.setenv("API_JWT_SECRET", "test-secret-32-chars-long-padding!")

    m = _import_api_main()
    assert m.app.docs_url is None
    assert m.app.openapi_url is None


def test_requirements_lock_exists_and_is_nonempty():
    lockfile = Path("requirements.prod.lock.txt")
    assert lockfile.exists(), "requirements.prod.lock.txt is missing"
    content = lockfile.read_text(encoding="utf-8").strip()
    assert len(content) > 100, "requirements.prod.lock.txt appears empty or corrupt"


def test_changelog_exists_with_current_version():
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    pyproject = toml.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]
    assert (
        f"[{version}]" in changelog
    ), f"CHANGELOG.md does not contain entry for current version [{version}]"
