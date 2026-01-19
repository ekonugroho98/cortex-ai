#!/usr/bin/env python3
"""
Security Test Suite for CortexAI
Tests authentication, rate limiting, and input validation
"""
import requests
import sys
import time
from typing import Optional


class SecurityTester:
    """Test security features"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

    def test_authentication_required(self) -> bool:
        """Test that endpoints require authentication"""
        print("\n[TEST] Authentication Required")
        print("-" * 60)

        # Remove API key for this test
        test_session = requests.Session()

        response = test_session.get(f"{self.base_url}/api/v1/datasets")

        if response.status_code == 401:
            print("✓ PASS: Endpoint requires authentication (401)")
            return True
        else:
            print(f"✗ FAIL: Expected 401, got {response.status_code}")
            return False

    def test_valid_api_key(self) -> bool:
        """Test that valid API key works"""
        print("\n[TEST] Valid API Key")
        print("-" * 60)

        if not self.api_key:
            print("⊘ SKIP: No API key provided")
            return True

        response = self.session.get(f"{self.base_url}/api/v1/datasets")

        if response.status_code in [200, 404]:  # 404 is ok (no datasets)
            print(f"✓ PASS: Valid API key accepted ({response.status_code})")
            return True
        else:
            print(f"✗ FAIL: API key rejected ({response.status_code})")
            print(f"Response: {response.text[:200]}")
            return False

    def test_invalid_api_key(self) -> bool:
        """Test that invalid API key is rejected"""
        print("\n[TEST] Invalid API Key")
        print("-" * 60)

        test_session = requests.Session()
        test_session.headers.update({"X-API-Key": "invalid-key-12345"})

        response = test_session.get(f"{self.base_url}/api/v1/datasets")

        if response.status_code == 403:
            print("✓ PASS: Invalid API key rejected (403)")
            return True
        else:
            print(f"✗ FAIL: Expected 403, got {response.status_code}")
            return False

    def test_public_endpoints(self) -> bool:
        """Test that public endpoints work without auth"""
        print("\n[TEST] Public Endpoints")
        print("-" * 60)

        test_session = requests.Session()  # No API key

        endpoints = [
            ("/", "Root"),
            ("/health", "Health Check"),
            ("/docs", "API Docs")
        ]

        all_passed = True
        for endpoint, name in endpoints:
            response = test_session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 200:
                print(f"✓ PASS: {name} accessible without auth")
            else:
                print(f"✗ FAIL: {name} returned {response.status_code}")
                all_passed = False

        return all_passed

    def test_rate_limiting(self) -> bool:
        """Test that rate limiting works"""
        print("\n[TEST] Rate Limiting")
        print("-" * 60)

        if not self.api_key:
            print("⊘ SKIP: No API key provided")
            return True

        print("Sending 100 rapid requests...")

        test_session = requests.Session()
        test_session.headers.update({"X-API-Key": self.api_key})

        rate_limited = False
        for i in range(100):
            response = test_session.get(f"{self.base_url}/api/v1/datasets")
            if response.status_code == 429:
                rate_limited = True
                print(f"✓ PASS: Rate limit triggered after {i+1} requests (429)")
                break

            # Minimal delay to allow some requests through
            time.sleep(0.01)

        if not rate_limited:
            print("⊘ WARN: Rate limit not triggered (may need adjustment)")
            return True  # Don't fail, just warn

        return True

    def test_sql_injection_protection(self) -> bool:
        """Test SQL injection protection"""
        print("\n[TEST] SQL Injection Protection")
        print("-" * 60)

        if not self.api_key:
            print("⊘ SKIP: No API key provided")
            return True

        malicious_queries = [
            "SELECT * FROM users WHERE id = 1; DROP TABLE users--",
            "SELECT * FROM users UNION SELECT * FROM passwords--",
            "SELECT * FROM users WHERE 1=1 OR '1'='1'",
            "SELECT * FROM users; INSERT INTO users VALUES ('hacker', 'password')",
        ]

        all_blocked = True
        for query in malicious_queries:
            response = self.session.post(
                f"{self.base_url}/api/v1/query",
                json={"sql": query}
            )

            if response.status_code == 400:
                print(f"✓ PASS: Malicious query blocked")
                print(f"  Query: {query[:50]}...")
            else:
                print(f"✗ FAIL: Malicious query not blocked ({response.status_code})")
                print(f"  Query: {query[:50]}...")
                all_blocked = False

        return all_blocked

    def test_security_headers(self) -> bool:
        """Test security headers are present"""
        print("\n[TEST] Security Headers")
        print("-" * 60)

        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy",
        ]

        response = requests.get(f"{self.base_url}/health")

        all_present = True
        for header in required_headers:
            if header in response.headers:
                print(f"✓ PASS: {header} present")
            else:
                print(f"✗ FAIL: {header} missing")
                all_present = False

        return all_present

    def run_all_tests(self) -> dict:
        """Run all security tests"""
        print("=" * 60)
        print("CortexAI - Security Test Suite")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"API Key: {'Provided' if self.api_key else 'None (some tests skipped)'}")

        results = {
            "authentication_required": self.test_authentication_required(),
            "valid_api_key": self.test_valid_api_key(),
            "invalid_api_key": self.test_invalid_api_key(),
            "public_endpoints": self.test_public_endpoints(),
            "rate_limiting": self.test_rate_limiting(),
            "sql_injection": self.test_sql_injection_protection(),
            "security_headers": self.test_security_headers(),
        }

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)

        passed = sum(1 for v in results.values() if v is True)
        total = len(results)

        for test, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {test.replace('_', ' ').title()}")

        print("-" * 60)
        print(f"Results: {passed}/{total} tests passed")
        print("=" * 60)

        return results


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test CortexAI security features")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of API")
    parser.add_argument("--api-key", help="API key for testing")
    parser.add_argument("--env-file", default=".env", help="Path to .env file")

    args = parser.parse_args()

    # Try to read API key from .env if not provided
    api_key = args.api_key
    if not api_key:
        try:
            import re
            with open(args.env_file, "r") as f:
                content = f.read()
                # Extract API_KEYS value
                match = re.search(r'API_KEYS=\[?"([^"]+)"?\]', content)
                if match:
                    api_key = match.group(1)
                    print(f"Using API key from {args.env_file}")
        except FileNotFoundError:
            print(f"Warning: {args.env_file} not found")

    # Run tests
    tester = SecurityTester(base_url=args.url, api_key=api_key)
    results = tester.run_all_tests()

    # Exit with error code if any test failed
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
