"""
Query Endpoints
"""
from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.models.bigquery import (
    DirectQueryRequest,
    QueryResponse
)
from app.services.bigquery_service import bigquery_service

router = APIRouter(tags=["Query"])


@router.post("/query", response_model=QueryResponse)
async def execute_query(request: DirectQueryRequest):
    """
    Execute direct SQL query to BigQuery

    This endpoint allows you to execute raw SQL queries against BigQuery.
    The query will be validated and executed with the provided parameters.

    - **sql**: SQL query string (required)
    - **dry_run**: If true, validates the query without executing (default: false)
    - **timeout_ms**: Query timeout in milliseconds (default: 60000, max: 300000)
    - **use_query_cache**: Use cached results if available (default: true)
    - **use_legacy_sql**: Use legacy SQL syntax (default: false)

    Example:
    ```json
    {
        "sql": "SELECT * FROM `project.dataset.table` LIMIT 10",
        "dry_run": false
    }
    ```
    """
    try:
        logger.info(f"Executing query: {request.sql[:100]}...")

        result = bigquery_service.execute_query(
            sql=request.sql,
            project_id=request.project_id,
            dry_run=request.dry_run,
            timeout_ms=request.timeout_ms,
            use_query_cache=request.use_query_cache,
            use_legacy_sql=request.use_legacy_sql
        )

        response = QueryResponse(
            status="success",
            data=result["data"],
            metadata=result["metadata"],
            row_count=result["row_count"],
            columns=result["columns"]
        )

        return response

    except Exception as e:
        logger.error(f"Query execution failed: {e}")

        # Parse error for better error messages
        error_message = str(e)

        if "Not found" in error_message or "does not exist" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "BQ_TABLE_NOT_FOUND",
                    "message": "Table or resource not found",
                    "details": {"error": error_message}
                }
            )

        if "syntax" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "BQ_SYNTAX_ERROR",
                    "message": "SQL syntax error",
                    "details": {"error": error_message}
                }
            )

        if "quota" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error_code": "BQ_QUOTA_EXCEEDED",
                    "message": "BigQuery quota exceeded",
                    "details": {"error": error_message}
                }
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "BQ_QUERY_ERROR",
                "message": "Query execution failed",
                "details": {"error": error_message}
            }
        )
