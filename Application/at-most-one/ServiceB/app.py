import os
import time
import logging

from fastapi import FastAPI, Request
from pydantic import BaseModel

from opentelemetry import metrics, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

logger = logging.getLogger(__name__)
app = FastAPI()

OTEL_ENDPOINT = os.getenv("OpenTelemetry__Endpoint")

resource = Resource.create({ResourceAttributes.SERVICE_NAME: "service-b"})
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)
trace_exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

metric_exporter = OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True)
metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=1000)
metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metrics_provider)

HTTPXClientInstrumentor().instrument()
FastAPIInstrumentor.instrument_app(app)


class Message(BaseModel):
    message: str


@app.post("/api/message-b")
async def receive_message(payload: Message, request: Request):
    logger.info(
        f"[ServiceB] {time.strftime('%Y-%m-%d %H:%M:%S')} "
        f"from={request.client.host}:{request.client.port} message={payload.message!r}"
    )
    return {"status": "ok", "received": payload.message}
