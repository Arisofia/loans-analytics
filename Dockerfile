# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
  build-essential \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports for Streamlit and FastAPI
EXPOSE 8501
EXPOSE 8000

# Create non-root user and set permissions
RUN useradd --system --create-home --home-dir /app appuser \
  && chown -R appuser:appuser /app
USER appuser

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || curl --fail http://localhost:8000/health || exit 1

# Default command (Streamlit)
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
