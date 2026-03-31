# ── Stage 1: Dependency install ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy only dependency manifests first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install production deps into /app/.venv
RUN uv sync --frozen --no-dev


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim

# curl is needed for the healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the pre-built venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY . .

# Put the venv on PATH so plain `python` / `uvicorn` work without `uv run`
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
