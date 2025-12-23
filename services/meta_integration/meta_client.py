"""
Meta (Instagram/Facebook) API Client
------------------------------------
Handles OAuth and Graph API requests for backend integration.
"""
import os
import requests
from typing import Optional, Dict, Any

META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
META_REDIRECT_URI = os.getenv("META_REDIRECT_URI")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")  # Optional: for long-lived tokens

class MetaAPIClient:
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or META_ACCESS_TOKEN
        self.base_url = "https://graph.facebook.com/v19.0"

    def get_auth_url(self, scope: str = "instagram_basic, pages_show_list, pages_read_engagement") -> str:
        return (
            f"https://www.facebook.com/v19.0/dialog/oauth?client_id={META_APP_ID}"
            f"&redirect_uri={META_REDIRECT_URI}&scope={scope}&response_type=code"
        )

    def exchange_code(self, code: str) -> Dict[str, Any]:
        url = f"{self.base_url}/oauth/access_token"
        params = {
            "client_id": META_APP_ID,
            "redirect_uri": META_REDIRECT_URI,
            "client_secret": META_APP_SECRET,
            "code": code,
        }
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_user_accounts(self) -> Dict[str, Any]:
        url = f"{self.base_url}/me/accounts"
        params = {"access_token": self.access_token}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_instagram_insights(self, ig_user_id: str, metric: str = "impressions,reach,profile_views") -> Dict[str, Any]:
        url = f"{self.base_url}/{ig_user_id}/insights"
        params = {"metric": metric, "access_token": self.access_token}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
