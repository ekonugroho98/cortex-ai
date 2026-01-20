"""
Query Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from loguru import logger
import time

from app.models.bigquery import (
    DirectQueryRequest,
    QueryResponse
)
from app.services.bigquery_service import BigQueryService
from app.utils.validators import validate_sql_query
from app.dependencies import get_bigquery_service_async
from app.utils.security import (
    data_masker,
    cost_tracker,
    audit_logger
)

router = APIRouter(tags=["Query"])


@router.post("/query", response_model=QueryResponse)
async def execute_query(
    request: DirectQueryRequest,
    req: Request,
    bq: BigQueryService = Depends(get_bigquery_service_async)
):
    """
    Execute direct SQL query to BigQuery (ASYNC)

    This endpoint allows you to execute raw SQL queries against BigQuery.
    The query will be validated and executed with the provided parameters.

    **Production Security Features:**
    - SQL validation (SELECT only)
    - Query cost tracking and limits
    - Data masking for sensitive columns
    - Enhanced audit logging

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
    start_time = time.time()
    api_key = req.headers.get("X-API-Key", "unknown")

    try:
        # Validate SQL query for security
        is_valid, validation_errors = validate_sql_query(
            request.sql,
            allow_only_select=True
        )

        if not is_valid:
            logger.warning(f"SQL validation failed: {validation_errors}")
            audit_logger.log_query(
                sql=request.sql,
                api_key=api_key,
                user_context={"api_key": api_key},
                execution_time_ms=int((time.time() - start_time) * 1000),
                row_count=0,
                bytes_processed=0,
                success=False,
                error="SQL validation failed"
            )
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

        # Check cost limits
        total_bytes = result.get("metadata", {}).get("total_bytes_processed", 0)
        within_limits, cost_error = cost_tracker.check_cost_limits(total_bytes, api_key)

        if not within_limits:
            audit_logger.log_query(
                sql=request.sql,
                api_key=api_key,
                user_context={"api_key": api_key},
                execution_time_ms=int((time.time() - start_time) * 1000),
                row_count=result.get("row_count", 0),
                bytes_processed=total_bytes,
                success=False,
                error=cost_error
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error_code": "COST_LIMIT_EXCEEDED",
                    "message": cost_error
                }
            )

        # Apply data masking
        masked_data = data_masker.mask_data(
            result["data"],
            result.get("columns", [])
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Log query cost for audit
        cost_tracker.log_query_cost(
            sql=request.sql,
            total_bytes_processed=total_bytes,
            api_key=api_key,
            duration_ms=duration_ms
        )

        # Audit log
        audit_logger.log_query(
            sql=request.sql,
            api_key=api_key,
            user_context={"api_key": api_key},
            execution_time_ms=duration_ms,
            row_count=result.get("row_count", 0),
            bytes_processed=total_bytes,
            success=True
        )

        response = QueryResponse(
            status="success",
            data=masked_data,
            metadata=result["metadata"],
            row_count=result["row_count"],
            columns=result["columns"]
        )

        return response

    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)

        duration_ms = int((time.time() - start_time) * 1000)

        # Audit log for failed query
        audit_logger.log_query(
            sql=request.sql if hasattr(request, 'sql') else "",
            api_key=api_key,
            user_context={"api_key": api_key},
            execution_time_ms=duration_ms,
            row_count=0,
            bytes_processed=0,
            success=False,
            error=str(e)
        )

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
