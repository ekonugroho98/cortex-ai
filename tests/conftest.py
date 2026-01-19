"""
Pytest Configuration and Fixtures
"""
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from typing import Dict, List
from datetime import datetime
import os


# ============== BigQuery Fixtures ==============

@pytest.fixture
def mock_bigquery_client():
    """Mock BigQuery client"""
    client = MagicMock()
    return client


@pytest.fixture
def mock_bigquery_service():
    """Mock BigQuery service"""
    service = MagicMock()
    service.list_datasets = Mock(return_value=[
        {
            "dataset_id": "test_dataset_1",
            "project": "test-project",
            "location": "US",
            "tables_count": 5
        },
        {
            "dataset_id": "test_dataset_2",
            "project": "test-project",
            "location": "US",
            "tables_count": 3
        }
    ])

    service.list_tables = Mock(return_value=[
        {
            "table_id": "table1",
            "dataset_id": "test_dataset",
            "project": "test-project",
            "table_type": "TABLE",
            "num_rows": 1000,
            "num_bytes": 1024000
        },
        {
            "table_id": "table2",
            "dataset_id": "test_dataset",
            "project": "test-project",
            "table_type": "VIEW",
            "num_rows": 500,
            "num_bytes": 512000
        }
    ])

    service.get_table = Mock(return_value={
        "table_id": "table1",
        "dataset_id": "test_dataset",
        "project": "test-project",
        "table_type": "TABLE",
        "num_rows": 1000,
        "num_bytes": 1024000,
        "schema": [
            {"name": "id", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "name", "type": "STRING", "mode": "NULLABLE"},
            {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE"}
        ]
    })

    service.execute_query = Mock(return_value={
        "data": [
            {"id": 1, "name": "Test 1"},
            {"id": 2, "name": "Test 2"}
        ],
        "metadata": {
            "job_id": "test-job-123",
            "total_rows_processed": 2,
            "total_bytes_processed": 1024,
            "bytes_billed": 10240,
            "cache_hit": False,
            "execution_time_ms": 150
        },
        "row_count": 2,
        "columns": ["id", "name"]
    })

    service.test_connection = Mock(return_value=True)
    return service


@pytest.fixture
def sample_query_result() -> Dict:
    """Sample query result"""
    return {
        "data": [
            {"id": 1, "name": "Test 1", "value": 100.5},
            {"id": 2, "name": "Test 2", "value": 200.5},
            {"id": 3, "name": "Test 3", "value": 300.5}
        ],
        "metadata": {
            "job_id": "test-job-123",
            "total_rows_processed": 3,
            "total_bytes_processed": 2048,
            "bytes_billed": 20480,
            "cache_hit": False,
            "execution_time_ms": 250
        },
        "row_count": 3,
        "columns": ["id", "name", "value"]
    }


# ============== Claude CLI Fixtures ==============

@pytest.fixture
def mock_claude_cli_service():
    """Mock Claude CLI service"""
    service = MagicMock()
    service.is_available = Mock(return_value=True)
    service.execute_prompt = Mock(return_value={
        "status": "success",
        "output": "Test response from Claude",
        "reasoning": "Test reasoning",
        "execution_time_ms": 500
    })
    return service


@pytest.fixture
def sample_claude_response() -> Dict:
    """Sample Claude response"""
    return {
        "status": "success",
        "output": "Based on the data, here are the insights...",
        "reasoning": "Let me analyze the query results...",
        "execution_time_ms": 750
    }


# ============== API Test Fixtures ==============

@pytest.fixture
def mock_api_key():
    """Mock API key for testing"""
    return "test-api-key-12345"


@pytest.fixture
def api_headers(mock_api_key):
    """API headers with authentication"""
    return {
        "X-API-Key": mock_api_key,
        "Content-Type": "application/json"
    }


@pytest.fixture
def sample_query_request() -> Dict:
    """Sample query request"""
    return {
        "sql": "SELECT * FROM `test-project.test_dataset.table1` LIMIT 10",
        "dry_run": False,
        "timeout_ms": 30000
    }


# ============== Environment Fixtures ==============

@pytest.fixture
def test_env_vars():
    """Test environment variables"""
    return {
        "GCP_PROJECT_ID": "test-project",
        "GOOGLE_APPLICATION_CREDENTIALS": "/tmp/test-sa.json",
        "API_KEYS": '["test-api-key-12345"]',
        "ENABLE_AUTH": "true",
        "RATE_LIMIT_PER_MINUTE": "60",
        "FASTAPI_ENV": "test",
        "LOG_LEVEL": "DEBUG"
    }


@pytest.fixture
def temp_env_file(tmp_path, test_env_vars):
    """Create temporary .env file for testing"""
    env_file = tmp_path / ".env"
    with open(env_file, "w") as f:
        for key, value in test_env_vars.items():
            f.write(f"{key}={value}\n")
    return str(env_file)


# ============== Async Test Fixtures ==============

@pytest.fixture
def async_mock():
    """Create async mock"""
    return AsyncMock()


# ============== Performance Test Fixtures ==============

@pytest.fixture
def performance_test_config():
    """Configuration for performance tests"""
    return {
        "max_query_time_ms": 5000,
        "max_rows_returned": 10000,
        "max_response_size_mb": 10
    }


# ============== Sample Data Fixtures ==============

@pytest.fixture
def sample_datasets() -> List[Dict]:
    """Sample dataset list"""
    return [
        {
            "dataset_id": "dataset1",
            "project": "test-project",
            "location": "US",
            "tables_count": 5,
            "created_at": datetime.now(),
            "modified_at": datetime.now()
        },
        {
            "dataset_id": "dataset2",
            "project": "test-project",
            "location": "EU",
            "tables_count": 3,
            "created_at": datetime.now(),
            "modified_at": datetime.now()
        }
    ]


@pytest.fixture
def sample_tables() -> List[Dict]:
    """Sample table list"""
    return [
        {
            "table_id": "users",
            "dataset_id": "dataset1",
            "project": "test-project",
            "table_type": "TABLE",
            "num_rows": 10000,
            "num_bytes": 10240000,
            "created_at": datetime.now(),
            "modified_at": datetime.now(),
            "full_table_id": "test-project.dataset1.users"
        },
        {
            "table_id": "orders",
            "dataset_id": "dataset1",
            "project": "test-project",
            "table_type": "TABLE",
            "num_rows": 50000,
            "num_bytes": 51200000,
            "created_at": datetime.now(),
            "modified_at": datetime.now(),
            "full_table_id": "test-project.dataset1.orders"
        }
    ]


@pytest.fixture
def sample_table_schema() -> List[Dict]:
    """Sample table schema"""
    return [
        {"name": "id", "type": "INTEGER", "mode": "NULLABLE", "description": "User ID"},
        {"name": "name", "type": "STRING", "mode": "NULLABLE", "description": "User name"},
        {"name": "email", "type": "STRING", "mode": "REQUIRED", "description": "User email"},
        {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE", "description": "Creation time"}
    ]


# ============== Test Client Fixture ==============

@pytest.fixture
async def test_client_with_mocks(mock_bigquery_service, mock_claude_cli_service):
    """Test client with mocked services"""
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    from app.main import app

    # Patch the global service instances
    with patch('app.services.bigquery_service.bigquery_service', mock_bigquery_service), \
         patch('app.services.claude_cli_service.claude_cli_service', mock_claude_cli_service):
        client = TestClient(app)
        yield client

    # Cleanup is handled by context manager


# ============== Error Test Fixtures ==============

@pytest.fixture
def bigquery_error_response():
    """Sample BigQuery error"""
    return {
        "status": "error",
        "error_code": "BQ_QUERY_ERROR",
        "message": "Query execution failed"
    }


@pytest.fixture
def timeout_error():
    """Timeout error mock"""
    import asyncio
    raise asyncio.TimeoutError("Query timeout")


@pytest.fixture
def connection_error():
    """Connection error mock"""
    import google.auth.exceptions
    raise google.auth.exceptions.DefaultCredentialsError("Credentials not found")


# ============== Rate Limiting Fixtures ==============

@pytest.fixture
def rate_limit_config():
    """Rate limiting configuration"""
    return {
        "requests_per_minute": 60,
        "burst_size": 10,
        "window_seconds": 60
    }


# ============== Security Test Fixtures ==============

@pytest.fixture
def valid_sql_queries():
    """List of valid SQL queries for testing"""
    return [
        "SELECT * FROM table1 LIMIT 10",
        "SELECT id, name FROM users WHERE active = true",
        "SELECT COUNT(*) as total FROM orders",
        "SELECT * FROM dataset1.table1 WHERE date > '2024-01-01'"
    ]


@pytest.fixture
def malicious_sql_queries():
    """List of malicious SQL queries for testing"""
    return [
        "SELECT * FROM users; DROP TABLE users--",
        "SELECT * FROM users UNION SELECT * FROM passwords",
        "SELECT * FROM users WHERE 1=1 OR '1'='1'",
        "SELECT * FROM users; INSERT INTO users VALUES ('hacker', 'pass')",
        "SELECT * FROM users WHERE id = 1 AND SLEEP(10)"
    ]


# ============== Pytest Configuration ==============

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "security: Security tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests"
    )
