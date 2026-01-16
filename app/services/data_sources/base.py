"""
Abstract Base Class for Data Sources
All data source implementations must inherit from this interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum


class DataSourceStatus(Enum):
    """Data source connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"


class DataSourceInterface(ABC):
    """
    Abstract base class for all data sources

    All data source implementations (BigQuery, PostgreSQL, Elasticsearch, APM, Kubernetes)
    must inherit from this class and implement all abstract methods.
    """

    source_type: str = None  # Must be set by child class
    display_name: str = None  # Human-readable name

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize data source with configuration

        Args:
            config: Dictionary containing connection parameters
        """
        self.config = config
        self.status = DataSourceStatus.DISCONNECTED
        self.connection = None

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to data source

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Close connection to data source

        Returns:
            bool: True if disconnection successful
        """
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test if connection is working

        Returns:
            Dict with keys:
                - status: "healthy" | "unhealthy" | "error"
                - message: str
                - latency_ms: int (optional)
                - metadata: dict (optional)
        """
        pass

    @abstractmethod
    async def query(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute query and return results

        Args:
            query: Query string (SQL, DSL, etc depending on source)
            params: Additional parameters for the query

        Returns:
            Dict with keys:
                - data: List[Dict] - Query results
                - row_count: int - Number of rows returned
                - metadata: Dict - Query metadata (execution time, etc)
                - columns: List[str] - Column names (if applicable)
        """
        pass

    @abstractmethod
    async def get_schema(self, **kwargs) -> Dict[str, Any]:
        """
        Get schema/metadata from data source

        For databases: tables, columns, types
        For Elasticsearch: indices, mappings
        For APM: services, metrics available
        For Kubernetes: resources, namespaces

        Args:
            **kwargs: Source-specific parameters

        Returns:
            Dict with schema information
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return what this source can do

        Returns:
            Dict with keys:
                - query_types: List[str] - Types of queries supported
                - supports_aggregation: bool
                - supports_joins: bool
                - max_result_size: int
                - features: List[str] - Additional features
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of data source

        Returns:
            Dict with keys:
                - source_type: str
                - status: str
                - display_name: str
        """
        return {
            "source_type": self.source_type,
            "display_name": self.display_name,
            "status": self.status.value
        }

    def validate_config(self) -> List[str]:
        """
        Validate configuration

        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        required_fields = self.get_required_config_fields()

        for field in required_fields:
            if field not in self.config:
                errors.append(f"Missing required config field: {field}")

        return errors

    @abstractmethod
    def get_required_config_fields(self) -> List[str]:
        """
        Return list of required configuration fields

        Returns:
            List of field names
        """
        pass
