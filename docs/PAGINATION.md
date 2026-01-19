# Pagination Documentation

## Overview

All list endpoints in CortexAI support pagination to prevent memory issues and improve response times when dealing with large datasets.

## Pagination Parameters

All paginated endpoints accept these query parameters:

| Parameter | Type | Default | Limits | Description |
|-----------|------|---------|--------|-------------|
| `page` | integer | 1 | ≥ 1 | Page number (1-indexed) |
| `page_size` | integer | 50 | 1-1000 | Number of items per page |

## Response Format

Paginated endpoints return a standardized response format:

```json
{
  "data": [
    { /* item 1 */ },
    { /* item 2 */ },
    ...
  ],
  "pagination": {
    "page": 2,
    "page_size": 50,
    "total": 150,
    "total_pages": 3,
    "has_next": true,
    "has_prev": true
  }
}
```

### Pagination Metadata

| Field | Type | Description |
|-------|------|-------------|
| `page` | integer | Current page number |
| `page_size` | integer | Items per page |
| `total` | integer | Total number of items across all pages |
| `total_pages` | integer | Total number of pages |
| `has_next` | boolean | Whether there's a next page |
| `has_prev` | boolean | Whether there's a previous page |

## Usage Examples

### Basic Pagination

```bash
# Get first page (default: page=1, page_size=50)
curl -H "X-API-Key: your-key" \
  https://api.example.com/datasets

# Get second page with 20 items per page
curl -H "X-API-Key: your-key" \
  "https://api.example.com/datasets?page=2&page_size=20"

# Get last page
curl -H "X-API-Key: your-key" \
  "https://api.example.com/datasets?page=10&page_size=10"
```

### Python Example

```python
import requests

headers = {"X-API-Key": "your-key"}
page = 1
page_size = 50

while True:
    params = {"page": page, "page_size": page_size}
    response = requests.get(
        "https://api.example.com/datasets",
        headers=headers,
        params=params
    )
    data = response.json()

    # Process items
    for item in data["data"]:
        process_item(item)

    # Check if there's a next page
    if not data["pagination"]["has_next"]:
        break

    page += 1
```

### JavaScript Example

```javascript
async function fetchAllDatasets() {
  let page = 1;
  const pageSize = 50;
  let allDatasets = [];

  while (true) {
    const response = await fetch(
      `https://api.example.com/datasets?page=${page}&page_size=${pageSize}`,
      {
        headers: { "X-API-Key": "your-key" }
      }
    );

    const data = await response.json();
    allDatasets.push(...data.data);

    if (!data.pagination.has_next) break;
    page++;
  }

  return allDatasets;
}
```

## Paginated Endpoints

### Datasets

**List all datasets:**

```
GET /datasets?page=1&page_size=50
```

Response: `PaginatedResponse[DatasetResponse]`

### Tables

**List all tables in a dataset:**

```
GET /datasets/{dataset_id}/tables?page=1&page_size=50
```

Response: `PaginatedResponse[TableResponse]`

## Best Practices

### 1. Choose Appropriate Page Size

- **Small page size (10-50)**: Better for UI rendering, slower for large exports
- **Medium page size (50-100)**: Good balance for most use cases
- **Large page size (100-1000)**: Best for bulk data processing

```bash
# Good for UI display
curl "/datasets?page_size=20"

# Good for bulk processing
curl "/datasets?page_size=500"
```

### 2. Handle Edge Cases

```python
# Handle empty results
response = api_call("/datasets?page=999")
if response["pagination"]["total"] == 0:
    print("No datasets found")

# Handle single page
if not response["pagination"]["has_next"] and response["pagination"]["page"] == 1:
    print("All results fit on first page")
```

### 3. Use has_next/has_prev for Navigation

```python
# Build pagination UI
def build_pagination_ui(response):
    pagination = response["pagination"]

    links = []
    if pagination["has_prev"]:
        links.append({"rel": "prev", "page": pagination["page"] - 1})

    links.append({"rel": "current", "page": pagination["page"]})

    if pagination["has_next"]:
        links.append({"rel": "next", "page": pagination["page"] + 1})

    return links
```

### 4. Cache Results Wisely

```python
import hashlib
import time

def fetch_with_cache(endpoint, params, cache_ttl=300):
    cache_key = hashlib.md5(f"{endpoint}{params}".encode()).hexdigest()

    # Check cache
    if is_cached(cache_key) and cache_age(cache_key) < cache_ttl:
        return get_from_cache(cache_key)

    # Fetch from API
    response = api_call(endpoint, params)

    # Cache only if it's a complete result (single page or last page)
    if not response["pagination"]["has_next"]:
        save_to_cache(cache_key, response)

    return response
```

## Performance Considerations

### Memory Usage

With pagination, memory usage is controlled:

```python
# Without pagination: Loads ALL datasets into memory
all_datasets = list_datasets()  # Could be 10,000+ items!

# With pagination: Only loads requested page
datasets = list_datasets(page=1, page_size=50)  # Only 50 items in memory
```

### Response Time

Larger page sizes increase response time:

```
page_size=50  → ~200ms
page_size=500 → ~800ms
page_size=1000 → ~1500ms
```

**Recommendation**: Start with default (50), increase only if needed.

## Error Handling

### Invalid Page Number

```bash
# Invalid: page must be >= 1
curl "/datasets?page=0"
# HTTP 422: Unprocessable Entity
```

### Invalid Page Size

```bash
# Invalid: page_size must be between 1 and 1000
curl "/datasets?page_size=2000"
# HTTP 422: Unprocessable Entity
```

### Page Beyond Available Data

```bash
# Valid request but returns empty data
curl "/datasets?page=999"
# HTTP 200: OK
# {
#   "data": [],
#   "pagination": {
#     "page": 999,
#     "total": 50,
#     "total_pages": 1,
#     "has_next": false,
#     "has_prev": false
#   }
# }
```

## Implementation Details

### Backend Utility Functions

The `paginate_list()` utility function handles pagination:

```python
from app.utils.common import paginate_list

items = [{"id": i} for i in range(1000)]
result = paginate_list(items, page=2, page_size=50)

# Returns:
# {
#   "data": items[50:100],
#   "pagination": {
#     "page": 2,
#     "page_size": 50,
#     "total": 1000,
#     "total_pages": 20,
#     "has_next": True,
#     "has_prev": True
#   }
# }
```

### Response Models

Type-safe Pydantic models ensure consistency:

```python
from app.models.bigquery import PaginatedResponse, DatasetResponse

@router.get("/datasets", response_model=PaginatedResponse[DatasetResponse])
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000)
):
    # ... implementation
    pass
```

## Migration Guide

### From Non-Paginated to Paginated

**Before (deprecated):**
```json
{
  "status": "success",
  "count": 150,
  "data": [...]
}
```

**After (current):**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 150,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

**Code Changes:**

```python
# Old code
response = api.get("/datasets")
datasets = response["data"]

# New code
response = api.get("/datasets?page=1&page_size=50")
datasets = response["data"]
total = response["pagination"]["total"]
```

## Testing

```bash
# Test pagination
curl -H "X-API-Key: test" \
  "http://localhost:8000/datasets?page=1&page_size=10" | jq

# Test with mock data
python -c "
from tests.mocks import MockBigQueryService
from app.utils.common import paginate_list

service = MockBigQueryService()
for i in range(100):
    service.add_dataset(f'dataset_{i}')

datasets = service.list_datasets()
result = paginate_list(datasets, page=2, page_size=10)
print(f'Page 2: {len(result[\"data\"])} items')
print(f'Total: {result[\"pagination\"][\"total\"]} items')
"
```

## Related Documentation

- [API Documentation](./API.md)
- [Rate Limiting](./RATE_LIMITING.md)
- [Error Handling](./ERRORS.md)
