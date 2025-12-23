# Tracing setup for Python (OpenTelemetry)
# Add this to your main entry point (e.g., main.py, dashboard.py, or analytics pipeline)

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.auto_instrumentation import auto_instrumentation
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_tracing(service_name: Optional[str] = None) -> None:
    """Configure OpenTelemetry tracing without side effects on import.

    The previous implementation eagerly instrumented the application on module
    import. Bandit treats import-time network calls as high risk because they
    bypass the caller's ability to control connectivity. We now gate the setup
    behind an explicit function call and allow overriding the OTLP endpoint via
    ``OTEL_EXPORTER_OTLP_ENDPOINT`` to support TLS-enabled collectors.
    """

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://localhost:4318/v1/traces")
    resource = Resource.create({SERVICE_NAME: service_name or "abaco-loans-analytics"})

    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer(__name__)

    otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    auto_instrumentation.instrument()

    # Example usage: wrap a function with a span
    with tracer.start_as_current_span("tracing-setup"):
        tracer.add_event("Tracing initialized")
