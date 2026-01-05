"""
Tests for src.tracing_setup.

Validates OpenTelemetry tracing initialization and safe no-op behavior.
"""

import os
import unittest
from unittest.mock import patch

from opentelemetry.sdk.trace import TracerProvider

from src import tracing_setup


class TestTracingSetup(unittest.TestCase):
    """Test cases for tracing setup helpers."""

    def tearDown(self) -> None:
        os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)

    def test_init_tracing_returns_provider(self) -> None:
        with (
            patch("src.tracing_setup.OTLPSpanExporter"),
            patch("src.tracing_setup.BatchSpanProcessor"),
        ):
            provider = tracing_setup.init_tracing(
                service_name="test-service",
                service_version="0.1.0",
                otlp_endpoint="http://localhost:4318",
            )

        self.assertIsInstance(provider, TracerProvider)

    def test_init_tracing_uses_env_endpoint(self) -> None:
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://example.com:4318"
        with (
            patch("src.tracing_setup.OTLPSpanExporter") as mock_exporter,
            patch("src.tracing_setup.BatchSpanProcessor"),
        ):
            tracing_setup.init_tracing(service_name="test-service")

        _, kwargs = mock_exporter.call_args
        self.assertEqual(kwargs.get("endpoint"), "http://example.com:4318")

    def test_enable_auto_instrumentation_does_not_raise(self) -> None:
        tracing_setup.enable_auto_instrumentation()

    def test_get_tracer_returns_tracer(self) -> None:
        tracer = tracing_setup.get_tracer("test.module")
        self.assertIsNotNone(tracer)


if __name__ == "__main__":
    unittest.main()
