# Multi-stage Dockerfile for BigQuery AI Service
# Supports both standalone Docker and Kubernetes deployment

# ============== Stage 1: Builder ==============
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /build

# Install system dependencies (include Node.js for Claude Code CLI)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x (required for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally via npm
RUN npm install -g @anthropic-ai/claude-code

# Verify installation
RUN claude-code --version || echo "Claude Code CLI installed"

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

# Install runtime dependencies and Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    libc6 \
    libgcc1 \
    libstdc++6 \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x in runtime (required for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /install /usr/local

# Copy Node.js and npm packages from builder
COPY --from=builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY ./app ./app
COPY .env.example .env.example

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create logs directory
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Use entrypoint script to properly handle environment variables
ENTRYPOINT ["docker-entrypoint.sh"]
