from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests
from requests import Response


class AbacoAnalyticsApiClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_token: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("ABACO_API_BASE_URL") or "http://localhost:3000/api"
        ).rstrip("/")
        self.api_token = api_token or os.getenv("ABACO_API_TOKEN")
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def _handle_response(self, resp: Response) -> Any:
        if 200 <= resp.status_code < 300:
            if resp.content:
                return resp.json()
            return None

        try:
            payload = resp.json()
        except ValueError:
            resp.raise_for_status()
            return None

        error_msg = payload.get("message") or payload.get("error") or f"HTTP {resp.status_code}"
        raise RuntimeError(f"Abaco API error {resp.status_code}: {error_msg}")

    def get_drilldown_statuses(self) -> Dict[str, str]:
        url = f"{self.base_url}/drilldowns/status"
        resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def calculate_all_kpis(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/analytics/kpis"
        resp = requests.post(url, json=portfolio, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def calculate_par30(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/analytics/kpis/par30"
        resp = requests.post(url, json=portfolio, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def calculate_par90(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/analytics/kpis/par90"
        resp = requests.post(url, json=portfolio, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def calculate_collection_rate(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/analytics/kpis/collection-rate"
        resp = requests.post(url, json=portfolio, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def calculate_portfolio_health(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/analytics/kpis/portfolio-health"
        resp = requests.post(url, json=portfolio, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def calculate_ltv(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/analytics/kpis/ltv"
        resp = requests.post(url, json=portfolio, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def calculate_dti(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/analytics/kpis/dti"
        resp = requests.post(url, json=portfolio, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def calculate_portfolio_yield(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/analytics/kpis/portfolio-yield"
        resp = requests.post(url, json=portfolio, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def get_risk_alerts(
        self,
        portfolio: Dict[str, Any],
        ltv_threshold: float = 80.0,
        dti_threshold: float = 50.0,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/analytics/risk-alerts"
        body = dict(portfolio)
        body["ltv_threshold"] = ltv_threshold
        body["dti_threshold"] = dti_threshold
        resp = requests.post(url, json=body, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def run_full_analysis(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/analytics/full-analysis"
        resp = requests.post(url, json=portfolio, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def get_executive_summary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/analytics/executive-summary"
        resp = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def get_data_quality_profile(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/data-quality/profile"
        resp = requests.post(url, json=portfolio, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)

    def validate_loan_data(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/data-quality/validate"
        resp = requests.post(url, json=portfolio, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(resp)
