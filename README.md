# CortexAI - Enterprise Intelligence Platform

**CortexAI** is an enterprise-grade AI platform for data-driven decision making and operational intelligence. It connects to multiple data sources and uses AI to investigate issues, analyze patterns, and provide actionable insights.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Ready-blue.svg)](https://cloud.google.com/run)

## 🎯 Overview

CortexAI serves as the central intelligence hub for enterprises, enabling:

- 📊 **Multi-Source Data Investigation** - Query and analyze data across databases, data warehouses, logs, and monitoring systems
- 🤖 **AI-Powered Analysis** - Claude AI orchestrates investigations and correlates data from multiple sources
- 🔍 **Issue Resolution** - Rapid root cause analysis for technical and business issues
- 📈 **Business Intelligence** - Data-driven insights for management decisions
- ⚡ **Operational Excellence** - Monitor and optimize enterprise operations
- ☁️ **Cloud Native** - Ready for deployment on GCP (Cloud Run, GKE)

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────┐
│                  CortexAI Platform                    │
│         (FastAPI + Claude AI Orchestrator)            │
└───────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┬──────────────┐
        │                   │                   │              │
        ▼                   ▼                   ▼              ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐  ┌──────────┐
│  BigQuery   │    │ Databases   │    │Elasticsearch│  │   APM    │
│  Service    │    │  Service    │    │   Service   │  │ Service  │
│ (Analytics) │    │ (Squad DBs) │    │   (Logs)    │  │(Metrics) │
└─────────────┘    └─────────────┘    └─────────────┘  └──────────┘
        │                   │                   │              │
        ▼                   ▼                   ▼              ▼
   GCP BigQuery      PostgreSQL/MySQL     ELK Stack      Datadog/
                      (per squad)                        NewRelic
```

## ✨ Key Features

### Phase 1: Foundation ✅
- **BigQuery Integration**
  - Natural language to SQL conversion
  - Dataset and table exploration
  - Direct SQL query execution
  - AI-powered query generation

### Phase 2: Multi-Source Support (Current)
- **Multiple Database Support**
  - PostgreSQL per squad
  - MySQL databases
  - Automatic schema discovery

- **Observability Integration**
  - Elasticsearch for logs and errors
  - APM integration (Datadog, NewRelic)
  - Kubernetes metrics and events

- **AI Investigation Orchestrator**
  - Cross-source correlation
  - Root cause analysis
  - Timeline reconstruction
  - Automated remediation recommendations

### Phase 3: Advanced Features (Planned)
- **Anomaly Detection**
- **Alert Integration**
- **Dashboard & Visualization**
- **Historical Analysis**
- **Predictive Insights**

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for Claude Code CLI)
- Google Cloud Project with BigQuery API enabled
- Claude Code CLI installed

### Installation

1. **Clone and setup:**
```bash
cd /path/to/cortex-ai
./scripts/setup.sh
```

2. **Install Claude Code CLI:**
```bash
npm install -g @anthropic-ai/claude-code
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the server:**
```bash
make dev
```

Access the API at **http://localhost:8000**
Interactive docs at **http://localhost:8000/docs**

## 📚 API Documentation

### Core Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### BigQuery AI Agent
```bash
curl -X POST http://localhost:8000/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show me top 10 users by revenue",
    "dataset_id": "analytics",
    "dry_run": false
  }'
```

#### Multi-Source Investigation (Coming Soon)
```bash
curl -X POST http://localhost:8000/api/v1/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Why is payment service slow in production?",
    "context": {
      "environment": "production",
      "time_range": {
        "start": "2026-01-15T10:00:00Z",
        "end": "2026-01-15T11:00:00Z"
      }
    }
  }'
```

See [CURL_COMMANDS.md](CURL_COMMANDS.md) for complete API reference.

## 🔧 Configuration

CortexAI uses a flexible configuration system to support multiple data sources:

```yaml
# config/sources.yaml
data_sources:
  bigquery:
    enabled: true
    project_id: your-project-id

  databases:
    - name: squad_payment_prod
      type: postgresql
      host: postgres-payment.squad-payment.svc
      database: payment_db

  elasticsearch:
    enabled: true
    hosts: [https://elasticsearch.logging.svc:9200]

  apm:
    datadog:
      enabled: true
      api_key: ${DATADOG_API_KEY}
```

## 📖 Documentation

- **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)** ⭐ **Start Here for New Claude Code Sessions!** - Complete project context
- [Architecture Design](docs/MULTI_SOURCE_ARCHITECTURE.md) - Complete architecture documentation
- [CURL Commands](CURL_COMMANDS.md) - API reference and examples
- [Multi-Source Setup](MULTI_SOURCE_SETUP.md) - Implementation guide
- [Claude CLI Setup](docs/CLAUDE_CLI_SETUP.md) - AI agent configuration

## 🏢 Use Cases

### For Management
- **Strategic Decision Making** - Analyze business metrics and trends
- **Performance Monitoring** - Track KPIs across departments
- **Resource Planning** - Data-driven capacity planning

### For IT Operations
- **Incident Investigation** - Rapid root cause analysis
- **Performance Debugging** - Identify bottlenecks across systems
- **Log Analysis** - Search and correlate logs from multiple sources

### For Data Teams
- **Ad-Hoc Analysis** - Natural language queries to any data source
- **Schema Discovery** - Automatic metadata extraction
- **Cross-Source Joins** - Combine data from multiple systems

## 🔒 Security

- ✅ Service account credentials never committed to git
- ✅ Environment-based configuration
- ✅ Squad-level data isolation
- ✅ API key authentication support
- ✅ Rate limiting capabilities
- ✅ Audit logging

## 🚢 Deployment

### Docker
```bash
make docker-build
make docker-run
```

### Kubernetes
```bash
make k8s-apply
make k8s-status
```

## 🗺️ Roadmap

### Q1 2026 (Current)
- ✅ BigQuery integration
- ✅ Claude AI agent
- ✅ Base multi-source architecture
- 🔄 PostgreSQL connector
- 🔄 Elasticsearch connector

### Q2 2026
- 🔄 APM integration (Datadog, NewRelic)
- 🔄 Kubernetes connector
- 🔄 Investigation orchestrator
- 📊 Dashboard integration

### Q3-Q4 2026
- 🔮 Anomaly detection
- 🔮 Alert integration
- 🔮 Historical analysis
- 🔮 Predictive insights

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for details.

## 📄 License

MIT License - see LICENSE file for details

## 💬 Support

For issues and questions:
- 📧 Email: support@cortexai.enterprise
- 📚 Documentation: See /docs folder
- 🔧 Issues: Create GitHub issue

## 🙏 Acknowledgments

- **Anthropic** - Claude AI and Claude Code CLI
- **Z.ai** - GLM-4.7 model provider
- **Google Cloud** - BigQuery platform
- **FastAPI** - Web framework
- All open-source contributors

---

**CortexAI** - Enterprise Intelligence for Data-Driven Decisions

*Version: 1.0.0*
*Status: Foundation Complete, Multi-Source in Development*
*Target: Production Ready Q2 2026*
