# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="NiA FBT26 App"
LABEL org.opencontainers.image.description="Advanced Flipper Zero Development Suite"
LABEL org.opencontainers.image.source="https://github.com/NaTo1000/NiA-FBT26"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source
COPY src/ ./src/
COPY config/ ./config/
COPY versions/ ./versions/

# Environment defaults (overridable at runtime)
ENV NIA_ENV=production \
    NIA_LOG_LEVEL=INFO \
    NIA_SERVER_PORT=8080 \
    NIA_DEBUG=false

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import json; json.load(open('config/runtime.json'))" || exit 1

ENTRYPOINT ["python3", "src/main.py"]
CMD ["--config", "config/runtime.json"]
