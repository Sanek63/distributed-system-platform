from fastapi import FastAPI
from fastapi.middleware import Middleware

from core.logging import setup_logger
from core.opentelemetry import setup_observability
from core.config import config
from core.middleware import LoggerTracingMiddleware

from api.v1 import router as router_v1


def configure_application() -> FastAPI:
    setup_logger()

    app = FastAPI(
        title=config.APP_NAME,
        middleware=[Middleware(LoggerTracingMiddleware)],

    )
    app.include_router(router_v1)

    setup_observability(
        app=app,
        service_name=config.APP_NAME,
        otel_endpoint=config.OPENTELEMETRY_ENDRPOIND,
    )

    return app


app = configure_application()
