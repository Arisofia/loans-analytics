import json
from unittest.mock import Mock

import pytest

from apps.analytics.src.azure_blob_exporter import AzureBlobKPIExporter
from apps.analytics.src.enterprise_analytics_engine import LoanAnalyticsEngine


def test_upload_metrics_uses_blob_service_client():
    container_client = Mock()
    blob_service_client = Mock()
    blob_service_client.get_container_client.return_value = container_client

    exporter = AzureBlobKPIExporter(container_name="kpis", blob_service_client=blob_service_client)
    blob_path = exporter.upload_metrics({"portfolio_yield_percent": 4.2})

    blob_service_client.get_container_client.assert_called_once_with("kpis")
    container_client.create_container.assert_called_once()
    args, kwargs = container_client.upload_blob.call_args
    assert kwargs["overwrite"] is True
    assert kwargs["content_settings"].content_type == "application/json"

    payload = json.loads(kwargs["data"])
    assert payload["metrics"] == {"portfolio_yield_percent": 4.2}
    assert blob_path.startswith("kpis/kpi-dashboard-")


def test_upload_metrics_requires_payload():
    exporter = AzureBlobKPIExporter(container_name="kpis", blob_service_client=Mock())
    with pytest.raises(ValueError):
        exporter.upload_metrics({})


def test_upload_metrics_rejects_non_numeric_payloads():
    exporter = AzureBlobKPIExporter(container_name="kpis", blob_service_client=Mock())
    with pytest.raises(ValueError):
        exporter.upload_metrics({"portfolio": "high"})


def test_upload_metrics_rejects_non_string_blob_name():
    exporter = AzureBlobKPIExporter(container_name="kpis", blob_service_client=Mock())
    with pytest.raises(ValueError):
        exporter.upload_metrics({"portfolio_yield_percent": 4.2}, blob_name=42)  # type: ignore[arg-type]


def test_exporter_requires_valid_container_name():
    with pytest.raises(ValueError):
        AzureBlobKPIExporter(container_name="  ", blob_service_client=Mock())


def test_engine_exports_to_blob(monkeypatch):
    data = {
        "loan_amount": [100000, 200000],
        "appraised_value": [150000, 250000],
        "borrower_income": [60000, 80000],
        "monthly_debt": [1000, 1500],
        "loan_status": ["current", "current"],
        "interest_rate": [0.04, 0.05],
        "principal_balance": [95000, 195000],
    }
    engine = LoanAnalyticsEngine.from_dict(data)

    exporter = AzureBlobKPIExporter(container_name="kpis", blob_service_client=Mock())
    upload_spy = Mock(return_value="kpis/kpi-dashboard.json")
    exporter.upload_metrics = upload_spy

    result_path = engine.export_kpis_to_blob(exporter, blob_name="dashboard.json")

    upload_spy.assert_called_once()
<<<<<<< HEAD
    called_payload, called_blob_name = (
        upload_spy.call_args[0][0],
        upload_spy.call_args[1]["blob_name"],
    )
=======
    called_payload = upload_spy.call_args[0][0]
    called_blob_name = upload_spy.call_args[1]["blob_name"]
>>>>>>> origin/main
    assert called_blob_name == "dashboard.json"
    assert "portfolio_delinquency_rate_percent" in called_payload
    assert result_path == "kpis/kpi-dashboard.json"


def test_engine_rejects_non_string_blob_name():
    data = {
        "loan_amount": [100000, 200000],
        "appraised_value": [150000, 250000],
        "borrower_income": [60000, 80000],
        "monthly_debt": [1000, 1500],
        "loan_status": ["current", "current"],
        "interest_rate": [0.04, 0.05],
        "principal_balance": [95000, 195000],
    }
    engine = LoanAnalyticsEngine.from_dict(data)

    exporter = AzureBlobKPIExporter(container_name="kpis", blob_service_client=Mock())

    with pytest.raises(ValueError):
        engine.export_kpis_to_blob(exporter, blob_name=123)  # type: ignore[arg-type]
