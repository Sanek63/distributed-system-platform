import os
import httpx
import logging
import uuid

from fastapi import FastAPI, HTTPException, Request
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

from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed


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

logging.getLogger("httpx").setLevel(logging.WARNING)


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
    messageId: str | None = Field(default=None)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(
        f"[service-a][in] {request.method} {request.url.path} "
        f"traceparent={request.headers.get('traceparent')} baggage={request.headers.get('baggage')}"
    )
    return await call_next(request)


@app.post("/api/message-a")
async def accept_and_forward(payload: Message):
    attempt_no = 0
    timeout = httpx.Timeout(connect=1.0, read=1.0, write=1.0, pool=1.0)

    if not payload.messageId:
        payload.messageId = str(uuid.uuid4())

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_fixed(0.2),
                reraise=True,
            ):
                with attempt:
                    attempt_no += 1

                    logger.info(f"[service-a] attempt={attempt_no} call service-b messageId={payload.messageId}")

                    try:
                        resp = await client.post(
                            f"{SERVICE_B_URL}/api/message-b",
                            json=payload.model_dump(),
                            headers={"Idempotency-Key": payload.messageId},
                        )
                    except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                        logger.info(f"[service-a] timeout -> connection aborted: {type(e).__name__}")
                        raise HTTPException(status_code=504, detail="Timeout calling service-b")

        except Exception as e:
            logger.info(f"[service-a] forward failed after retries: {type(e).__name__}")
            raise HTTPException(
                status_code=502,
                detail=f"Failed to forward to ServiceB after retries: {type(e).__name__}",
            )

    logger.info(f"[service-a] forwarded OK status={resp.status_code} messageId={payload.messageId}")

    return {"status": "forwarded", "service_b_status_code": resp.status_code, "messageId": payload.messageId}
