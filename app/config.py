"""
Application Configuration using Pydantic Settings
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # BigQuery Configuration
    google_application_credentials: str = Field(
        default="",
        description="Path to Google Cloud service account JSON file"
    )
    gcp_project_id: str = Field(
        default="",
        description="Google Cloud Project ID"
    )
    bigquery_location: str = Field(
        default="US",
        description="BigQuery dataset location"
    )

    # FastAPI Configuration
    fastapi_env: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    fastapi_port: int = Field(
        default=8000,
        description="FastAPI server port"
    )
    fastapi_host: str = Field(
        default="0.0.0.0",
        description="FastAPI server host"
    )
    fastapi_reload: bool = Field(
        default=True,
        description="Enable auto-reload in development"
    )
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API v1 prefix"
    )

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )

    # Security Configuration
    api_key_header: str = Field(
        default="X-API-Key",
        description="API key header name"
    )
    api_keys: List[str] = Field(
        default=[],
        description="List of valid API keys for authentication"
    )
    enable_auth: bool = Field(
        default=True,
        description="Enable authentication middleware"
    )
    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute per IP/API key"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    # Claude Code CLI (Phase 2)
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude Code CLI"
    )
    claude_workspace_path: str = Field(
        default="/tmp/claude-workspace",
        description="Path to Claude Code CLI workspace (use /tmp for Cloud Run)"
    )
    claude_timeout: int = Field(
        default=300,
        ge=10,
        le=600,
        description="Claude CLI timeout in seconds"
    )

    # Production Security Settings
    enable_row_level_security: bool = Field(
        default=True,
        description="Enable row-level security enforcement"
    )
    max_query_bytes_processed: int = Field(
        default=10_000_000_000,
        ge=1_000_000_000,
        description="Maximum bytes processed per query (default: 10GB)"
    )
    enable_query_cost_tracking: bool = Field(
        default=True,
        description="Enable query cost tracking and limits"
    )
    enable_data_masking: bool = Field(
        default=True,
        description="Enable automatic data masking for sensitive columns"
    )
    enable_pii_detection: bool = Field(
        default=True,
        description="Enable PII/PHI detection in prompts"
    )
    sensitive_columns: List[str] = Field(
        default=[
            "email", "phone", "ssn", "social_security_number",
            "credit_card", "password", "secret", "token",
            "api_key", "access_key", "private_key"
        ],
        description="List of sensitive column names for masking"
    )
    pii_keywords: List[str] = Field(
        default=[
            "password", "ssn", "social security", "credit card",
            "bank account", "pin", "secret", "private key",
            "access token", "api key", "personal data"
        ],
        description="PII keywords to detect in prompts"
    )
    enable_audit_logging: bool = Field(
        default=True,
        description="Enable detailed audit logging for compliance"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @field_validator("api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, v):
        """Parse API keys from string or list"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @field_validator("google_application_credentials")
    @classmethod
    def validate_credentials(cls, v):
        """Validate Google Cloud credentials path"""
        # In Cloud Run, credentials are optional (uses default service account)
        # Only validate in local development
        import os
        if os.getenv("FASTAPI_ENV", "development") == "development":
            if not v:
                raise ValueError(
                    "GOOGLE_APPLICATION_CREDENTIALS must be set in development. "
                    "Provide path to service account JSON file."
                )
        return v

    @field_validator("gcp_project_id")
    @classmethod
    def validate_project_id(cls, v):
        """Validate GCP project ID"""
        if not v:
            raise ValueError("GCP_PROJECT_ID must be set")
        return v


# Global settings instance
settings = Settings()
