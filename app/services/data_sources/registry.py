"""
Data Source Registry
Central registry for all available data source types
"""

from typing import Dict, Type, List
from app.services.data_sources.base import DataSourceInterface
from loguru import logger


class DataSourceRegistry:
    """
    Registry for all available data sources

    This class maintains a registry of all data source implementations
    and provides methods to register, retrieve, and list sources.
    """

    _sources: Dict[str, Type[DataSourceInterface]] = {}

    @classmethod
    def register(cls, source_type: str, source_class: Type[DataSourceInterface]):
        """
        Register a new data source

        Args:
            source_type: Unique identifier for the source type
            source_class: Class implementing DataSourceInterface
        """
        cls._sources[source_type] = source_class
        logger.info(f"Registered data source: {source_type}")

    @classmethod
    def unregister(cls, source_type: str):
        """
        Unregister a data source

        Args:
            source_type: Source type to unregister
        """
        if source_type in cls._sources:
            del cls._sources[source_type]
            logger.info(f"Unregistered data source: {source_type}")

    @classmethod
    def get_source(cls, source_type: str) -> Type[DataSourceInterface]:
        """
        Get data source class by type

        Args:
            source_type: Type identifier

        Returns:
            DataSourceInterface class or None if not found
        """
        return cls._sources.get(source_type)

    @classmethod
    def is_registered(cls, source_type: str) -> bool:
        """
        Check if a source type is registered

        Args:
            source_type: Type identifier

        Returns:
            bool: True if registered
        """
        return source_type in cls._sources

    @classmethod
    def list_sources(cls) -> List[str]:
        """
        List all registered source types

        Returns:
            List of source type identifiers
        """
        return list(cls._sources.keys())

    @classmethod
    def get_source_info(cls, source_type: str) -> Dict:
        """
        Get information about a registered source

        Args:
            source_type: Type identifier

        Returns:
            Dict with source information or None if not found
        """
        source_class = cls._sources.get(source_type)
        if not source_class:
            return None

        # Create a temporary instance to get info
        temp_instance = source_class.__new__(source_class)
        return {
            "source_type": source_type,
            "display_name": getattr(temp_instance, 'display_name', source_type),
            "class_name": source_class.__name__,
            "module": source_class.__module__
        }

    @classmethod
    def get_all_source_info(cls) -> List[Dict]:
        """
        Get information about all registered sources

        Returns:
            List of dicts with source information
        """
        return [
            cls.get_source_info(source_type)
            for source_type in cls.list_sources()
        ]

    @classmethod
    def clear(cls):
        """
        Clear all registered sources (mainly for testing)
        """
        cls._sources.clear()
        logger.warning("Cleared all registered data sources")
