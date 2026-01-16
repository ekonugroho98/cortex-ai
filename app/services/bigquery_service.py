"""
BigQuery Service Layer
Handles all BigQuery operations
"""
import time
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.cloud.bigquery import Dataset, Table, Client, QueryJobConfig
from google.api_core.exceptions import GoogleAPIError
from loguru import logger

from app.config import settings


class BigQueryService:
    """Service for interacting with Google BigQuery"""

    def __init__(self):
        """Initialize BigQuery client"""
        try:
            self.client = Client(
                project=settings.gcp_project_id,
                credentials=None  # Uses GOOGLE_APPLICATION_CREDENTIALS env
            )
            self.project_id = settings.gcp_project_id
            logger.info(f"BigQuery client initialized for project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise

    def test_connection(self) -> bool:
        """Test BigQuery connection"""
        try:
            # Simple query to test connection
            query_job = self.client.query("SELECT 1 as test")
            query_job.result()
            logger.info("BigQuery connection test successful")
            return True
        except Exception as e:
            logger.error(f"BigQuery connection test failed: {e}")
            return False

    def list_datasets(self) -> List[Dict[str, Any]]:
        """
        List all datasets in the project

        Returns:
            List of datasets with metadata
        """
        try:
            datasets = list(self.client.list_datasets())
            result = []

            for dataset in datasets:
                dataset_ref = dataset.reference
                dataset_obj = Dataset(dataset_ref)

                # Get full dataset info
                dataset_info = self.client.get_dataset(dataset_ref)

                # Count tables
                tables = list(self.client.list_tables(dataset_ref))
                tables_count = len(tables)

                result.append({
                    "dataset_id": dataset.dataset_id,
                    "project": dataset.project,
                    "location": dataset_info.location,
                    "tables_count": tables_count,
                    "created_at": dataset_info.created,
                    "modified_at": dataset_info.modified
                })

            logger.info(f"Listed {len(result)} datasets")
            return result

        except GoogleAPIError as e:
            logger.error(f"Failed to list datasets: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing datasets: {e}")
            raise

    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get details of a specific dataset

        Args:
            dataset_id: Dataset ID

        Returns:
            Dataset details
        """
        try:
            dataset_ref = f"{self.project_id}.{dataset_id}"
            dataset = self.client.get_dataset(dataset_ref)

            # Count tables
            tables = list(self.client.list_tables(dataset_ref))
            tables_count = len(tables)

            result = {
                "dataset_id": dataset.dataset_id,
                "project": dataset.project,
                "location": dataset.location,
                "tables_count": tables_count,
                "created_at": dataset.created,
                "modified_at": dataset.modified
            }

            logger.info(f"Retrieved dataset: {dataset_id}")
            return result

        except GoogleAPIError as e:
            logger.error(f"Failed to get dataset {dataset_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting dataset {dataset_id}: {e}")
            raise

    def list_tables(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        List all tables in a dataset

        Args:
            dataset_id: Dataset ID

        Returns:
            List of tables with metadata
        """
        try:
            dataset_ref = f"{self.project_id}.{dataset_id}"
            tables = list(self.client.list_tables(dataset_ref))
            result = []

            for table in tables:
                table_ref = table.reference
                table_obj = Table(table_ref)
                table_info = self.client.get_table(table_ref)

                result.append({
                    "table_id": table.table_id,
                    "dataset_id": table.dataset_id,
                    "project": table.project,
                    "table_type": table.table_type,
                    "num_rows": table_info.num_rows,
                    "num_bytes": table_info.num_bytes,
                    "created_at": table_info.created,
                    "modified_at": table_info.modified,
                    "full_table_id": f"{table.project}.{table.dataset_id}.{table.table_id}"
                })

            logger.info(f"Listed {len(result)} tables in dataset {dataset_id}")
            return result

        except GoogleAPIError as e:
            logger.error(f"Failed to list tables in dataset {dataset_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing tables in dataset {dataset_id}: {e}")
            raise

    def get_table(self, dataset_id: str, table_id: str) -> Dict[str, Any]:
        """
        Get details of a specific table

        Args:
            dataset_id: Dataset ID
            table_id: Table ID

        Returns:
            Table details with schema
        """
        try:
            table_ref = f"{self.project_id}.{dataset_id}.{table_id}"
            table = self.client.get_table(table_ref)

            result = {
                "table_id": table.table_id,
                "dataset_id": table.dataset_id,
                "project": table.project,
                "table_type": table.table_type,
                "num_rows": table.num_rows,
                "num_bytes": table.num_bytes,
                "created_at": table.created,
                "modified_at": table.modified,
                "full_table_id": f"{table.project}.{table.dataset_id}.{table.table_id}",
                "schema": [
                    {
                        "name": field.name,
                        "type": field.field_type,
                        "mode": field.mode,
                        "description": field.description
                    }
                    for field in table.schema
                ]
            }

            logger.info(f"Retrieved table: {table_ref}")
            return result

        except GoogleAPIError as e:
            logger.error(f"Failed to get table {dataset_id}.{table_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting table {dataset_id}.{table_id}: {e}")
            raise

    def execute_query(
        self,
        sql: str,
        project_id: Optional[str] = None,
        dry_run: bool = False,
        timeout_ms: int = 60000,
        use_query_cache: bool = True,
        use_legacy_sql: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a SQL query

        Args:
            sql: SQL query string
            project_id: Override project ID
            dry_run: Validate query without executing
            timeout_ms: Query timeout in milliseconds
            use_query_cache: Use cached results if available
            use_legacy_sql: Use legacy SQL syntax

        Returns:
            Query results with metadata
        """
        start_time = time.time()

        try:
            # Configure query job
            job_config = QueryJobConfig()
            job_config.dry_run = dry_run
            job_config.use_query_cache = use_query_cache
            job_config.use_legacy_sql = use_legacy_sql

            # Execute query
            query_job = self.client.query(
                sql,
                project=project_id or self.project_id,
                job_config=job_config,
                timeout=timeout_ms / 1000  # Convert to seconds
            )

            # Wait for completion
            result = query_job.result()

            execution_time = int((time.time() - start_time) * 1000)

            # Extract metadata
            metadata = {
                "job_id": query_job.job_id,
                "total_rows_processed": query_job.total_bytes_processed and (
                    query_job.total_bytes_processed // 1000  # Rough estimate
                ),
                "total_bytes_processed": query_job.total_bytes_processed,
                "bytes_billed": query_job.total_bytes_billed,
                "cache_hit": query_job.cache_hit,
                "execution_time_ms": execution_time,
                "slot_time_ms": query_job.slot_millis if hasattr(query_job, 'slot_millis') else None
            }

            # Convert results to list of dicts
            rows = []
            columns = []

            if result.schema:
                columns = [field.name for field in result.schema]

                for row in result:
                    row_dict = {}
                    for i, field in enumerate(result.schema):
                        value = row[i]
                        # Convert to serializable types
                        if hasattr(value, 'isoformat'):  # datetime
                            value = value.isoformat()
                        elif hasattr(value, 'to_json'):  # geo data
                            value = str(value)
                        row_dict[field.name] = value
                    rows.append(row_dict)

            response = {
                "metadata": metadata,
                "data": rows,
                "row_count": len(rows),
                "columns": columns
            }

            logger.info(
                f"Query executed successfully. "
                f"Job ID: {query_job.job_id}, "
                f"Rows: {len(rows)}, "
                f"Time: {execution_time}ms"
            )

            return response

        except GoogleAPIError as e:
            logger.error(f"BigQuery API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise


# Global service instance
bigquery_service = BigQueryService()
