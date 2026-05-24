# Multi-stage Dockerfile for the Super Orchestrator (port 7000)

# ── Stage 1: build dependencies ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install \
    fastapi uvicorn httpx pyyaml

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /install /usr/local
COPY src/orchestration/ ./src/orchestration/
COPY config/orchestration/settings.yaml ./config/orchestration/settings.yaml

ENV PYTHONPATH=/app

EXPOSE 7000

CMD ["uvicorn", "src.orchestration.super_orchestrator:app", \
     "--host", "0.0.0.0", "--port", "7000"]
