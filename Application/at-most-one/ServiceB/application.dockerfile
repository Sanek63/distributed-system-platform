FROM python:3.12-slim

WORKDIR /code

RUN pip install --no-cache-dir -U \
    fastapi \
    uvicorn[standard] \
    httpx \
    pydantic-settings \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-semantic-conventions \
    opentelemetry-exporter-otlp-proto-grpc \
    opentelemetry-instrumentation-asgi \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-instrumentation-httpx 

COPY . /code

ENV PYTHONUNBUFFERED=1
EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
