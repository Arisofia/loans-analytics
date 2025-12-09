from datetime import datetime, timedelta
import hashlib
import json
import logging
from typing import Dict, Any

from airflow import DAG
from airflow.operators.python import PythonOperator


def _hash_payload(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def download_cascade_exports(**context):
    logging.info("Downloading Cascade exports")
    payload = {"source": "cascade", "date": context['ds']}
    context["ti"].xcom_push(key="ingest_payload_hash", value=_hash_payload(payload))


def validate_raw_data(**context):
    logging.info("Validating raw data and applying schema checks")
    # Placeholder for data validation logic


def compute_kpis(**context):
    logging.info("Computing KPIs and writing snapshots")
    # Placeholder for KPI computation logic
    context["ti"].xcom_push(key="kpi_snapshot_id", value="latest")


def trigger_agents(**context):
    kpi_snapshot_id = context["ti"].xcom_pull(key="kpi_snapshot_id")
    logging.info(f"Triggering agent layer with snapshot {kpi_snapshot_id}")


def publish_lineage(**context):
    logging.info("Publishing lineage to downstream warehouse and audit tables")


def build_refresh_dag():
    default_args = {
        "owner": "analytics",
        "depends_on_past": False,
        "email_on_failure": True,
        "email": ["data-team@example.com"],
        "retries": 1,
        "retry_delay": timedelta(minutes=10),
    }

    with DAG(
        dag_id="daily_kpi_refresh",
        default_args=default_args,
        schedule_interval="0 7 * * *",
        start_date=datetime(2024, 1, 1),
        catchup=False,
        tags=["kpi", "contracts", "agents"],
    ) as dag:
        download = PythonOperator(
            task_id="download_cascade_exports",
            python_callable=download_cascade_exports,
        )

        validate = PythonOperator(
            task_id="validate_raw_data",
            python_callable=validate_raw_data,
            provide_context=True,
        )

        compute = PythonOperator(
            task_id="compute_kpis",
            python_callable=compute_kpis,
            provide_context=True,
        )

        agents = PythonOperator(
            task_id="trigger_agents",
            python_callable=trigger_agents,
            provide_context=True,
        )

        lineage = PythonOperator(
            task_id="publish_lineage",
            python_callable=publish_lineage,
            provide_context=True,
        )

        download >> validate >> compute >> agents >> lineage

    return dag


dag = build_refresh_dag()
