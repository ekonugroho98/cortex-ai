"""
Table Endpoints
"""
from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.models.bigquery import (
    TableResponse,
    TablesListResponse
)
from app.services.bigquery_service import bigquery_service

router = APIRouter(tags=["Tables"])


@router.get("/datasets/{dataset_id}/tables", response_model=TablesListResponse)
async def list_tables(dataset_id: str):
    """
    List all tables in a dataset

    Args:
        dataset_id: Dataset ID

    Returns:
        List of tables with metadata
    """
    try:
        tables = bigquery_service.list_tables(dataset_id)

        return TablesListResponse(
            status="success",
            dataset_id=dataset_id,
            count=len(tables),
            data=tables
        )

    except Exception as e:
        logger.error(f"Failed to list tables for dataset {dataset_id}: {e}")

        # Check if dataset not found
        if "Not found" in str(e) or "does not exist" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "BQ_DATASET_NOT_FOUND",
                    "message": f"Dataset '{dataset_id}' not found",
                    "details": {"dataset_id": dataset_id}
                }
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "BQ_LIST_TABLES_ERROR",
                "message": "Failed to list tables",
                "details": {"error": str(e)}
            }
        )


@router.get("/datasets/{dataset_id}/tables/{table_id}", response_model=TableResponse)
async def get_table(dataset_id: str, table_id: str):
    """
    Get details of a specific table including schema

    Args:
        dataset_id: Dataset ID
        table_id: Table ID

    Returns:
        Table details with schema
    """
    try:
        table = bigquery_service.get_table(dataset_id, table_id)
        return TableResponse(**table)

    except Exception as e:
        logger.error(f"Failed to get table {dataset_id}.{table_id}: {e}")

        # Check if table not found
        if "Not found" in str(e) or "does not exist" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "BQ_TABLE_NOT_FOUND",
                    "message": f"Table '{dataset_id}.{table_id}' not found",
                    "details": {
                        "dataset_id": dataset_id,
                        "table_id": table_id
                    }
                }
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "BQ_GET_TABLE_ERROR",
                "message": "Failed to get table details",
                "details": {"error": str(e)}
            }
        )
