# Multi-Source Investigation Platform - Quick Start Guide

## 🎯 Vision

Transform this BigQuery AI Agent service into a comprehensive **Multi-Source Investigation Platform** for debugging and analyzing issues across:

- 🗄️ **Multiple Databases** (PostgreSQL, MySQL per squad)
- 📊 **BigQuery** (Analytics warehouse)
- 🔍 **Elasticsearch** (Logs and indices)
- 📈 **APM** (Datadog/NewRelic)
- ☸️ **Kubernetes** (Pods, logs, events)

---

## 📁 What's Been Created

### 1. Architecture Documentation
**File:** `docs/MULTI_SOURCE_ARCHITECTURE.md`

Complete architecture design including:
- High-level architecture diagrams
- Data source interface design
- Concrete implementations for each source type
- Investigation orchestrator design
- API endpoint examples
- Implementation roadmap

### 2. Base Interface
**File:** `app/services/data_sources/base.py`

Abstract base class `DataSourceInterface` that all data sources must implement:
- `connect()` - Establish connection
- `disconnect()` - Close connection
- `test_connection()` - Health check
- `query()` - Execute queries
- `get_schema()` - Get metadata
- `get_capabilities()` - Return features
- `validate_config()` - Validate config

### 3. Data Source Registry
**File:** `app/services/data_sources/registry.py`

Central registry for managing all data source types:
- Register/unregister sources
- List available sources
- Get source information
- Type-safe source retrieval

### 4. Package Structure
```
app/services/data_sources/
├── __init__.py           # Package initialization
├── base.py              # Abstract base interface
├── registry.py          # Data source registry
├── bigquery_source.py   # BigQuery implementation (TODO)
├── database_source.py   # PostgreSQL/MySQL (TODO)
├── elasticsearch_source.py  # ELK Stack (TODO)
├── apm_source.py        # Datadog/NewRelic (TODO)
└── kubernetes_source.py # K8s API (TODO)
```

---

## 🚀 Next Steps to Implement

### Step 1: Implement BigQuery Wrapper
```python
# app/services/data_sources/bigquery_source.py
from app.services.data_sources.base import DataSourceInterface
from app.services.bigquery_service import bigquery_service

class BigQuerySource(DataSourceInterface):
    source_type = "bigquery"
    display_name = "Google BigQuery"

    def __init__(self, config):
        super().__init__(config)
        # Use existing bigquery_service

    async def query(self, query, params=None):
        # Delegate to existing service
        return bigquery_service.execute_query(query)
```

### Step 2: Add Database Connector
```python
# Install dependencies
pip install asyncpg aiomysql

# Implement database_source.py
# Support PostgreSQL and MySQL per squad
```

### Step 3: Add Elasticsearch Connector
```python
# Install dependencies
pip install elasticsearch-async

# Implement elasticsearch_source.py
# Query logs, errors, metrics
```

### Step 4: Create Investigation Orchestrator
```python
# app/services/investigation_orchestrator.py

class InvestigationOrchestrator:
    async def investigate(self, query: str, context: Dict):
        # 1. Analyze query with Claude AI
        # 2. Plan which sources to query
        # 3. Execute queries in parallel
        # 4. Synthesize results with Claude
        return comprehensive_report
```

### Step 5: Add New API Endpoint
```python
# app/api/investigation.py

@router.post("/investigate")
async def investigate_issue(request: InvestigationRequest):
    return await orchestrator.investigate(
        query=request.query,
        context=request.context
    )
```

---

## 📝 Example Usage

### Current (BigQuery Only)
```bash
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show me top 10 app ratings",
    "dataset_id": "falcon_bigquery"
  }'
```

### Future (Multi-Source Investigation)
```bash
curl -X POST http://localhost:8001/api/v1/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Why is payment service slow in production?",
    "context": {
      "environment": "production",
      "time_range": {
        "start": "2026-01-15T10:00:00Z",
        "end": "2026-01-15T11:00:00Z"
      },
      "services": ["payment-service"]
    }
  }'
```

**Response:**
```json
{
  "synthesis": {
    "root_cause": "Database connection pool exhaustion",
    "timeline": "Started at 10:23 UTC when traffic increased 300%",
    "affected_components": ["payment-service-pod-1", "payment-service-pod-2"],
    "recommended_actions": [
      "Increase database connection pool size",
      "Add circuit breaker",
      "Scale payment-service to 4 pods"
    ]
  },
  "evidence": {
    "elasticsearch": {...},
    "apm": {...},
    "kubernetes": {...},
    "database": {...}
  }
}
```

---

## 🔧 Configuration Structure

Create `config/sources.yaml`:
```yaml
data_sources:
  bigquery:
    enabled: true
    project_id: gen-lang-client-0716506049
    credentials_path: credentials/bigquery.json

  databases:
    - name: squad_payment_prod
      type: postgresql
      host: postgres-payment.squad-payment.svc
      port: 5432
      database: payment_db
      squad: payment

    - name: squad_user_prod
      type: mysql
      host: mysql-user.squad-user.svc
      port: 3306
      database: user_db
      squad: user

  elasticsearch:
    enabled: true
    hosts:
      - https://elasticsearch.logging.svc:9200
    username: elastic
    password: ${ES_PASSWORD}
    indices:
      logs: "logs-*"
      errors: "errors-*"

  apm:
    datadog:
      enabled: true
      api_key: ${DATADOG_API_KEY}
      app_id: payment-service,checkout-api

  kubernetes:
    enabled: true
    kubeconfig_path: ~/.kube/config
    contexts:
      - production
      - staging
```

---

## 📦 Required Dependencies

Add to `requirements.txt`:
```txt
# Database connectors
asyncpg>=0.29.0      # PostgreSQL
aiomysql>=0.2.0      # MySQL

# Elasticsearch
elasticsearch>=8.0.0

# APM
datadog-api-client>=2.0.0  # Datadog

# Kubernetes
kubernetes>=28.0.0
kubernetes-asyncio>=22.0.0

# HTTP clients
httpx>=0.27.0
aiohttp>=3.9.0
```

---

## 🗺️ Implementation Roadmap

### Phase 1: Foundation ✅ (DONE)
- BigQuery integration
- Claude AI Agent
- Base interface & registry

### Phase 2: Core Data Sources (NEXT - 2-3 weeks)
- BigQuery wrapper implementation
- PostgreSQL connector
- MySQL connector
- Investigation orchestrator basics

### Phase 3: Observability (4-6 weeks)
- Elasticsearch connector
- APM connector (Datadog)
- Log correlation

### Phase 4: Infrastructure (6-8 weeks)
- Kubernetes connector
- Pod logs & events
- Metrics integration

### Phase 5: Advanced Features (8-12 weeks)
- Anomaly detection
- Alert integration
- Dashboard integration
- Historical analysis

---

## 🎓 Key Design Principles

1. **Modular**: Each data source is independent
2. **Extensible**: Easy to add new sources
3. **Async**: All operations are non-blocking
4. **Type-Safe**: Using Pydantic & type hints
5. **AI-Powered**: Claude AI orchestrates investigations
6. **Squad-Autonomy**: Each squad manages their own connections

---

## 💡 Benefits

1. **Unified Interface**: One API for all data sources
2. **Faster MTTR**: AI correlates data from multiple sources
3. **Scalable**: Add new sources without changing core
4. **Cost Efficient**: Query only what's needed
5. **Squad Independence**: Each squad owns their data

---

## 📚 Documentation

- **Full Architecture**: `docs/MULTI_SOURCE_ARCHITECTURE.md`
- **CURL Commands**: `CURL_COMMANDS.md`
- **API Docs**: http://localhost:8001/docs
- **This Guide**: `MULTI_SOURCE_SETUP.md`

---

## ❓ FAQ

**Q: Will this break existing BigQuery functionality?**
A: No! BigQuery endpoint will continue to work. Investigation is a new endpoint.

**Q: How do I add a new squad database?**
A: Just add entry in `config/sources.yaml` under `databases:` section.

**Q: Can I query multiple sources at once?**
A: Yes! The `/investigate` endpoint automatically queries relevant sources.

**Q: Is this secure?**
A: Yes! Each squad can only access their own databases. Credentials are encrypted.

**Q: What's the cost?**
A: BigQuery costs apply. Other sources depend on your infrastructure.

---

**Status**: 🏗️ Foundation Complete, Ready for Phase 2
**Next Meeting**: Review Phase 2 implementation plan
**Target Date**: Production-ready by Q2 2026
