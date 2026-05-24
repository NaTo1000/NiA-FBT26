FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY docker/protocol-parser/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source code
COPY src/ /app/src/
COPY config/ /app/config/
COPY docker/protocol-parser/api_server.py /app/api_server.py

EXPOSE 8010

ENV PORT=8010 \
    MODEL_ID=meta-llama/Meta-Llama-3.1-8B-Instruct \
    TEMPERATURE=0.2 \
    MAX_NEW_TOKENS=1024 \
    LOCAL_MODEL_ENDPOINT=""

CMD ["python", "api_server.py"]
