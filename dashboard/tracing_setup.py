"""OpenTelemetry tracing setup for Abaco Analytics (dashboard-local copy).

This file lives in the Streamlit app root so the dashboard can be deployed as
its own App Service project root (i.e., deploy ./dashboard).

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
    service_name: str = "abaco-dashboard",
    service_version: str = "1.0.0",
    otlp_endpoint: Optional[str] = None,
) -> TracerProvider:
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
        }
    )

    tracer_provider = TracerProvider(resource=resource)

    # If another TracerProvider is already set (e.g. by auto-instrumentation or platform
    # init), avoid overriding it. Prefer the existing provider but still attach span
    # processors if possible.
    try:
        current_provider = trace.get_tracer_provider()
        if not isinstance(current_provider, TracerProvider):
            trace.set_tracer_provider(tracer_provider)
        else:
            # Use the existing provider instead of overriding
            tracer_provider = current_provider
            logger.info("Using existing tracer provider; not overriding.")
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not set tracer provider (it may already be initialized): %s", str(exc))
        tracer_provider = trace.get_tracer_provider()

    if otlp_endpoint is None:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

    try:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("OTEL tracing initialized with endpoint: %s", otlp_endpoint)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to initialize OTEL exporter for %s: %s", otlp_endpoint, str(exc))

    return tracer_provider


def enable_auto_instrumentation() -> None:
    try:
        # HTTPX instrumentation API changed in some package versions: try the newer
        # name first (HTTPXClientInstrumentor), then fall back to the older one
        # (HttpxInstrumentor) for compatibility.
        HTTPXInstrumentor = None
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor as HTTPXInstrumentor
        except ImportError:
            try:
                from opentelemetry.instrumentation.httpx import HttpxInstrumentor as HTTPXInstrumentor
            except ImportError:
                HTTPXInstrumentor = None

        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
        from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor

        if HTTPXInstrumentor is not None:
            try:
                HTTPXInstrumentor().instrument()
            except Exception:
                logger.exception("Failed to instrument httpx")
        else:
            logger.info(
                "HTTPX instrumentation not enabled: no compatible HTTPXInstrumentor could be imported"
            )

        RequestsInstrumentor().instrument()
        URLLib3Instrumentor().instrument()
        SQLite3Instrumentor().instrument()

        try:
            from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

            Psycopg2Instrumentor().instrument()
        except Exception:
            pass

        try:
            from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor

            PsycopgInstrumentor().instrument()
        except Exception:
            pass

        logger.info("Auto-instrumentation enabled for HTTP and DB clients")
    except Exception as exc:  # pragma: no cover
        logger.warning("Auto-instrumentation setup failed: %s", str(exc))


def get_tracer(name: str = __name__) -> trace.Tracer:
    return trace.get_tracer(name)


if not isinstance(trace.get_tracer_provider(), TracerProvider):
    try:
        init_tracing()
        enable_auto_instrumentation()
    except Exception as exc:  # pragma: no cover
        logger.warning("Tracing auto-init failed (will retry on explicit init): %s", str(exc))
