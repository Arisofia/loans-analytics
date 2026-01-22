"""
Unit tests for AzureBlobKPIExporter and related Azure Blob Storage integration.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

from src.analytics.azure_blob_exporter import AzureBlobKPIExporter


def test_exporter_requires_non_empty_container():
    """
    Test that AzureBlobKPIExporter raises ValueError for empty container_name.
    """
    with pytest.raises(ValueError, match="non-empty container_name"):
        AzureBlobKPIExporter(container_name="")


def test_exporter_requires_connection_or_url():
    """
    Test that AzureBlobKPIExporter raises ValueError if neither
    connection_string nor account_url is provided.
    """
    with pytest.raises(ValueError, match="Either connection_string or account_url"):
        AzureBlobKPIExporter(container_name="valid-container")


def test_exporter_initialization_with_connection_string():
    """
    Test initialization of AzureBlobKPIExporter with a connection string.
    """
    mock_client = MagicMock(spec=BlobServiceClient)
    with patch("src.analytics.azure_blob_exporter.BlobServiceClient") as mock_bsc:
        mock_bsc.from_connection_string.return_value = mock_client
        exporter = AzureBlobKPIExporter(
            container_name="test-container", connection_string="mock-connection-string"
        )
        assert exporter.container_name == "test-container"
        mock_bsc.from_connection_string.assert_called_once()


def test_exporter_initialization_with_account_url():
    """
    Test initialization of AzureBlobKPIExporter with an account URL and
    credential.
    """
    mock_client = MagicMock(spec=BlobServiceClient)
    with patch("src.analytics.azure_blob_exporter.BlobServiceClient") as mock_bsc:
        mock_bsc.return_value = mock_client
        exporter = AzureBlobKPIExporter(
            container_name="test-container",
            account_url="https://test.blob.core.windows.net",
            credential=MagicMock(),
        )
        assert exporter.container_name == "test-container"


def test_exporter_uses_provided_blob_service_client():
    """
    Test that AzureBlobKPIExporter uses a provided BlobServiceClient instance.
    """
    mock_client = MagicMock(spec=BlobServiceClient)
    exporter = AzureBlobKPIExporter(
        container_name="test-container", blob_service_client=mock_client
    )
    assert exporter.blob_service_client == mock_client


def test_upload_metrics_requires_dict():
    """
    Test that upload_metrics raises ValueError if metrics argument is not a
    dictionary.
    """
    exporter = AzureBlobKPIExporter(container_name="test", blob_service_client=MagicMock())
    with pytest.raises(ValueError, match="must be a non-empty dictionary"):
        exporter.upload_metrics("not-a-dict")


def test_upload_metrics_requires_non_empty_dict():
    """
    Test that upload_metrics raises ValueError if metrics dictionary is empty.
    """
    exporter = AzureBlobKPIExporter(container_name="test", blob_service_client=MagicMock())
    with pytest.raises(ValueError, match="must be a non-empty dictionary"):
        exporter.upload_metrics({})


def test_upload_metrics_blob_name_must_be_string():
    """
    Test that upload_metrics raises ValueError if blob_name is not a string.
    """
    exporter = AzureBlobKPIExporter(container_name="test", blob_service_client=MagicMock())
    with pytest.raises(ValueError, match="blob_name must be a string"):
        exporter.upload_metrics({"metric1": 1.0}, blob_name=123)


def test_upload_metrics_keys_must_be_strings():
    """
    Test that upload_metrics raises ValueError if metric keys are not strings.
    """
    exporter = AzureBlobKPIExporter(container_name="test", blob_service_client=MagicMock())
    with pytest.raises(ValueError, match="Metric keys must be non-empty strings"):
        exporter.upload_metrics({123: 1.0})


def test_upload_metrics_values_must_be_numeric():
    """
    Test that upload_metrics raises ValueError if metric values are not
    numeric.
    """
    exporter = AzureBlobKPIExporter(container_name="test", blob_service_client=MagicMock())
    with pytest.raises(ValueError, match="Metric values must be numeric"):
        exporter.upload_metrics({"metric1": "not-numeric"})


def test_upload_metrics_rejects_boolean_values():
    """
    Test that upload_metrics raises ValueError if metric values are boolean.
    """
    exporter = AzureBlobKPIExporter(container_name="test", blob_service_client=MagicMock())
    with pytest.raises(ValueError, match="Metric values must be numeric"):
        exporter.upload_metrics({"metric1": True})


def test_upload_metrics_rejects_empty_key():
    """
    Test that upload_metrics raises ValueError if metric key is empty string.
    """
    exporter = AzureBlobKPIExporter(container_name="test", blob_service_client=MagicMock())
    with pytest.raises(ValueError, match="Metric keys must be non-empty strings"):
        exporter.upload_metrics({"": 1.0})


def test_upload_metrics_successful_upload():
    """
    Test that upload_metrics successfully uploads metrics and returns blob
    path.
    """
    mock_client = MagicMock(spec=BlobServiceClient)
    mock_container = MagicMock()
    mock_client.get_container_client.return_value = mock_container

    exporter = AzureBlobKPIExporter(
        container_name="test-container", blob_service_client=mock_client
    )

    metrics = {"portfolio_yield": 4.5, "delinquency_rate": 2.3}
    result = exporter.upload_metrics(metrics, blob_name="test-blob.json")

    assert result == "test-container/test-blob.json"
    mock_container.upload_blob.assert_called_once()


def test_upload_metrics_creates_blob_path_with_timestamp():
    """
    Test that upload_metrics creates a blob path with a timestamp if blob_name
    is not provided.
    """
    mock_client = MagicMock(spec=BlobServiceClient)
    mock_container = MagicMock()
    mock_client.get_container_client.return_value = mock_container

    exporter = AzureBlobKPIExporter(
        container_name="test-container", blob_service_client=mock_client
    )

    metrics = {"metric1": 1.0}
    result = exporter.upload_metrics(metrics)

    assert "kpi-dashboard-" in result
    assert result.endswith(".json")


def test_upload_metrics_handles_container_already_exists():
    """
    Test that upload_metrics handles ResourceExistsError when container already
    exists.
    """
    mock_client = MagicMock(spec=BlobServiceClient)
    mock_container = MagicMock()
    mock_container.create_container.side_effect = ResourceExistsError("Container exists")
    mock_client.get_container_client.return_value = mock_container

    exporter = AzureBlobKPIExporter(
        container_name="test-container", blob_service_client=mock_client
    )

    metrics = {"metric1": 1.0}
    result = exporter.upload_metrics(metrics)

    assert result.startswith("test-container/")
    mock_container.upload_blob.assert_called_once()


def test_upload_metrics_payload_structure():
    """
    Test that upload_metrics payload structure includes generated_at and
    metrics keys.
    """
    mock_client = MagicMock(spec=BlobServiceClient)
    mock_container = MagicMock()
    mock_client.get_container_client.return_value = mock_container

    exporter = AzureBlobKPIExporter(
        container_name="test-container", blob_service_client=mock_client
    )

    metrics = {"portfolio_yield": 4.5, "delinquency_rate": 2.3}
    exporter.upload_metrics(metrics, blob_name="test.json")

    call_args = mock_container.upload_blob.call_args
    uploaded_data = json.loads(call_args[1]["data"])

    assert "generated_at" in uploaded_data
    assert "metrics" in uploaded_data
    assert abs(uploaded_data["metrics"]["portfolio_yield"] - 4.5) < 1e-6


def test_upload_metrics_int_values_converted_to_float():
    """
    Test that upload_metrics converts integer metric values to float in the
    payload.
    """
    mock_client = MagicMock(spec=BlobServiceClient)
    mock_container = MagicMock()
    mock_client.get_container_client.return_value = mock_container

    exporter = AzureBlobKPIExporter(container_name="test", blob_service_client=mock_client)

    metrics = {"metric1": 5}
    exporter.upload_metrics(metrics, blob_name="test.json")

    call_args = mock_container.upload_blob.call_args
    uploaded_data = json.loads(call_args[1]["data"])

    assert abs(uploaded_data["metrics"]["metric1"] - 5.0) < 1e-6


def test_container_name_whitespace_stripped():
    """
    Test that container name whitespace is stripped from the container_name
    argument.
    """
    exporter = AzureBlobKPIExporter(
        container_name="  test-container  ", blob_service_client=MagicMock()
    )
    assert exporter.container_name == "test-container"
