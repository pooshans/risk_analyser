"""
All data models for diff service.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class HealthResponse(BaseModel):
  """Health check response model."""
  status: str
  service: str
  version: str


class PRMetadata(BaseModel):
  """PR metadata model."""
  pr_number: int
  repository: str
  author: str
  title: str
  description: str = ""  # Default empty string
  base_branch: str = "main"  # Default value
  head_branch: str = "unknown"  # Default value
  created_at: str = ""  # Default empty string

  @validator('description', pre=True)
  def handle_none_description(cls, v):
    """Convert None to empty string for description."""
    return v if v is not None else ""

  @validator('title', pre=True)
  def handle_none_title(cls, v):
    """Convert None to empty string for title."""
    return v if v is not None else "No Title"

  @validator('author', pre=True)
  def handle_none_author(cls, v):
    """Convert None to default for author."""
    return v if v is not None else "unknown"

  @validator('base_branch', pre=True)
  def handle_none_base_branch(cls, v):
    """Convert None to default for base_branch."""
    return v if v is not None else "main"

  @validator('head_branch', pre=True)
  def handle_none_head_branch(cls, v):
    """Convert None to default for head_branch."""
    return v if v is not None else "unknown"

  @validator('created_at', pre=True)
  def handle_none_created_at(cls, v):
    """Convert None to empty string for created_at."""
    return v if v is not None else ""


class FileDiff(BaseModel):
  """File diff model."""
  file_path: str
  change_type: str = "modified"  # Default value
  additions: int = 0  # Default value
  deletions: int = 0  # Default value
  patch: str = ""  # Default empty string

  @validator('file_path', pre=True)
  def handle_none_file_path(cls, v):
    """Convert None to default for file_path."""
    return v if v is not None else "unknown_file"

  @validator('change_type', pre=True)
  def handle_none_change_type(cls, v):
    """Convert None to default for change_type."""
    return v if v is not None else "modified"

  @validator('patch', pre=True)
  def handle_none_patch(cls, v):
    """Convert None to empty string for patch."""
    return v if v is not None else ""


class ParsedDiff(BaseModel):
  """Parsed diff result model."""
  pr_metadata: PRMetadata
  modified_files: List[FileDiff]
  commit_messages: List[str]
  total_additions: int
  total_deletions: int
  processing_time_ms: Optional[int] = None


class EmbeddingContext(BaseModel):
  """Context data for embedding service."""
  symbol_name: str
  symbol_type: str  # 'function', 'class', 'variable'
  file_path: str
  context: str
  change_type: str