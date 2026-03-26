"""HTTP client for the Decision Intelligence API surface.

All ``/decision/*`` endpoints are wrapped here so that Streamlit pages
never import ``httpx`` directly — they call this module instead.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[assignment]

_DEFAULT_BASE = os.getenv("DECISION_API_URL", "http://localhost:8000")


class DecisionAPIClient:
    """Thin wrapper around the Decision Intelligence routes."""

    def __init__(self, base_url: str | None = None, timeout: int = 30):
        self.base_url = (base_url or _DEFAULT_BASE).rstrip("/")
        self.timeout = timeout

    # ── helpers ──────────────────────────────────────────────────────
    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if httpx is None:
            raise RuntimeError("httpx is not installed")
        url = f"{self.base_url}{path}"
        resp = httpx.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _get(self, path: str) -> Any:
        if httpx is None:
            raise RuntimeError("httpx is not installed")
        url = f"{self.base_url}{path}"
        resp = httpx.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ── metric engine ───────────────────────────────────────────────
    def run_metrics(
        self,
        marts: Dict[str, Any],
        equity: float = 200_000,
        lgd: float = 0.10,
        min_collection_rate: float = 0.985,
    ) -> Dict[str, Any]:
        return self._post(
            "/decision/metrics/run",
            {
                "marts": marts,
                "equity": equity,
                "lgd": lgd,
                "min_collection_rate": min_collection_rate,
            },
        )

    # ── agents ──────────────────────────────────────────────────────
    def list_agents(self) -> Dict[str, Any]:
        return self._get("/decision/agents/")

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        return self._get(f"/decision/agents/{agent_id}")

    # ── decision center ─────────────────────────────────────────────
    def run_decision(
        self,
        portfolio_data: List[Dict[str, Any]],
        business_rules: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return self._post(
            "/decision/center/run",
            {
                "portfolio_data": portfolio_data,
                "business_rules": business_rules or {},
            },
        )

    # ── scenarios ───────────────────────────────────────────────────
    def run_scenario(
        self,
        scenario: str,
        current_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self._post(
            f"/decision/scenarios/{scenario}",
            {"current_metrics": current_metrics},
        )

    def compare_scenarios(
        self, current_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._post(
            "/decision/scenarios/compare",
            {"current_metrics": current_metrics},
        )

    # ── reports ─────────────────────────────────────────────────────
    def generate_report(
        self,
        report_type: str,
        metrics: Dict[str, Any],
        scenarios: List[Dict[str, Any]] | None = None,
        alerts: List[str] | None = None,
        actions: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        return self._post(
            f"/decision/reports/{report_type}",
            {
                "metrics": metrics,
                "scenarios": scenarios or [],
                "alerts": alerts or [],
                "actions": actions or [],
            },
        )

    # ── data quality ────────────────────────────────────────────────
    def run_quality(
        self, records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return self._post(
            "/decision/quality/run",
            {"records": records},
        )
