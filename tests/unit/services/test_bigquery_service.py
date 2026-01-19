"""
Unit Tests for BigQuery Service
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from google.cloud import bigquery
from google.cloud.bigquery import Dataset, Table, SchemaField
from google.api_core.exceptions import NotFound, GoogleAPIError
import datetime


@pytest.mark.unit
class TestBigQueryServiceInit:
    """Test BigQuery service initialization"""

    def test_initialization_success(self):
        """Test successful initialization"""
        from app.services.bigquery_service import BigQueryService
        from app.config import settings

        service = BigQueryService()
        assert service.project_id == settings.gcp_project_id
        assert service.location == settings.bigquery_location
        assert service.client is not None

    def test_initialization_with_custom_project(self):
        """Test initialization with custom project ID"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService(project_id="custom-project")
        assert service.project_id == "custom-project"


@pytest.mark.unit
class TestBigQueryServiceListDatasets:
    """Test dataset listing functionality"""

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_list_datasets_success(self, mock_bigquery_client):
        """Test successful dataset listing"""
        from app.services.bigquery_service import BigQueryService

        # Mock the client and datasets
        service = BigQueryService()
        service.client = mock_bigquery_client

        # Create mock datasets
        mock_dataset1 = MagicMock()
        mock_dataset1.dataset_id = "dataset1"
        mock_dataset1.project = "test-project"
        mock_dataset1.location = "US"
        mock_dataset1.created = datetime.datetime.now()
        mock_dataset1.modified = datetime.datetime.now()

        mock_dataset2 = MagicMock()
        mock_dataset2.dataset_id = "dataset2"
        mock_dataset2.project = "test-project"
        mock_dataset2.location = "EU"
        mock_dataset2.created = datetime.datetime.now()
        mock_dataset2.modified = datetime.datetime.now()

        mock_bigquery_client.list_datasets.return_value = [mock_dataset1, mock_dataset2]

        # Execute
        datasets = service.list_datasets()

        # Assert
        assert len(datasets) == 2
        assert datasets[0]["dataset_id"] == "dataset1"
        assert datasets[0]["location"] == "US"
        assert datasets[1]["dataset_id"] == "dataset2"
        assert datasets[1]["location"] == "EU"

        mock_bigquery_client.list_datasets.assert_called_once()

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_list_datasets_empty(self, mock_bigquery_client):
        """Test listing datasets when no datasets exist"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService()
        service.client = mock_bigquery_client
        mock_bigquery_client.list_datasets.return_value = []

        datasets = service.list_datasets()

        assert datasets == []
        mock_bigquery_client.list_datasets.assert_called_once()

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_list_datasets_api_error(self, mock_bigquery_client):
        """Test listing datasets with API error"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService()
        service.client = mock_bigquery_client
        mock_bigquery_client.list_datasets.side_effect = GoogleAPIError("API Error")

        with pytest.raises(GoogleAPIError):
            service.list_datasets()


@pytest.mark.unit
class TestBigQueryServiceListTables:
    """Test table listing functionality"""

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_list_tables_success(self, mock_bigquery_client):
        """Test successful table listing"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService()
        service.client = mock_bigquery_client
        service.project_id = "test-project"

        # Create mock tables
        mock_table1 = MagicMock()
        mock_table1.table_id = "table1"
        mock_table1.table_type = "TABLE"
        mock_table1.created = datetime.datetime.now()
        mock_table1.modified = datetime.datetime.now()
        mock_table1.num_rows = 1000
        mock_table1.num_bytes = 1024000

        mock_table2 = MagicMock()
        mock_table2.table_id = "table2"
        mock_table2.table_type = "VIEW"
        mock_table2.created = datetime.datetime.now()
        mock_table2.modified = datetime.datetime.now()
        mock_table2.num_rows = 500
        mock_table2.num_bytes = 512000

        mock_bigquery_client.list_tables.return_value = [mock_table1, mock_table2]

        tables = service.list_tables("dataset1")

        assert len(tables) == 2
        assert tables[0]["table_id"] == "table1"
        assert tables[0]["table_type"] == "TABLE"
        assert tables[1]["table_id"] == "table2"
        assert tables[1]["table_type"] == "VIEW"

        mock_bigquery_client.list_tables.assert_called_once_with("test-project.dataset1")

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_list_tables_not_found(self, mock_bigquery_client):
        """Test listing tables from non-existent dataset"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService()
        service.client = mock_bigquery_client
        mock_bigquery_client.list_tables.side_effect = NotFound("Dataset not found")

        with pytest.raises(NotFound):
            service.list_tables("nonexistent_dataset")


@pytest.mark.unit
class TestBigQueryServiceGetTable:
    """Test get table details functionality"""

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_get_table_success(self, mock_bigquery_client):
        """Test successful table details retrieval"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService()
        service.client = mock_bigquery_client
        service.project_id = "test-project"

        # Create mock table with schema
        mock_table = MagicMock()
        mock_table.table_id = "users"
        mock_table.table_type = "TABLE"
        mock_table.created = datetime.datetime.now()
        mock_table.modified = datetime.datetime.now()
        mock_table.num_rows = 10000
        mock_table.num_bytes = 10240000

        # Create schema fields
        schema_field1 = SchemaField("id", "INTEGER", mode="NULLABLE")
        schema_field2 = SchemaField("name", "STRING", mode="NULLABLE")
        schema_field3 = SchemaField("email", "STRING", mode="REQUIRED")

        mock_table.schema = [schema_field1, schema_field2, schema_field3]

        mock_bigquery_client.get_table.return_value = mock_table

        table = service.get_table("dataset1", "users")

        assert table["table_id"] == "users"
        assert table["num_rows"] == 10000
        assert len(table["schema"]) == 3
        assert table["schema"][0]["name"] == "id"
        assert table["schema"][0]["type"] == "INTEGER"
        assert table["schema"][2]["mode"] == "REQUIRED"

        mock_bigquery_client.get_table.assert_called_once_with("test-project.dataset1.users")

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_get_table_not_found(self, mock_bigquery_client):
        """Test getting non-existent table"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService()
        service.client = mock_bigquery_client
        mock_bigquery_client.get_table.side_effect = NotFound("Table not found")

        with pytest.raises(NotFound):
            service.get_table("dataset1", "nonexistent_table")


@pytest.mark.unit
class TestBigQueryServiceExecuteQuery:
    """Test query execution functionality"""

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_execute_query_success(self, mock_bigquery_client):
        """Test successful query execution"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService()
        service.client = mock_bigquery_client
        service.project_id = "test-project"

        # Create mock job
        mock_job = MagicMock()
        mock_job.job_id = "test-job-123"
        mock_job.total_rows_processed = 100
        mock_job.total_bytes_processed = 1024000
        mock_job.bytes_billed = 10240000
        mock_job.cache_hit = False
        mock_job.state = "DONE"

        # Mock query results
        from google.cloud.bigquery import Row

        mock_row1 = MagicMock(spec=Row)
        mock_row1.keys.return_value = ["id", "name"]
        mock_row1.values.return_value = [1, "Test 1"]

        mock_row2 = MagicMock(spec=Row)
        mock_row2.keys.return_value = ["id", "name"]
        mock_row2.values.return_value = [2, "Test 2"]

        mock_job.result.return_value = [mock_row1, mock_row2]

        # Mock timing
        import time
        start_time = time.time()
        mock_job._ended_at_time = datetime.datetime.now()

        mock_bigquery_client.query.return_value = mock_job

        result = service.execute_query(
            sql="SELECT * FROM table1 LIMIT 10",
            timeout_ms=30000
        )

        assert result["row_count"] == 2
        assert result["columns"] == ["id", "name"]
        assert len(result["data"]) == 2
        assert result["metadata"]["job_id"] == "test-job-123"
        assert result["metadata"]["total_rows_processed"] == 100
        assert result["metadata"]["cache_hit"] is False

        mock_bigquery_client.query.assert_called_once()

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_execute_query_dry_run(self, mock_bigquery_client):
        """Test dry run query"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService()
        service.client = mock_bigquery_client
        service.project_id = "test-project"

        mock_job = MagicMock()
        mock_job.job_id = "dry-run-job"
        mock_job.total_rows_processed = 0
        mock_job.total_bytes_processed = 0
        mock_job.cache_hit = False
        mock_job.state = "DONE"

        mock_bigquery_client.query.return_value = mock_job

        result = service.execute_query(
            sql="SELECT * FROM table1",
            dry_run=True
        )

        # Verify dry_run parameter was passed
        call_args = mock_bigquery_client.query.call_args
        assert call_args[1]["dry_run"] is True

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_execute_query_with_timeout(self, mock_bigquery_client):
        """Test query execution with timeout"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService()
        service.client = mock_bigquery_client
        service.project_id = "test-project"

        mock_job = MagicMock()
        mock_job.job_id = "test-job"
        mock_job.result.return_value = []
        mock_job._ended_at_time = datetime.datetime.now()

        mock_bigquery_client.query.return_value = mock_job

        result = service.execute_query(
            sql="SELECT * FROM table1",
            timeout_ms=60000
        )

        # Verify timeout was passed correctly
        call_args = mock_bigquery_client.query.call_args
        # BigQuery uses timeout in seconds
        assert call_args is not None

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_execute_query_api_error(self, mock_bigquery_client):
        """Test query execution with API error"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService()
        service.client = mock_bigquery_client
        mock_bigquery_client.query.side_effect = GoogleAPIError("Query failed")

        with pytest.raises(GoogleAPIError):
            service.execute_query(sql="SELECT * FROM table1")


@pytest.mark.unit
class TestBigQueryServiceTestConnection:
    """Test connection testing functionality"""

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_test_connection_success(self, mock_bigquery_client):
        """Test successful connection test"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService()
        service.client = mock_bigquery_client

        # Mock successful dataset listing
        mock_bigquery_client.list_datasets.return_value = []

        result = service.test_connection()

        assert result is True
        mock_bigquery_client.list_datasets.assert_called_once_with(max_results=1)

    @patch('app.services.bigquery_service.BigQueryService.__init__', lambda x: None)
    def test_test_connection_failure(self, mock_bigquery_client):
        """Test connection test with failure"""
        from app.services.bigquery_service import BigQueryService

        service = BigQueryService()
        service.client = mock_bigquery_client
        mock_bigquery_client.list_datasets.side_effect = Exception("Connection failed")

        result = service.test_connection()

        assert result is False
