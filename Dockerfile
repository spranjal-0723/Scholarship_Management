# Multi-stage production Dockerfile for Scholarship and Fee Management System
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

FROM python:3.12-slim AS runner

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
COPY . /app

# Non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=5000 \
    FLASK_DEBUG=false \
    PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["gunicorn", "--chdir", "backend", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120"]
