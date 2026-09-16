# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build tools needed by some packages (e.g. numpy, pydantic)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer-caching
COPY requirements.txt .

# Install into a prefix so we can copy only the installed packages
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy project source
COPY . .

# Create a non-root user for security
RUN adduser --disabled-password --no-create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose both service ports
EXPOSE 8000 8501

# Default: FastAPI backend.
# Override CMD in docker-compose to run Streamlit.
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
