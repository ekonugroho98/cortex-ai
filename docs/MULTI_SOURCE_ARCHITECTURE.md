# Multi-Source Investigation Platform - Architecture Design

## Vision

Transform this service from a BigQuery-only AI Agent into a comprehensive **Investigation Platform** that can query and analyze issues across multiple data sources:

- 🗄️ **Multiple Databases** (PostgreSQL, MySQL, MongoDB per squad)
- 📊 **BigQuery** (Analytics data warehouse)
- 🔍 **Elasticsearch** (Logs and indices)
- 📈 **APM** (Application Performance Monitoring - Datadog/NewRelic)
- ☸️ **Kubernetes** (Pod logs, events, metrics)

---

## Current Architecture (BigQuery Only)

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Client    │─────▶│  FastAPI Service │─────▶│  BigQuery API   │
│  (Web/Mob)  │      │   (Python)       │      │  (GCP)          │
└─────────────┘      └──────────────────┘      └─────────────────┘
                            │
                            │ (Subprocess)
                            ▼
                     ┌──────────────────┐
                     │  Claude Code CLI │
                     │  (Z.ai GLM-4.7)  │
                     └──────────────────┘
```

---

## Target Architecture (Multi-Source)

```
┌─────────────┐      ┌──────────────────────────────────┐
│   Client    │─────▶│   Investigation Orchestrator     │
│  (Web/Mob)  │      │   (FastAPI + Claude AI Agent)    │
└─────────────┘      └──────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────────┐
        │           Data Source Router                  │
        │  - Analyze query intent                       │
        │  - Route to appropriate source(s)             │
        │  - Aggregate results                          │
        └───────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┬──────────────┐
        │                   │                   │              │
        ▼                   ▼                   ▼              ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐  ┌──────────┐
│  BigQuery   │    │ Databases   │    │Elasticsearch│  │   APM    │
│  Service    │    │  Service    │    │   Service   │  │ Service  │
└─────────────┘    └─────────────┘    └─────────────┘  └──────────┘
        │                   │                   │              │
        ▼                   ▼                   ▼              ▼
   GCP BigQuery      Squad DBs          ELK Stack      Datadog/APM
                      (Postgres/MySQL)                  (NewRelic)
```

---

## Data Source Services Structure

### 1. Abstract Base Interface

```python
# app/services/data_sources/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class DataSourceInterface(ABC):
    """Abstract base class for all data sources"""

    source_type: str
    config_schema: Dict[str, Any]

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to data source"""
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test if connection is working"""
        pass

    @abstractmethod
    async def query(self, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query and return results"""
        pass

    @abstractmethod
    def get_schema(self, database: str = None) -> Dict[str, Any]:
        """Get schema/metadata from data source"""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return what this source can do"""
        pass
```

### 2. Data Source Registry

```python
# app/services/data_sources/registry.py
from typing import Dict, Type
from app.services.data_sources.base import DataSourceInterface

class DataSourceRegistry:
    """Registry for all available data sources"""

    _sources: Dict[str, Type[DataSourceInterface]] = {}

    @classmethod
    def register(cls, source_type: str, source_class: Type[DataSourceInterface]):
        """Register a new data source"""
        cls._sources[source_type] = source_class

    @classmethod
    def get_source(cls, source_type: str) -> Type[DataSourceInterface]:
        """Get data source class by type"""
        return cls._sources.get(source_type)

    @classmethod
    def list_sources(cls) -> List[str]:
        """List all registered source types"""
        return list(cls._sources.keys())
```

### 3. Concrete Implementations

#### BigQuery Service (Existing)
```python
# app/services/data_sources/bigquery_source.py
from app.services.data_sources.base import DataSourceInterface

class BigQuerySource(DataSourceInterface):
    source_type = "bigquery"

    def __init__(self, project_id: str, credentials_path: str):
        # Existing BigQuery implementation
        pass
```

#### PostgreSQL/MySQL Service
```python
# app/services/data_sources/database_source.py
import asyncpg
import aiomysql
from app.services.data_sources.base import DataSourceInterface

class DatabaseSource(DataSourceInterface):
    source_type = "database"  # postgresql, mysql

    def __init__(self, host: str, port: int, database: str,
                 username: str, password: str, db_type: str):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.db_type = db_type  # postgresql, mysql
        self.connection = None

    async def connect(self) -> bool:
        """Connect to PostgreSQL or MySQL"""
        if self.db_type == "postgresql":
            self.connection = await asyncpg.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password
            )
        elif self.db_type == "mysql":
            self.connection = await aiomysql.connect(
                host=self.host,
                port=self.port,
                db=self.database,
                user=self.username,
                password=self.password
            )
        return True

    async def query(self, query: str, params: Dict = None) -> Dict:
        """Execute SQL query"""
        results = await self.connection.fetch(query)
        return {
            "data": [dict(row) for row in results],
            "row_count": len(results)
        }

    def get_schema(self, database: str = None) -> Dict:
        """Get database schema"""
        # Query information_schema
        pass
```

#### Elasticsearch Service
```python
# app/services/data_sources/elasticsearch_source.py
from elasticsearch import AsyncElasticsearch
from app.services.data_sources.base import DataSourceInterface

class ElasticsearchSource(DataSourceInterface):
    source_type = "elasticsearch"

    def __init__(self, hosts: list, username: str, password: str):
        self.hosts = hosts
        self.username = username
        self.password = password
        self.client = None

    async def connect(self) -> bool:
        """Connect to Elasticsearch"""
        self.client = AsyncElasticsearch(
            hosts=self.hosts,
            basic_auth=(self.username, self.password)
        )
        return await self.client.ping()

    async def query(self, query: str, params: Dict = None) -> Dict:
        """Execute Elasticsearch query"""
        index = params.get("index", "*")
        query_dsl = params.get("query_dsl", {"match_all": {}})

        response = await self.client.search(
            index=index,
            body={"query": query_dsl},
            size=params.get("size", 100)
        )

        return {
            "data": [hit["_source"] for hit in response["hits"]["hits"]],
            "total": response["hits"]["total"]["value"],
            "took": response["took"]
        }

    def get_schema(self, index: str = None) -> Dict:
        """Get index mappings"""
        # Get mappings for indices
        pass
```

#### APM Service (Datadog/NewRelic)
```python
# app/services/data_sources/apm_source.py
import httpx
from app.services.data_sources.base import DataSourceInterface

class APMSource(DataSourceInterface):
    source_type = "apm"  # datadog, newrelic

    def __init__(self, provider: str, api_key: str, app_id: str):
        self.provider = provider
        self.api_key = api_key
        self.app_id = app_id
        self.base_url = {
            "datadog": "https://api.datadoghq.com/api/v1",
            "newrelic": "https://api.newrelic.com/v2"
        }

    async def query(self, query: str, params: Dict = None) -> Dict:
        """Query APM data"""
        if self.provider == "datadog":
            return await self._query_datadog(query, params)
        elif self.provider == "newrelic":
            return await self._query_newrelic(query, params)

    async def _query_datadog(self, query: str, params: Dict) -> Dict:
        """Query Datadog API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url['datadog']}/query",
                headers={"DD-API-KEY": self.api_key},
                params={
                    "query": query,
                    "from": params.get("from_ts"),
                    "to": params.get("to_ts")
                }
            )
            return response.json()
```

#### Kubernetes Service
```python
# app/services/data_sources/kubernetes_source.py
from kubernetes import client, config
from kubernetes_asyncio import client as async_client
from app.services.data_sources.base import DataSourceInterface

class KubernetesSource(DataSourceInterface):
    source_type = "kubernetes"

    def __init__(self, kubeconfig_path: str = None, context: str = None):
        self.kubeconfig_path = kubeconfig_path
        self.context = context
        self.core_api = None
        self.apps_api = None

    async def connect(self) -> bool:
        """Load kubernetes config"""
        await async_client.config.load_kube_config(
            config_file=self.kubeconfig_path,
            context=self.context
        )
        self.core_api = async_client.CoreV1Api()
        self.apps_api = async_client.AppsV1Api()
        return True

    async def query(self, query: str, params: Dict = None) -> Dict:
        """Execute kubernetes query"""
        query_type = params.get("type")  # pods, logs, events, deployments

        if query_type == "pods":
            return await self._get_pods(params)
        elif query_type == "logs":
            return await self._get_logs(params)
        elif query_type == "events":
            return await self._get_events(params)
        elif query_type == "deployments":
            return await self._get_deployments(params)

    async def _get_pods(self, params: Dict) -> Dict:
        """Get pods in namespace"""
        pods = await self.core_api.list_namespaced_pod(
            namespace=params.get("namespace", "default")
        )
        return {
            "data": [
                {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "created": pod.metadata.creation_timestamp
                }
                for pod in pods.items
            ]
        }

    async def _get_logs(self, params: Dict) -> Dict:
        """Get pod logs"""
        logs = await self.core_api.read_namespaced_pod_log(
            name=params["pod_name"],
            namespace=params["namespace"],
            tail_lines=params.get("tail_lines", 100)
        )
        return {"data": logs.split("\n")}
```

---

## Investigation Orchestrator

```python
# app/services/investigation_orchestrator.py
from typing import List, Dict, Any
from app.services.data_sources.registry import DataSourceRegistry

class InvestigationOrchestrator:
    """Main orchestrator for multi-source investigations"""

    def __init__(self, claude_cli_service):
        self.claude = claude_cli_service
        self.data_sources = {}
        self._init_data_sources()

    def _init_data_sources(self):
        """Initialize all configured data sources"""
        # Load from environment/config
        from app.config import settings

        # Initialize BigQuery
        if settings.GCP_PROJECT_ID:
            from app.services.data_sources.bigquery_source import BigQuerySource
            self.data_sources["bigquery"] = BigQuerySource(
                project_id=settings.GCP_PROJECT_ID,
                credentials_path=settings.GOOGLE_APPLICATION_CREDENTIALS
            )

        # Initialize Databases (squad databases)
        # Initialize Elasticsearch
        # Initialize APM
        # Initialize Kubernetes

    async def investigate(self, query: str, context: Dict = None) -> Dict:
        """
        Main investigation method

        1. Use Claude AI to understand query intent
        2. Determine which data sources to query
        3. Execute queries in parallel
        4. Aggregate and correlate results
        5. Return comprehensive answer
        """

        # Step 1: Analyze query with Claude
        analysis = await self._analyze_query(query)

        # Step 2: Plan investigation
        plan = await self._plan_investigation(analysis, context)

        # Step 3: Execute queries
        results = await self._execute_investigation_plan(plan)

        # Step 4: Synthesize results with Claude
        synthesis = await self._synthesize_results(query, results)

        return {
            "query": query,
            "analysis": analysis,
            "plan": plan,
            "raw_results": results,
            "synthesis": synthesis
        }

    async def _analyze_query(self, query: str) -> Dict:
        """Use Claude to understand what user is asking"""
        prompt = f"""
        Analyze this investigation query:
        "{query}"

        Determine:
        1. What type of issue is being investigated?
        2. Which data sources are relevant?
        3. What time range?
        4. What services/components are involved?

        Available data sources:
        - bigquery: Analytics data, metrics
        - database: Transactional data (PostgreSQL/MySQL per squad)
        - elasticsearch: Logs, errors, events
        - apm: Performance metrics, traces
        - kubernetes: Pod status, events, logs

        Return as JSON:
        {{
            "issue_type": "...",
            "relevant_sources": ["...", "..."],
            "time_range": {{"start": "...", "end": "..."}},
            "services": ["...", "..."],
            "keywords": ["...", "..."]
        }}
        """

        result = await self.claude.execute_prompt(
            prompt=prompt,
            bigquery_context={},
            timeout=60
        )

        return result["parsed_content"]

    async def _plan_investigation(self, analysis: Dict, context: Dict) -> List[Dict]:
        """Create investigation plan with queries for each source"""
        plan = []

        for source in analysis["relevant_sources"]:
            if source in self.data_sources:
                # Generate source-specific query
                query_plan = await self._generate_source_query(
                    source, analysis, context
                )
                plan.append(query_plan)

        return plan

    async def _execute_investigation_plan(self, plan: List[Dict]) -> Dict:
        """Execute all queries in parallel"""
        import asyncio

        tasks = []
        for plan_item in plan:
            source = self.data_sources[plan_item["source"]]
            task = source.query(plan_item["query"], plan_item.get("params"))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            plan[i]["source"]: results[i]
            for i in range(len(plan))
        }

    async def _synthesize_results(self, query: str, results: Dict) -> Dict:
        """Use Claude to synthesize results from all sources"""
        prompt = f"""
        Original query: "{query}"

        Results from multiple data sources:
        {json.dumps(results, indent=2)}

        Synthesize these results into a comprehensive investigation report.
        Highlight:
        1. Root cause analysis
        2. Timeline of events
        3. Affected components/services
        4. Recommended actions
        5. Related issues or patterns
        """

        result = await self.claude.execute_prompt(
            prompt=prompt,
            bigquery_context={},
            timeout=120
        )

        return result["parsed_content"]
```

---

## API Endpoints

### Current (BigQuery Only)
```python
POST /api/v1/query-agent
{
  "prompt": "Show me top 10 users by revenue",
  "dataset_id": "analytics",
  "dry_run": false
}
```

### Future (Multi-Source Investigation)
```python
POST /api/v1/investigate
{
  "query": "Why is payment service slow in production?",
  "context": {
    "environment": "production",
    "time_range": {
      "start": "2026-01-15T10:00:00Z",
      "end": "2026-01-15T11:00:00Z"
    },
    "services": ["payment-service", "checkout-api"]
  },
  "sources": ["elasticsearch", "apm", "kubernetes", "database"]
}
```

Response:
```json
{
  "query": "Why is payment service slow in production?",
  "analysis": {
    "issue_type": "performance_degradation",
    "relevant_sources": ["elasticsearch", "apm", "kubernetes", "database"]
  },
  "plan": [
    {
      "source": "elasticsearch",
      "query": "ERROR logs from payment-service",
      "params": {"index": "logs-production-*", "time_range": "1h"}
    },
    {
      "source": "apm",
      "query": "trace duration > 5s from payment-service",
      "params": {"service": "payment-service"}
    },
    {
      "source": "kubernetes",
      "query": "pod restarts in payment namespace",
      "params": {"namespace": "payment"}
    },
    {
      "source": "database",
      "query": "slow queries from payment transactions",
      "params": {"database": "squad_payment_prod"}
    }
  ],
  "raw_results": {
    "elasticsearch": {...},
    "apm": {...},
    "kubernetes": {...},
    "database": {...}
  },
  "synthesis": {
    "root_cause": "Database connection pool exhaustion in payment-service",
    "timeline": "Started at 10:23 UTC when traffic increased 300%",
    "affected_components": ["payment-service-pod-1", "payment-service-pod-2"],
    "recommended_actions": [
      "Increase database connection pool size",
      "Add circuit breaker for payment database",
      "Scale payment-service to 4 pods"
    ],
    "related_issues": "Similar issue occurred on 2026-01-10"
  }
}
```

---

## Configuration Structure

```yaml
# config/sources.yaml
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
      metrics: "metrics-*"

  apm:
    datadog:
      enabled: true
      api_key: ${DATADOG_API_KEY}
      app_id: payment-service,checkout-api
    newrelic:
      enabled: false

  kubernetes:
    enabled: true
    kubeconfig_path: ~/.kube/config
    contexts:
      - production
      - staging
```

---

## Implementation Roadmap

### Phase 1: Foundation (Current) ✅
- BigQuery integration
- Claude AI Agent for natural language to SQL
- Basic API endpoints

### Phase 2: Multi-Source Support (Next)
- Abstract DataSource interface
- Data source registry
- Database connector (PostgreSQL, MySQL)
- Elasticsearch connector
- Investigation orchestrator

### Phase 3: APM & Kubernetes
- Datadog/NewRelic integration
- Kubernetes API integration
- Pod logs, events, metrics

### Phase 4: Advanced Features
- Correlation engine
- Anomaly detection
- Alert integration
- Dashboard integration
- Historical analysis

### Phase 5: Enterprise Features
- Multi-tenant support
- RBAC (Role-Based Access Control)
- Audit logging
- Rate limiting per squad
- Cost optimization

---

## Squad Database Support

```python
# Squad-specific database routing
squad_databases = {
    "payment": {
        "host": "postgres-payment.squad-payment.svc",
        "database": "payment_db"
    },
    "user": {
        "host": "mysql-user.squad-user.svc",
        "database": "user_db"
    },
    "inventory": {
        "host": "postgres-inventory.squad-inventory.svc",
        "database": "inventory_db"
    }
}

# Auto-route based on query
query = "Show me recent payment failures"
# Automatically routes to squad_payment database

query = "Check user registrations today"
# Automatically routes to squad_user database
```

---

## Benefits

1. **Unified Investigation Interface**: One platform for all debugging needs
2. **AI-Powered**: Claude AI understands context and correlates data
3. **Faster MTTR**: Reduce mean time to resolution
4. **Squad Autonomy**: Each squad can connect their own databases
5. **Scalable**: Easy to add new data sources
6. **Cost Efficient**: Query only what's needed, use AI to optimize

---

## Next Steps

1. Review and approve this architecture
2. Set up configuration for squad databases
3. Implement DataSource interface
4. Add PostgreSQL connector
5. Add Elasticsearch connector
6. Test with real investigation scenarios
7. Gradual rollout to squads

---

**Status**: 🚧 Under Development
**Target**: Production-ready by Q2 2026
