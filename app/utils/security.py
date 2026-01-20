"""
Production Security Utilities

Provides advanced security features for production deployments with sensitive data:
- Row-level security
- Query cost tracking and limits
- Data masking for sensitive columns
- PII/PHI detection
- Enhanced audit logging
"""
import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
from app.config import settings


class DataMasker:
    """
    Masks sensitive data in query results
    """

    def __init__(self, sensitive_columns: Optional[List[str]] = None):
        """
        Initialize data masker

        Args:
            sensitive_columns: List of column names to mask
        """
        self.sensitive_columns = sensitive_columns or settings.sensitive_columns
        self.sensitive_patterns = [
            (r'email', self._mask_email),
            (r'phone', self._mask_phone),
            (r'ssn|social_security', self._mask_ssn),
            (r'credit_card|card_number', self._mask_credit_card),
            (r'password|secret|token', self._mask_full),
            (r'api_key|access_key|private_key', self._mask_full),
        ]

    def mask_data(self, data: List[Dict[str, Any]], columns: List[str]) -> List[Dict[str, Any]]:
        """
        Mask sensitive data in query results

        Args:
            data: Query results (list of rows)
            columns: Column names

        Returns:
            Masked data
        """
        if not settings.enable_data_masking:
            return data

        masked_data = []
        for row in data:
            masked_row = {}
            for col_name, col_value in zip(columns, row.values()):
                if self._is_sensitive_column(col_name):
                    masked_row[col_name] = self._mask_value(col_name, col_value)
                else:
                    masked_row[col_name] = col_value
            masked_data.append(masked_row)

        return masked_data

    def _is_sensitive_column(self, column_name: str) -> bool:
        """Check if column is sensitive"""
        col_lower = column_name.lower()

        # Direct match
        if any(sensitive in col_lower for sensitive in self.sensitive_columns):
            return True

        # Pattern match
        for pattern, _ in self.sensitive_patterns:
            if re.search(pattern, col_lower):
                return True

        return False

    def _mask_value(self, column_name: str, value: Any) -> str:
        """Mask value based on column type"""
        col_lower = column_name.lower()

        for pattern, mask_func in self.sensitive_patterns:
            if re.search(pattern, col_lower):
                return mask_func(value)

        # Default masking
        return self._mask_generic(value)

    def _mask_email(self, value: Any) -> str:
        """Mask email address"""
        if not value or value is None:
            return "***@***.***"

        email = str(value)
        parts = email.split("@")
        if len(parts) != 2:
            return "***@***.***"

        username = parts[0]
        domain = parts[1]

        # Show first 2 chars of username
        masked_username = username[:2] + "***" if len(username) > 2 else "***"

        # Mask domain
        domain_parts = domain.split(".")
        if len(domain_parts) >= 2:
            masked_domain = "***." + ".".join(domain_parts[-2:])
        else:
            masked_domain = "***.***"

        return f"{masked_username}@{masked_domain}"

    def _mask_phone(self, value: Any) -> str:
        """Mask phone number"""
        if not value or value is None:
            return "***-***-****"

        phone = str(value)
        # Keep last 4 digits
        if len(phone) >= 4:
            return "***-***-" + phone[-4:]
        return "***-***-****"

    def _mask_ssn(self, value: Any) -> str:
        """Mask SSN"""
        return "***-**-****"

    def _mask_credit_card(self, value: Any) -> str:
        """Mask credit card number"""
        if not value or value is None:
            return "****-****-****-****"

        card = str(value).replace("-", "").replace(" ", "")
        if len(card) >= 4:
            return "****-****-****-" + card[-4:]
        return "****-****-****-****"

    def _mask_full(self, value: Any) -> str:
        """Completely mask value"""
        return "***"

    def _mask_generic(self, value: Any) -> str:
        """Generic masking"""
        if not value or value is None:
            return "***"
        return str(value)[:1] + "***" if len(str(value)) > 1 else "***"


class PIIDetector:
    """
    Detects PII/PHI in user prompts
    """

    def __init__(self, pii_keywords: Optional[List[str]] = None):
        """
        Initialize PII detector

        Args:
            pii_keywords: List of PII keywords to detect
        """
        self.pii_keywords = pii_keywords or settings.pii_keywords

    def contains_pii_request(self, prompt: str) -> Tuple[bool, List[str]]:
        """
        Check if prompt contains PII/PHI request

        Args:
            prompt: User prompt

        Returns:
            Tuple of (has_pii, detected_keywords)
        """
        if not settings.enable_pii_detection:
            return False, []

        prompt_lower = prompt.lower()
        detected = []

        for keyword in self.pii_keywords:
            if keyword.lower() in prompt_lower:
                detected.append(keyword)

        return len(detected) > 0, detected


class QueryCostTracker:
    """
    Tracks and limits query costs
    """

    def __init__(self, max_bytes: Optional[int] = None):
        """
        Initialize cost tracker

        Args:
            max_bytes: Maximum bytes allowed per query
        """
        self.max_bytes = max_bytes or settings.max_query_bytes_processed

    def check_cost_limits(
        self,
        total_bytes_processed: int,
        api_key: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if query exceeds cost limits

        Args:
            total_bytes_processed: Bytes processed by query
            api_key: API key for tracking

        Returns:
            Tuple of (within_limits, error_message)
        """
        if not settings.enable_query_cost_tracking:
            return True, None

        if total_bytes_processed > self.max_bytes:
            gb_processed = total_bytes_processed / 1_000_000_000
            gb_limit = self.max_bytes / 1_000_000_000

            error = (
                f"Query cost limit exceeded. "
                f"Processed: {gb_processed:.2f}GB, Limit: {gb_limit:.2f}GB. "
                f"Please add more filters to reduce data processed."
            )

            logger.warning(
                f"Query cost limit exceeded for {api_key[:8]}...: "
                f"{gb_processed:.2f}GB > {gb_limit:.2f}GB"
            )

            return False, error

        return True, None

    def log_query_cost(
        self,
        sql: str,
        total_bytes_processed: int,
        api_key: str,
        duration_ms: int
    ):
        """
        Log query cost for audit

        Args:
            sql: SQL query (hashed)
            total_bytes_processed: Bytes processed
            api_key: API key
            duration_ms: Query duration
        """
        if not settings.enable_query_cost_tracking:
            return

        # Hash SQL for logging (don't log raw SQL)
        sql_hash = hashlib.sha256(sql.encode()).hexdigest()[:16]

        gb_processed = total_bytes_processed / 1_000_000_000
        estimated_cost_usd = gb_processed * 5  # BigQuery: $5 per TB

        logger.info(
            f"Query cost: {gb_processed:.4f}GB (${estimated_cost_usd:.4f}) | "
            f"Duration: {duration_ms}ms | SQL: {sql_hash} | API: {api_key[:8]}..."
        )


class RowLevelSecurityEnforcer:
    """
    Enforces row-level security policies

    Note: This is a simplified implementation. For production,
    consider using BigQuery's native row-level security.
    """

    def __init__(self):
        """Initialize RLS enforcer"""
        self.enabled = settings.enable_row_level_security

        # Define RLS policies (example)
        # In production, load from database or config
        self.policies = {
            "users": {
                "filter_department": lambda user_dept, row_dept: row_dept == user_dept,
                "filter_region": lambda user_region, row_region: row_region == user_region,
            }
        }

    def apply_row_filters(
        self,
        sql: str,
        table_name: str,
        user_context: Dict[str, Any]
    ) -> str:
        """
        Apply row-level filters to SQL query

        Args:
            sql: Original SQL query
            table_name: Table being queried
            user_context: User context (department, region, etc.)

        Returns:
            SQL with RLS filters applied
        """
        if not self.enabled:
            return sql

        if table_name not in self.policies:
            return sql

        # Add WHERE clause for row filtering
        # This is a simplified implementation
        # In production, use SQL parser for proper modification

        logger.info(
            f"Applying row-level security for table {table_name} "
            f"user {user_context.get('user_id', 'unknown')}"
        )

        # Example: Add department filter
        if "department" in user_context:
            dept_filter = f" department = '{user_context['department']}'"
            if "WHERE" in sql.upper():
                sql = sql + f" AND {dept_filter}"
            else:
                sql = sql + f" WHERE {dept_filter}"

        return sql


class AuditLogger:
    """
    Enhanced audit logging for compliance
    """

    def __init__(self):
        """Initialize audit logger"""
        self.enabled = settings.enable_audit_logging

    def log_query(
        self,
        sql: str,
        api_key: str,
        user_context: Dict[str, Any],
        execution_time_ms: int,
        row_count: int,
        bytes_processed: int,
        success: bool,
        error: Optional[str] = None
    ):
        """
        Log query execution for audit

        Args:
            sql: SQL query executed
            api_key: API key used
            user_context: User context
            execution_time_ms: Execution time
            row_count: Number of rows returned
            bytes_processed: Bytes processed
            success: Whether query succeeded
            error: Error message if failed
        """
        if not self.enabled:
            return

        # Hash sensitive data
        sql_hash = hashlib.sha256(sql.encode()).hexdigest()[:16]
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]

        audit_entry = {
            "event": "query_executed",
            "sql_hash": sql_hash,
            "api_key_hash": api_key_hash,
            "user_id": user_context.get("user_id", "unknown"),
            "execution_time_ms": execution_time_ms,
            "row_count": row_count,
            "bytes_processed": bytes_processed,
            "success": success,
            "error": error,
            "timestamp": logger._core.extra["timestamp"] if hasattr(logger, '_core') else None
        }

        if success:
            logger.info(f"AUDIT: {audit_entry}")
        else:
            logger.error(f"AUDIT: {audit_entry}")

    def log_ai_agent_request(
        self,
        prompt: str,
        api_key: str,
        generated_sql: str,
        validation_passed: bool,
        execution_time_ms: int
    ):
        """
        Log AI agent request for audit

        Args:
            prompt: User prompt
            api_key: API key used
            generated_sql: SQL generated by AI
            validation_passed: Whether validation passed
            execution_time_ms: Total execution time
        """
        if not self.enabled:
            return

        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        sql_hash = hashlib.sha256(generated_sql.encode()).hexdigest()[:16]
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]

        audit_entry = {
            "event": "ai_agent_request",
            "prompt_hash": prompt_hash,
            "api_key_hash": api_key_hash,
            "generated_sql_hash": sql_hash,
            "validation_passed": validation_passed,
            "execution_time_ms": execution_time_ms
        }

        logger.info(f"AUDIT: {audit_entry}")


# Global instances
data_masker = DataMasker()
pii_detector = PIIDetector()
cost_tracker = QueryCostTracker()
rls_enforcer = RowLevelSecurityEnforcer()
audit_logger = AuditLogger()
