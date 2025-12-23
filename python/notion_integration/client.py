"""
Notion Integration Client
------------------------
Production-ready module for secure Notion API access and data extraction.
"""

import logging
import os
from typing import Any, Dict, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class NotionClient:
    def __init__(self, token_env: str | None = None, version_env: str | None = None):
        token_key = token_env or "NOTION_META_TOKEN"
        version_key = version_env or "NOTION_VERSION"
        self.token = os.getenv(token_key)
        self.version = os.getenv(version_key, "2022-06-28")
        if not self.token:
            raise ValueError(f"Environment variable {token_key} is not set")

        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def query_database(self, database_id: str) -> List[Dict[str, Any]]:
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.version,
            "Content-Type": "application/json",
        }
        results = []
        has_more = True
        start_cursor = None
        while has_more:
            body: dict[str, object] = {"start_cursor": start_cursor} if start_cursor else {}
            response = self.session.post(url, headers=headers, json=body, timeout=30)
            response.raise_for_status()
            data = response.json()
            results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
        return results
