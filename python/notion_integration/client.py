"""
Notion Integration Client
------------------------
Production-ready module for secure Notion API access and data extraction.
"""

import os
import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class NotionClient:
    def __init__(self, token_env: str = "NOTION_META_TOKEN", version_env: str = "NOTION_VERSION"):
        self.token = os.getenv(token_env)
        self.version = os.getenv(version_env, "2022-06-28")
        if not self.token:
            raise ValueError(f"Environment variable {token_env} is not set")

    def query_database(self, database_id: str) -> List[Dict[str, Any]]:
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.version,
            "Content-Type": "application/json"
        }
        results = []
        has_more = True
        start_cursor = None
        while has_more:
            body = {"start_cursor": start_cursor} if start_cursor else {}
            response = requests.post(url, headers=headers, json=body, timeout=30)
            response.raise_for_status()
            data = response.json()
            results.extend(data.get('results', []))
            has_more = data.get('has_more', False)
            start_cursor = data.get('next_cursor')
        return results
