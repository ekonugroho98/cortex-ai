"""
FastAPI Application - CortexAI Enterprise Intelligence Platform
"""
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys

from app.config import settings
from app.api import health, datasets, tables, query, claude_agent
from app.middleware.security import RateLimitMiddleware, SecurityHeadersMiddleware
from app.middleware.auth import AuthMiddleware


# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting CortexAI Enterprise Intelligence Platform...")
    logger.info(f"Environment: {settings.fastapi_env}")
    logger.info(f"GCP Project: {settings.gcp_project_id}")

    # Test BigQuery connection
    try:
        from app.services.bigquery_service import bigquery_service
        bq_connected = bigquery_service.test_connection()
        if bq_connected:
            logger.info("✓ BigQuery connection successful")
        else:
            logger.warning("⚠ BigQuery connection failed")
    except Exception as e:
        logger.error(f"✗ BigQuery initialization error: {e}")

    # Check Claude CLI availability
    try:
        from app.services.claude_cli_service import claude_cli_service
        claude_available = claude_cli_service.is_available()
        if claude_available:
            logger.info("✓ Claude Code CLI available")
        else:
            logger.warning("⚠ Claude Code CLI not found in PATH")
    except Exception as e:
        logger.warning(f"⚠ Claude CLI check failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down CortexAI Platform...")


# Create FastAPI app
app = FastAPI(
    title="CortexAI - Enterprise Intelligence Platform",
    description="AI-powered enterprise platform for data-driven decisions and multi-source investigations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)

# Add authentication middleware if enabled
if settings.enable_auth and settings.api_keys:
    logger.info(f"✓ Authentication enabled with {len(settings.api_keys)} API key(s)")
    app.add_middleware(AuthMiddleware, api_keys=settings.api_keys)
else:
    logger.warning("⚠ Authentication disabled - API requests will not be authenticated")



# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with sanitized error messages"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Don't expose internal errors to clients
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(datasets.router, prefix=settings.api_v1_prefix, tags=["Datasets"])
app.include_router(tables.router, prefix=settings.api_v1_prefix, tags=["Tables"])
app.include_router(query.router, prefix=settings.api_v1_prefix, tags=["Query"])
app.include_router(claude_agent.router, prefix=settings.api_v1_prefix, tags=["Claude AI Agent"])


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint"""
    claude_status = "unknown"
    try:
        from app.services.claude_cli_service import claude_cli_service
        claude_status = "available" if claude_cli_service.is_available() else "unavailable"
    except (ImportError, AttributeError, OSError) as e:
        logger.debug(f"Claude CLI check skipped: {e}")
        pass

    return {
        "service": "BigQuery AI Service",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.fastapi_env,
        "claude_cli": claude_status,
        "docs": "/docs",
        "health": "/health",
        "api": settings.api_v1_prefix
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.fastapi_reload,
        log_level=settings.log_level.lower()
    )
