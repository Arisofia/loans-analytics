#!/bin/bash

# Startup script for Abaco Analytics Dashboard on Azure Web App
# This script runs the Streamlit application on port 8000
# Azure Web Apps require the app to listen on port 8000 for the default configuration

set -e

echo "🚀 Starting Abaco Analytics Dashboard..."

# Set environment variables for production
export STREAMLIT_SERVER_PORT=8000
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_LOGGER_LEVEL=info
export STREAMLIT_CLIENT_LOGGER_LEVEL=info

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --quiet

echo "✅ Dependencies installed"

# Run Streamlit app
echo "🎯 Starting Streamlit application on port 8000..."
exec streamlit run streamlit_app.py \
	--server.port=8000 \
	--server.address=0.0.0.0 \
	--logger.level=info \
	--client.logger.level=info
