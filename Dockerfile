# Stage 1: Build dependencies with uv
FROM python:3.11-slim AS builder

# Install uv by copying the binary from the official uv image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./
# COPY uv.lock ./   # uncomment if you have a lock file

# Install dependencies (no lock-related flags needed)
RUN uv sync --no-dev --no-install-project

# Stage 2: Production image
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY app ./app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]