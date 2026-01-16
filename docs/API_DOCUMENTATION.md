# API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

**Phase 1**: No authentication required

**Phase 2**: API key authentication via `X-API-Key` header

## Response Format

All responses follow this structure:

### Success Response
```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response
```json
{
  "status": "error",
  "error_code": "ERROR_CODE",
  "message": "Human readable error message",
  "details": { ... }
}
```

## Endpoints

### 1. Health Check

#### 1.1 Root Endpoint
```http
GET /
```

Returns service information.

**Response:**
```json
{
  "service": "BigQuery AI Service",
  "version": "1.0.0",
  "status": "running",
  "environment": "development",
  "docs": "/docs",
  "health": "/health",
  "api": "/api/v1"
}
```

#### 1.2 Health Check
```http
GET /health
```

Tests BigQuery connection and returns health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "bigquery_connected": true,
  "project_id": "your-project-id",
  "timestamp": "2026-01-15T10:00:00Z"
}
```

**Error Responses:**
- `503 Service Unavailable` - BigQuery connection failed

---

### 2. Datasets

#### 2.1 List Datasets
```http
GET /api/v1/datasets
```

Returns all datasets in the project.

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "data": [
    {
      "dataset_id": "analytics",
      "project": "my-project",
      "location": "US",
      "tables_count": 15,
      "created_at": "2024-01-01T00:00:00Z",
      "modified_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Error Responses:**
- `500 Internal Server Error` - Failed to list datasets

#### 2.2 Get Dataset
```http
GET /api/v1/datasets/{dataset_id}
```

Returns details of a specific dataset.

**Path Parameters:**
- `dataset_id` (string, required) - Dataset ID

**Response:**
```json
{
  "dataset_id": "analytics",
  "project": "my-project",
  "location": "US",
  "tables_count": 15,
  "created_at": "2024-01-01T00:00:00Z",
  "modified_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Dataset not found
- `500 Internal Server Error` - Failed to get dataset

---

### 3. Tables

#### 3.1 List Tables
```http
GET /api/v1/datasets/{dataset_id}/tables
```

Returns all tables in a dataset.

**Path Parameters:**
- `dataset_id` (string, required) - Dataset ID

**Response:**
```json
{
  "status": "success",
  "dataset_id": "analytics",
  "count": 15,
  "data": [
    {
      "table_id": "users",
      "dataset_id": "analytics",
      "project": "my-project",
      "table_type": "TABLE",
      "num_rows": 1000000,
      "num_bytes": 50000000,
      "created_at": "2024-01-01T00:00:00Z",
      "modified_at": "2024-01-15T10:30:00Z",
      "full_table_id": "my-project.analytics.users"
    }
  ]
}
```

**Table Types:**
- `TABLE` - Standard table
- `VIEW` - View
- `EXTERNAL` - External table

**Error Responses:**
- `404 Not Found` - Dataset not found
- `500 Internal Server Error` - Failed to list tables

#### 3.2 Get Table
```http
GET /api/v1/datasets/{dataset_id}/tables/{table_id}
```

Returns table details including schema.

**Path Parameters:**
- `dataset_id` (string, required) - Dataset ID
- `table_id` (string, required) - Table ID

**Response:**
```json
{
  "table_id": "users",
  "dataset_id": "analytics",
  "project": "my-project",
  "table_type": "TABLE",
  "num_rows": 1000000,
  "num_bytes": 50000000,
  "created_at": "2024-01-01T00:00:00Z",
  "modified_at": "2024-01-15T10:30:00Z",
  "full_table_id": "my-project.analytics.users",
  "schema": [
    {
      "name": "user_id",
      "type": "INTEGER",
      "mode": "REQUIRED"
    },
    {
      "name": "email",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "metadata",
      "type": "STRUCT",
      "mode": "REPEATED"
    }
  ]
}
```

**Error Responses:**
- `404 Not Found` - Table not found
- `500 Internal Server Error` - Failed to get table

---

### 4. Query

#### 4.1 Execute Query
```http
POST /api/v1/query
```

Executes a direct SQL query.

**Request Body:**
```json
{
  "sql": "SELECT * FROM `project.dataset.table` LIMIT 10",
  "project_id": "my-project",
  "dry_run": false,
  "timeout_ms": 60000,
  "use_query_cache": true,
  "use_legacy_sql": false
}
```

**Parameters:**
- `sql` (string, required) - SQL query to execute
- `project_id` (string, optional) - Override project ID
- `dry_run` (boolean, default: false) - Validate without executing
- `timeout_ms` (integer, default: 60000, range: 1000-300000) - Query timeout in milliseconds
- `use_query_cache` (boolean, default: true) - Use cached results
- `use_legacy_sql` (boolean, default: false) - Use legacy SQL syntax

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "user_id": 1,
      "email": "user@example.com",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "metadata": {
    "job_id": "job-abc123xyz",
    "total_rows_processed": 1000,
    "total_bytes_processed": 1024000,
    "bytes_billed": 10240000,
    "cache_hit": false,
    "execution_time_ms": 1250,
    "slot_time_ms": 5000
  },
  "row_count": 1,
  "columns": ["user_id", "email", "created_at"]
}
```

**Error Responses:**
- `400 Bad Request` - SQL syntax error
- `404 Not Found` - Table not found
- `429 Too Many Requests` - Quota exceeded
- `500 Internal Server Error` - Query execution failed

---

## Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `BQ_LIST_DATASETS_ERROR` | Failed to list datasets | 500 |
| `BQ_DATASET_NOT_FOUND` | Dataset not found | 404 |
| `BQ_LIST_TABLES_ERROR` | Failed to list tables | 500 |
| `BQ_TABLE_NOT_FOUND` | Table not found | 404 |
| `BQ_GET_TABLE_ERROR` | Failed to get table details | 500 |
| `BQ_QUERY_ERROR` | Query execution failed | 500 |
| `BQ_SYNTAX_ERROR` | SQL syntax error | 400 |
| `BQ_QUOTA_EXCEEDED` | BigQuery quota exceeded | 429 |
| `INTERNAL_SERVER_ERROR` | Unexpected error | 500 |

---

## Rate Limiting

**Phase 1**: No rate limiting

**Phase 2**: Rate limiting will be implemented

---

## Examples

### Example 1: List all datasets
```bash
curl http://localhost:8000/api/v1/datasets
```

### Example 2: Get table schema
```bash
curl http://localhost:8000/api/v1/datasets/analytics/tables/users
```

### Example 3: Execute query
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT COUNT(*) as total FROM `project.dataset.table`"
  }'
```

### Example 4: Dry run query validation
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM `project.dataset.table` LIMIT 1000",
    "dry_run": true
  }'
```

---

## Best Practices

1. **Use dry_run first** - Validate queries before executing
2. **Set appropriate timeouts** - Default is 60 seconds
3. **Use query cache** - Enable for repeated queries
4. **Limit results** - Use LIMIT clause to reduce costs
5. **Monitor bytes processed** - Check response metadata for usage

---

## Data Types

BigQuery data types are converted to JSON-compatible types:

| BigQuery Type | JSON Type |
|---------------|-----------|
| INTEGER | number |
| FLOAT | number |
| BOOLEAN | boolean |
| STRING | string |
| TIMESTAMP | string (ISO 8601) |
| DATE | string (ISO 8601) |
| DATETIME | string (ISO 8601) |
| TIME | string (ISO 8601) |
| ARRAY | array |
| STRUCT | object |
| BYTES | string (base64) |

---

## Pagination

**Phase 1**: Results are returned in single response (no pagination)

**Phase 2**: Pagination will be implemented for large result sets
