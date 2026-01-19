"""
Table Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from loguru import logger
from typing import Dict, Any

from app.models.bigquery import (
    TableResponse,
    TablesListResponse,
    PaginatedResponse
)
from app.services.bigquery_service import BigQueryService
from app.dependencies import get_bigquery_service_async
from app.utils.common import paginate_list

router = APIRouter(tags=["Tables"])


@router.get("/datasets/{dataset_id}/tables", response_model=PaginatedResponse[TableResponse])
async def list_tables(
    dataset_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    bq: BigQueryService = Depends(get_bigquery_service_async)
) -> PaginatedResponse[TableResponse]:
    """
    List all tables in a dataset (with pagination)

    Args:
        dataset_id: Dataset ID
        page: Page number (1-indexed, default: 1)
        page_size: Items per page (default: 50, max: 1000)
        bq: BigQuery service (injected via dependency injection)

    Returns:
        Paginated list of tables with metadata

    Example:
        GET /datasets/analytics/tables?page=2&page_size=20

        Response:
        {
            "data": [...],
            "pagination": {
                "page": 2,
                "page_size": 20,
                "total": 150,
                "total_pages": 8,
                "has_next": true,
                "has_prev": true
            }
        }
    """
    try:
        tables = await bq.list_tables_async(dataset_id)

        # Paginate results
        result = paginate_list(tables, page=page, page_size=page_size)

        return PaginatedResponse[TableResponse](
            data=result["data"],
            pagination=result["pagination"]
        )

    except Exception as e:
        logger.error(f"Failed to list tables for dataset {dataset_id}: {e}", exc_info=True)

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
                "error_code": "LIST_TABLES_ERROR",
                "message": "Failed to list tables"
            }
        )


@router.get("/datasets/{dataset_id}/tables/{table_id}", response_model=TableResponse)
async def get_table(
    dataset_id: str,
    table_id: str,
    bq: BigQueryService = Depends(get_bigquery_service_async)
) -> TableResponse:
    """
    Get details of a specific table including schema

    Args:
        dataset_id: Dataset ID
        table_id: Table ID
        bq: BigQuery service (injected via dependency injection)

    Returns:
        Table details with schema
    """
    try:
        table = await bq.get_table_async(dataset_id, table_id)
        return TableResponse(**table)

    except Exception as e:
        logger.error(f"Failed to get table {dataset_id}.{table_id}: {e}", exc_info=True)

        error_msg = str(e)
        if "Not found" in error_msg or "does not exist" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "TABLE_NOT_FOUND",
                    "message": f"Table '{dataset_id}.{table_id}' not found"
                }
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "GET_TABLE_ERROR",
                "message": "Failed to get table details"
            }
        )
