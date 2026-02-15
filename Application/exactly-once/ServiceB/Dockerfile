FROM python:3.12-slim

WORKDIR /code

RUN pip install --no-cache-dir -U \
    fastapi \
    tenacity \
    uvicorn[standard] \
    httpx \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-semantic-conventions \
    opentelemetry-exporter-otlp-proto-grpc \
    opentelemetry-instrumentation-asgi \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-instrumentation-httpx

COPY app.py /code/app.py

ENV PYTHONUNBUFFERED=1
EXPOSE 80

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80", "--no-access-log", "--log-level", "warning"]