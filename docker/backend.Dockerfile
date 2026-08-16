FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

# ---------- targets ----------

FROM base AS api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

FROM base AS celery-worker
CMD ["celery", "-A", "app.workers.celery_app:celery_app", "worker", \
     "--loglevel=info", "--concurrency=4", "-Q", "default,sync,ingest,eval"]

FROM base AS celery-beat
CMD ["celery", "-A", "app.workers.celery_app:celery_app", "beat", "--loglevel=info"]
