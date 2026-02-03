#!/bin/bash
# Quick start script for Prometheus + Grafana monitoring stack
# Usage: bash scripts/start_monitoring.sh

set -e

echo "🚀 Starting Prometheus + Grafana monitoring stack..."
echo ""

# Load environment variables
if [ ! -f .env.local ]; then
    echo "❌ Error: .env.local not found"
    echo "   Run: cp .env.example .env.local"
    exit 1
fi

source scripts/load_env.sh > /dev/null 2>&1

# Check required variables
if [ -z "$SUPABASE_SECRET_API_KEY" ]; then
    echo "❌ Error: SUPABASE_SECRET_API_KEY not set in .env.local"
    exit 1
fi

if [ -z "$SUPABASE_PROJECT_REF" ]; then
    echo "❌ Error: SUPABASE_PROJECT_REF not set in .env.local"
    exit 1
fi

# Set Grafana password if not set
if [ -z "$GRAFANA_ADMIN_PASSWORD" ]; then
    export GRAFANA_ADMIN_PASSWORD="admin123"
    echo "⚠️  Using default Grafana password: admin123"
    echo "   Set GRAFANA_ADMIN_PASSWORD in .env.local for production"
fi

# Export variables for docker-compose
export SUPABASE_SECRET_API_KEY
export SUPABASE_PROJECT_REF
export GRAFANA_ADMIN_PASSWORD

echo "✅ Environment variables loaded"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Start Docker Desktop and try again"
    exit 1
fi

echo "🐳 Starting Docker containers..."
docker-compose -f docker-compose.monitoring.yml up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.monitoring.yml ps

echo ""
echo "✅ Monitoring stack started successfully!"
echo ""
echo "🌐 Access URLs:"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana:    http://localhost:3001 (admin / ${GRAFANA_ADMIN_PASSWORD})"
echo "   Alertmanager: http://localhost:9093"
echo ""
echo "📋 Next steps:"
echo "   1. Open Grafana: http://localhost:3001"
echo "   2. Login with admin / ${GRAFANA_ADMIN_PASSWORD}"
echo "   3. Add Prometheus datasource: http://prometheus:9090"
echo "   4. Import Supabase dashboard (ID: 19822)"
echo ""
echo "📚 Full guide: docs/PROMETHEUS_GRAFANA_QUICKSTART.md"
echo ""
echo "🔧 Useful commands:"
echo "   View logs:  docker-compose -f docker-compose.monitoring.yml logs -f"
echo "   Stop:       docker-compose -f docker-compose.monitoring.yml down"
echo "   Restart:    docker-compose -f docker-compose.monitoring.yml restart"
