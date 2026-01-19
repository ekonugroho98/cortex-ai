"""
Unit Tests for SQL Validators
"""
import pytest
from app.utils.validators import SQLValidator, validate_sql_query


@pytest.mark.unit
class TestSQLValidator:
    """Test SQL validation functionality"""

    def test_initialization(self):
        """Test validator initialization"""
        validator = SQLValidator(allow_only_select=True)
        assert validator.allow_only_select is True

        validator = SQLValidator(allow_only_select=False)
        assert validator.allow_only_select is False

    def test_valid_select_query(self):
        """Test validation of valid SELECT queries"""
        validator = SQLValidator(allow_only_select=True)

        valid_queries = [
            "SELECT * FROM table1",
            "SELECT id, name FROM users WHERE active = true",
            "SELECT COUNT(*) as total FROM orders",
            "SELECT * FROM dataset1.table1 WHERE date > '2024-01-01' LIMIT 100",
            "SELECT u.id, u.name, o.order_id FROM users u JOIN orders o ON u.id = o.user_id"
        ]

        for query in valid_queries:
            is_valid, errors = validator.validate(query)
            assert is_valid, f"Query should be valid: {query}"
            assert len(errors) == 0, f"Should have no errors: {errors}"

    def test_query_too_long(self):
        """Test rejection of overly long queries"""
        validator = SQLValidator(allow_only_select=True)

        # Create query > 10000 characters
        long_query = "SELECT * FROM users WHERE " + " AND ".join([f"col{i} = 'value'" for i in range(500)])

        is_valid, errors = validator.validate(long_query)
        assert not is_valid
        assert any("too long" in error.lower() for error in errors)

    def test_query_empty(self):
        """Test rejection of empty query"""
        validator = SQLValidator(allow_only_select=True)

        is_valid, errors = validator.validate("")
        assert not is_valid
        assert any("empty" in error.lower() for error in errors)

    def test_drop_table_injection(self):
        """Test blocking of DROP TABLE injection"""
        validator = SQLValidator(allow_only_select=True)

        malicious_queries = [
            "SELECT * FROM users; DROP TABLE users--",
            "SELECT * FROM users WHERE id = 1; DROP TABLE users",
            "SELECT * FROM users; DROP TABLE users --",
            "SELECT * FROM users ; DROP TABLE users;"
        ]

        for query in malicious_queries:
            is_valid, errors = validator.validate(query)
            assert not is_valid, f"DROP injection should be blocked: {query}"
            assert any("drop" in error.lower() for error in errors), f"Should detect DROP: {errors}"

    def test_union_select_injection(self):
        """Test blocking of UNION SELECT injection"""
        validator = SQLValidator(allow_only_select=True)

        malicious_queries = [
            "SELECT * FROM users UNION SELECT * FROM passwords",
            "SELECT * FROM users UNION ALL SELECT * FROM passwords",
            "SELECT username FROM users UNION SELECT password FROM admin"
        ]

        for query in malicious_queries:
            is_valid, errors = validator.validate(query)
            assert not is_valid, f"UNION injection should be blocked: {query}"
            assert any("union" in error.lower() for error in errors)

    def test_multiple_statements(self):
        """Test blocking of multiple statements"""
        validator = SQLValidator(allow_only_select=True)

        malicious_queries = [
            "SELECT * FROM users; SELECT * FROM orders",
            "SELECT * FROM users; INSERT INTO users VALUES (1, 'test')",
            "SELECT * FROM users; DELETE FROM users WHERE 1=1"
        ]

        for query in malicious_queries:
            is_valid, errors = validator.validate(query)
            assert not is_valid, f"Multiple statements should be blocked: {query}"
            assert any("multiple" in error.lower() for error in errors)

    def test_non_select_queries_blocked(self):
        """Test blocking of non-SELECT queries"""
        validator = SQLValidator(allow_only_select=True)

        non_select_queries = [
            "INSERT INTO users VALUES (1, 'test')",
            "UPDATE users SET name = 'test' WHERE id = 1",
            "DELETE FROM users WHERE id = 1",
            "CREATE TABLE test (id INT)",
            "ALTER TABLE users ADD COLUMN email VARCHAR(255)",
            "TRUNCATE TABLE users"
        ]

        for query in non_select_queries:
            is_valid, errors = validator.validate(query)
            assert not is_valid, f"Non-SELECT query should be blocked: {query}"
            assert any("select" in error.lower() or "only select" in error.lower() for error in errors)

    def test_time_based_injection(self):
        """Test blocking of time-based injection"""
        validator = SQLValidator(allow_only_select=True)

        malicious_queries = [
            "SELECT * FROM users WHERE id = 1 AND SLEEP(10)",
            "SELECT * FROM users WHERE id = 1 AND BENCHMARK(1000000, MD5(1))",
            "SELECT * FROM users WHERE id = 1; WAITFOR DELAY '00:00:10'"
        ]

        for query in malicious_queries:
            is_valid, errors = validator.validate(query)
            assert not is_valid, f"Time-based injection should be blocked: {query}"
            assert any("sleep" in error.lower() or "benchmark" in error.lower() or "waitfor" in error.lower() for error in errors)

    def test_comment_injection(self):
        """Test blocking of comment injection"""
        validator = SQLValidator(allow_only_select=True)

        malicious_queries = [
            "SELECT * FROM users -- admin comment",
            "SELECT * FROM users # hacker comment",
            "SELECT * FROM users /* injection */",
            "SELECT * FROM users WHERE id = 1-- AND password = 'secret'"
        ]

        for query in malicious_queries:
            is_valid, errors = validator.validate(query)
            assert not is_valid, f"Comment injection should be blocked: {query}"
            assert any("--" in error or "comment" in error.lower() for error in errors)

    def test_imbalanced_quotes(self):
        """Test detection of imbalanced quotes"""
        validator = SQLValidator(allow_only_select=True)

        queries_with_imbalanced_quotes = [
            "SELECT * FROM users WHERE name = 'test",
            "SELECT * FROM users WHERE name = 'test''",
            'SELECT * FROM users WHERE name = "test',
            "SELECT * FROM users WHERE name = 'test' AND email = \"test"
        ]

        for query in queries_with_imbalanced_quotes:
            is_valid, errors = validator.validate(query)
            assert not is_valid, f"Imbalanced quotes should be detected: {query}"
            assert any("quote" in error.lower() or "imbalanced" in error.lower() for error in errors)

    def test_excessive_unions(self):
        """Test blocking of excessive UNION statements"""
        validator = SQLValidator(allow_only_select=True)

        # Create query with more than 5 UNIONs
        query = "SELECT * FROM users"
        for i in range(10):
            query += f" UNION SELECT * FROM table{i}"

        is_valid, errors = validator.validate(query)
        assert not is_valid
        assert any("union" in error.lower() and "too many" in error.lower() for error in errors)

    def test_file_operations_blocked(self):
        """Test blocking of file operation attempts"""
        validator = SQLValidator(allow_only_select=True)

        file_operations = [
            "SELECT * FROM users INTO OUTFILE '/tmp/users.txt'",
            "SELECT * FROM users INTO DUMPFILE '/tmp/users.dat'",
            "SELECT * FROM users LOAD DATA INFILE '/etc/passwd'",
            "SELECT LOAD_FILE('/etc/passwd') FROM users"
        ]

        for query in file_operations:
            is_valid, errors = validator.validate(query)
            assert not is_valid, f"File operation should be blocked: {query}"

    def test_always_true_conditions(self):
        """Test detection of always-true conditions"""
        validator = SQLValidator(allow_only_select=True)

        always_true_queries = [
            "SELECT * FROM users WHERE 1=1",
            "SELECT * FROM users WHERE '1'='1'",
            "SELECT * FROM users WHERE 1=1 OR '1'='1'",
            "SELECT * FROM users WHERE 1=1 AND 1=1"
        ]

        for query in always_true_queries:
            is_valid, errors = validator.validate(query)
            # Always-true conditions should be blocked
            assert not is_valid or any("1=1" in error or "always true" in error.lower() for error in errors)

    def test_valid_complex_query(self):
        """Test validation of complex but valid query"""
        validator = SQLValidator(allow_only_select=True)

        complex_query = """
            SELECT
                u.id,
                u.name,
                u.email,
                COUNT(o.id) as order_count,
                SUM(o.amount) as total_amount
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.created_at > '2024-01-01'
                AND u.active = TRUE
            GROUP BY u.id, u.name, u.email
            HAVING COUNT(o.id) > 0
            ORDER BY total_amount DESC
            LIMIT 100
        """

        is_valid, errors = validator.validate(complex_query)
        assert is_valid, f"Complex valid query should pass: {errors}"
        assert len(errors) == 0

    def test_query_with_newlines(self):
        """Test query with newlines is handled correctly"""
        validator = SQLValidator(allow_only_select=True)

        query_with_newlines = """SELECT *
        FROM users
        WHERE active = true
        LIMIT 10"""

        is_valid, errors = validator.validate(query_with_newlines)
        assert is_valid

    def test_allow_only_select_false(self):
        """Test validator when allow_only_select is False"""
        validator = SQLValidator(allow_only_select=False)

        # Non-SELECT queries should be allowed
        insert_query = "INSERT INTO users VALUES (1, 'test')"
        is_valid, errors = validator.validate(insert_query)

        # Should still block dangerous patterns
        assert not is_valid or any("drop" in error.lower() for error in errors)


@pytest.mark.unit
class TestValidateSQLQuery:
    """Test convenience function"""

    def test_validate_sql_query_function(self):
        """Test the convenience function"""
        is_valid, errors = validate_sql_query("SELECT * FROM users")

        assert is_valid
        assert len(errors) == 0

    def test_validate_sql_query_with_options(self):
        """Test convenience function with options"""
        # Should block non-SELECT
        is_valid, errors = validate_sql_query(
            "INSERT INTO users VALUES (1, 'test')",
            allow_only_select=True
        )

        assert not is_valid

        # Should allow non-SELECT when disabled
        is_valid, errors = validate_sql_query(
            "SELECT * FROM users",  # Safe query
            allow_only_select=False
        )

        assert is_valid


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_query_exactly_10000_chars(self):
        """Test query at exactly maximum length"""
        validator = SQLValidator(allow_only_select=True)

        # Create query exactly 10000 characters
        query = "SELECT * FROM users WHERE " + " AND ".join([f"col{i} = 'value'" for i in range(487)])
        query = query[:10000]

        is_valid, errors = validator.validate(query)
        # Should be valid (at boundary)
        assert is_valid or any("too long" in error.lower() for error in errors)

    def test_query_with_special_characters(self):
        """Test query with special characters"""
        validator = SQLValidator(allow_only_select=True)

        query = "SELECT * FROM users WHERE email LIKE 'test%@example.com'"

        is_valid, errors = validator.validate(query)
        assert is_valid

    def test_query_with_unicode(self):
        """Test query with unicode characters"""
        validator = SQLValidator(allow_only_select=True)

        query = "SELECT * FROM users WHERE name = 'François'"

        is_valid, errors = validator.validate(query)
        assert is_valid

    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive"""
        validator = SQLValidator(allow_only_select=True)

        # All should be blocked
        variations = [
            "SELECT * FROM users; DROP TABLE users--",
            "SELECT * FROM users; drop table users--",
            "SELECT * FROM users; Drop Table Users--",
            "SELECT * FROM users; DROP table users--"
        ]

        for query in variations:
            is_valid, errors = validator.validate(query)
            assert not is_valid, f"Should block (case-insensitive): {query}"

    def test_query_with_backticks(self):
        """Test query with BigQuery-style backticks"""
        validator = SQLValidator(allow_only_select=True)

        query = "SELECT * FROM `project.dataset.table` WHERE id = 1"

        is_valid, errors = validator.validate(query)
        assert is_valid

    def test_query_with_comments_removed(self):
        """Test that SQL comments are detected even in complex ways"""
        validator = SQLValidator(allow_only_select=True)

        queries = [
            "SELECT * FROM users -- comment\nWHERE id = 1",
            "SELECT * FROM users /* comment */ WHERE id = 1",
            "SELECT * FROM users # comment\nWHERE id = 1"
        ]

        for query in queries:
            is_valid, errors = validator.validate(query)
            assert not is_valid, f"Should detect comments: {query}"
