"""
Claude AI Agent Endpoints
Natural language to SQL using Claude Code CLI
"""
from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from loguru import logger
import json
import time

from app.models.bigquery import (
    DirectQueryRequest,
    QueryResponse,
    ErrorResponse
)
from app.services.bigquery_service import BigQueryService
from app.dependencies import get_bigquery_service_async
from app.services.claude_cli_service import claude_cli_service
from app.utils.prompt_validator import validate_user_prompt
from app.utils.validators import validate_sql_query
from app.utils.security import (
    pii_detector,
    data_masker,
    cost_tracker,
    audit_logger
)

router = APIRouter(tags=["Claude AI Agent"])


class AgentRequest(BaseModel):
    """Request model for Claude AI agent"""
    prompt: str = Field(..., description="Natural language prompt")
    project_id: Optional[str] = Field(None, description="GCP Project ID")
    dataset_id: Optional[str] = Field(None, description="Dataset ID to focus on")
    dry_run: bool = Field(False, description="Generate SQL without executing")
    timeout: int = Field(300, description="Agent timeout in seconds", ge=10, le=600)


class AgentResponse(BaseModel):
    """Response model for Claude AI agent"""
    status: str
    prompt: str
    generated_sql: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    agent_metadata: Dict[str, Any]
    reasoning: Optional[str] = None


@router.post("/query-agent", response_model=AgentResponse)
async def query_with_agent(
    request: AgentRequest,
    req: Request,
    bq: BigQueryService = Depends(get_bigquery_service_async)
) -> AgentResponse:
    """
    Convert natural language to BigQuery SQL using Claude Code CLI

    This endpoint uses Claude Code CLI as an AI agent to:
    1. Understand your natural language request
    2. Generate optimized BigQuery SQL query
    3. Execute the query (optional)
    4. Return results

    **Production Security Features:**
    - PII/PHI detection in prompts
    - Prompt validation (30+ dangerous patterns)
    - SQL validation (SELECT only)
    - Query cost tracking and limits
    - Data masking for sensitive columns
    - Enhanced audit logging

    Example request:
    ```json
    {
        "prompt": "Show me top 10 users by revenue in January 2024",
        "dataset_id": "analytics",
        "dry_run": false
    }
    ```

    The agent will:
    - Analyze your request
    - Query BigQuery schema to understand available tables
    - Generate the appropriate SQL query
    - Execute and return results
    """
    start_time = time.time()
    api_key = req.headers.get("X-API-Key", "unknown")

    try:
        logger.info(f"Received agent request: {request.prompt[:100]}...")

        # Step 0: Check for PII/PHI requests
        logger.info("Checking for PII/PHI in prompt...")
        has_pii, pii_keywords = pii_detector.contains_pii_request(request.prompt)

        if has_pii:
            logger.warning(f"PII/PHI detected in prompt: {pii_keywords}")
            audit_logger.log_ai_agent_request(
                prompt=request.prompt,
                api_key=api_key,
                generated_sql="",
                validation_passed=False,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "PII_DETECTED",
                    "message": "Cannot query sensitive data (PII/PHI) via AI agent. "
                              "Please use direct SQL query with proper authorization.",
                    "details": {"detected_keywords": pii_keywords}
                }
            )

        # Step 1: Validate prompt for security
        logger.info("Validating prompt for security...")
        is_prompt_valid, prompt_errors = validate_user_prompt(request.prompt)

        if not is_prompt_valid:
            logger.warning(f"Prompt validation failed: {prompt_errors}")
            audit_logger.log_ai_agent_request(
                prompt=request.prompt,
                api_key=api_key,
                generated_sql="",
                validation_passed=False,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_PROMPT",
                    "message": "Prompt validation failed - request appears to be unsafe or not data-related",
                    "details": {"errors": prompt_errors}
                }
            )

        # Step 2: Gather BigQuery context
        logger.info("Gathering BigQuery context...")
        bq_context = await _gather_bigquery_context(
            bq=bq,
            project_id=request.project_id,
            dataset_id=request.dataset_id
        )

        # Step 3: Execute prompt via Claude CLI
        logger.info("Executing prompt via Claude CLI...")
        claude_result = await claude_cli_service.execute_prompt(
            prompt=request.prompt,
            bigquery_context=bq_context,
            timeout=request.timeout
        )

        # Step 4: Extract generated SQL
        generated_sql = claude_result["parsed_content"].get("sql_query")

        if not generated_sql:
            audit_logger.log_ai_agent_request(
                prompt=request.prompt,
                api_key=api_key,
                generated_sql="",
                validation_passed=False,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "CLAUDE_NO_SQL",
                    "message": "Claude AI did not generate a SQL query"
                }
            )

        logger.info(f"Generated SQL: {generated_sql[:200]}...")

        # Step 5: Validate generated SQL for security
        logger.info("Validating generated SQL...")
        is_sql_valid, sql_errors = validate_sql_query(generated_sql, allow_only_select=True)

        if not is_sql_valid:
            logger.warning(f"Generated SQL validation failed: {sql_errors}")
            audit_logger.log_ai_agent_request(
                prompt=request.prompt,
                api_key=api_key,
                generated_sql=generated_sql,
                validation_passed=False,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "CLAUDE_GENERATED_INVALID_SQL",
                    "message": "Claude AI generated invalid SQL query",
                    "details": {"errors": sql_errors, "sql": generated_sql[:500]}
                }
            )

        # Step 6: Execute SQL if not dry run
        execution_result = None
        if not request.dry_run:
            logger.info("Executing generated SQL...")
            execution_result = await bq.execute_query_async(
                sql=generated_sql,
                project_id=request.project_id,
                dry_run=False
            )

            # Check cost limits
            total_bytes = execution_result.get("metadata", {}).get("total_bytes_processed", 0)
            within_limits, cost_error = cost_tracker.check_cost_limits(total_bytes, api_key)

            if not within_limits:
                audit_logger.log_query(
                    sql=generated_sql,
                    api_key=api_key,
                    user_context={"api_key": api_key},
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    row_count=0,
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
                execution_result["data"],
                execution_result.get("columns", [])
            )
            execution_result["data"] = masked_data

            # Log query cost
            duration_ms = int((time.time() - start_time) * 1000)
            cost_tracker.log_query_cost(
                sql=generated_sql,
                total_bytes_processed=total_bytes,
                api_key=api_key,
                duration_ms=duration_ms
            )

            # Audit log
            audit_logger.log_query(
                sql=generated_sql,
                api_key=api_key,
                user_context={"api_key": api_key, "method": "ai_agent"},
                execution_time_ms=duration_ms,
                row_count=execution_result.get("row_count", 0),
                bytes_processed=total_bytes,
                success=True
            )
        else:
            logger.info("Dry run - skipping execution")

        # Step 7: Log AI agent request
        duration_ms = int((time.time() - start_time) * 1000)
        audit_logger.log_ai_agent_request(
            prompt=request.prompt,
            api_key=api_key,
            generated_sql=generated_sql,
            validation_passed=True,
            execution_time_ms=duration_ms
        )

        # Step 8: Return response
        return AgentResponse(
            status="success",
            prompt=request.prompt,
            generated_sql=generated_sql,
            execution_result=execution_result,
            agent_metadata={
                "model": "glm-4.7",
                "method": "claude-code-cli",
                "workspace": claude_result["workspace"],
                "raw_output_length": len(claude_result["raw_output"]),
                "pii_check": "passed",
                "prompt_validation": "passed",
                "sql_validation": "passed",
                "cost_tracking": "enabled" if execution_result else "skipped",
                "data_masking": "applied" if execution_result else "skipped"
            },
            reasoning=claude_result["parsed_content"].get("text")[:500]
        )

    except TimeoutError as e:
        logger.error(f"Claude CLI timeout: {e}", exc_info=True)
        duration_ms = int((time.time() - start_time) * 1000)
        audit_logger.log_ai_agent_request(
            prompt=request.prompt,
            api_key=api_key,
            generated_sql="",
            validation_passed=False,
            execution_time_ms=duration_ms
        )
        raise HTTPException(
            status_code=504,
            detail={
                "error_code": "CLAUDE_TIMEOUT",
                "message": "Claude AI agent timed out"
            }
        )

    except RuntimeError as e:
        logger.error(f"Claude CLI error: {e}", exc_info=True)
        duration_ms = int((time.time() - start_time) * 1000)
        audit_logger.log_ai_agent_request(
            prompt=request.prompt,
            api_key=api_key,
            generated_sql="",
            validation_passed=False,
            execution_time_ms=duration_ms
        )
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "CLAUDE_UNAVAILABLE",
                "message": "Claude Code CLI is not available"
            }
        )

    except Exception as e:
        logger.error(f"Agent request failed: {e}", exc_info=True)
        duration_ms = int((time.time() - start_time) * 1000)
        audit_logger.log_ai_agent_request(
            prompt=request.prompt,
            api_key=api_key,
            generated_sql="",
            validation_passed=False,
            execution_time_ms=duration_ms
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "AGENT_ERROR",
                "message": "Agent request failed"
            }
        )


@router.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time Claude AI agent interaction

    This allows for interactive sessions where you can:
    - Send natural language prompts
    - Receive streaming responses
    - Have multi-turn conversations
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        # Initialize session
        session_context: Dict[str, Any] = {
            "project_id": None,
            "dataset_id": None
        }

        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type", "prompt")

            logger.info(f"WebSocket message type: {message_type}")

            if message_type == "prompt":
                # Process prompt
                prompt = data.get("prompt", "")

                # Send acknowledgment
                await websocket.send_json({
                    "type": "status",
                    "message": "Processing your request..."
                })

                try:
                    # Gather context
                    # Note: WebSocket can't use Depends, so we need to pass bq directly
                    from app.services.bigquery_service import bigquery_service as bq_global
                    bq_context = await _gather_bigquery_context(
                        bq=bq_global,
                        project_id=session_context["project_id"],
                        dataset_id=session_context["dataset_id"]
                    )

                    # Execute via Claude CLI
                    result = await claude_cli_service.execute_prompt(
                        prompt=prompt,
                        bigquery_context=bq_context,
                        timeout=300
                    )

                    # Send response
                    await websocket.send_json({
                        "type": "response",
                        "prompt": prompt,
                        "generated_sql": result["parsed_content"].get("sql_query"),
                        "reasoning": result["parsed_content"].get("text", "")[:500],
                        "metadata": {
                            "model": "glm-4.7",
                            "workspace": result["workspace"]
                        }
                    })

                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

            elif message_type == "configure":
                # Update session configuration
                session_context["project_id"] = data.get("project_id")
                session_context["dataset_id"] = data.get("dataset_id")

                await websocket.send_json({
                    "type": "configured",
                    "context": session_context
                })

            elif message_type == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.close(code=1011, reason=str(e))


async def _gather_bigquery_context(
    bq: BigQueryService,
    project_id: Optional[str] = None,
    dataset_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Gather BigQuery context for Claude CLI

    Args:
        bq: BigQuery service instance
        project_id: GCP Project ID
        dataset_id: Dataset ID to focus on

    Returns:
        Dictionary with schema and table information
    """
    try:
        project = project_id or bq.project_id

        # Get datasets
        if dataset_id:
            # Focus on specific dataset
            dataset = await bq.get_dataset_async(dataset_id)

            # Get tables for this dataset
            tables = await bq.list_tables_async(dataset_id)

            # Enhance with table details
            for table_info in tables:
                table_id = table_info["table_id"]
                table_details = await bq.get_table_async(dataset_id, table_id)
                table_info["schema"] = table_details.get("schema", [])

            datasets = [dataset]
            datasets[0]["tables"] = tables

        else:
            # Get all datasets (limit to first 10 for performance)
            all_datasets = await bq.list_datasets_async()
            all_datasets = all_datasets[:10]
            datasets = []

            for dataset in all_datasets:
                ds_id = dataset["dataset_id"]

                # Get tables for each dataset
                tables = await bq.list_tables_async(ds_id)
                tables = tables[:5]  # Limit tables

                # Enhance with schema
                for table_info in tables:
                    table_id = table_info["table_id"]
                    try:
                        table_details = await bq.get_table_async(ds_id, table_id)
                        table_info["schema"] = table_details.get("schema", [])
                    except (KeyError, AttributeError, Exception) as e:
                        logger.debug(f"Could not retrieve schema for table {table_id}: {e}")
                        table_info["schema"] = []

                dataset["tables"] = tables
                datasets.append(dataset)

        return {
            "project_id": project,
            "location": "US",
            "datasets": datasets
        }

    except Exception as e:
        logger.error(f"Failed to gather BigQuery context: {e}", exc_info=True)
        # Return minimal context
        return {
            "project_id": project_id or bq.project_id,
            "location": "US",
            "datasets": []
        }


# Import BaseModel
from pydantic import BaseModel, Field
