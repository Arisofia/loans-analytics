"""
Azure Application Insights Tracing Integration (OpenTelemetry)
Enables distributed tracing, logging, and metrics collection for the analytics dashboard.
This implementation uses OpenTelemetry, the current industry standard replacing OpenCensus.
"""

import logging
import os
from typing import Any, Callable, Optional

try:
    from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

    HAS_OTEL_AZURE = True
except (ImportError, Exception):
    HAS_OTEL_AZURE = False

from opentelemetry import trace

# Configure logging
logger = logging.getLogger(__name__)


def _env_flag(name: str) -> bool:
    value = os.getenv(name)
    if value is None:
        return False
    return value.strip().lower() not in ("", "0", "false", "no")


def _telemetry_disabled() -> bool:
    return (
        _env_flag("DISABLE_TELEMETRY")
        or _env_flag("DISABLE_AZURE_TRACING")
        or _env_flag("CI")
        or bool(os.getenv("PYTEST_CURRENT_TEST"))
    )


def setup_azure_tracing(
    service_name: str = "abaco-analytics",
) -> Optional[trace.Tracer]:
    """Initialize Azure Application Insights tracing using OpenTelemetry.

    This function sets up the global TracerProvider and configures the Azure monitor exporter.
    Returns the tracer instance for the specified service.
    """
    if _telemetry_disabled():
        return trace.get_tracer(__name__)

    if not HAS_OTEL_AZURE:
        logger.warning(
            "Azure OpenTelemetry dependencies not fully functional. Tracing disabled."
        )
        return trace.get_tracer(service_name)

    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

    if (
        not connection_string
        or "00000000-0000-0000-0000-000000000000" in connection_string
    ):
        logger.warning(
            "Azure Application Insights connection string is missing or invalid. Tracing disabled."
        )
        return trace.get_tracer(__name__)

    try:
        # Create a resource to identify the service
        resource = Resource.create({SERVICE_NAME: service_name})

        # Configure TracerProvider with a sampler
        # ParentBasedTraceIdRatio(1.0) samples 100% of traces unless the parent span says otherwise
        sampler = ParentBasedTraceIdRatio(1.0)
        provider = TracerProvider(resource=resource, sampler=sampler)

        # Configure the Azure Monitor exporter
        exporter = AzureMonitorTraceExporter(connection_string=connection_string)
        span_processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(span_processor)

        # Set the global tracer provider
        trace.set_tracer_provider(provider)

        return trace.get_tracer(service_name)
    except Exception as e:
        logger.error("Failed to initialize Azure OpenTelemetry tracing: %s", e)
        return trace.get_tracer(__name__)


# Initialize global tracer
_tracer = setup_azure_tracing()


def trace_analytics_job(
    job_name: str, client_id: str, run_id: str
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for tracing analytics batch jobs using OpenTelemetry."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        from functools import wraps

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _tracer or trace.get_tracer(__name__)

            with tracer.start_as_current_span(f"{job_name}.{run_id}") as span:
                span.set_attribute("client_id", client_id)
                span.set_attribute("run_id", run_id)
                span.set_attribute("job_name", job_name)

                msg_prefix = "[TRACE]" if _tracer else "[TRACE-MOCK]"
                logger.info(
                    "%s Starting job: %s | client_id=%s | run_id=%s",
                    msg_prefix,
                    job_name,
                    client_id,
                    run_id,
                )
                try:
                    result = func(*args, **kwargs)
                    logger.info("%s Job completed: %s", msg_prefix, job_name)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    logger.error(
                        "%s Job failed: %s | error=%s", msg_prefix, job_name, e
                    )
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


if __name__ == "__main__":
    setup_azure_tracing()
    logger.info("Azure Application Insights tracing (OpenTelemetry) initialized")
