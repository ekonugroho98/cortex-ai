"""
Health Check Endpoints
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.bigquery import HealthCheckResponse
from app.services.bigquery_service import bigquery_service
from app import __version__

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint

    Returns service status and BigQuery connection status
    """
    try:
        # Test BigQuery connection
        bq_connected = bigquery_service.test_connection()

        return HealthCheckResponse(
            status="healthy" if bq_connected else "unhealthy",
            version=__version__,
            bigquery_connected=bq_connected,
            project_id=bigquery_service.project_id
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "message": "Service unavailable",
                "error": str(e)
            }
        )


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "BigQuery AI Service",
        "version": __version__,
        "status": "running",
        "docs": "/docs"
    }
