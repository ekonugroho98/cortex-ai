"""
Mock Service Implementations for Testing

This module provides mock implementations of service interfaces for testing.
These mocks allow fast, isolated tests without external dependencies.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.interfaces import BigQueryServiceProtocol, ClaudeCLIServiceProtocol


class MockBigQueryService(BigQueryServiceProtocol):
    """
    Mock BigQuery service for testing.

    Provides in-memory implementations of all BigQuery operations.
    Use this in unit tests to avoid hitting real BigQuery API.

    Example:
        mock_service = MockBigQueryService()
        datasets = mock_service.list_datasets()
        assert len(datasets) > 0
    """

    def __init__(self, project_id: str = "test-project"):
        """
        Initialize mock service

        Args:
            project_id: Mock project ID
        """
        self._project_id = project_id
        self._datasets = {
            "test_dataset": {
                "dataset_id": "test_dataset",
                "project": project_id,
                "location": "US",
                "tables_count": 2,
                "created_at": datetime.now(),
                "modified_at": datetime.now()
            }
        }
        self._tables = {
            "test_dataset": [
                {
                    "table_id": "users",
                    "dataset_id": "test_dataset",
                    "project": project_id,
                    "table_type": "TABLE",
                    "num_rows": 1000,
                    "num_bytes": 102400,
                    "created_at": datetime.now(),
                    "modified_at": datetime.now(),
                    "full_table_id": f"{project_id}.test_dataset.users",
                    "schema": [
                        {"name": "id", "type": "INTEGER", "mode": "REQUIRED", "description": "User ID"},
                        {"name": "name", "type": "STRING", "mode": "NULLABLE", "description": "User name"},
                        {"name": "email", "type": "STRING", "mode": "NULLABLE", "description": "User email"}
                    ]
                },
                {
                    "table_id": "orders",
                    "dataset_id": "test_dataset",
                    "project": project_id,
                    "table_type": "TABLE",
                    "num_rows": 5000,
                    "num_bytes": 512000,
                    "created_at": datetime.now(),
                    "modified_at": datetime.now(),
                    "full_table_id": f"{project_id}.test_dataset.orders",
                    "schema": [
                        {"name": "id", "type": "INTEGER", "mode": "REQUIRED", "description": "Order ID"},
                        {"name": "user_id", "type": "INTEGER", "mode": "REQUIRED", "description": "User ID"},
                        {"name": "total", "type": "FLOAT", "mode": "NULLABLE", "description": "Order total"}
                    ]
                }
            ]
        }
        self._query_results = []

    def test_connection(self) -> bool:
        """Mock connection test - always returns True"""
        return True

    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all mock datasets"""
        return list(self._datasets.values())

    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Get mock dataset details"""
        if dataset_id not in self._datasets:
            raise Exception(f"Dataset '{dataset_id}' not found")
        return self._datasets[dataset_id]

    def list_tables(self, dataset_id: str) -> List[Dict[str, Any]]:
        """List mock tables in dataset"""
        if dataset_id not in self._datasets:
            raise Exception(f"Dataset '{dataset_id}' not found")
        return self._tables.get(dataset_id, [])

    def get_table(self, dataset_id: str, table_id: str) -> Dict[str, Any]:
        """Get mock table details with schema"""
        tables = self.list_tables(dataset_id)
        for table in tables:
            if table["table_id"] == table_id:
                return table
        raise Exception(f"Table '{dataset_id}.{table_id}' not found")

    def execute_query(
        self,
        sql: str,
        project_id: Optional[str] = None,
        dry_run: bool = False,
        timeout_ms: int = 60000,
        use_query_cache: bool = True,
        use_legacy_sql: bool = False
    ) -> Dict[str, Any]:
        """
        Mock query execution

        Returns:
            Mock query results with sample data
        """
        if dry_run:
            return {
                "metadata": {
                    "job_id": "mock-job-123",
                    "total_bytes_processed": 0,
                    "cache_hit": False,
                    "execution_time_ms": 10
                },
                "data": [],
                "row_count": 0,
                "columns": []
            }

        # Return mock results
        return {
            "metadata": {
                "job_id": "mock-job-123",
                "total_bytes_processed": 1024,
                "bytes_billed": 1024,
                "cache_hit": use_query_cache,
                "execution_time_ms": 100
            },
            "data": self._query_results or [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"}
            ],
            "row_count": len(self._query_results) or 2,
            "columns": ["id", "name", "email"]
        }

    # Async versions (simply call sync versions)

    async def test_connection_async(self) -> bool:
        return self.test_connection()

    async def list_datasets_async(self) -> List[Dict[str, Any]]:
        return self.list_datasets()

    async def get_dataset_async(self, dataset_id: str) -> Dict[str, Any]:
        return self.get_dataset(dataset_id)

    async def list_tables_async(self, dataset_id: str) -> List[Dict[str, Any]]:
        return self.list_tables(dataset_id)

    async def get_table_async(self, dataset_id: str, table_id: str) -> Dict[str, Any]:
        return self.get_table(dataset_id, table_id)

    async def execute_query_async(
        self,
        sql: str,
        project_id: Optional[str] = None,
        dry_run: bool = False,
        timeout_ms: int = 60000,
        use_query_cache: bool = True,
        use_legacy_sql: bool = False
    ) -> Dict[str, Any]:
        return self.execute_query(sql, project_id, dry_run, timeout_ms, use_query_cache, use_legacy_sql)

    # Properties

    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def client(self) -> Any:
        """Mock client - returns None"""
        return None

    # Helper methods for testing

    def add_dataset(self, dataset_id: str, **kwargs) -> None:
        """Add a mock dataset"""
        self._datasets[dataset_id] = {
            "dataset_id": dataset_id,
            "project": self._project_id,
            "location": "US",
            "tables_count": 0,
            "created_at": datetime.now(),
            "modified_at": datetime.now(),
            **kwargs
        }

    def add_table(self, dataset_id: str, table_id: str, **kwargs) -> None:
        """Add a mock table"""
        if dataset_id not in self._tables:
            self._tables[dataset_id] = []

        self._tables[dataset_id].append({
            "table_id": table_id,
            "dataset_id": dataset_id,
            "project": self._project_id,
            "table_type": "TABLE",
            "num_rows": 0,
            "num_bytes": 0,
            "created_at": datetime.now(),
            "modified_at": datetime.now(),
            "full_table_id": f"{self._project_id}.{dataset_id}.{table_id}",
            "schema": [],
            **kwargs
        })

    def set_query_results(self, results: List[Dict[str, Any]]) -> None:
        """Set custom query results to return"""
        self._query_results = results


class MockClaudeCLIService(ClaudeCLIServiceProtocol):
    """
    Mock Claude CLI service for testing.

    Provides in-memory implementations of Claude CLI operations.
    Use this in unit tests to avoid executing real Claude CLI.

    Example:
        mock_service = MockClaudeCLIService()
        result = await mock_service.execute_prompt("Show me users")
        assert "SELECT" in result["parsed_content"]["sql_query"]
    """

    def __init__(self, workspace: str = "/tmp/mock-workspace"):
        """
        Initialize mock service

        Args:
            workspace: Mock workspace directory
        """
        self._workspace = workspace
        self._is_available = True

    async def execute_prompt(
        self,
        prompt: str,
        bigquery_context: Dict[str, Any],
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Mock prompt execution

        Returns:
            Mock Claude CLI response with generated SQL
        """
        # Generate a simple SQL query based on prompt
        sql_query = "SELECT * FROM `project.dataset.table` LIMIT 10"

        return {
            "raw_output": f"Claude response for: {prompt}",
            "parsed_content": {
                "sql_query": sql_query,
                "text": f"Here's a query to {prompt.lower()}"
            },
            "workspace": self._workspace,
            "execution_time": 0.5
        }

    @property
    def workspace(self) -> str:
        return self._workspace

    @property
    def is_available(self) -> bool:
        return self._is_available

    # Helper methods for testing

    def set_available(self, available: bool) -> None:
        """Set whether the service is available"""
        self._is_available = available

    def set_workspace(self, workspace: str) -> None:
        """Set the workspace directory"""
        self._workspace = workspace
