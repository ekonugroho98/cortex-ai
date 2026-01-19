# Interface Protocols Documentation

## Overview

CortexAI uses Python's `Protocol` type to define service interfaces. This provides better testability, flexibility, and type safety compared to traditional inheritance.

## What are Protocols?

Protocols are a way to define structural subtyping in Python (similar to Go's interfaces or Java's interfaces but more flexible). A class is considered to implement a protocol if it has all the required methods and properties, regardless of inheritance.

## Benefits

1. **Easy Mocking**: Create mock implementations without inheritance
2. **Multiple Implementations**: Support different backends (real, mock, cache, etc.)
3. **Type Safety**: Catch errors at development time with mypy/pyright
4. **Loose Coupling**: Depend on abstractions, not concretions
5. **Better Documentation**: Interfaces serve as documentation

## Available Protocols

### 1. BigQueryServiceProtocol

Defines interface for BigQuery operations:

```python
from app.interfaces import BigQueryServiceProtocol

def process_datasets(service: BigQueryServiceProtocol):
    datasets = service.list_datasets()
    # ... process datasets
```

**Methods**:
- `test_connection() -> bool`
- `list_datasets() -> List[Dict[str, Any]]`
- `get_dataset(dataset_id: str) -> Dict[str, Any]`
- `list_tables(dataset_id: str) -> List[Dict[str, Any]]`
- `get_table(dataset_id: str, table_id: str) -> Dict[str, Any]`
- `execute_query(sql: str, ...) -> Dict[str, Any]`
- Async versions of all above methods

**Properties**:
- `project_id: str`
- `client: Any`

### 2. ClaudeCLIServiceProtocol

Defines interface for Claude CLI operations:

```python
from app.interfaces import ClaudeCLIServiceProtocol

async def generate_sql(service: ClaudeCLIServiceProtocol, prompt: str):
    result = await service.execute_prompt(prompt, {...})
    return result["parsed_content"]["sql_query"]
```

**Methods**:
- `execute_prompt(prompt, bigquery_context, timeout) -> Dict[str, Any]`

**Properties**:
- `workspace: str`
- `is_available: bool`

## Usage Examples

### 1. Using Protocols in FastAPI Endpoints

```python
from app.interfaces import BigQueryServiceProtocol
from app.dependencies import get_bigquery_service_async

@router.get("/datasets")
async def list_datasets(
    bq: BigQueryServiceProtocol = Depends(get_bigquery_service_async)
):
    # bq can be any implementation (real, mock, cached, etc.)
    datasets = await bq.list_datasets_async()
    return {"datasets": datasets}
```

### 2. Creating Mock Implementations

```python
from app.interfaces import BigQueryServiceProtocol

class MyMockBigQueryService:
    """No inheritance needed! Just implement the methods."""

    def list_datasets(self):
        return [{"dataset_id": "mock"}]

    # ... implement other required methods

    async def list_datasets_async(self):
        return self.list_datasets()

    @property
    def project_id(self):
        return "mock-project"

# Use it
service: BigQueryServiceProtocol = MyMockBigQueryService()
datasets = service.list_datasets()
```

### 3. Using Pre-built Mocks

```python
from tests.mocks import MockBigQueryService
from app.interfaces import BigQueryServiceProtocol

# Create mock
mock_bq: BigQueryServiceProtocol = MockBigQueryService()

# Add test data
mock_bq.add_dataset("test_dataset")
mock_bq.add_table("test_dataset", "users", num_rows=1000)

# Use in tests
datasets = mock_bq.list_datasets()
assert len(datasets) == 1
```

### 4. Writing Protocol-Based Tests

```python
import pytest
from app.interfaces import BigQueryServiceProtocol

@pytest.mark.asyncio
async def test_dataset_listing():
    # This test works with ANY implementation
    service: BigQueryServiceProtocol = MockBigQueryService()

    datasets = await service.list_datasets_async()
    assert isinstance(datasets, list)
    assert all("dataset_id" in d for d in datasets)
```

### 5. Multiple Implementations

```python
from app.interfaces import BigQueryServiceProtocol

class RealBigQueryService:
    """Real implementation using Google Cloud"""
    # ... implementation

class CachedBigQueryService:
    """Cached implementation wrapping real service"""
    def __init__(self, real_service: BigQueryServiceProtocol):
        self._real = real_service
        self._cache = {}

    def list_datasets(self):
        if "datasets" not in self._cache:
            self._cache["datasets"] = self._real.list_datasets()
        return self._cache["datasets"]

# Use cached version
real = RealBigQueryService()
cached: BigQueryServiceProtocol = CachedBigQueryService(real)
```

## Type Checking

Protocols work seamlessly with type checkers:

```bash
# Install mypy
pip install mypy

# Run type checker
mypy app/

# Or with pyright
npm install -g pyright
pyright app/
```

Example error detection:

```python
from app.interfaces import BigQueryServiceProtocol

class BadService:
    pass  # Missing required methods!

# Type checker will complain:
service: BigQueryServiceProtocol = BadService()  # ERROR!
```

## Migration from Concrete Types

When updating existing code to use protocols:

**Before**:
```python
from app.services.bigquery_service import BigQueryService

def my_function(service: BigQueryService):
    return service.list_datasets()
```

**After**:
```python
from app.interfaces import BigQueryServiceProtocol

def my_function(service: BigQueryServiceProtocol):
    return service.list_datasets()
```

This change is backward compatible - existing BigQueryService still works!

## Best Practices

1. **Always use Protocol types in function signatures**, not concrete classes
2. **Use pre-built mocks** from `tests.mocks` when writing tests
3. **Implement Protocol directly** without inheritance when creating custom mocks
4. **Add type hints** to all methods when implementing protocols
5. **Run type checker** (`mypy` or `pyright`) to catch protocol violations
6. **Document protocol conformance** in custom implementations

## Testing with Protocols

```python
# tests/test_my_feature.py
import pytest
from app.interfaces import BigQueryServiceProtocol
from tests.mocks import MockBigQueryService

@pytest.fixture
def mock_bq() -> BigQueryServiceProtocol:
    """Return mock BigQuery service"""
    service = MockBigQueryService()
    service.add_dataset("test")
    service.add_table("test", "users")
    return service

@pytest.mark.asyncio
async def test_my_feature(mock_bq: BigQueryServiceProtocol):
    # Test works with any implementation
    datasets = await mock_bq.list_datasets_async()
    assert len(datasets) > 0
```

## Additional Resources

- [PEP 544 - Protocols](https://www.python.org/dev/peps/pep-0544/)
- [typing.Protocol Documentation](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [Protocol vs ABC](https://mypy.readthedocs.io/en/stable/protocols.html)
