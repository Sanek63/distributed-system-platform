from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, ResourceAttributes
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def build_resource(service_name: str) -> Resource:
    return Resource.create({ResourceAttributes.SERVICE_NAME: service_name})


def setup_tracing(
    *,
    resource: Resource,
    otel_endpoint: str,
    insecure: bool = True,
) -> TracerProvider:
    trace_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(trace_provider)

    trace_exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=insecure)
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

    return trace_provider


def setup_metrics(
    *,
    resource: Resource,
    otel_endpoint: str,
    insecure: bool = True,
    export_interval_millis: int = 1000,
) -> MeterProvider:
    metric_exporter = OTLPMetricExporter(endpoint=otel_endpoint, insecure=insecure)
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=export_interval_millis,
    )
    metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(metrics_provider)

    return metrics_provider


def instrument_fastapi_and_httpx(app) -> None:
    HTTPXClientInstrumentor().instrument()
    FastAPIInstrumentor.instrument_app(app)


def setup_observability(
    *,
    app,
    service_name: str,
    otel_endpoint: str,
    insecure: bool = True,
    export_interval_millis: int = 1000,
) -> None:
    resource = build_resource(service_name)

    setup_tracing(
        resource=resource,
        otel_endpoint=otel_endpoint,
        insecure=insecure,
    )
    setup_metrics(
        resource=resource,
        otel_endpoint=otel_endpoint,
        insecure=insecure,
        export_interval_millis=export_interval_millis,
    )
    instrument_fastapi_and_httpx(app)
