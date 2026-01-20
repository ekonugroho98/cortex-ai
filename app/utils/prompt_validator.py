"""
Prompt Validator for Claude AI Agent

Validates user prompts to prevent prompt injection attacks
and restrict Claude AI capabilities to SQL generation only.
"""
import re
from typing import Tuple, List
from loguru import logger


class PromptValidator:
    """
    Validates prompts for Claude AI agent to prevent security issues
    """

    # Dangerous patterns that could lead to command injection
    DANGEROUS_PATTERNS = [
        # Command execution attempts
        r'\brm\s+-',  # rm with flags (dangerous)
        r'\brm\s+/',  # rm with path
        r'\brm\s+\.',  # rm with file starting with dot
        r'\bmv\s+.*\s+/etc',  # mv to system dir
        r'\bcp\s+.*\s+/etc',  # cp to system dir
        r'\bls\s+/-',  # ls with flags
        r'\bls\s+/etc',  # ls system dir
        r'\bcurl\s+',  # curl command
        r'\bwget\s+',  # wget command
        r'\bnc\s+',  # netcat
        r'\bbash\s+-',  # bash with flags
        r'\bsh\s+-',  # shell with flags
        r'\bpython\s+.*\.py',  # Python scripts
        r'\bnode\s+.*\.js',  # Node scripts
        r'\bwget\s+',
        r'\bgit\s+',  # git commands
        r'\bsudo\s+',  # sudo
        r'\bsu\s+',  # su

        # File operations
        r'\.\./',  # Path traversal (double dots)
        r'/etc/passwd',  # Specific sensitive file
        r'/etc/shadow',  # Shadow file
        r'/proc/',  # Process info
        r'/sys/',  # System info
        r'\.env\s',  # Environment files (with space after)
        r'\.env$',  # Environment files (end of line)
        r'id_rsa',  # SSH keys
        r'\.ssh/',  # SSH directory
        r'>\s*/',  # Redirect to file (overwriting)
        r'>>\s*/',  # Append to file

        # Code execution
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\(',
        r'__import__\s*\(',
        r'subprocess\s*\(',
        r'os\.system',
        r'popen',

        # Prompt injection
        r'ignore\s+(all\s+)?previous\s+instructions',
        r'disregard\s+(all\s+)?previous\s+instructions',
        r'forget\s+(all\s+)?previous\s+instructions',
        r'override\s+(all\s+)?previous\s+instructions',
        r'new\s+context\s*:',
        r'change\s+context\s*:',
        r'instead\s+of\s+the\s+above',
    ]

    # Maximum prompt length to prevent DoS
    MAX_PROMPT_LENGTH = 2000

    # Allowed keywords for data queries
    ALLOWED_KEYWORDS = [
        'select', 'from', 'where', 'join', 'left', 'right', 'inner', 'outer',
        'group', 'by', 'order', 'having', 'limit', 'offset', 'and', 'or', 'not',
        'in', 'like', 'between', 'is', 'null', 'count', 'sum', 'avg', 'max', 'min',
        'distinct', 'as', 'with', 'case', 'when', 'then', 'else', 'end',
        'window', 'over', 'partition', 'rows', 'range', 'unbounded',
        'extract', 'date', 'time', 'timestamp', 'datetime', 'interval',
        'table', 'tables', 'column', 'columns', 'schema', 'dataset',
        'show', 'list', 'find', 'get', 'top', 'bottom', 'first', 'last',
        'users', 'orders', 'revenue', 'sales', 'analytics', 'data',
        'how', 'many', 'much', 'count', 'total', 'average', 'sum',
        'per', 'by', 'for', 'in', 'of', 'the', 'a', 'an'
    ]

    def __init__(self):
        """Initialize prompt validator"""
        # Compile dangerous patterns for performance
        self.dangerous_regex = re.compile(
            '|'.join(self.DANGEROUS_PATTERNS),
            re.IGNORECASE
        )

    def validate(self, prompt: str) -> Tuple[bool, List[str]]:
        """
        Validate prompt for security issues

        Args:
            prompt: User prompt to validate

        Returns:
            Tuple of (is_valid, list_of_errors)

        Example:
            validator = PromptValidator()
            is_valid, errors = validator.validate("Show me top 10 users")
            # (True, [])

            is_valid, errors = validator.validate("Show users; rm -rf /")
            # (False, ["Dangerous pattern detected: rm command"])
        """
        errors = []

        # Check 1: Prompt length
        if len(prompt) > self.MAX_PROMPT_LENGTH:
            errors.append(f"Prompt too long (max {self.MAX_PROMPT_LENGTH} characters)")

        # Check 2: Dangerous patterns
        dangerous_matches = self.dangerous_regex.findall(prompt)
        if dangerous_matches:
            for match in dangerous_matches:
                errors.append(f"Potentially dangerous pattern detected: {match}")

        # Check 3: Suspicious instructions
        lower_prompt = prompt.lower()

        suspicious_indicators = [
            ('also', 'Multiple instructions'),
            ('then', 'Command chaining'),
            ('after that', 'Command chaining'),
            ('next,', 'Command chaining'),
            ('finally', 'Command chaining'),
            ('additionally', 'Command chaining'),
            ('besides', 'Command chaining'),
            ('create file', 'File operation'),
            ('write to', 'File operation'),
            ('save to', 'File operation'),
            ('download', 'External resource'),
            ('upload', 'External resource'),
            ('fetch', 'External resource'),
            ('install', 'Package installation'),
            ('import', 'Code import'),
            ('require', 'Package require'),
            ('exec', 'Code execution'),
            ('eval', 'Code evaluation'),
            ('system', 'System command'),
        ]

        for indicator, reason in suspicious_indicators:
            # Check if these words appear in potentially suspicious context
            if indicator in lower_prompt:
                # Additional check: is it in a legitimate context?
                if self._is_suspicious_context(prompt, indicator):
                    errors.append(f"Suspicious instruction detected: {indicator} ({reason})")

        # Check 4: Ensure prompt is query-related
        if not self._is_query_related(prompt):
            errors.append("Prompt does not appear to be data-related. Please ask questions about your data.")

        is_valid = len(errors) == 0
        return is_valid, errors

    def _is_suspicious_context(self, prompt: str, indicator: str) -> bool:
        """
        Check if an indicator appears in suspicious context

        Args:
            prompt: Full prompt
            indicator: Suspicious word found

        Returns:
            True if context is suspicious
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', prompt)

        # Check if indicator appears in a different sentence than data keywords
        for sentence in sentences:
            if indicator in sentence.lower():
                # If sentence doesn't contain data keywords, it's suspicious
                data_keywords = ['select', 'show', 'get', 'find', 'list', 'count', 'total',
                               'users', 'orders', 'table', 'dataset', 'data', 'query']
                if not any(kw in sentence.lower() for kw in data_keywords):
                    return True

        return False

    def _is_query_related(self, prompt: str) -> bool:
        """
        Check if prompt is related to data queries

        Args:
            prompt: User prompt

        Returns:
            True if prompt appears to be data-related
        """
        lower_prompt = prompt.lower()

        # Must contain at least one data-related keyword
        data_keywords = [
            'select', 'show', 'get', 'find', 'list', 'count', 'total',
            'users', 'orders', 'table', 'tables', 'dataset', 'data',
            'query', 'sql', 'row', 'column', 'revenue', 'sales',
            'how many', 'how much', 'top', 'bottom', 'average', 'sum'
        ]

        return any(kw in lower_prompt for kw in data_keywords)

    def sanitize(self, prompt: str) -> str:
        """
        Sanitize prompt by removing dangerous characters

        Args:
            prompt: User prompt

        Returns:
            Sanitized prompt
        """
        # Remove control characters
        prompt = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', prompt)

        # Remove multiple spaces
        prompt = re.sub(r'\s+', ' ', prompt)

        # Trim whitespace
        prompt = prompt.strip()

        return prompt


# Global validator instance
prompt_validator = PromptValidator()


def validate_user_prompt(prompt: str) -> Tuple[bool, List[str]]:
    """
    Validate user prompt for Claude AI agent

    Args:
        prompt: User prompt to validate

    Returns:
        Tuple of (is_valid, list_of_errors)

    Example:
        is_valid, errors = validate_user_prompt("Show top 10 users")
        if not is_valid:
            raise HTTPException(status_code=400, detail={"errors": errors})
    """
    return prompt_validator.validate(prompt)
