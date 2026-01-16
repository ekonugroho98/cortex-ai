"""
Data Sources Package
Multi-source investigation platform supports multiple data sources
"""

from app.services.data_sources.base import DataSourceInterface
from app.services.data_sources.registry import DataSourceRegistry

__all__ = ["DataSourceInterface", "DataSourceRegistry"]
