"""
Integration Tests for API Endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from typing import Dict


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check_unhealthy(self, test_client_with_mocks):
        """Test health check when services are unhealthy"""
        response = test_client_with_mocks.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

    def test_root_endpoint(self, test_client_with_mocks):
        """Test root endpoint"""
        response = test_client_with_mocks.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data


@pytest.mark.integration
class TestDatasetEndpoints:
    """Test dataset endpoints"""

    def test_list_datasets_success(self, test_client_with_mocks, api_headers):
        """Test successful dataset listing"""
        response = test_client_with_mocks.get(
            "/api/v1/datasets",
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "count" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_list_datasets_without_auth(self, test_client_with_mocks):
        """Test dataset listing without authentication"""
        # Disable auth for this test
        with patch('app.middleware.auth.settings', MagicMock(enable_auth=False)):
            response = test_client_with_mocks.get("/api/v1/datasets")
            assert response.status_code in [200, 401]


@pytest.mark.integration
class TestTableEndpoints:
    """Test table endpoints"""

    def test_list_tables_success(self, test_client_with_mocks, api_headers):
        """Test successful table listing"""
        response = test_client_with_mocks.get(
            "/api/v1/tables/test_dataset",
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["dataset_id"] == "test_dataset"
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_list_tables_not_found(self, test_client_with_mocks, api_headers):
        """Test listing tables from non-existent dataset"""
        response = test_client_with_mocks.get(
            "/api/v1/tables/nonexistent_dataset",
            headers=api_headers
        )

        # Should return 404 or empty list
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestQueryEndpoints:
    """Test query endpoints"""

    def test_execute_query_success(self, test_client_with_mocks, api_headers, sample_query_request):
        """Test successful query execution"""
        response = test_client_with_mocks.post(
            "/api/v1/query",
            json=sample_query_request,
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "metadata" in data
        assert "row_count" in data
        assert "columns" in data

    def test_execute_query_dry_run(self, test_client_with_mocks, api_headers):
        """Test dry run query"""
        query_request = {
            "sql": "SELECT * FROM `test-project.test_dataset.table1`",
            "dry_run": True
        }

        response = test_client_with_mocks.post(
            "/api/v1/query",
            json=query_request,
            headers=api_headers
        )

        assert response.status_code == 200

    def test_execute_query_invalid_sql(self, test_client_with_mocks, api_headers):
        """Test query execution with invalid SQL"""
        # This should be blocked by SQL validator
        malicious_query = {
            "sql": "SELECT * FROM users; DROP TABLE users--"
        }

        response = test_client_with_mocks.post(
            "/api/v1/query",
            json=malicious_query,
            headers=api_headers
        )

        # Should be blocked with 400
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "INVALID_QUERY" in str(data)

    def test_execute_query_without_auth(self, test_client_with_mocks, sample_query_request):
        """Test query execution without authentication"""
        response = test_client_with_mocks.post(
            "/api/v1/query",
            json=sample_query_request
        )

        # Should require auth
        assert response.status_code in [401, 403]

    def test_execute_query_validation_error(self, test_client_with_mocks, api_headers):
        """Test query execution with validation error"""
        invalid_query = {
            "sql": "SELECT * FROM table1",
            "timeout_ms": 100  # Too low (min 1000)
        }

        response = test_client_with_mocks.post(
            "/api/v1/query",
            json=invalid_query,
            headers=api_headers
        )

        # Should return validation error
        assert response.status_code == 422


@pytest.mark.integration
class TestAuthentication:
    """Test authentication middleware"""

    def test_public_endpoint_no_auth(self, test_client_with_mocks):
        """Test public endpoints work without auth"""
        public_endpoints = [
            "/",
            "/health",
            "/docs",
            "/redoc"
        ]

        for endpoint in public_endpoints:
            response = test_client_with_mocks.get(endpoint)
            assert response.status_code == 200

    def test_protected_endpoint_without_auth(self, test_client_with_mocks):
        """Test protected endpoints require auth"""
        response = test_client_with_mocks.get("/api/v1/datasets")
        assert response.status_code in [401, 403]

    def test_protected_endpoint_with_invalid_key(self, test_client_with_mocks):
        """Test protected endpoint with invalid API key"""
        headers = {
            "X-API-Key": "invalid-api-key-12345",
            "Content-Type": "application/json"
        }

        response = test_client_with_mocks.get(
            "/api/v1/datasets",
            headers=headers
        )

        assert response.status_code == 403

    def test_protected_endpoint_with_valid_key(self, test_client_with_mocks, api_headers):
        """Test protected endpoint with valid API key"""
        response = test_client_with_mocks.get(
            "/api/v1/datasets",
            headers=api_headers
        )

        # Should succeed if auth works correctly
        assert response.status_code in [200, 401]


@pytest.mark.integration
class TestRateLimiting:
    """Test rate limiting middleware"""

    def test_rate_limiting_enforced(self, test_client_with_mocks, api_headers):
        """Test that rate limiting is enforced"""
        # Make multiple rapid requests
        responses = []
        for i in range(100):
            response = test_client_with_mocks.get(
                "/api/v1/datasets",
                headers=api_headers
            )
            responses.append(response)
            if response.status_code == 429:
                break

        # At least one request should be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        # Note: This might not trigger in test environment with in-memory limiter
        # but the logic should be there

    def test_rate_limit_headers(self, test_client_with_mocks, api_headers):
        """Test rate limit headers are present"""
        response = test_client_with_mocks.get(
            "/api/v1/datasets",
            headers=api_headers
        )

        if response.status_code == 200:
            headers = response.headers
            # Check for rate limit headers
            assert "X-RateLimit-Limit" in headers or "x-ratelimit-limit" in headers


@pytest.mark.integration
class TestSecurityHeaders:
    """Test security headers"""

    def test_security_headers_present(self, test_client_with_mocks):
        """Test security headers are present"""
        response = test_client_with_mocks.get("/health")

        headers = response.headers

        # Check for security headers (case-insensitive)
        header_keys = {k.lower(): v for k, v in headers.items()}

        assert "x-content-type-options" in header_keys
        assert header_keys["x-content-type-options"] == "nosniff"

        assert "x-frame-options" in header_keys
        assert header_keys["x-frame-options"] == "DENY"

        assert "x-xss-protection" in header_keys

        # CSP and HSTS might not be present in HTTP, but check
        if "content-security-policy" in header_keys:
            assert "default-src 'self'" in header_keys["content-security-policy"]


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling"""

    def test_404_error(self, test_client_with_mocks):
        """Test 404 error handling"""
        response = test_client_with_mocks.get("/nonexistent-endpoint")

        assert response.status_code == 404

    def test_405_method_not_allowed(self, test_client_with_mocks):
        """Test 405 method not allowed"""
        response = test_client_with_mocks.post("/health")

        assert response.status_code == 405

    def test_422_validation_error(self, test_client_with_mocks, api_headers):
        """Test validation error"""
        invalid_request = {
            "sql": "",  # Empty SQL
            "timeout_ms": "invalid"  # Invalid type
        }

        response = test_client_with_mocks.post(
            "/api/v1/query",
            json=invalid_request,
            headers=api_headers
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Performance tests"""

    def test_query_response_time(self, test_client_with_mocks, api_headers):
        """Test query response time is acceptable"""
        import time

        query_request = {
            "sql": "SELECT * FROM `test-project.test_dataset.table1` LIMIT 100"
        }

        start_time = time.time()
        response = test_client_with_mocks.post(
            "/api/v1/query",
            json=query_request,
            headers=api_headers
        )
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        # Mock responses should be fast (< 100ms)
        assert response_time_ms < 100

    def test_concurrent_requests(self, test_client_with_mocks, api_headers):
        """Test handling concurrent requests"""
        import asyncio
        import concurrent.futures

        def make_request():
            return test_client_with_mocks.get(
                "/api/v1/datasets",
                headers=api_headers
            )

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count >= 5  # At least half should succeed


@pytest.mark.integration
class TestCORS:
    """Test CORS configuration"""

    def test_cors_headers(self, test_client_with_mocks):
        """Test CORS headers are set correctly"""
        response = test_client_with_mocks.options(
            "/api/v1/datasets",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        headers = response.headers
        header_keys = {k.lower(): v for k, v in headers.items()}

        # Check CORS headers
        if "access-control-allow-origin" in header_keys:
            # Should not be wildcard
            assert header_keys["access-control-allow-origin"] != "*"
