"""Shared fixtures for end-to-end tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests

DEFAULT_FRONTEND_URLS = ("http://localhost:8501", "http://localhost:8000")


def _streamlit_health_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/_stcore/health"


def _is_streamlit_up(base_url: str, timeout: int = 2) -> bool:
    try:
        return requests.get(_streamlit_health_url(base_url), timeout=timeout).status_code < 500
    except Exception:
        return False


def _resolve_frontend_base_url() -> str:
    explicit = os.getenv("FRONTEND_BASE_URL")
    if explicit and _is_streamlit_up(explicit):
        return explicit

    for url in DEFAULT_FRONTEND_URLS:
        if _is_streamlit_up(url):
            return url
    return DEFAULT_FRONTEND_URLS[0]


@pytest.fixture(scope="session")
def frontend_base_url() -> str:
    return _resolve_frontend_base_url()


@pytest.fixture(scope="session")
def backend_base_url() -> str:
    return os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def csv_path() -> Path:
    path = Path(os.getenv("CSV_PATH", "data/raw/abaco_real_data_20260202.csv")).resolve()
    if not path.exists():
        pytest.skip(f"CSV file not found for E2E flow: {path}")
    return path


@pytest.fixture(scope="session")
def agent_outputs_dir() -> Path:
    path = Path("data/agent_outputs").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture()
def clean_agent_outputs(agent_outputs_dir: Path) -> dict[str, set[Path]]:
    before = set(agent_outputs_dir.glob("*_response.json"))
    return {"before": before}


def is_service_up(url: str, timeout: int = 3) -> bool:
    try:
        return requests.get(url, timeout=timeout).status_code < 500
    except Exception:
        return False
