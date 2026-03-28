# Generic Model Runner Dockerfile
# Configured at runtime via MODEL_ROLE and MODEL_PORT env vars.

FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn httpx pyyaml requests

COPY docker/model_runner/model_runner.py ./model_runner.py
COPY config/orchestration/settings.yaml ./config/orchestration/settings.yaml

ENV PYTHONPATH=/app

CMD ["sh", "-c", "uvicorn model_runner:app --host 0.0.0.0 --port ${MODEL_PORT:-8001}"]
