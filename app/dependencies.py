"""
Dependency Injection Configuration

This module provides dependency injection functions for FastAPI endpoints.
Using FastAPI's Depends() makes services testable and loosely coupled.
"""
from functools import lru_cache
from typing import Optional, Union

from fastapi import Depends

from app.config import settings
from app.services.bigquery_service import BigQueryService
from app.services.claude_cli_service import ClaudeCLIService
from app.interfaces import BigQueryServiceProtocol, ClaudeCLIServiceProtocol


# ============== BigQuery Service Dependencies ==============

@lru_cache()
def _get_bigquery_service_instance() -> BigQueryService:
    """
    Create and cache BigQuery service instance.

    Returns:
        BigQueryService: Cached service instance

    Note:
        Using lru_cache ensures singleton pattern within the application lifecycle
    """
    return BigQueryService()


def get_bigquery_service() -> BigQueryServiceProtocol:
    """
    Get BigQuery service instance for dependency injection.

    Usage:
        @router.get("/datasets")
        async def list_datasets(
            bq: BigQueryServiceProtocol = Depends(get_bigquery_service)
        ):
            return bq.list_datasets()

    Returns:
        BigQueryServiceProtocol: Service instance following the protocol
    """
    return _get_bigquery_service_instance()


def get_bigquery_service_async() -> BigQueryServiceProtocol:
    """
    Get BigQuery service instance for async dependency injection.

    Usage:
        @router.get("/datasets")
        async def list_datasets(
            bq: BigQueryServiceProtocol = Depends(get_bigquery_service_async)
        ):
            datasets = await bq.list_datasets_async()
            return {"datasets": datasets}

    Returns:
        BigQueryServiceProtocol: Service instance following the protocol
    """
    return _get_bigquery_service_instance()


# ============== Claude CLI Service Dependencies ==============

@lru_cache()
def _get_claude_cli_service_instance() -> ClaudeCLIService:
    """
    Create and cache Claude CLI service instance.

    Returns:
        ClaudeCLIService: Cached service instance
    """
    return ClaudeCLIService()


def get_claude_cli_service() -> ClaudeCLIServiceProtocol:
    """
    Get Claude CLI service instance for dependency injection.

    Usage:
        @router.post("/query-agent")
        async def query_agent(
            request: QueryAgentRequest,
            claude: ClaudeCLIServiceProtocol = Depends(get_claude_cli_service)
        ):
            return await claude.execute_prompt(request.prompt)

    Returns:
        ClaudeCLIServiceProtocol: Service instance following the protocol
    """
    return _get_claude_cli_service_instance()


# ============== Multiple Service Dependencies ==============

def get_data_services(
    bigquery: BigQueryServiceProtocol = Depends(get_bigquery_service),
    claude: ClaudeCLIServiceProtocol = Depends(get_claude_cli_service)
) -> tuple[BigQueryServiceProtocol, ClaudeCLIServiceProtocol]:
    """
    Get multiple services at once.

    Usage:
        @router.get("/context")
        async def get_context(
            services: tuple = Depends(get_data_services)
        ):
            bq, claude = services
            # Use both services

    Returns:
        tuple: (BigQueryService, ClaudeCLIService)
    """
    return bigquery, claude


# ============== Optional/Conditional Dependencies ==============

def get_optional_bigquery_service(
    use_bigquery: bool = True
) -> Optional[BigQueryService]:
    """
    Get optional BigQuery service.

    Args:
        use_bigquery: Whether to use BigQuery service

    Returns:
        Optional[BigQueryService]: Service instance or None
    """
    if use_bigquery:
        return _get_bigquery_service_instance()
    return None


def get_bigquery_service_with_project(
    project_id: Optional[str] = None
) -> BigQueryService:
    """
    Get BigQuery service with custom project ID.

    Args:
        project_id: Custom project ID (overrides default)

    Returns:
        BigQueryService: Service instance with custom project
    """
    if project_id:
        return BigQueryService(project_id=project_id)
    return _get_bigquery_service_instance()


# ============== Testing Helpers ==============

def clear_service_cache():
    """
    Clear cached service instances.

    Useful for testing to ensure fresh service instances.
    Not recommended for production use.

    Example:
        def test_something():
            clear_service_cache()
            service = get_bigquery_service()
            # Fresh instance
    """
    _get_bigquery_service_instance.cache_clear()
    _get_claude_cli_service_instance.cache_clear()


# ============== Mock Dependencies for Testing ==============

class MockBigQueryService:
    """Mock BigQuery service for testing"""

    def __init__(self):
        self.datasets = [
            {"dataset_id": "test_dataset", "project": "test", "location": "US"}
        ]
        self.tables = [
            {"table_id": "test_table", "dataset_id": "test_dataset", "project": "test"}
        ]

    def list_datasets(self):
        return self.datasets

    def list_tables(self, dataset_id: str):
        return self.tables

    def get_table(self, dataset_id: str, table_id: str):
        return self.tables[0] if self.tables else None

    def execute_query(self, sql: str, **kwargs):
        return {
            "data": [],
            "metadata": {},
            "row_count": 0,
            "columns": []
        }

    def test_connection(self):
        return True


class MockClaudeCLIService:
    """Mock Claude CLI service for testing"""

    def __init__(self):
        self.available = True
        self.last_prompt = None

    def is_available(self):
        return self.available

    def execute_prompt(self, prompt: str, **kwargs):
        self.last_prompt = prompt
        return {
            "status": "success",
            "output": "Mock response",
            "reasoning": "Mock reasoning",
            "execution_time_ms": 100
        }


def get_mock_bigquery_service() -> MockBigQueryService:
    """Get mock BigQuery service for testing"""
    return MockBigQueryService()


def get_mock_claude_cli_service() -> MockClaudeCLIService:
    """Get mock Claude CLI service for testing"""
    return MockClaudeCLIService()


# ============== Health Check Dependencies ==============

async def check_bigquery_health(
    bq: BigQueryService = Depends(get_bigquery_service)
) -> dict:
    """
    Check BigQuery service health.

    Returns:
        dict: Health status with connection info
    """
    try:
        is_connected = bq.test_connection()
        return {
            "service": "bigquery",
            "status": "healthy" if is_connected else "unhealthy",
            "connected": is_connected,
            "project_id": bq.project_id
        }
    except Exception as e:
        return {
            "service": "bigquery",
            "status": "unhealthy",
            "error": str(e)
        }


async def check_claude_cli_health(
    claude: ClaudeCLIService = Depends(get_claude_cli_service)
) -> dict:
    """
    Check Claude CLI service health.

    Returns:
        dict: Health status with availability info
    """
    try:
        is_available = claude.is_available()
        return {
            "service": "claude_cli",
            "status": "healthy" if is_available else "unhealthy",
            "available": is_available
        }
    except Exception as e:
        return {
            "service": "claude_cli",
            "status": "unhealthy",
            "error": str(e)
        }
