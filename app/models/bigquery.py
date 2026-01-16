"""
Pydantic models for BigQuery operations
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============== Dataset Models ==============

class DatasetResponse(BaseModel):
    """Response model for BigQuery dataset"""
    dataset_id: str = Field(..., description="Dataset ID")
    project: str = Field(..., description="GCP Project ID")
    location: str = Field(..., description="Dataset location (e.g., US, EU)")
    tables_count: Optional[int] = Field(None, description="Number of tables in dataset")
    created_at: Optional[datetime] = Field(None, description="Dataset creation time")
    modified_at: Optional[datetime] = Field(None, description="Last modified time")

    class Config:
        """Pydantic config"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DatasetsListResponse(BaseModel):
    """Response model for list of datasets"""
    status: str = Field(default="success", description="Response status")
    count: int = Field(..., description="Number of datasets")
    data: List[DatasetResponse] = Field(..., description="List of datasets")


# ============== Table Models ==============

class TableResponse(BaseModel):
    """Response model for BigQuery table"""
    table_id: str = Field(..., description="Table ID")
    dataset_id: str = Field(..., description="Dataset ID")
    project: str = Field(..., description="GCP Project ID")
    table_type: str = Field(..., description="Table type: TABLE, VIEW, EXTERNAL")
    num_rows: Optional[int] = Field(None, description="Number of rows")
    num_bytes: Optional[int] = Field(None, description="Size in bytes")
    created_at: Optional[datetime] = Field(None, description="Table creation time")
    modified_at: Optional[datetime] = Field(None, description="Last modified time")
    full_table_id: str = Field(..., description="Full table reference: project.dataset.table")

    class Config:
        """Pydantic config"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TablesListResponse(BaseModel):
    """Response model for list of tables"""
    status: str = Field(default="success", description="Response status")
    dataset_id: str = Field(..., description="Dataset ID")
    count: int = Field(..., description="Number of tables")
    data: List[TableResponse] = Field(..., description="List of tables")


# ============== Query Models ==============

class DirectQueryRequest(BaseModel):
    """Request model for direct SQL query"""
    sql: str = Field(..., description="SQL query to execute", min_length=1)
    project_id: Optional[str] = Field(None, description="GCP Project ID (overrides default)")
    dry_run: bool = Field(False, description="Validate query without executing")
    timeout_ms: Optional[int] = Field(60000, description="Query timeout in milliseconds", ge=1000, le=300000)
    use_query_cache: bool = Field(True, description="Use query cache")
    use_legacy_sql: bool = Field(False, description="Use legacy SQL")

    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
                "sql": "SELECT * FROM `project.dataset.table` LIMIT 10",
                "dry_run": False,
                "timeout_ms": 60000
            }
        }


class QueryRow(BaseModel):
    """Single row result"""
    data: Dict[str, Any] = Field(..., description="Row data as key-value pairs")


class QueryMetadata(BaseModel):
    """Query execution metadata"""
    job_id: str = Field(..., description="BigQuery job ID")
    total_rows_processed: Optional[int] = Field(None, description="Total rows processed")
    total_bytes_processed: Optional[int] = Field(None, description="Total bytes processed")
    bytes_billed: Optional[int] = Field(None, description="Bytes billed")
    cache_hit: bool = Field(..., description="Query result from cache")
    execution_time_ms: int = Field(..., description="Query execution time in milliseconds")
    slot_time_ms: Optional[int] = Field(None, description="Slot milliseconds consumed")


class QueryResponse(BaseModel):
    """Response model for query results"""
    status: str = Field(default="success", description="Response status")
    data: List[Dict[str, Any]] = Field(..., description="Query results")
    metadata: QueryMetadata = Field(..., description="Query execution metadata")
    row_count: int = Field(..., description="Number of rows returned")
    columns: List[str] = Field(..., description="Column names")

    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": [
                    {"column1": "value1", "column2": 123}
                ],
                "metadata": {
                    "job_id": "job-abc123",
                    "total_rows_processed": 1000,
                    "total_bytes_processed": 1024000,
                    "bytes_billed": 10240000,
                    "cache_hit": False,
                    "execution_time_ms": 1250,
                    "slot_time_ms": 5000
                },
                "row_count": 1,
                "columns": ["column1", "column2"]
            }
        }


# ============== Error Models ==============

class ErrorResponse(BaseModel):
    """Standard error response model"""
    status: str = Field(default="error", description="Response status")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
                "status": "error",
                "error_code": "BQ_QUERY_ERROR",
                "message": "Query execution failed",
                "details": {
                    "job_id": "job-abc123",
                    "errors": [
                        {
                            "message": "Table not found",
                            "location": "query",
                            "reason": "notFound"
                        }
                    ]
                }
            }
        }


# ============== Health Check Models ==============

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status: healthy, unhealthy")
    version: str = Field(..., description="Service version")
    bigquery_connected: bool = Field(..., description="BigQuery connection status")
    project_id: str = Field(..., description="GCP Project ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
