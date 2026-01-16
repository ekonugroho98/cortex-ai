# BigQuery AI Service - CURL Commands Reference

Dokumentasi lengkap curl commands untuk BigQuery AI Service API.

## Base URL
```
http://localhost:8001
```

## API Endpoints

---

## 1. Health Check & Service Info

### 1.1 Service Information
```bash
curl http://localhost:8001/
```

**Response:**
```json
{
  "service": "BigQuery AI Service",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

### 1.2 Health Check
```bash
curl http://localhost:8001/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "bigquery_connected": true,
  "project_id": "gen-lang-client-0716506049",
  "timestamp": "2026-01-15T18:40:58.096099"
}
```

---

## 2. Datasets API

### 2.1 List All Datasets
```bash
curl http://localhost:8001/api/v1/datasets
```

**Response:**
```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "dataset_id": "falcon_bigquery",
      "project": "gen-lang-client-0716506049",
      "location": "US",
      "tables_count": 17,
      "created_at": "2026-01-15T08:38:14.664000+00:00",
      "modified_at": "2026-01-15T08:38:14.664000+00:00"
    }
  ]
}
```

### 2.2 Get Dataset Details
```bash
curl http://localhost:8001/api/v1/datasets/falcon_bigquery
```

---

## 3. Tables API

### 3.1 List All Tables in Dataset
```bash
curl http://localhost:8001/api/v1/datasets/falcon_bigquery/tables
```

**Response:**
```json
{
  "status": "success",
  "dataset_id": "falcon_bigquery",
  "count": 17,
  "data": [
    {
      "table_id": "appstore_ratings",
      "dataset_id": "falcon_bigquery",
      "project": "gen-lang-client-0716506049",
      "table_type": "TABLE",
      "num_rows": 60,
      "num_bytes": 4860,
      "created_at": "2026-01-15T11:28:46.749000+00:00",
      "modified_at": "2026-01-15T11:28:46.749000+00:00",
      "full_table_id": "gen-lang-client-0716506049.falcon_bigquery.appstore_ratings"
    }
  ]
}
```

### 3.2 Get Table Schema (Basic Info)
```bash
curl http://localhost:8001/api/v1/datasets/falcon_bigquery/tables/appstore_ratings
```

---

## 4. Direct SQL Query API

### 4.1 Execute Direct SQL Query
```bash
curl -X POST http://localhost:8001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM `gen-lang-client-0716506049.falcon_bigquery.appstore_ratings` LIMIT 10",
    "dry_run": false
  }'
```

### 4.2 Dry Run Query (Validate Only)
```bash
curl -X POST http://localhost:8001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT COUNT(*) FROM `gen-lang-client-0716506049.falcon_bigquery.appstore_ratings`",
    "dry_run": true
  }'
```

---

## 5. Claude AI Agent API ⭐

### 5.1 Basic Natural Language Query
```bash
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show me top 10 app ratings",
    "dataset_id": "falcon_bigquery",
    "dry_run": false
  }'
```

### 5.2 Dry Run (Generate SQL Only)
```bash
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Count total records in appstore_ratings",
    "dataset_id": "falcon_bigquery",
    "dry_run": true
  }'
```

### 5.3 Query with Custom Timeout
```bash
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show me all data from the largest table",
    "dataset_id": "falcon_bigquery",
    "timeout": 600,
    "dry_run": false
  }'
```

### 5.4 Get Table Schema via Agent
```bash
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show me the complete schema of appstore_ratings table including all columns and data types",
    "dataset_id": "falcon_bigquery",
    "dry_run": false
  }'
```

### 5.5 Get All Tables Schema in Dataset
```bash
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show me schema of all tables in falcon_bigquery dataset",
    "dataset_id": "falcon_bigquery",
    "dry_run": false
  }'
```

### 5.6 Aggregation Query
```bash
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Count records grouped by rating",
    "dataset_id": "falcon_bigquery",
    "dry_run": false
  }'
```

### 5.7 Query with Project ID
```bash
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "List all datasets",
    "project_id": "gen-lang-client-0716506049",
    "dry_run": false
  }'
```

---

## Request Parameters Reference

### AgentRequest Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `prompt` | string | Yes | Natural language prompt | "Show me top 10 users" |
| `dataset_id` | string | No | Dataset ID to focus on | "falcon_bigquery" |
| `project_id` | string | No | GCP Project ID | "gen-lang-client-0716506049" |
| `dry_run` | boolean | No | Generate SQL without executing | false |
| `timeout` | integer | No | Agent timeout in seconds (10-600) | 300 |

---

## Response Format

### Success Response (Agent)
```json
{
  "status": "success",
  "prompt": "Show me top 10 app ratings",
  "generated_sql": "SELECT app_name, rating FROM ...",
  "execution_result": {
    "metadata": {
      "job_id": "ca492049-31b1-44ce-abd2-c4b03ce78ac6",
      "total_rows_processed": 2,
      "total_bytes_processed": 2220,
      "bytes_billed": 10485760,
      "cache_hit": false,
      "execution_time_ms": 1200,
      "slot_time_ms": 30
    },
    "data": [
      {
        "app_name": "mybb",
        "rating": 4.5
      }
    ],
    "row_count": 10,
    "columns": ["app_name", "rating"]
  },
  "agent_metadata": {
    "model": "glm-4.7",
    "method": "claude-code-cli",
    "workspace": "claude-workspace/bigquery_context",
    "raw_output_length": 190
  },
  "reasoning": "Explanation from Claude AI..."
}
```

### Error Response
```json
{
  "detail": {
    "error_code": "AGENT_ERROR",
    "message": "Agent request failed",
    "details": {
      "error": "Error details here"
    }
  }
}
```

---

## Tips & Best Practices

### 1. Use `dry_run: true` for Testing
```bash
# Test query without executing
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Your prompt here",
    "dataset_id": "falcon_bigquery",
    "dry_run": true
  }'
```

### 2. Adjust Timeout for Complex Queries
```bash
# Increase timeout for heavy queries
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Complex analytical query",
    "dataset_id": "falcon_bigquery",
    "timeout": 600,
    "dry_run": false
  }'
```

### 3. Check Schema Before Querying
```bash
# Get table schema first
curl http://localhost:8001/api/v1/datasets/falcon_bigquery/tables

# Or use agent to get detailed schema
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show me schema of TABLE_NAME",
    "dataset_id": "falcon_bigquery",
    "dry_run": false
  }'
```

### 4. Pretty Print JSON Response
```bash
# Use python3 or jq for pretty output
curl -s http://localhost:8001/api/v1/datasets | python3 -m json.tool
curl -s http://localhost:8001/api/v1/datasets | jq
```

---

## Common Use Cases

### 1. Quick Data Exploration
```bash
# List all datasets
curl http://localhost:8001/api/v1/datasets

# List tables in dataset
curl http://localhost:8001/api/v1/datasets/falcon_bigquery/tables

# Get sample data
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show me 10 sample records",
    "dataset_id": "falcon_bigquery",
    "dry_run": false
  }'
```

### 2. Data Analysis
```bash
# Aggregation queries
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Count records grouped by category",
    "dataset_id": "falcon_bigquery",
    "dry_run": false
  }'
```

### 4. Schema Discovery
```bash
# Get complete table schema
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show me the complete schema of TABLE_NAME",
    "dataset_id": "falcon_bigquery",
    "dry_run": false
  }'
```

---

## Available Tables in falcon_bigquery Dataset

Based on the current dataset, the following tables are available:

- `appstore_ratings` - App ratings and reviews data
- `availability` - Vehicle availability data
- `bluebird_knowledge` - Knowledge base Q&A
- `complaints` - Customer complaints
- `driver_policies` - Policy information
- ... and 12 more tables

---

## Error Handling

### Common Errors and Solutions

#### 1. BigQuery Connection Error
```json
{
  "detail": "BigQuery connection failed"
}
```
**Solution:** Check credentials and BigQuery API access

#### 2. No SQL Generated
```json
{
  "detail": {
    "error_code": "CLAUDE_NO_SQL",
    "message": "Claude AI did not generate a SQL query"
  }
}
```
**Solution:** Refine your prompt or check if the table/columns exist

#### 3. Invalid Query
```json
{
  "detail": {
    "error_code": "AGENT_ERROR",
    "message": "Agent request failed",
    "details": {
      "error": "400 Unrecognized name: column_name"
    }
  }
}
```
**Solution:** Check column names in the schema, use `keys` parameter to specify correct columns

---

## Interactive API Documentation

For interactive API documentation with Swagger UI:
```
http://localhost:8001/docs
```

For ReDoc documentation:
```
http://localhost:8001/redoc
```

---

## Support

For issues and questions:
- Check API documentation at `/docs`
- Review error messages in response
- Verify dataset_id and table names
- Use `dry_run: true` to test queries before execution

---

**Last Updated:** January 15, 2026
**API Version:** v1
**Service Version:** 1.0.0
