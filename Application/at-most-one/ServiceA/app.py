import os
import httpx

from fastapi import FastAPI, HTTPException
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

app = FastAPI()

SERVICE_B_URL = os.getenv("ServiceB__Url")
OTEL_ENDPOINT = os.getenv("OpenTelemetry__Endpoint")

resource = Resource.create({ResourceAttributes.SERVICE_NAME: "service-a"})
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)
trace_exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

metric_exporter = OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True)
metric_reader = PeriodicExportingMetricReader(
    metric_exporter,
    export_interval_millis=1000,
)
metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metrics_provider)

HTTPXClientInstrumentor().instrument()
FastAPIInstrumentor.instrument_app(app)


class Message(BaseModel):
    message: str


@app.post("/api/message-a")
async def accept_and_forward(payload: Message):
    async with httpx.AsyncClient(timeout=2.0) as client:
        try:
            resp = await client.post(
                f"{SERVICE_B_URL}/api/message-b",
                json=payload.model_dump(),
            )
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to forward to ServiceB: {type(e).__name__}",
            )

    return {"status": "forwarded", "service_b_status_code": resp.status_code}
