"""OpenTelemetry tracing setup for Abaco Analytics.

Configures distributed tracing with support for:
- Azure Application Insights (via OTLP exporter)
- Local OTEL collector (fallback)
- Auto-instrumentation of common libraries (httpx, requests, etc.)
"""

import logging
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def init_tracing(
    service_name: str = "abaco-analytics",
    service_version: str = "1.0.0",
    otlp_endpoint: Optional[str] = None,
) -> TracerProvider:
    """Initialize OpenTelemetry tracing with Azure or local OTEL exporter.

    Args:
        service_name: Name of the service for resource labels.
        service_version: Version of the service.
        otlp_endpoint: OTLP exporter endpoint. If None, uses env var or
                       defaults to localhost:4318.

    Returns:
        Configured TracerProvider instance.
    """
    # Create resource with service attributes
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
        }
    )

    # Initialize tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Determine OTLP endpoint
    if otlp_endpoint is None:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

    try:
        # Create OTLP exporter
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)

        # Add batch span processor
        span_processor = BatchSpanProcessor(exporter)
        tracer_provider.add_span_processor(span_processor)

        logger.info("OTEL tracing initialized with endpoint: %s", otlp_endpoint)
    except Exception as e:
        logger.warning("Failed to initialize OTEL exporter for %s: %s", otlp_endpoint, str(e))

    return tracer_provider


def enable_auto_instrumentation() -> None:
    """Enable auto-instrumentation for common libraries.

    Instruments:
    - httpx (HTTP client)
    - requests (HTTP client)
    - urllib3 (low-level HTTP)
    - sql (database queries)
    """
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
        from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor

        HTTPXClientInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        URLLib3Instrumentor().instrument()
        SQLite3Instrumentor().instrument()

        try:
            PsycopgInstrumentor().instrument()
        except Exception:  # psycopg might not be installed
            pass

        logger.info("Auto-instrumentation enabled for HTTP and DB clients")
    except Exception as e:
        logger.warning("Auto-instrumentation setup failed: %s", str(e))


def get_tracer(name: str = __name__) -> trace.Tracer:
    """Get a tracer instance for the given module name.

    Args:
        name: Module/component name for the tracer.

    Returns:
        Tracer instance.
    """
    return trace.get_tracer(name)


# Initialize on import if not already done
if not isinstance(trace.get_tracer_provider(), TracerProvider):
    try:
        init_tracing()
        enable_auto_instrumentation()
    except Exception as e:
        logger.warning("Tracing auto-init failed (will retry on explicit init): %s", str(e))
