import os
import time
import logging
import random
import asyncio

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field

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


_old_factory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs):
    record = _old_factory(*args, **kwargs)
    span = trace.get_current_span()
    ctx = span.get_span_context()
    record.trace_id = f"{ctx.trace_id:032x}" if ctx and ctx.is_valid else "-"
    record.span_id = f"{ctx.span_id:016x}" if ctx and ctx.is_valid else "-"
    return record


logging.setLogRecordFactory(record_factory)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:[trace_id=%(trace_id)s span_id=%(span_id)s] %(message)s",
)
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
    messageId: str | None = Field(default=None)


_idempotency_store: dict[str, dict] = {}
_idempotency_lock = asyncio.Lock()


@app.post("/api/message-b")
async def receive_message(payload: Message, request: Request):
    logger.info(
        f"[service-b][in] {request.method} {request.url.path} "
        f"traceparent={request.headers.get('traceparent')} baggage={request.headers.get('baggage')}"
    )

    message_id = payload.messageId or request.headers.get("Idempotency-Key")
    if not message_id:
        raise HTTPException(status_code=400, detail="Missing messageId / Idempotency-Key")

    async with _idempotency_lock:
        cached = _idempotency_store.get(message_id)
        if cached is not None:
            logger.info(f"[service-b] idempotent hit messageId={message_id}")
            return cached

    r = random.random()
    if r < 0.20:
        delay_s = random.uniform(1.2, 3.5)
        logger.info(f"[service-b] random delay {delay_s:.2f}s")
        await asyncio.sleep(delay_s)

    elif r < 0.30:
        logger.info("[service-b] random failure 500")
        raise HTTPException(status_code=500, detail="Random failure")

    logger.info(f"[service-b] received messageId={message_id} message={payload.message!r} at={time.strftime('%Y-%m-%d %H:%M:%S')}")

    result = {"status": "ok", "received": payload.message, "messageId": message_id}

    async with _idempotency_lock:
        _idempotency_store[message_id] = result

    return result
