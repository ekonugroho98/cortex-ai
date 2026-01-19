"""
SQL Query Validator for Security
"""
import re
from loguru import logger
from typing import List, Tuple


class SQLValidator:
    """
    Validate SQL queries to prevent injection attacks
    """

    # Dangerous keywords/patterns that could indicate injection
    DANGEROUS_PATTERNS = [
        r";\s*DROP\s+",  # DROP statements
        r";\s*DELETE\s+",  # DELETE statements
        r";\s*INSERT\s+",  # INSERT statements
        r";\s*UPDATE\s+",  # UPDATE statements
        r";\s*ALTER\s+",  # ALTER statements
        r";\s*CREATE\s+",  # CREATE statements
        r";\s*TRUNCATE\s+",  # TRUNCATE statements
        r";\s*EXEC\s*\(?",  # EXEC/EXECUTE statements
        r";\s*EXECUTE\s+",  # EXECUTE statements
        r"\bUNION\s+(?:ALL\s+)?SELECT\b",  # UNION SELECT injection (with or without ALL)
        r"\bINTO\s+OUTFILE\b",  # File write attempts
        r"\bINTO\s+DUMPFILE\b",  # File write attempts
        r"\bLOAD\s+DATA\b",  # Data loading
        r"\bLOAD_FILE\s*\(",  # File reading
        r"\bBENCHMARK\s*\(",  # Time-based injection
        r"\bSLEEP\s*\(",  # Time-based injection
        r"\bWAITFOR\s+DELAY\b",  # Time-based injection
        r"--",  # SQL comments (-- style)
        r"#",  # SQL comments (# style)
        r"/\*.*?\*/",  # Multi-line comments
        r";\s*--",  # Comment after statement
        r"\bor\s+1\s*=\s*1\b",  # Always true condition
        r"\band\s+1\s*=\s*1\b",  # Always true condition
        r"\bor\s+'1'\s*=\s*'1'",  # Always true condition (string)
        r"\band\s+'1'\s*=\s*'1'",  # Always true condition (string)
    ]

    # Allowed keywords for SELECT queries
    ALLOWED_KEYWORDS = [
        "SELECT", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "OUTER", "FULL",
        "ON", "AND", "OR", "NOT", "IN", "EXISTS", "BETWEEN", "LIKE", "IS", "NULL",
        "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET", "ASC", "DESC",
        "DISTINCT", "AS", "WITH", "CASE", "WHEN", "THEN", "ELSE", "END",
        "COUNT", "SUM", "AVG", "MIN", "MAX", "ARRAY_AGG", "STRING_AGG"
    ]

    def __init__(self, allow_only_select: bool = True):
        """
        Initialize SQL validator

        Args:
            allow_only_select: If True, only allow SELECT queries
        """
        self.allow_only_select = allow_only_select

    def validate(self, sql: str) -> Tuple[bool, List[str]]:
        """
        Validate SQL query

        Args:
            sql: SQL query string

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not sql or not sql.strip():
            errors.append("Query cannot be empty")
            return False, errors

        sql_upper = sql.upper().strip()

        # Check if query starts with SELECT (if restricted)
        if self.allow_only_select and not sql_upper.startswith("SELECT"):
            errors.append("Only SELECT queries are allowed")
            logger.warning(f"Non-SELECT query attempted: {sql[:50]}...")
            return False, errors

        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE | re.MULTILINE):
                errors.append(f"Query contains dangerous pattern: {pattern}")
                logger.warning(f"Dangerous SQL pattern detected: {pattern} in query: {sql[:50]}...")

        # Check for multiple statements
        if ";" in sql and not sql.strip().endswith(";"):
            errors.append("Multiple SQL statements are not allowed")
            logger.warning("Multiple SQL statements detected")

        # Check for quote imbalance (potential injection)
        single_quotes = sql.count("'")
        double_quotes = sql.count('"')
        backticks = sql.count("`")

        if single_quotes % 2 != 0:
            errors.append("Imbalanced single quotes detected")
            logger.warning("Imbalanced single quotes in SQL query")

        if double_quotes % 2 != 0:
            errors.append("Imbalanced double quotes detected")
            logger.warning("Imbalanced double quotes in SQL query")

        # Check query length (prevent overly complex queries)
        if len(sql) > 10000:
            errors.append("Query too long (max 10000 characters)")
            logger.warning(f"Overly long query detected: {len(sql)} characters")

        # Check for excessive UNION statements
        union_count = len(re.findall(r"\bUNION\b", sql, re.IGNORECASE))
        if union_count > 5:
            errors.append("Too many UNION statements (max 5)")
            logger.warning(f"Excessive UNION statements: {union_count}")

        is_valid = len(errors) == 0

        if is_valid:
            logger.debug(f"SQL query validated successfully: {sql[:50]}...")

        return is_valid, errors


def validate_sql_query(sql: str, allow_only_select: bool = True) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate SQL query

    Args:
        sql: SQL query string
        allow_only_select: If True, only allow SELECT queries

    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = SQLValidator(allow_only_select=allow_only_select)
    return validator.validate(sql)
