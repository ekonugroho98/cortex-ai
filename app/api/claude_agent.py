"""
Claude AI Agent Endpoints
Natural language to SQL using Claude Code CLI
"""
from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from loguru import logger
import json

from app.models.bigquery import (
    DirectQueryRequest,
    QueryResponse,
    ErrorResponse
)
from app.services.bigquery_service import bigquery_service
from app.services.claude_cli_service import claude_cli_service

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
async def query_with_agent(request: AgentRequest):
    """
    Convert natural language to BigQuery SQL using Claude Code CLI

    This endpoint uses Claude Code CLI as an AI agent to:
    1. Understand your natural language request
    2. Generate optimized BigQuery SQL query
    3. Execute the query (optional)
    4. Return results

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
    try:
        logger.info(f"Received agent request: {request.prompt[:100]}...")

        # Step 1: Gather BigQuery context
        logger.info("Gathering BigQuery context...")
        bq_context = await _gather_bigquery_context(
            project_id=request.project_id,
            dataset_id=request.dataset_id
        )

        # Step 2: Execute prompt via Claude CLI
        logger.info("Executing prompt via Claude CLI...")
        claude_result = await claude_cli_service.execute_prompt(
            prompt=request.prompt,
            bigquery_context=bq_context,
            timeout=request.timeout
        )

        # Step 3: Extract generated SQL
        generated_sql = claude_result["parsed_content"].get("sql_query")

        if not generated_sql:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "CLAUDE_NO_SQL",
                    "message": "Claude AI did not generate a SQL query",
                    "details": {
                        "raw_output": claude_result["raw_output"][:1000]
                    }
                }
            )

        logger.info(f"Generated SQL: {generated_sql[:200]}...")

        # Step 4: Execute SQL if not dry run
        execution_result = None
        if not request.dry_run:
            logger.info("Executing generated SQL...")
            execution_result = bigquery_service.execute_query(
                sql=generated_sql,
                project_id=request.project_id,
                dry_run=False
            )
        else:
            logger.info("Dry run - skipping execution")

        # Step 5: Return response
        return AgentResponse(
            status="success",
            prompt=request.prompt,
            generated_sql=generated_sql,
            execution_result=execution_result,
            agent_metadata={
                "model": "glm-4.7",
                "method": "claude-code-cli",
                "workspace": claude_result["workspace"],
                "raw_output_length": len(claude_result["raw_output"])
            },
            reasoning=claude_result["parsed_content"].get("text")[:500]
        )

    except TimeoutError as e:
        logger.error(f"Claude CLI timeout: {e}")
        raise HTTPException(
            status_code=504,
            detail={
                "error_code": "CLAUDE_TIMEOUT",
                "message": "Claude AI agent timed out",
                "details": {"error": str(e)}
            }
        )

    except RuntimeError as e:
        logger.error(f"Claude CLI error: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "CLAUDE_UNAVAILABLE",
                "message": "Claude Code CLI is not available",
                "details": {"error": str(e)}
            }
        )

    except Exception as e:
        logger.error(f"Agent request failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "AGENT_ERROR",
                "message": "Agent request failed",
                "details": {"error": str(e)}
            }
        )


@router.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket):
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
        session_context = {
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
                    bq_context = await _gather_bigquery_context(
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
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))


async def _gather_bigquery_context(
    project_id: Optional[str] = None,
    dataset_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Gather BigQuery context for Claude CLI

    Args:
        project_id: GCP Project ID
        dataset_id: Dataset ID to focus on

    Returns:
        Dictionary with schema and table information
    """
    try:
        project = project_id or bigquery_service.project_id

        # Get datasets
        if dataset_id:
            # Focus on specific dataset
            datasets = [bigquery_service.get_dataset(dataset_id)]

            # Get tables for this dataset
            tables = bigquery_service.list_tables(dataset_id)

            # Enhance with table details
            for table_info in tables:
                table_id = table_info["table_id"]
                table_details = bigquery_service.get_table(dataset_id, table_id)
                table_info["schema"] = table_details.get("schema", [])

            datasets[0]["tables"] = tables

        else:
            # Get all datasets (limit to first 10 for performance)
            all_datasets = bigquery_service.list_datasets()[:10]
            datasets = []

            for dataset in all_datasets:
                ds_id = dataset["dataset_id"]

                # Get tables for each dataset
                tables = bigquery_service.list_tables(ds_id)[:5]  # Limit tables

                # Enhance with schema
                for table_info in tables:
                    table_id = table_info["table_id"]
                    try:
                        table_details = bigquery_service.get_table(ds_id, table_id)
                        table_info["schema"] = table_details.get("schema", [])
                    except:
                        table_info["schema"] = []

                dataset["tables"] = tables
                datasets.append(dataset)

        return {
            "project_id": project,
            "location": "US",
            "datasets": datasets
        }

    except Exception as e:
        logger.error(f"Failed to gather BigQuery context: {e}")
        # Return minimal context
        return {
            "project_id": project_id or bigquery_service.project_id,
            "location": "US",
            "datasets": []
        }


# Import BaseModel
from pydantic import BaseModel, Field
