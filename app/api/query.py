"""
Query Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger

from app.models.bigquery import (
    DirectQueryRequest,
    QueryResponse
)
from app.services.bigquery_service import BigQueryService
from app.utils.validators import validate_sql_query
from app.dependencies import get_bigquery_service_async

router = APIRouter(tags=["Query"])


@router.post("/query", response_model=QueryResponse)
async def execute_query(
    request: DirectQueryRequest,
    bq: BigQueryService = Depends(get_bigquery_service_async)
):
    """
    Execute direct SQL query to BigQuery (ASYNC)

    This endpoint allows you to execute raw SQL queries against BigQuery.
    The query will be validated and executed with the provided parameters.

    Uses async execution to prevent blocking the event loop during
    potentially long-running BigQuery queries.

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
        # Validate SQL query for security
        is_valid, validation_errors = validate_sql_query(
            request.sql,
            allow_only_select=True
        )

        if not is_valid:
            logger.warning(f"SQL validation failed: {validation_errors}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_QUERY",
                    "message": "Query validation failed",
                    "details": {"errors": validation_errors}
                }
            )

        logger.info(f"Executing query async: {request.sql[:100]}...")

        # Use async version to prevent blocking
        result = await bq.execute_query_async(
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
        logger.error(f"Query execution failed: {e}", exc_info=True)

        # Sanitize error messages - don't expose internal details to clients
        error_message = str(e)

        if "Not found" in error_message or "does not exist" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "RESOURCE_NOT_FOUND",
                    "message": "Requested resource was not found"
                }
            )

        if "syntax" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "SYNTAX_ERROR",
                    "message": "SQL syntax error in query"
                }
            )

        if "quota" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error_code": "QUOTA_EXCEEDED",
                    "message": "Query quota exceeded. Please try again later."
                }
            )

        # Generic error for all other cases
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "QUERY_EXECUTION_FAILED",
                "message": "Query execution failed. Please check your query and try again."
            }
        )
