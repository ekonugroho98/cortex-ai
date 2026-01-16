# Phase 3 Roadmap - Future Enhancements

> **Status**: PLANNED - Not yet implemented
> **Priority**: After Phase 1 & 2 are stable

## Overview

This document outlines planned features for Phase 3 of the BigQuery AI Service.
These features are noted for future implementation but are NOT currently prioritized.

---

## 1. Caching Layer with Redis

### Description
Add Redis caching for frequently accessed BigQuery schema metadata and query results.

### Benefits
- Reduce BigQuery API calls and costs
- Faster response times for repeated queries
- Lower latency for schema metadata

### Implementation Plan
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│ FastAPI      │─────▶│ Redis Cache │
│             │      │              │      │             │
│             │      │              │─────▶│ BigQuery    │
└─────────────┘      └──────────────┘      └─────────────┘
```

### Tasks
- [ ] Add Redis to requirements.txt
- [ ] Create cache service layer
- [ ] Cache schema metadata (TTL: 1 hour)
- [ ] Cache query results (TTL: configurable)
- [ ] Cache invalidation strategy
- [ ] Update Docker Compose for Redis
- [ ] Update Kubernetes manifests for Redis deployment

### Files to Create/Modify
- `app/services/cache_service.py` (NEW)
- `docker-compose.yml` - Add Redis service
- `k8s/redis-deployment.yaml` (NEW)
- Update BigQuery service to use cache

---

## 2. Authentication & Authorization

### Description
Add API key authentication and optional OAuth2 support.

### Features
- API key based authentication
- Rate limiting per API key
- User management (admin can manage keys)
- Audit logging

### Implementation Plan
```
Request → API Key Validation → Rate Limit Check → Process Request
```

### Tasks
- [ ] Implement API key middleware
- [ ] Add rate limiting with slowapi
- [ ] Create API key management endpoints
- [ ] Add user/role system
- [ ] Audit logging for all queries
- [ ] Update documentation

### Files to Create/Modify
- `app/middleware/auth.py` (NEW)
- `app/services/auth_service.py` (NEW)
- `app/api/admin.py` (NEW)
- Update environment variables for auth config

---

## 3. Query History & Analytics

### Description
Track and analyze query history for insights and optimization.

### Features
- Store query history in database
- Query statistics and analytics
- Popular queries tracking
- Cost analysis per query
- Performance metrics

### Implementation Plan
```
Query Execution → Log to Database → Analytics Dashboard
```

### Tasks
- [ ] Add PostgreSQL/SQLite for history storage
- [ ] Create query history models
- [ ] Store all queries with metadata
- [ ] Create analytics endpoints
- [ ] Build dashboard (optional)
- [ ] Query export functionality

### Files to Create/Modify
- `app/models/query_history.py` (NEW)
- `app/services/analytics_service.py` (NEW)
- `app/api/analytics.py` (NEW)
- `k8s/postgres-deployment.yaml` (NEW)

---

## 4. Export Functionality

### Description
Allow users to export query results to various formats.

### Features
- Export to CSV
- Export to JSON
- Export to Excel
- Streaming export for large datasets
- Background job for large exports

### Implementation Plan
```
Query Results → Format Converter → Download Link
```

### Tasks
- [ ] Create export service
- [ ] Add export endpoints
- [ ] Implement CSV/JSON/Excel formatters
- [ ] Background jobs for large exports
- [ ] Signed URL for downloads (if using GCS)

### Files to Create/Modify
- `app/services/export_service.py` (NEW)
- `app/api/export.py` (NEW)

---

## 5. Multi-Turn Conversation Improvements

### Description
Enhance WebSocket chat with better conversation context management.

### Features
- Conversation history tracking
- Context-aware follow-up questions
- Query refinement suggestions
- Entity recognition and caching

### Implementation Plan
```
User Message → Update Context → Generate Response → Update History
```

### Tasks
- [ ] Add conversation context manager
- [ ] Implement conversation history storage
- [ ] Add follow-up question suggestions
- [ ] Entity extraction and caching
- [ ] Better prompt engineering for context

### Files to Create/Modify
- `app/services/conversation_service.py` (NEW)
- Update `claude_cli_service.py` for context management

---

## 6. Advanced Prompt Engineering

### Description
Improve prompt templates for better SQL generation.

### Features
- Few-shot learning examples
- Dynamic prompt assembly based on user intent
- Query optimization suggestions
- Error correction and retry logic

### Tasks
- [ ] Create prompt template system
- [ ] Add few-shot examples
- [ ] Intent detection
- [ ] Automatic query optimization
- [ ] Error correction loop

### Files to Create/Modify
- `app/services/prompt_service.py` (NEW)
- Update `claude_cli_service.py` with new templates

---

## 7. Monitoring & Observability

### Description
Add comprehensive monitoring and alerting.

### Features
- Metrics collection (Prometheus)
- Distributed tracing (optional)
- Health check improvements
- Alerting rules
- Dashboard (Grafana)

### Implementation Plan
```
Service → Metrics Export → Prometheus → Grafana Dashboard
```

### Tasks
- [ ] Add Prometheus metrics
- [ ] Create health check endpoints
- [ ] Setup alerting rules
- [ ] Create Grafana dashboard
- [ ] Log aggregation

### Files to Create/Modify
- `app/metrics.py` (NEW)
- `k8s/prometheus-config.yaml` (NEW)
- `k8s/grafana-config.yaml` (NEW)

---

## 8. Performance Optimization

### Description
Optimize performance for high-load scenarios.

### Features
- Connection pooling
- Async query execution
- Result pagination
- Query result streaming

### Tasks
- [ ] Implement connection pooling
- [ ] Add pagination to all list endpoints
- [ ] Stream large query results
- [ ] Optimize Claude CLI subprocess management
- [ ] Add query queue for heavy workloads

### Files to Create/Modify
- Update `bigquery_service.py` for connection pooling
- Update all list endpoints for pagination
- Add result streaming

---

## Priority Order (When Implementing)

1. **High Priority**
   - Authentication & Authorization
   - Caching Layer with Redis
   - Query History & Analytics

2. **Medium Priority**
   - Export Functionality
   - Multi-Turn Conversation Improvements
   - Performance Optimization

3. **Low Priority**
   - Advanced Prompt Engineering
   - Monitoring & Observability

---

## Notes

- All features in this document are PLANNED only
- Implementation will start AFTER Phase 1 & 2 are stable
- Priority may change based on user feedback
- Each feature should be implemented incrementally
- All new features need tests and documentation

---

## Dependencies

Some features depend on others:
- Export functionality depends on Query History
- Analytics depends on Query History
- Multi-turn improvements depend on Conversation Service
- Monitoring depends on all services

---

**Last Updated**: 2026-01-15
**Status**: Phase 1 & 2 currently in focus
