#!/bin/bash

# Dependency Radar - Quick Start Script
# Usage: ./start.sh [prod|dev]

set -e

MODE=${1:-prod}

echo "🚀 Dependency Radar - Starting in $MODE mode..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not available. Please install Docker Compose."
    exit 1
fi

# Determine docker-compose command
if docker compose version &> /dev/null; then
    DC="docker compose"
else
    DC="docker-compose"
fi

case $MODE in
    prod)
        echo "📦 Building production images..."
        $DC build
        echo "🔄 Starting services (production mode)..."
        $DC up -d
        echo ""
        echo "✅ Services started!"
        echo ""
        echo "📍 Frontend: http://localhost:5173"
        echo "📍 Backend:  http://localhost:8000"
        echo "📍 API Docs: http://localhost:8000/docs"
        echo ""
        echo "To view logs: $DC logs -f"
        echo "To stop:      $DC down"
        ;;
    dev)
        echo "📦 Starting development environment..."
        $DC -f docker-compose.dev.yml up -d
        echo ""
        echo "✅ Development services started!"
        echo ""
        echo "📍 Frontend: http://localhost:5173 (with hot-reload)"
        echo "📍 Backend:  http://localhost:8000 (with auto-reload)"
        echo "📍 pgAdmin:  http://localhost:5050 (admin@radar.local / admin)"
        echo "📍 API Docs: http://localhost:8000/docs"
        echo ""
        echo "To view logs: $DC -f docker-compose.dev.yml logs -f"
        echo "To stop:      $DC -f docker-compose.dev.yml down"
        ;;
    *)
        echo "❌ Unknown mode: $MODE"
        echo "Usage: $0 [prod|dev]"
        exit 1
        ;;
esac

echo ""
echo "💡 First time? Register a project:"
echo "   curl -X POST 'http://localhost:8000/api/v1/projects/register' \\"
echo "     -H 'X-API-Key: default-api-key' \\"
echo "     -F 'project_name=my-app' \\"
echo "     -F 'environment=Dev' \\"
echo "     -F 'dependency_file=@requirements.txt'"
echo ""
