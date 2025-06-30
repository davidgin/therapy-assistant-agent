#!/bin/bash

# Therapy Assistant - Async Server Startup Script

echo "Starting Therapy Assistant API (Async Version)..."

# Set default environment variables if not set
export OPENAI_API_KEY=${OPENAI_API_KEY:-"your_openai_api_key_here"}
export DATABASE_URL=${DATABASE_URL:-"sqlite+aiosqlite:///./therapy_assistant.db"}
export SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}

# Create necessary directories
mkdir -p backend/logs
mkdir -p backend/data/synthetic
mkdir -p backend/data/analysis_results

# Change to backend directory
cd backend

# Install/update dependencies
echo "Installing async dependencies..."
pip install -r requirements.txt

# Run database migrations if needed
echo "Running database migrations..."
alembic upgrade head

# Start the async server
echo "Starting async FastAPI server..."
uvicorn app.main_auth_async:app --host 0.0.0.0 --port 8000 --reload --log-level info

echo "Server stopped."