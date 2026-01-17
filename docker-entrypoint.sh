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
echo "Python version: $(python --version)"
echo "=================================="

# List installed packages for debugging
echo "Checking critical dependencies..."
python -c "
import sys
try:
    import fastapi
    print(f'✓ FastAPI {fastapi.__version__}')
except ImportError as e:
    print(f'✗ FastAPI: {e}')
    sys.exit(1)

try:
    import uvicorn
    print(f'✓ Uvicorn {uvicorn.__version__}')
except ImportError as e:
    print(f'✗ Uvicorn: {e}')
    sys.exit(1)

try:
    import google.cloud.bigquery
    print(f'✓ google-cloud-bigquery installed')
except ImportError as e:
    print(f'✗ google-cloud-bigquery: {e}')
    sys.exit(1)

print('✓ All critical dependencies OK')
"

# Check if app module exists
echo ""
echo "Checking app.main module..."
python -c "import app.main; print('✓ app.main imported successfully')" 2>&1 || {
    echo "✗ Failed to import app.main"
    echo "Showing traceback..."
    python -c "import app.main" 2>&1 || true
    exit 1
}

echo ""
echo "Starting uvicorn server on 0.0.0.0:${PORT}..."
# Execute uvicorn with the resolved PORT variable
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --log-level info
