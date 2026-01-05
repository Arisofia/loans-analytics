"""
Meta (Facebook) output integration for pixel tracking, ads insights, and campaign data.

Handles:
- Facebook Pixel event tracking for analytics events
- Ads Manager API for campaign performance data
- Audience insights and demographic data
- Custom audience creation from analytics segments
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, cast

import requests

logger = logging.getLogger(__name__)


class MetaOutputClient:
    """Sync analytics data to Meta platforms (Facebook Pixel, Ads Manager, etc.)."""

    def __init__(
        self,
        pixel_id: Optional[str] = None,
        access_token: Optional[str] = None,
        ad_account_id: Optional[str] = None,
    ):
        self.pixel_id = pixel_id or os.getenv("META_PIXEL_ID")
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN")
        self.ad_account_id = ad_account_id or os.getenv("META_AD_ACCOUNT_ID")

        self.base_url = "https://graph.facebook.com/v18.0"
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

        if not self.access_token:
            logger.warning("Meta credentials not configured. Meta export disabled.")

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make authenticated request to Meta API."""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("headers", self.headers)

        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.RequestException as e:
            logger.error(f"Meta API error: {e}")
            return {}

    def track_pixel_event(
        self,
        event_name: str,
        event_data: Dict[str, Any],
        user_data: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Track custom event via Facebook Pixel."""
        if not self.pixel_id or not self.access_token:
            logger.warning("Meta Pixel credentials not configured")
            return False

        try:
            payload = {
                "data": [
                    {
                        "event_name": event_name,
                        "event_time": int(datetime.now(timezone.utc).timestamp()),
                        "event_id": f"{event_name}_{datetime.now(timezone.utc).isoformat()}",
                        "event_source_url": "https://abaco-analytics-dashboard.azurewebsites.net",
                        "user_data": user_data or {},
                        "custom_data": event_data,
                    }
                ],
                "access_token": self.access_token,
            }

            response = self._request(
                "POST",
                f"/{self.pixel_id}/events",
                json=payload,
            )

            success = response.get("events_received") == 1
            if success:
                logger.info(f"Tracked Meta Pixel event: {event_name}")
            else:
                logger.warning(f"Failed to track Meta Pixel event: {event_name}")

            return success

        except Exception as e:
            logger.error(f"Error tracking Meta Pixel event: {e}")
            return False

    def track_kpi_updates(
        self,
        kpi_metrics: Dict[str, Any],
    ) -> Dict[str, bool]:
        """Track KPI updates as Meta Pixel events for cross-platform analytics."""
        results = {}

        for kpi_name, metric_data in kpi_metrics.items():
            event_data = {
                "currency": "USD",
                "value": float(metric_data.get("current_value", 0)),
                "content_name": kpi_name,
                "content_type": "product",
                "custom_properties": {
                    "unit": metric_data.get("unit", ""),
                    "status": metric_data.get("status", "neutral"),
                },
            }

            success = self.track_pixel_event(
                event_name="KPIUpdate",
                event_data=event_data,
            )
            results[kpi_name] = success

        return results

    def get_ads_insights(
        self,
        date_start: Optional[str] = None,
        date_stop: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve ads performance insights from Meta Ads Manager."""
        if not self.ad_account_id or not self.access_token:
            logger.warning("Meta Ads credentials not configured")
            return []

        date_start = date_start or (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        date_stop = date_stop or datetime.now().strftime("%Y-%m-%d")

        fields = fields or [
            "campaign_id",
            "campaign_name",
            "spend",
            "impressions",
            "clicks",
            "ctr",
            "cpp",
            "cpc",
        ]

        try:
            params = {
                "access_token": self.access_token,
                "fields": ",".join(fields),
                "time_range": json.dumps(
                    {
                        "since": date_start,
                        "until": date_stop,
                    }
                ),
                "level": "campaign",
            }

            response = self._request(
                "GET",
                f"/act_{self.ad_account_id}/insights",
                params=params,
            )

            insights = cast(List[Dict[str, Any]], response.get("data", []))
            logger.info(f"Retrieved {len(insights)} ad campaigns from Meta")
            return insights

        except Exception as e:
            logger.error(f"Error retrieving Meta ads insights: {e}")
            return []

    def create_custom_audience(
        self,
        audience_name: str,
        customer_list: List[str],
        hashed: bool = True,
    ) -> Optional[str]:
        """Create a custom audience in Meta Ads Manager from analytics segment."""
        if not self.ad_account_id or not self.access_token:
            logger.warning("Meta Ads credentials not configured")
            return None

        try:
            payload = {
                "access_token": self.access_token,
                "name": audience_name,
                "customer_file_source": "USER_PROVIDED_ONLY",
                "data": customer_list,
                "hashed": hashed,
            }

            response = self._request(
                "POST",
                f"/act_{self.ad_account_id}/audiences",
                json=payload,
            )

            audience_id = response.get("id")
            if audience_id:
                logger.info(f"Created Meta custom audience: {audience_name} ({audience_id})")
            else:
                logger.warning(f"Failed to create Meta custom audience: {audience_name}")

            return audience_id

        except Exception as e:
            logger.error(f"Error creating Meta custom audience: {e}")
            return None

    def sync_batch_export(
        self,
        export_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Sync batch export data to Meta platforms.

        Args:
            export_data: Dict with 'kpi_metrics', 'customer_segments', etc.

        Returns:
            Dict with results from Meta sync operations
        """
        if not self.access_token:
            logger.warning("Meta export skipped: credentials not configured")
            return {}

        results: Dict[str, Any] = {
            "pixel_events_tracked": {},
            "ads_insights_retrieved": [],
            "custom_audiences_created": {},
            "success": False,
        }

        try:
            if "kpi_metrics" in export_data:
                results["pixel_events_tracked"] = self.track_kpi_updates(export_data["kpi_metrics"])

            results["ads_insights_retrieved"] = self.get_ads_insights()

            if "customer_segments" in export_data:
                for segment_name, customer_list in export_data["customer_segments"].items():
                    audience_id = self.create_custom_audience(
                        audience_name=f"analytics_{segment_name}",
                        customer_list=customer_list,
                    )
                    if audience_id:
                        results["custom_audiences_created"][segment_name] = audience_id

            results["success"] = True
            logger.info("Meta batch sync completed")

        except Exception as e:
            logger.error(f"Meta batch sync failed: {e}")
            results["error"] = str(e)

        return results
