# Build context: repository root (so services/shared is reachable)
# Build:  docker build -f services/module1-integrity/Dockerfile -t researchly-m1 .
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/module1-integrity/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy service code + shared utils. Layout inside /app mirrors the services/ tree
# so `from shared.embedding_utils import embed` works via the sys.path bootstrap
# in app/main.py.
COPY services/module1-integrity/app ./app
COPY services/shared ./shared

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
