"""Lightweight Supabase writer used by tests.

This reproduces the small API surface used in unit tests: `SupabaseAuth` and
`SupabaseWriter` with `upsert_pipeline_run` and `insert_kpi_values`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import requests


@dataclass
class SupabaseAuth:
    url: str
    service_role_key: str


class SupabaseWriter:
    def __init__(self, auth: SupabaseAuth) -> None:
        self.auth = auth

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.auth.service_role_key,
            "Authorization": f"Bearer {self.auth.service_role_key}",
            "Prefer": "resolution=merge-duplicates",
        }

    def upsert_pipeline_run(self, run: Dict[str, Any]) -> None:
        # Build URL to upsert into analytics.pipeline_runs
        base = self.auth.url.rstrip("/")
        url = f"{base}/rest/v1/analytics.pipeline_runs?on_conflict=run_id"

        body = [dict(run)]
        # Ensure datetime is ISO formatted
        if isinstance(body[0].get("started_at"), datetime):
            body[0]["started_at"] = body[0]["started_at"].isoformat()

        resp = requests.post(url, headers=self._headers(), data=json.dumps(body))
        resp.raise_for_status()

    def insert_kpi_values(self, kpis: List[Dict[str, Any]]) -> None:
        if not kpis:
            return
        base = self.auth.url.rstrip("/")
        url = f"{base}/rest/v1/analytics.kpi_values"
        resp = requests.post(url, headers=self._headers(), data=json.dumps(kpis))
        resp.raise_for_status()
