# Security Setup Guide

This guide explains how to configure and use the security features implemented in CortexAI.

## Overview

The following security improvements have been implemented:

1. **Authentication** - API key-based authentication
2. **Rate Limiting** - Request throttling per IP/API key
3. **SQL Injection Protection** - Query validation and sanitization
4. **CORS Configuration** - Controlled cross-origin access
5. **Security Headers** - HTTP security headers (CSP, HSTS, etc.)
6. **Input Validation** - Pydantic-based validation
7. **Error Sanitization** - Generic errors to clients, detailed to logs

---

## 1. Authentication Setup

### Generate Secure API Keys

Generate a secure API key using Python:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Example output: `a1b2c3d4e5f6...` (64 characters)

### Configure API Keys

Add to your `.env` file:

```bash
# Security Configuration
API_KEY_HEADER=X-API-Key
API_KEYS=["your-generated-api-key-here"]
ENABLE_AUTH=true
```

You can specify multiple API keys:

```bash
API_KEYS=["key1", "key2", "key3"]
```

### Using API Keys

Include the API key in your requests:

**Using Header (Recommended):**

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM `project.dataset.table` LIMIT 10"}'
```

**Using Cookie:**

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -b "api_key=your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM `project.dataset.table` LIMIT 10"}'
```

### Disabling Authentication (Not Recommended for Production)

For local development only:

```bash
ENABLE_AUTH=false
```

**Warning:** Never disable authentication in production environments!

---

## 2. Rate Limiting

### Configuration

Configure rate limits in `.env`:

```bash
# Maximum requests per minute per IP/API key
RATE_LIMIT_PER_MINUTE=60
```

### Response Headers

All API responses include rate limit headers:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
```

### When Limit Exceeded

```json
{
  "status": "error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Please try again later."
}
```

HTTP Status: `429 Too Many Requests`

### Best Practices

- **Development:** 60-100 requests/minute
- **Production:** 10-60 requests/minute (depending on use case)
- **Admin endpoints:** Consider stricter limits (10-20/minute)

---

## 3. SQL Injection Protection

### What's Protected

The SQL validator blocks:

- Dangerous keywords (DROP, DELETE, INSERT, UPDATE, etc.)
- Multiple statements (semicolon injection)
- UNION SELECT attacks
- File operations (OUTFILE, DUMPFILE, LOAD_FILE)
- Time-based injection (SLEEP, BENCHMARK, WAITFOR)
- Comment-based injection (--, /* */)
- Always-true conditions (1=1)

### Validation Rules

1. **SELECT Only:** Only SELECT queries are allowed
2. **Length Limit:** Maximum 10,000 characters
3. **Quote Balance:** Imbalanced quotes are rejected
4. **Complexity Limit:** Maximum 5 UNION statements

### Example: Valid Query

```json
{
  "sql": "SELECT customer_id, order_date FROM `project.dataset.orders` WHERE status = 'completed' LIMIT 100"
}
```

### Example: Blocked Query

```json
{
  "sql": "SELECT * FROM users WHERE id = 1; DROP TABLE users--"
}
```

Response:

```json
{
  "status": "error",
  "error_code": "INVALID_QUERY",
  "message": "Query validation failed",
  "details": {
    "errors": [
      "Query contains dangerous pattern: ;\\s*DROP\\s+",
      "Multiple SQL statements are not allowed"
    ]
  }
}
```

---

## 4. CORS Configuration

### Current Configuration

```python
allow_origins=["http://localhost:3000", "http://localhost:8080"]
allow_methods=["GET", "POST", "PUT", "DELETE"]
allow_headers=["X-API-Key", "Content-Type", "Authorization"]
```

### For Production

Update `.env` with your actual domains:

```bash
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]
```

**Never use `["*"]` in production!**

---

## 5. Security Headers

The following headers are automatically added to all responses:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### Content Security Policy (CSP)

Current policy allows:

- Same-origin resources by default
- Inline scripts (for API documentation)
- Data images
- Same-origin connections

Customize CSP in `app/middleware/security.py:SecurityHeadersMiddleware` if needed.

---

## 6. Input Validation

### Pydantic Models

All request models have validation:

#### Query Request

```python
- sql: min_length=1, max_length=10000
- project_id: Regex validation (6-30 chars, lowercase, alphanumeric, hyphens)
- timeout_ms: ge=1000, le=300000 (1-300 seconds)
```

#### Validation Error Example

```json
{
  "detail": [
    {
      "loc": ["body", "sql"],
      "msg": "ensure this value has at most 10000 characters",
      "type": "value_error.any_str.max_length"
    }
  ]
}
```

---

## 7. Error Handling

### Error Response Format

```json
{
  "status": "error",
  "error_code": "ERROR_CODE",
  "message": "Generic error message for client"
}
```

### Security Principle

- **Client receives:** Generic, safe error messages
- **Logs contain:** Detailed error information with stack traces

### Example: Internal Error

```json
{
  "status": "error",
  "error_code": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred. Please try again later."
}
```

Server logs:

```
2025-01-19 10:30:45 | ERROR | app.api.query:execute_query:79 - Query execution failed: Table 'project.dataset.table' not found
Traceback (most recent call last):
  File "app/api/query.py", line 59, in execute_query
    result = bigquery_service.execute_query(...)
...
```

---

## 8. Public Endpoints

The following endpoints do **not** require authentication:

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /docs` - API documentation
- `GET /redoc` - Alternative documentation
- `GET /openapi.json` - OpenAPI schema

All other endpoints require authentication.

---

## 9. Deployment Security Checklist

### Pre-Deployment

- [ ] Generate strong API keys (64 character hex)
- [ ] Set `ENABLE_AUTH=true`
- [ ] Configure `CORS_ORIGINS` with actual domains
- [ ] Set appropriate `RATE_LIMIT_PER_MINUTE`
- [ ] Review and update security headers if needed
- [ ] Set `FASTAPI_ENV=production`

### Credential Management

- [ ] Never commit `.env` file to git
- [ ] Use environment variables or secret management
- [ ] Rotate credentials regularly (monthly/quarterly)
- [ ] Use different credentials for dev/staging/prod

### GCP Specific

- [ ] Use service accounts with minimal permissions
- [ ] Enable BigQuery audit logging
- [ ] Set up quota limits in GCP project
- [ ] Use VPC endpoints if possible

---

## 10. Monitoring and Logging

### Logs Location

- **File:** `logs/app.log`
- **Rotation:** 500 MB per file
- **Retention:** 10 days

### Log Levels

```bash
# Development
LOG_LEVEL=DEBUG

# Production
LOG_LEVEL=INFO
```

### Security Events to Monitor

- Failed authentication attempts
- Rate limit violations
- SQL validation failures
- Unusual query patterns
- High error rates

---

## 11. Testing Security Features

### Test Authentication

```bash
# Should succeed
curl -H "X-API-Key: valid-key" http://localhost:8000/api/v1/datasets

# Should fail with 401
curl http://localhost:8000/api/v1/datasets

# Should fail with 403
curl -H "X-API-Key: invalid-key" http://localhost:8000/api/v1/datasets
```

### Test Rate Limiting

```bash
# Send requests rapidly
for i in {1..100}; do
  curl -H "X-API-Key: valid-key" http://localhost:8000/api/v1/datasets
done
```

Should receive `429 Too Many Requests` after limit.

### Test SQL Injection Protection

```bash
# Should be blocked
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: valid-key" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM users WHERE id = 1; DROP TABLE users--"}'
```

Should receive `400 Bad Request` with validation errors.

---

## 12. Troubleshooting

### Authentication Issues

**Problem:** All requests return 401 Unauthorized

**Solution:**
1. Check `ENABLE_AUTH=true` in `.env`
2. Verify `API_KEYS` is correctly formatted JSON array
3. Ensure API key is sent in `X-API-Key` header

### CORS Errors

**Problem:** Browser blocks requests with CORS error

**Solution:**
1. Add your frontend domain to `CORS_ORIGINS`
2. Restart the application
3. Clear browser cache

### Rate Limiting Too Strict

**Problem:** Legitimate requests blocked

**Solution:**
1. Increase `RATE_LIMIT_PER_MINUTE` in `.env`
2. Consider implementing API key-based rate limits
3. Use Redis for distributed rate limiting

---

## 13. Additional Recommendations

### Future Enhancements

1. **Redis-based Rate Limiting** - For distributed systems
2. **JWT Authentication** - For user-based auth
3. **OAuth2 Integration** - For third-party access
4. **IP Whitelisting** - For admin endpoints
5. **Request Signing** - For additional security
6. **Audit Logging** - Track all sensitive operations
7. **Web Application Firewall (WAF)** - Additional protection layer

### Security Scanning

Add to CI/CD:

```bash
# Dependency vulnerability scan
pip-audit check --output json

# Security linting
bandit -r app/

# Secret scanning
gitleaks detect --source .
```

---

## 14. Security Contact

For security concerns or vulnerability reports:

- Create a private GitHub issue
- Email: security@yourdomain.com
- PGP Key: [Your PGP key here]

---

**Last Updated:** 2025-01-19
**Version:** 1.0.0
