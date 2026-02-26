# Base image - pin to Python 3.12 (minor) while tracking latest patch for security updates
FROM python:3.12-slim
# Set working directory
WORKDIR /app
# Copy requirements and install Python dependencies
COPY requirements.txt .
ENV PIP_DEFAULT_TIMEOUT=600
RUN pip install --no-cache-dir --retries 10 --prefer-binary -r requirements.txt
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
HEALTHCHECK CMD python -c "import sys,urllib.request;sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=5).status == 200 else 1)"
ENTRYPOINT ["python", "-m", "python.apps.analytics.api.main"]
