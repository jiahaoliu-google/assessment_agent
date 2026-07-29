# Multi-stage secure container build for Multi-Agent System
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt || true

# Production stage
FROM python:3.11-slim AS runner

WORKDIR /app

# Create non-root user and group for principle of least privilege
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

COPY --from=builder /install /usr/local
COPY . /app

# Ensure proper permissions
RUN chown -R appuser:appgroup /app

USER 10001

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["python3", "-m", "meal_planner.main"]
