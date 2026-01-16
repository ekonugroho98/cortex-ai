# CortexAI Project - Complete Context & Onboarding Guide

> **Important:** Save this file! This is your complete project context for new Claude Code sessions.

---

## 🚀 Quick Start for New Claude Code Session

### Step 1: Provide Context (Copy-Paste This)

```
I'm working on CortexAI - Enterprise Intelligence Platform in /Users/macbookpro/work/project/cortex-ai/

PROJECT OVERVIEW:
- Name: CortexAI Enterprise Intelligence Platform
- Location: /Users/macbookpro/work/project/cortex-ai/
- Tech Stack: FastAPI, Python 3.11+, Claude Code CLI, BigQuery
- Purpose: Multi-source AI platform for enterprise investigations & decision-making

CURRENT STATUS:
✅ Phase 1 Complete (BigQuery + AI Agent)
✅ Base multi-source architecture created
🔄 Phase 2 In Progress (PostgreSQL, Elasticsearch connectors)

KEY FILES:
- README.md - Project overview
- app/main.py - FastAPI application
- app/services/data_sources/ - Multi-source architecture
- docs/MULTI_SOURCE_ARCHITECTURE.md - Complete design
- CURL_COMMANDS.md - API reference

SERVER RUNNING ON:
- Port: 8001
- Base URL: http://localhost:8001
- Docs: http://localhost:8001/docs
```

### Step 2: Read This Context File

```bash
pwd
# Should show: /Users/macbookpro/work/project/cortex-ai
```

---

## 📚 Complete Project Documentation

### 1. Project Vision

**CortexAI** is an enterprise-grade AI platform that:
- Connects to multiple data sources (BigQuery, PostgreSQL, MySQL, Elasticsearch, APM, Kubernetes)
- Uses Claude AI to investigate issues and analyze data
- Helps management make data-driven decisions
- Enables rapid IT incident investigation

### 2. Architecture

```
CortexAI Platform (FastAPI + Claude AI Orchestrator)
    │
    ├── BigQuery Service (Analytics warehouse)
    ├── Database Service (PostgreSQL/MySQL per squad)
    ├── Elasticsearch Service (Logs & errors)
    ├── APM Service (Datadog/NewRelic metrics)
    └── Kubernetes Service (Pods, events, logs)
```

### 3. Current Implementation Status

#### ✅ Complete (Phase 1)
- BigQuery integration with natural language to SQL
- Claude AI agent for query generation
- Base API endpoints
- Docker & Kubernetes deployment ready
- Interactive documentation at /docs

#### ✅ Complete (Foundation)
- Abstract `DataSourceInterface` base class
- `DataSourceRegistry` for managing sources
- Multi-source architecture design
- Complete documentation

#### 🔄 In Progress (Phase 2)
- PostgreSQL connector implementation
- Elasticsearch connector implementation
- Investigation orchestrator
- Cross-source correlation

#### 🔮 Planned (Phase 3+)
- APM integration (Datadog, NewRelic)
- Kubernetes connector
- Anomaly detection
- Alert integration
- Dashboard & visualization

### 4. Project Structure

```
cortex-ai/
├── README.md                          # Main project overview
├── PROJECT_CONTEXT.md                 # THIS FILE - Session context
├── CURL_COMMANDS.md                   # API reference
├── MULTI_SOURCE_SETUP.md              # Implementation guide
│
├── app/                               # FastAPI application
│   ├── main.py                       # App entry point
│   ├── config.py                     # Configuration
│   ├── api/                          # API endpoints
│   │   ├── health.py                 # Health check
│   │   ├── datasets.py               # BigQuery datasets
│   │   ├── tables.py                 # BigQuery tables
│   │   ├── query.py                  # Direct SQL
│   │   └── claude_agent.py           # AI agent endpoints
│   │
│   ├── services/                     # Business logic
│   │   ├── bigquery_service.py       # BigQuery client
│   │   ├── claude_cli_service.py     # Claude CLI wrapper
│   │   └── data_sources/             # Multi-source layer
│   │       ├── __init__.py
│   │       ├── base.py               # Abstract interface
│   │       └── registry.py           # Source registry
│   │
│   └── models/                       # Pydantic models
│       └── bigquery.py
│
├── docs/                              # Documentation
│   ├── MULTI_SOURCE_ARCHITECTURE.md  # Complete architecture
│   ├── API_DOCUMENTATION.md
│   └── CLAUDE_CLI_SETUP.md
│
├── k8s/                               # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   └── secret.yaml
│
├── credentials/                       # GCP credentials (gitignored)
│   └── service-account.json
│
├── claude-workspace/                  # Claude CLI workspace
├── logs/                              # Application logs
├── venv/                              # Python virtual environment
│
├── .env                               # Environment variables
├── .env.example                       # Environment template
├── Dockerfile                         # Docker image
├── docker-compose.yml                 # Docker compose
├── Makefile                           # Make commands
└── requirements.txt                   # Python dependencies
```

### 5. Key Technologies

**Backend:**
- FastAPI 0.115.0 - Web framework
- Uvicorn 0.32.0 - ASGI server
- Pydantic 2.9.2 - Data validation
- Python 3.11+

**AI/ML:**
- Claude Code CLI - AI agent (npm install -g @anthropic-ai/claude-code)
- Z.ai GLM-4.7 - Model provider

**Data Sources:**
- google-cloud-bigquery 3.25.0 - BigQuery client
- (Planned) asyncpg - PostgreSQL
- (Planned) aiomysql - MySQL
- (Planned) elasticsearch - ELK Stack

**Development:**
- pytest - Testing
- loguru - Logging
- python-dotenv - Configuration

### 6. Environment Variables

```bash
# BigQuery Configuration
GOOGLE_APPLICATION_CREDENTIALS=credentials/service-account.json
GCP_PROJECT_ID=gen-lang-client-0716506049
BIGQUERY_LOCATION=US

# FastAPI Configuration
FASTAPI_ENV=development
FASTAPI_PORT=8000
FASTAPI_HOST=0.0.0.0

# Claude Code CLI
ANTHROPIC_API_KEY=your-zhipu-ai-api-key
CLAUDE_WORKSPACE_PATH=claude-workspace

# Z.ai Configuration for Claude Code CLI
# Update ~/.claude/settings.json with:
{
  "env": {
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-4.5-air",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-4.7",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-4.7"
  }
}
```

### 7. API Endpoints

#### Current Endpoints

```
GET  /                           # Service info
GET  /health                     # Health check
GET  /api/v1/datasets            # List all datasets
GET  /api/v1/datasets/{id}       # Get dataset details
GET  /api/v1/datasets/{id}/tables # List tables
GET  /api/v1/datasets/{id}/tables/{id} # Get table schema
POST /api/v1/query               # Execute SQL
POST /api/v1/query-agent         # AI agent (NL to SQL)
```

#### Planned Endpoints

```
POST /api/v1/investigate         # Multi-source investigation
GET  /api/v1/sources             # List data sources
POST /api/v1/sources/{type}/query # Query specific source
```

### 8. Common Commands

```bash
# Development
make dev                         # Start dev server (port 8000)
make run                         # Run server (port 8000)
make test                        # Run tests
make lint                        # Run linter
make format                      # Format code

# Docker
make docker-build                # Build Docker image
make docker-run                  # Run with docker-compose
make docker-stop                 # Stop containers

# Kubernetes
make k8s-apply                   # Deploy to K8s
make k8s-status                  # Check K8s status
make k8s-logs                    # View logs

# Setup
make setup                       # Initial setup
make init                        # Create .env from example
```

### 9. Testing the Service

```bash
# 1. Check health
curl http://localhost:8001/health

# 2. List datasets
curl http://localhost:8001/api/v1/datasets

# 3. AI Agent query
curl -X POST http://localhost:8001/api/v1/query-agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show me top 10 app ratings",
    "dataset_id": "falcon_bigquery",
    "dry_run": false
  }'
```

### 10. Development Workflow

#### Starting Development:

```bash
cd /Users/macbookpro/work/project/cortex-ai

# 1. Activate virtual environment
source venv/bin/activate

# 2. Start server (background)
make dev

# Or with credentials explicitly:
GOOGLE_APPLICATION_CREDENTIALS=credentials/service-account.json \
  venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### Making Changes:

```bash
# 1. Edit code (auto-reload will pick up changes)
vim app/main.py

# 2. Check logs
tail -f logs/app.log

# 3. Test changes
curl http://localhost:8001/health
```

#### Adding New Features:

1. Add endpoint in `app/api/`
2. Add service in `app/services/`
3. Add model in `app/models/`
4. Update `app/main.py` to include router
5. Test with curl or http://localhost:8001/docs

### 11. Important Notes

#### Server Management:
- Server runs on port 8001 (port 8000 might be in use)
- Auto-reload is enabled for development
- Logs stored in `logs/app.log`
- Background shell IDs: Check with `/tasks` command

#### Credentials:
- GCP credentials: `gen-lang-client-0716506049-bc8d7b7bce03.json`
- Project ID: `gen-lang-client-0716506049`
- Dataset: `falcon_bigquery` (17 tables)
- Z.ai API key configured

#### Claude Code CLI:
- Installed via npm: `npm install -g @anthropic-ai/claude-code`
- Config in `~/.claude/settings.json`
- Uses Z.ai GLM-4.7 model
- Workspace: `claude-workspace/bigquery_context`

### 12. Troubleshooting

#### Port Already in Use:
```bash
# Kill process on port 8000/8001
pkill -f uvicorn
# Or use different port
venv/bin/uvicorn app.main:app --port 8002
```

#### BigQuery Connection Failed:
```bash
# Check credentials file exists
ls -la credentials/service-account.json

# Verify project ID
echo $GCP_PROJECT_ID
```

#### Claude CLI Not Found:
```bash
# Check installation
which claude

# Reinstall
npm install -g @anthropic-ai/claude-code
```

### 13. Future Implementation Tasks

#### Priority 1 (Next 2-3 weeks):
- [ ] Implement `BigQuerySource` wrapper
- [ ] Create `DatabaseSource` (PostgreSQL, MySQL)
- [ ] Create `ElasticsearchSource` connector
- [ ] Build `InvestigationOrchestrator` base

#### Priority 2 (4-6 weeks):
- [ ] Add APM integration (Datadog)
- [ ] Kubernetes connector
- [ ] `/investigate` endpoint
- [ ] Cross-source correlation

#### Priority 3 (6-8 weeks):
- [ ] Anomaly detection
- [ ] Alert integration
- [ ] Dashboard UI
- [ ] Historical analysis

### 14. Related Documentation Files

- `README.md` - Main project README
- `MULTI_SOURCE_SETUP.md` - Quick start guide
- `docs/MULTI_SOURCE_ARCHITECTURE.md` - Detailed architecture
- `CURL_COMMANDS.md` - Complete API reference
- `docs/CLAUDE_CLI_SETUP.md` - AI agent setup

---

## 🎯 For New Sessions: Quick Reference

**When starting a new Claude Code session, always provide:**

1. **Project Location:** `/Users/macbookpro/work/project/cortex-ai/`
2. **Project Name:** CortexAI Enterprise Intelligence Platform
3. **Current Phase:** Multi-source architecture implementation
4. **Key Files:** Read `PROJECT_CONTEXT.md`, `README.md`, `docs/MULTI_SOURCE_ARCHITECTURE.md`
5. **Server Status:** Usually running on port 8001

**Then ask Claude to:**
```bash
cd /Users/macbookpro/work/project/cortex-ai
pwd
ls -la
```

---

## 📞 Support & Questions

- **Main Project Docs:** README.md
- **Architecture:** docs/MULTI_SOURCE_ARCHITECTURE.md
- **API Reference:** CURL_COMMANDS.md
- **Implementation:** MULTI_SOURCE_SETUP.md

---

**Last Updated:** 2026-01-16
**Project:** CortexAI Enterprise Intelligence Platform
**Version:** 1.0.0
**Status:** Phase 1 Complete, Phase 2 In Progress
