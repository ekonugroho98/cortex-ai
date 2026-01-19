"""
BigQuery Service Interface Protocol

This module defines the interface contract for BigQuery service implementations.
Using Protocol instead of ABC for better flexibility and duck typing support.
"""
from typing import Protocol, List, Dict, Any, Optional


class BigQueryServiceProtocol(Protocol):
    """
    Protocol defining the BigQuery service interface.

    This protocol defines the contract that any BigQuery service implementation
    must follow. It enables:
    - Easy mocking for tests
    - Multiple implementations (real BigQuery, mock, caching layer, etc.)
    - Type checking with mypy/pyright
    - Better documentation through interface definition

    Example implementation:
        class MyBigQueryService:
            def list_datasets(self) -> List[Dict[str, Any]]:
                # implementation
                pass

    Example usage in tests:
        class MockBigQueryService:
            def list_datasets(self) -> List[Dict[str, Any]]:
                return [{"dataset_id": "test"}]

        service: BigQueryServiceProtocol = MockBigQueryService()
    """

    def test_connection(self) -> bool:
        """
        Test BigQuery connection

        Returns:
            True if connection successful, False otherwise
        """
        ...

    def list_datasets(self) -> List[Dict[str, Any]]:
        """
        List all datasets in the project

        Returns:
            List of datasets with metadata including:
            - dataset_id: str
            - project: str
            - location: str
            - tables_count: int
            - created_at: datetime
            - modified_at: datetime
        """
        ...

    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get details of a specific dataset

        Args:
            dataset_id: Dataset ID

        Returns:
            Dataset details with same structure as list_datasets

        Raises:
            Exception: If dataset not found
        """
        ...

    def list_tables(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        List all tables in a dataset

        Args:
            dataset_id: Dataset ID

        Returns:
            List of tables with metadata including:
            - table_id: str
            - dataset_id: str
            - project: str
            - table_type: str
            - num_rows: int
            - num_bytes: int
            - created_at: datetime
            - modified_at: datetime
            - full_table_id: str
        """
        ...

    def get_table(self, dataset_id: str, table_id: str) -> Dict[str, Any]:
        """
        Get details of a specific table including schema

        Args:
            dataset_id: Dataset ID
            table_id: Table ID

        Returns:
            Table details with all metadata from list_tables plus:
            - schema: List[Dict[str, Any]] with field definitions

        Raises:
            Exception: If table not found
        """
        ...

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
        Execute a SQL query

        Args:
            sql: SQL query string
            project_id: Override project ID
            dry_run: Validate query without executing
            timeout_ms: Query timeout in milliseconds
            use_query_cache: Use cached results if available
            use_legacy_sql: Use legacy SQL syntax

        Returns:
            Query results with:
            - metadata: Dict with job_id, bytes_billed, execution_time_ms, etc.
            - data: List[Dict] with row data
            - row_count: int
            - columns: List[str] with column names

        Raises:
            Exception: If query execution fails
        """
        ...

    # Async versions

    async def test_connection_async(self) -> bool:
        """
        Async version of test_connection

        Returns:
            True if connection successful, False otherwise
        """
        ...

    async def list_datasets_async(self) -> List[Dict[str, Any]]:
        """
        Async version of list_datasets

        Returns:
            List of datasets with metadata
        """
        ...

    async def get_dataset_async(self, dataset_id: str) -> Dict[str, Any]:
        """
        Async version of get_dataset

        Args:
            dataset_id: Dataset ID

        Returns:
            Dataset details
        """
        ...

    async def list_tables_async(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        Async version of list_tables

        Args:
            dataset_id: Dataset ID

        Returns:
            List of tables with metadata
        """
        ...

    async def get_table_async(self, dataset_id: str, table_id: str) -> Dict[str, Any]:
        """
        Async version of get_table

        Args:
            dataset_id: Dataset ID
            table_id: Table ID

        Returns:
            Table details with schema
        """
        ...

    async def execute_query_async(
        self,
        sql: str,
        project_id: Optional[str] = None,
        dry_run: bool = False,
        timeout_ms: int = 60000,
        use_query_cache: bool = True,
        use_legacy_sql: bool = False
    ) -> Dict[str, Any]:
        """
        Async version of execute_query

        Args:
            sql: SQL query string
            project_id: Override project ID
            dry_run: Validate query without executing
            timeout_ms: Query timeout in milliseconds
            use_query_cache: Use cached results if available
            use_legacy_sql: Use legacy SQL syntax

        Returns:
            Query results with metadata
        """
        ...

    # Properties

    @property
    def project_id(self) -> str:
        """
        Get the Google Cloud project ID

        Returns:
            Project ID string
        """
        ...

    @property
    def client(self) -> Any:
        """
        Get the underlying BigQuery client

        Returns:
            BigQuery Client instance (google.cloud.bigquery.Client)
        """
        ...
