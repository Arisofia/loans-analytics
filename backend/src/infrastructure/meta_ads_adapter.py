"""Meta Ads (Facebook Marketing API) adapter.

Fetches ad spend and delivery data for the configured ad account and normalises
results into ``CanonicalAdSpendRecord`` objects.

Required environment variables
--------------------------------
META_ADS_ACCESS_TOKEN  – long-lived user or system-user access token
META_ADS_ACCOUNT_ID    – ad account ID in the form ``act_<numeric_id>``

Optional environment variables
--------------------------------
META_ADS_API_VERSION   – Graph API version to use (default: ``v19.0``)
META_ADS_REQUEST_TIMEOUT_SECONDS – HTTP timeout per request (default: 30)

The adapter never stores credentials; it reads them from the process environment
at call time so secrets can be managed via the host secret store (GitHub Actions
secrets → env vars, Docker environment, etc.).
"""
from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any, Dict, List, Optional

from backend.src.contracts.raw_schema import CanonicalAdSpendRecord

logger = logging.getLogger(__name__)

_DEFAULT_API_VERSION = "v19.0"
_FIELDS = ",".join(
    [
        "date_start",
        "date_stop",
        "account_id",
        "campaign_id",
        "campaign_name",
        "adset_id",
        "adset_name",
        "ad_id",
        "ad_name",
        "impressions",
        "reach",
        "clicks",
        "spend",
        "actions",
    ]
)


class MetaAdsAdapter:
    """Fetches Meta Ads insights and returns validated canonical records.

    Parameters
    ----------
    access_token:
        Meta long-lived access token. Reads ``META_ADS_ACCESS_TOKEN`` from env
        when not supplied directly.
    account_id:
        Ad account ID (``act_<numeric>``) . Reads ``META_ADS_ACCOUNT_ID`` from env
        when not supplied directly.
    api_version:
        Graph API version string, e.g. ``v19.0``.
    """

    _BASE_URL = "https://graph.facebook.com"

    def __init__(
        self,
        access_token: Optional[str] = None,
        account_id: Optional[str] = None,
        api_version: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self._access_token = access_token or os.environ.get("META_ADS_ACCESS_TOKEN", "")
        self._account_id = account_id or os.environ.get("META_ADS_ACCOUNT_ID", "")
        self._api_version = (
            api_version
            or os.environ.get("META_ADS_API_VERSION", _DEFAULT_API_VERSION)
        )
        self._timeout = int(os.environ.get("META_ADS_REQUEST_TIMEOUT_SECONDS", timeout))

        if not self._access_token:
            raise ValueError(
                "CRITICAL: META_ADS_ACCESS_TOKEN is not set. "
                "Provide it as an argument or via the META_ADS_ACCESS_TOKEN environment variable."
            )
        if not self._account_id:
            raise ValueError(
                "CRITICAL: META_ADS_ACCOUNT_ID is not set. "
                "Provide it as an argument or via the META_ADS_ACCOUNT_ID environment variable."
            )
        if not self._account_id.startswith("act_"):
            raise ValueError(
                f"CRITICAL: META_ADS_ACCOUNT_ID must be in the form 'act_<numeric_id>', got '{self._account_id}'"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_insights(
        self,
        date_from: date,
        date_to: date,
        level: str = "ad",
    ) -> List[CanonicalAdSpendRecord]:
        """Fetch ad delivery insights for the given date range.

        Parameters
        ----------
        date_from:
            First day of the reporting window (inclusive).
        date_to:
            Last day of the reporting window (inclusive).
        level:
            Breakdown level: ``"ad"`` | ``"adset"`` | ``"campaign"`` | ``"account"``.

        Returns
        -------
        List[CanonicalAdSpendRecord]
            Validated canonical records. Empty list if no data returned.
        """
        self._ensure_dependencies()

        if date_to < date_from:
            raise ValueError(
                f"date_to ({date_to}) must be >= date_from ({date_from})"
            )

        params = {
            "level": level,
            "fields": _FIELDS,
            "time_range": {
                "since": date_from.isoformat(),
                "until": date_to.isoformat(),
            },
            "time_increment": 1,  # one row per day
            "access_token": self._access_token,
        }

        url = f"{self._BASE_URL}/{self._api_version}/{self._account_id}/insights"
        raw_rows = self._paginate(url, params)

        records: List[CanonicalAdSpendRecord] = []
        for row in raw_rows:
            try:
                record = self._parse_row(row)
                records.append(record)
            except Exception as exc:
                logger.error(
                    "Failed to parse Meta Ads insight row (campaign_id=%s, date=%s): %s",
                    row.get("campaign_id", "unknown"),
                    row.get("date_start", "unknown"),
                    exc,
                )
                raise

        logger.info(
            "MetaAdsAdapter: fetched %d records from %s to %s (level=%s)",
            len(records),
            date_from,
            date_to,
            level,
        )
        return records

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _paginate(self, url: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Iterate through all cursor pages and return a flat list of rows."""
        import requests  # lazy import — optional dependency

        rows: List[Dict[str, Any]] = []
        next_url: Optional[str] = url
        current_params: Optional[Dict[str, Any]] = params

        while next_url:
            logger.debug("MetaAdsAdapter: GET %s", next_url)
            try:
                response = requests.get(
                    next_url, params=current_params, timeout=self._timeout
                )
            except requests.exceptions.RequestException as exc:
                raise RuntimeError(
                    f"CRITICAL: Meta Ads API request failed: {exc}"
                ) from exc

            if response.status_code != 200:
                raise RuntimeError(
                    f"CRITICAL: Meta Ads API returned HTTP {response.status_code}: {response.text[:500]}"
                )

            payload = response.json()

            if "error" in payload:
                err = payload["error"]
                raise RuntimeError(
                    f"CRITICAL: Meta Ads API error {err.get('code')}: {err.get('message')}"
                )

            data = payload.get("data", [])
            if not isinstance(data, list):
                raise RuntimeError(
                    f"CRITICAL: Unexpected Meta Ads API response shape: 'data' is {type(data)}"
                )
            rows.extend(data)

            paging = payload.get("paging", {})
            next_url = paging.get("next")
            current_params = None  # cursor URL already includes params

        return rows

    @staticmethod
    def _parse_row(row: Dict[str, Any]) -> CanonicalAdSpendRecord:
        """Map a raw API row to a ``CanonicalAdSpendRecord``."""
        impressions = int(row.get("impressions") or 0)
        reach = int(row.get("reach") or 0)
        clicks = int(row.get("clicks") or 0)
        spend = float(row.get("spend") or 0.0)

        # Extract lead conversions from the nested 'actions' array
        leads = 0
        for action in row.get("actions") or []:
            if action.get("action_type") in ("lead", "onsite_conversion.lead_grouped"):
                leads += int(action.get("value") or 0)

        ctr = (clicks / impressions) if impressions > 0 else None
        cpl = (spend / leads) if leads > 0 else None
        cpc = (spend / clicks) if clicks > 0 else None

        return CanonicalAdSpendRecord(
            date_start=date.fromisoformat(row["date_start"]),
            date_stop=date.fromisoformat(row["date_stop"]),
            account_id=row["account_id"],
            campaign_id=row["campaign_id"],
            campaign_name=row.get("campaign_name", ""),
            adset_id=row.get("adset_id"),
            adset_name=row.get("adset_name"),
            ad_id=row.get("ad_id"),
            ad_name=row.get("ad_name"),
            impressions=impressions,
            reach=reach,
            clicks=clicks,
            spend=spend,
            leads=leads,
            ctr=ctr,
            cpl=cpl,
            cpc=cpc,
        )

    @staticmethod
    def _ensure_dependencies() -> None:
        try:
            import requests  # noqa: F401
        except ImportError:
            raise ValueError(
                "CRITICAL: 'requests' is required for MetaAdsAdapter. "
                "Install it with: pip install requests"
            )
