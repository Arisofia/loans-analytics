"""Supabase writer for pipeline lineage/audit tables (minimal).

Uses Supabase PostgREST API.
Expected env vars:
- SUPABASE_URL (e.g., https://<project>.supabase.co)
- SUPABASE_SERVICE_ROLE (service role key)

Tables:
- analytics.pipeline_runs
- analytics.raw_artifacts
- analytics.kpi_values
- analytics.data_quality_results
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import requests


@dataclass(frozen=True)
class SupabaseAuth:
    url: str
    service_role_key: str


class SupabaseWriter:
    def __init__(self, auth: SupabaseAuth, schema: str = "analytics") -> None:
        base = auth.url.rstrip("/")
        self._rest_base = f"{base}/rest/v1"
        self._key = auth.service_role_key
        self._schema = schema

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _post(
        self,
        table: str,
        payload: list[dict[str, Any]] | dict[str, Any],
        *,
        params: dict[str, str] | None = None,
        prefer: str | None = None,
    ) -> requests.Response:
        qp = f"?{urlencode(params)}" if params else ""
        url = f"{self._rest_base}/{table}{qp}"
        data = json.dumps(payload, default=_json_default)
        resp = requests.post(url, headers=self._headers(prefer), data=data, timeout=30)
        resp.raise_for_status()
        return resp

    def upsert_pipeline_run(self, run: dict[str, Any]) -> None:
        # Upsert on primary key run_id.
        self._post(
            f"{self._schema}.pipeline_runs",
            [run],
            params={"on_conflict": "run_id"},
            prefer="resolution=merge-duplicates,return=minimal",
        )

    def insert_raw_artifacts(self, artifacts: list[dict[str, Any]]) -> None:
        if not artifacts:
            return
        self._post(
            f"{self._schema}.raw_artifacts",
            artifacts,
            prefer="return=minimal",
        )

    def insert_kpi_values(self, kpis: list[dict[str, Any]]) -> None:
        if not kpis:
            return
        self._post(
            f"{self._schema}.kpi_values",
            kpis,
            prefer="return=minimal",
        )

    def upsert_data_quality(self, result: dict[str, Any]) -> None:
        # Uniqueness enforced by uq_data_quality_results_run_id (run_id).
        self._post(
            f"{self._schema}.data_quality_results",
            [result],
            params={"on_conflict": "run_id"},
            prefer="resolution=merge-duplicates,return=minimal",
        )


def _json_default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)
