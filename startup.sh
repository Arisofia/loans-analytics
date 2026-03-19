#!/bin/bash

# Startup script for Abaco Analytics Dashboard
# This script runs the Streamlit application on a configurable port
# Default: 8000 (Azure Web Apps standard, aligns with API service)
# Override: set STREAMLIT_SERVER_PORT environment variable

set -e

echo "🚀 Starting Abaco Analytics Dashboard..."

# Determine canonical port from environment or use default (8000)
CANONICAL_PORT=${STREAMLIT_SERVER_PORT:-8000}
export STREAMLIT_SERVER_PORT=${CANONICAL_PORT}

# Set environment variables for production
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_LOGGER_LEVEL=info
export STREAMLIT_CLIENT_LOGGER_LEVEL=info

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --quiet

echo "✅ Dependencies installed"

# Run Streamlit app on the canonical port
echo "🎯 Starting Streamlit application on port ${CANONICAL_PORT}..."
exec streamlit run frontend/streamlit_app/app.py \
	--server.port=${CANONICAL_PORT} \
	--server.address=0.0.0.0 \
	--logger.level=info \
	--client.logger.level=info
