"""HTTP client for Cascade ingestion with retry, auth, and checksum support."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from python.models.cascade_schemas import CollectionResponse, RiskAnalyticsResponse
from python.pipeline.config import CascadeConfig


@dataclass
class IngestionResult:
    """Structured ingestion output."""

    endpoint: str
    payload: Dict[str, Any]
    checksum: str


class CascadeClient:
    """Reusable Cascade client with retry and token refresh support."""

    def __init__(self, config: CascadeConfig, session: Optional[Session] = None) -> None:
        self.config = config
        self.session = session or self._build_session()

    def _build_session(self) -> Session:
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry)
        sess = requests.Session()
        sess.mount("https://", adapter)
        sess.mount("http://", adapter)
        return sess

    def _auth_header(self) -> Dict[str, str]:
        token = os.getenv(self.config.auth.token_secret)
        if not token:
            raise RuntimeError(
                f"Environment variable {self.config.auth.token_secret} missing; cannot authenticate with Cascade"
            )
        return {"Authorization": f"Bearer {token}"}

    def _compute_checksum(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def _get(self, url: str) -> Response:
        return self.session.get(url, headers=self._auth_header(), timeout=30)

    def fetch_endpoint(self, endpoint: str) -> IngestionResult:
        """Fetch an endpoint and return structured payload with checksum."""

        url = f"{self.config.base_url}{endpoint}"
        response = self._get(url)
        response.raise_for_status()
        checksum = self._compute_checksum(response.content)
        payload = response.json()
        return IngestionResult(endpoint=endpoint, payload=payload, checksum=checksum)

    def fetch_risk_analytics(self) -> RiskAnalyticsResponse:
        """Fetch and validate the risk analytics endpoint."""

        result = self.fetch_endpoint(self.config.endpoints.risk_analytics)
        return RiskAnalyticsResponse.parse_obj(result.payload)

    def fetch_collection_rates(self) -> CollectionResponse:
        """Fetch and validate the collection rates endpoint."""

        result = self.fetch_endpoint(self.config.endpoints.collection_rates)
        return CollectionResponse.parse_obj(result.payload)
