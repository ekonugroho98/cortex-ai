#!/bin/bash
# Docker entrypoint script for CortexAI
# This script ensures environment variables are properly expanded

set -e

# Default PORT if not set (Cloud Run will set this automatically)
export PORT=${PORT:-8080}

echo "Starting CortexAI..."
echo "PORT=${PORT}"
echo "GCP_PROJECT_ID=${GCP_PROJECT_ID}"
echo "FASTAPI_ENV=${FASTAPI_ENV}"

# Execute uvicorn with the resolved PORT variable
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
