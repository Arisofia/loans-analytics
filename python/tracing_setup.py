# Tracing setup for Python (OpenTelemetry)
# Add this to your main entry point (e.g., main.py, dashboard.py, or analytics pipeline)

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.auto_instrumentation import auto_instrumentation
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Set up tracer provider
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure OTLP exporter (local endpoint)
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

auto_instrumentation.instrument()


# Example usage: wrap a function with a span
def traced_function():
    with tracer.start_as_current_span("example-span"):
        # ... your code here ...
        pass


# Call traced function in your workflow
traced_function()
