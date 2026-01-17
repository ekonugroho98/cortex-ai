#!/bin/bash
# Docker entrypoint script for CortexAI
# This script ensures environment variables are properly expanded

set -e

# Default PORT if not set (Cloud Run will set this automatically)
export PORT=${PORT:-8080}

echo "=================================="
echo "Starting CortexAI..."
echo "=================================="
echo "PORT=${PORT}"
echo "GCP_PROJECT_ID=${GCP_PROJECT_ID}"
echo "FASTAPI_ENV=${FASTAPI_ENV}"
echo "PYTHONUNBUFFERED=${PYTHONUNBUFFERED}"
echo "Working directory: $(pwd)"
echo "=================================="

# Check if app module exists
echo "Checking app.main module..."
python -c "import app.main; print('✓ app.main imported successfully')" || {
    echo "✗ Failed to import app.main"
    exit 1
}

echo "Starting uvicorn server on 0.0.0.0:${PORT}..."
# Execute uvicorn with the resolved PORT variable
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --log-level debug
