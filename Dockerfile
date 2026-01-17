# Multi-stage Dockerfile for BigQuery AI Service
# Supports both standalone Docker and Kubernetes deployment

# ============== Stage 1: Builder ==============
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies to /build/pip_packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ============== Stage 2: Runtime ==============
FROM python:3.11-slim

# Set labels
LABEL maintainer="your-email@example.com"
LABEL description="BigQuery AI Service - FastAPI with BigQuery Integration"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_ENV=production

# Install ALL runtime dependencies including Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    libc6 \
    libgcc1 \
    libstdc++6 \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x (required for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install Claude Code CLI globally (as root, then make accessible to appuser)
RUN npm install -g @anthropic-ai/claude-code && \
    npm cache clean --force && \
    chmod +x /usr/local/bin/claude-code 2>/dev/null || true

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY ./app ./app
COPY .env.example .env.example

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create logs directory and set permissions
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Add Node.js and npm to PATH for non-root user
ENV PATH="/usr/local/bin:/usr/bin:/bin:/node_modules/.bin:${PATH}"

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Use entrypoint script to properly handle environment variables
ENTRYPOINT ["docker-entrypoint.sh"]
