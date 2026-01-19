"""
Interface Protocols for CortexAI Services

This package defines Protocol-based interfaces for all major services.
These interfaces enable:
- Easy mocking for testing
- Multiple implementations
- Type checking with mypy/pyright
- Better documentation through interface definitions

Available Protocols:
- BigQueryServiceProtocol: Interface for BigQuery operations
- ClaudeCLIServiceProtocol: Interface for Claude CLI operations

Example Usage:
    from app.interfaces import BigQueryServiceProtocol

    # Use protocol for type hints
    def process_data(service: BigQueryServiceProtocol) -> None:
        datasets = service.list_datasets()
        # ...

    # Create mock implementation
    class MockBigQueryService:
        def list_datasets(self):
            return [{"dataset_id": "test"}]

    service: BigQueryServiceProtocol = MockBigQueryService()
"""
from app.interfaces.bigquery import BigQueryServiceProtocol
from app.interfaces.claude_cli import ClaudeCLIServiceProtocol

__all__ = [
    "BigQueryServiceProtocol",
    "ClaudeCLIServiceProtocol"
]
