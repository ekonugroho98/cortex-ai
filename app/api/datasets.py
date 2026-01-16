"""
Dataset Endpoints
"""
from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.models.bigquery import (
    DatasetResponse,
    DatasetsListResponse,
    ErrorResponse
)
from app.services.bigquery_service import bigquery_service

router = APIRouter(tags=["Datasets"])


@router.get("/datasets", response_model=DatasetsListResponse)
async def list_datasets():
    """
    List all BigQuery datasets in the project

    Returns:
        List of datasets with metadata including table count
    """
    try:
        datasets = bigquery_service.list_datasets()

        return DatasetsListResponse(
            status="success",
            count=len(datasets),
            data=datasets
        )

    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "BQ_LIST_DATASETS_ERROR",
                "message": "Failed to list datasets",
                "details": {"error": str(e)}
            }
        )


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str):
    """
    Get details of a specific dataset

    Args:
        dataset_id: Dataset ID

    Returns:
        Dataset details
    """
    try:
        dataset = bigquery_service.get_dataset(dataset_id)
        return DatasetResponse(**dataset)

    except Exception as e:
        logger.error(f"Failed to get dataset {dataset_id}: {e}")

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
                "error_code": "BQ_GET_DATASET_ERROR",
                "message": "Failed to get dataset details",
                "details": {"error": str(e)}
            }
        )
