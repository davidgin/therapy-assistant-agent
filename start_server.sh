#!/bin/bash

# Start the Therapy Assistant Agent API server

echo "🚀 Starting Therapy Assistant Agent API..."

# Change to backend directory
cd "$(dirname "$0")/backend"

# Set Python path
export PYTHONPATH="$(pwd)"

# Start the server
echo "📍 Server will be available at: http://localhost:8000"
echo "📍 API docs will be available at: http://localhost:8000/docs"
echo "📍 Health check: http://localhost:8000/health"
echo ""

uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload