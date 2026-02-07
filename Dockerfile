# Base image - pin to Python 3.12 (minor) while tracking latest patch for security updates
FROM python:3.12-slim
# Set working directory
WORKDIR /app
# Install system dependencies
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  curl \
  && rm -rf /var/lib/apt/lists/*
# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy application code
COPY . .
# Expose FastAPI port
EXPOSE 8000
# Bind to all interfaces so Azure health probes can reach the app
ENV API_HOST=0.0.0.0
# Create non-root user and set permissions
RUN useradd --system --create-home --home-dir /app appuser \
  && chown -R appuser:appuser /app
USER appuser
# Healthcheck and Entrypoint
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1
ENTRYPOINT ["python", "-m", "python.apps.analytics.api.main"]
