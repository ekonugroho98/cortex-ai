"""
Health Check Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from typing import Dict, Any

from app.models.bigquery import HealthCheckResponse
from app.services.bigquery_service import BigQueryService
from app.dependencies import get_bigquery_service_async
from app import __version__

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    bq: BigQueryService = Depends(get_bigquery_service_async)
) -> HealthCheckResponse:
    """
    Health check endpoint

    Returns service status and BigQuery connection status
    """
    try:
        # Test BigQuery connection
        bq_connected = await bq.test_connection_async()

        return HealthCheckResponse(
            status="healthy" if bq_connected else "unhealthy",
            version=__version__,
            bigquery_connected=bq_connected,
            project_id=bq.project_id
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "message": "Service unavailable"
            }
        )


@router.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "service": "BigQuery AI Service",
        "version": __version__,
        "status": "running",
        "docs": "/docs"
    }
