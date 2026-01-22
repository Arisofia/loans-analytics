"""
Supabase output integration for data persistence and real-time syncs.

Handles:
- Exporting KPI metrics to Supabase tables
- Raw analytics data persistence
- Time-series data for historical analysis
- Real-time KPI updates via Supabase Realtime
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

try:
    from supabase import create_client

    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False


class SupabaseOutputClient:
    """Sync analytics data to Supabase PostgreSQL database."""

    def __init__(self, url: Optional[str] = None, service_role_key: Optional[str] = None):
        self.url = url or os.getenv("SUPABASE_URL")
        self.service_role_key = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE")

        if not HAS_SUPABASE:
            logger.warning("supabase-py not installed. Supabase export disabled.")
            self.client = None
        elif self.url and self.service_role_key:
            try:
                self.client = create_client(self.url, self.service_role_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client: {e}")
                self.client = None
        else:
            logger.warning("Supabase credentials not configured")
            self.client = None

    def insert_kpi_metrics(
        self,
        kpi_metrics: Dict[str, Any],
        run_id: str,
    ) -> Dict[str, bool]:
        """Insert KPI metrics into Supabase analytics_kpi_metrics table."""
        if not self.client:
            logger.warning("Supabase client not initialized")
            return {}

        results = {}

        try:
            for kpi_name, metric_data in kpi_metrics.items():
                record = {
                    "kpi_name": kpi_name,
                    "run_id": run_id,
                    "current_value": metric_data.get("current_value"),
                    "previous_value": metric_data.get("previous_value"),
                    "unit": metric_data.get("unit", ""),
                    "status": metric_data.get("status", "neutral"),
                    "metadata": json.dumps(metric_data.get("metadata", {})),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }

                response = self.client.table("analytics_kpi_metrics").insert(record).execute()

                success = bool(response.data)
                results[kpi_name] = success

                if success:
                    logger.info(f"Inserted KPI metric: {kpi_name}")
                else:
                    logger.warning(f"Failed to insert KPI metric: {kpi_name}")

        except Exception as e:
            logger.error(f"Error inserting KPI metrics: {e}")

        return results

    def insert_raw_data(
        self,
        df: pd.DataFrame,
        table_name: str,
        run_id: str,
        batch_size: int = 1000,
    ) -> int:
        """Insert raw analytics data into Supabase table."""
        if not self.client:
            logger.warning("Supabase client not initialized")
            return 0

        try:
            total_inserted = 0

            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i : i + batch_size]
                batch_records = batch_df.to_dict(orient="records")

                for record in batch_records:
                    record["run_id"] = run_id
                    record["created_at"] = datetime.now(timezone.utc).isoformat()

                response = self.client.table(table_name).insert(batch_records).execute()

                if response.data:
                    total_inserted += len(response.data)
                    logger.info(f"Inserted {len(response.data)} records into {table_name}")

            logger.info(f"Total inserted: {total_inserted} records into {table_name}")
            return total_inserted

        except Exception as e:
            logger.error(f"Error inserting raw data into {table_name}: {e}")
            return 0

    def upsert_timeseries(
        self,
        timeseries_data: Dict[str, pd.DataFrame],
        run_id: str,
    ) -> Dict[str, int]:
        """Upsert time-series data into Supabase."""
        if not self.client:
            logger.warning("Supabase client not initialized")
            return {}

        results = {}

        try:
            for ts_name, ts_df in timeseries_data.items():
                ts_records = ts_df.to_dict(orient="records")

                for record in ts_records:
                    record["run_id"] = run_id
                    record["created_at"] = datetime.now(timezone.utc).isoformat()

                response = (
                    self.client.table("analytics_timeseries")
                    .upsert(ts_records, on_conflict="run_id,metric_name,period")
                    .execute()
                )

                inserted = len(response.data) if response.data else 0
                results[ts_name] = inserted

                logger.info(f"Upserted {inserted} timeseries records for {ts_name}")

        except Exception as e:
            logger.error(f"Error upserting timeseries data: {e}")

        return results

    def get_latest_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve latest KPI metrics from Supabase."""
        if not self.client:
            logger.warning("Supabase client not initialized")
            return []

        try:
            response = (
                self.client.table("analytics_kpi_metrics")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data if response.data else []  # type: ignore

        except Exception as e:
            logger.error(f"Error retrieving metrics from Supabase: {e}")
            return []

    def sync_batch_export(
        self,
        export_data: Dict[str, Any],
        run_id: str,
    ) -> Dict[str, Any]:
        """
        Sync complete batch export to Supabase.

        Args:
            export_data: Dict with 'kpi_metrics', 'raw_data_df', 'timeseries'
            run_id: Pipeline run ID

        Returns:
            Dict with results from each sync operation
        """
        if not self.client:
            logger.warning("Supabase export skipped: credentials not configured")
            return {}

        results = {
            "kpi_metrics_inserted": {},
            "raw_data_inserted": 0,
            "timeseries_upserted": {},
            "success": False,
        }

        try:
            if "kpi_metrics" in export_data:
                results["kpi_metrics_inserted"] = self.insert_kpi_metrics(
                    export_data["kpi_metrics"], run_id
                )

            if "raw_data_df" in export_data:
                df = export_data["raw_data_df"]
                table_name = export_data.get("raw_data_table", "analytics_raw_data")
                results["raw_data_inserted"] = self.insert_raw_data(df, table_name, run_id)

            if "timeseries" in export_data:
                results["timeseries_upserted"] = self.upsert_timeseries(
                    export_data["timeseries"], run_id
                )

            results["success"] = True
            logger.info(f"Supabase batch sync completed (run: {run_id})")

        except Exception as e:
            logger.error(f"Supabase batch sync failed: {e}")
            results["error"] = str(e)

        return results
