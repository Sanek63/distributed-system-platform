from uuid import uuid4

from starlette.types import ASGIApp, Receive, Scope, Send
from opentelemetry import metrics, trace

from core.logging import set_tracing_context, reset_session_context


class LoggerTracingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        span = trace.get_current_span()
        ctx = span.get_span_context()

        context = set_tracing_context(tracing_value=f"{ctx.trace_id:032x}")

        try:
            await self.app(scope, receive, send)
        except Exception as e:
            raise e
        finally:
            reset_session_context(context=context)
