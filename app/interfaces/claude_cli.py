"""
Claude CLI Service Interface Protocol

This module defines the interface contract for Claude CLI service implementations.
"""
from typing import Protocol, Dict, Any


class ClaudeCLIServiceProtocol(Protocol):
    """
    Protocol defining the Claude CLI service interface.

    This protocol defines the contract for any Claude CLI service implementation.
    It enables natural language to SQL conversion using Claude Code CLI.

    Example implementation:
        class MyClaudeCLIService:
            async def execute_prompt(self, prompt: str, ...):
                # implementation
                pass
    """

    async def execute_prompt(
        self,
        prompt: str,
        bigquery_context: Dict[str, Any],
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute a prompt via Claude CLI

        Args:
            prompt: Natural language prompt from user
            bigquery_context: BigQuery schema context with datasets and tables
            timeout: Maximum time to wait for completion in seconds

        Returns:
            Dictionary with:
            - raw_output: str - Raw Claude CLI output
            - parsed_content: Dict - Parsed content with:
                - sql_query: str - Generated SQL query
                - text: str - Explanation/reasoning
            - workspace: str - Workspace directory used
            - execution_time: float - Time taken in seconds

        Raises:
            TimeoutError: If Claude CLI execution times out
            RuntimeError: If Claude CLI is not available
            Exception: For other execution errors
        """
        ...

    @property
    def workspace(self) -> str:
        """
        Get the Claude CLI workspace directory

        Returns:
            Absolute path to workspace directory
        """
        ...

    @property
    def is_available(self) -> bool:
        """
        Check if Claude CLI is available

        Returns:
            True if Claude CLI can be executed, False otherwise
        """
        ...
