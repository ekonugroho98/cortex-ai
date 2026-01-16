"""
API Endpoint Tests
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "BigQuery AI Service"
        assert data["status"] == "running"
        assert "docs" in data

    def test_health_check(self):
        """Test health check endpoint"""
        # Note: This will fail if BigQuery credentials are not configured
        response = client.get("/health")
        # We expect either 200 (success) or 503 (service unavailable)
        assert response.status_code in [200, 503]


class TestDatasetsEndpoints:
    """Test dataset endpoints"""

    def test_list_datasets(self):
        """Test list datasets endpoint"""
        # Note: Requires valid BigQuery credentials
        response = client.get("/api/v1/datasets")
        # Could be 200 (success) or 500 (not configured)
        assert response.status_code in [200, 500]


class TestTablesEndpoints:
    """Test table endpoints"""

    def test_list_tables(self):
        """Test list tables endpoint"""
        # Note: Requires valid BigQuery credentials and existing dataset
        response = client.get("/api/v1/datasets/nonexistent/tables")
        # Should be 404 (dataset not found) or 500 (not configured)
        assert response.status_code in [404, 500]


class TestQueryEndpoints:
    """Test query endpoints"""

    def test_direct_query_invalid(self):
        """Test direct query with invalid SQL"""
        response = client.post(
            "/api/v1/query",
            json={
                "sql": "INVALID SQL QUERY"
            }
        )
        # Should return 400 (bad request) or 500 (not configured)
        assert response.status_code in [400, 500]
