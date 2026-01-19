"""
Dataset Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from loguru import logger
from typing import Optional
import time

from app.models.bigquery import (
    DatasetResponse,
    DatasetsListResponse,
    ErrorResponse,
    PaginatedResponse
)
from app.services.bigquery_service import BigQueryService
from app.dependencies import get_bigquery_service_async
from app.utils.common import paginate_list
from app.utils.logging import log_bigquery_operation

router = APIRouter(tags=["Datasets"])


@router.get("/datasets", response_model=PaginatedResponse[DatasetResponse])
async def list_datasets(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    bq: BigQueryService = Depends(get_bigquery_service_async)
) -> PaginatedResponse[DatasetResponse]:
    """
    List all BigQuery datasets in the project (with pagination)

    Args:
        page: Page number (1-indexed, default: 1)
        page_size: Items per page (default: 50, max: 1000)
        bq: BigQuery service (injected via dependency injection)

    Returns:
        Paginated list of datasets with metadata including table count

    Example:
        GET /datasets?page=2&page_size=10

        Response:
        {
            "data": [...],
            "pagination": {
                "page": 2,
                "page_size": 10,
                "total": 25,
                "total_pages": 3,
                "has_next": true,
                "has_prev": true
            }
        }
    """
    start_time = time.time()
    try:
        datasets = await bq.list_datasets_async()

        # Paginate results
        result = paginate_list(datasets, page=page, page_size=page_size)

        duration_ms = int((time.time() - start_time) * 1000)
        log_bigquery_operation(
            operation="list_datasets",
            success=True,
            duration_ms=duration_ms,
            result_count=len(datasets),
            page=page,
            page_size=page_size
        )

        return PaginatedResponse[DatasetResponse](
            data=result["data"],
            pagination=result["pagination"]
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_bigquery_operation(
            operation="list_datasets",
            success=False,
            duration_ms=duration_ms,
            error=str(e)
        )

        logger.error(f"Failed to list datasets: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "LIST_DATASETS_ERROR",
                "message": "Failed to list datasets"
            }
        )


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    bq: BigQueryService = Depends(get_bigquery_service_async)
) -> DatasetResponse:
    """
    Get details of a specific dataset

    Args:
        dataset_id: Dataset ID
        bq: BigQuery service (injected via dependency injection)

    Returns:
        Dataset details
    """
    try:
        dataset = await bq.get_dataset_async(dataset_id)
        return DatasetResponse(**dataset)

    except Exception as e:
        logger.error(f"Failed to get dataset {dataset_id}: {e}", exc_info=True)

        error_msg = str(e)
        if "Not found" in error_msg or "does not exist" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "DATASET_NOT_FOUND",
                    "message": f"Dataset '{dataset_id}' not found"
                }
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "GET_DATASET_ERROR",
                "message": "Failed to get dataset details"
            }
        )
