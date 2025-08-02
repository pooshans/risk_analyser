"""
Configuration management for diff service.
"""

from functools import lru_cache
from typing import Set
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
  """Application settings."""

  # GitHub Configuration
  github_token: str = Field(default="", description="GitHub API token")
  github_webhook_secret: str = Field(default="", description="GitHub webhook secret")

  # Service Configuration
  service_host: str = Field(default="0.0.0.0", description="Service host")
  service_port: int = Field(default=8000, description="Service port")
  log_level: str = Field(default="INFO", description="Log level")

  # GitHub API Settings
  github_api_timeout: int = Field(default=30, description="GitHub API timeout in seconds")
  github_max_retries: int = Field(default=3, description="Max retries for GitHub API")
  github_rate_limit_buffer: int = Field(default=100, description="Rate limit buffer")

  # File Processing Settings
  max_file_size_mb: int = Field(default=1, description="Max file size in MB")
  max_files_per_pr: int = Field(default=100, description="Max files per PR")
  supported_extensions: str = Field(
      default=".py,.js,.java,.ts,.go,.cpp,.c,.rb,.php,.cs",
      description="Comma-separated list of supported file extensions"
  )

  # Embedding Service Configuration
  embedding_service_url: str = Field(
      default="http://localhost:8001",
      description="Embedding service URL"
  )
  embedding_service_timeout: int = Field(
      default=60,
      description="Embedding service timeout in seconds"
  )

  # Monitoring
  enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
  metrics_port: int = Field(default=9090, description="Metrics port")

  # Development
  debug_mode: bool = Field(default=False, description="Enable debug mode")
  enable_request_logging: bool = Field(
      default=True,
      description="Enable request logging"
  )

  # Additional fields that might be in .env
  debug: bool = Field(default=False, description="Debug flag")
  host: str = Field(default="0.0.0.0", description="Host")
  port: int = Field(default=8000, description="Port")
  enable_step_3_integration: bool = Field(default=False, description="Enable step 3 integration")

  class Config:
    env_file = ".env"
    case_sensitive = False
    extra = "ignore"  # This allows extra fields to be ignored

  @property
  def supported_extensions_set(self) -> Set[str]:
    """Get supported file extensions as a set."""
    return {ext.strip() for ext in self.supported_extensions.split(',')}


@lru_cache()
def get_settings() -> Settings:
  """
  Get application settings (cached).

  Returns:
      Settings instance
  """
  return Settings()