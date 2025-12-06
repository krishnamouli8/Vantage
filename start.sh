#!/bin/bash

# Quick start script for Vantage platform

echo "🚀 Starting Vantage Observability Platform..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first:"
    echo "   sudo systemctl start docker"
    echo "   sudo usermod -aG docker \$USER"
    echo "   newgrp docker"
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Start services
echo "📦 Starting services with Docker Compose..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "✅ Vantage Platform Started!"
echo ""
echo "🌐 Available Services:"
echo "   • Collector API:      http://localhost:8000"
echo "   • API Documentation:  http://localhost:8000/docs"
echo "   • Redpanda Console:   http://localhost:8080"
echo "   • Health Check:       http://localhost:8000/health"
echo ""
echo "📝 Redpanda is running on port 9093 (avoiding conflict with Antigravity on 9092)"
echo ""
echo "🧪 Test the platform:"
echo "   cd vantage-agent"
echo "   ./venv/bin/python test_agent.py"
echo ""
echo "📖 View logs:"
echo "   docker compose logs -f collector"
echo ""
echo "🛑 Stop services:"
echo "   docker compose down"
