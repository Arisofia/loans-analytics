"""
Azure Application Insights Tracing Integration
Enables distributed tracing, logging, and metrics collection for the analytics dashboard
"""

import logging
import os
from typing import Any, Callable, Tuple

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer


def setup_azure_tracing() -> Tuple[logging.Logger, Tracer]:
    """Initialize Azure Application Insights tracing.

    This function is idempotent: it will not add duplicate AzureLogHandler
    instances to the root logger if one already exists. Callers should prefer
    to initialize tracing once at module import time and reuse the returned
    `(logger, tracer)` pair rather than invoking this repeatedly.
    """

    connection_string = os.getenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "InstrumentationKey=00000000-0000-0000-0000-000000000000",
    )

    # Configure logging handler only if not already present
    logger = logging.getLogger()
    has_azure_handler = any(isinstance(h, AzureLogHandler) for h in logger.handlers)

    if not has_azure_handler:
        handler = AzureLogHandler(connection_string=connection_string)
        handler.setLevel(logging.INFO)

        # Configure formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    # Configure trace exporter and tracer (ok to recreate tracer object)
    trace_exporter = AzureExporter(connection_string=connection_string)
    tracer = Tracer(
        exporter=trace_exporter,
        sampler=ProbabilitySampler(rate=1.0),  # Sample 100% in development, adjust for production
    )

    return logger, tracer


# Initialize once at module import so tracing/log handlers are not
# repeatedly created for every decorated function invocation.
try:
    _logger, _tracer = setup_azure_tracing()
except Exception:
    # If initialization fails (missing packages or config), fall back to
    # module-level defaults so decorators still work without tracing.
    _logger = logging.getLogger(__name__)


def trace_analytics_job(
    job_name: str, client_id: str, run_id: str
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for tracing analytics batch jobs.

    Uses module-level `_tracer` and `_logger` that were initialized once at
    import time to prevent resource leaks and duplicated handlers.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        from functools import wraps

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = _logger
            tracer = globals().get("_tracer")

            if tracer is not None:
                with tracer.span(name=f"{job_name}.{run_id}") as span:
                    span.add_attribute("client_id", client_id)
                    span.add_attribute("run_id", run_id)
                    span.add_attribute("job_name", job_name)

                    logger.info(
                        "[TRACE] Starting job: %s | client_id=%s | run_id=%s",
                        job_name,
                        client_id,
                        run_id,
                    )
                    try:
                        result = func(*args, **kwargs)
                        logger.info("[TRACE] Job completed: %s", job_name)
                        span.add_attribute("status", "success")
                        return result
                    except Exception as e:
                        logger.error("[TRACE] Job failed: %s | error=%s", job_name, e)
                        span.add_attribute("status", "failed")
                        span.add_attribute("error", str(e))
                        raise
            else:
                # Tracing not available; run function normally and log start/finish.
                logger.info(
                    "[TRACE-MOCK] Starting job: %s | client_id=%s | run_id=%s",
                    job_name,
                    client_id,
                    run_id,
                )
                try:
                    result = func(*args, **kwargs)
                    logger.info("[TRACE-MOCK] Job completed: %s", job_name)
                    return result
                except Exception as e:
                    logger.error("[TRACE-MOCK] Job failed: %s | error=%s", job_name, e)
                    raise

        return wrapper

    return decorator


# Example usage in batch runner
if __name__ == "__main__":
    logger, tracer = setup_azure_tracing()
    logger.info("Azure Application Insights tracing initialized")
