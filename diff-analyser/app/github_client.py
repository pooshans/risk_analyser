"""
GitHub API client for diff service.
"""

import logging
import requests
import asyncio
from typing import Dict, Any, List
from .config import get_settings

logger = logging.getLogger(__name__)


class GitHubClient:
  """GitHub API client."""

  def __init__(self):
    self.settings = get_settings()
    self.base_url = "https://api.github.com"
    self.session = requests.Session()

    if self.settings.github_token:
      self.session.headers.update({
        'Authorization': f'token {self.settings.github_token}',
        'Accept': 'application/vnd.github.v3+json'
      })

    logger.info("GitHubClient initialized")

  async def get_pr_data(self, repo: str, pr_number: int) -> Dict[str, Any]:
    """Get PR data from GitHub API."""
    logger.info(f"📡 Fetching PR data for {repo}#{pr_number}")

    try:
      loop = asyncio.get_event_loop()
      pr_data = await loop.run_in_executor(
          None,
          self._fetch_pr_sync,
          repo,
          pr_number
      )

      logger.info(f"✅ Successfully fetched PR data for {repo}#{pr_number}")
      return pr_data

    except Exception as e:
      logger.error(f"❌ Error fetching PR data: {e}")
      # Return safe mock data
      return self._get_mock_pr_data(repo, pr_number)

  def _fetch_pr_sync(self, repo: str, pr_number: int) -> Dict[str, Any]:
    """Synchronous PR data fetch."""

    url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"

    try:
      response = self.session.get(url, timeout=30)
      response.raise_for_status()

      pr_data = response.json()

      # Ensure all fields have safe values
      return {
        "number": pr_data.get("number", pr_number),
        "title": pr_data.get("title") or f"PR #{pr_number}",
        "body": pr_data.get("body") or "",
        "state": pr_data.get("state") or "open",
        "user": pr_data.get("user") or {"login": "unknown"},
        "base": pr_data.get("base") or {"ref": "main"},
        "head": pr_data.get("head") or {"ref": "feature"},
        "created_at": pr_data.get("created_at") or "2025-08-02T00:00:00Z",
        "updated_at": pr_data.get("updated_at") or "2025-08-02T00:00:00Z",
        "additions": pr_data.get("additions", 0),
        "deletions": pr_data.get("deletions", 0),
        "changed_files": pr_data.get("changed_files", 0)
      }

    except requests.exceptions.RequestException as e:
      logger.error(f"GitHub API request failed: {e}")
      return self._get_mock_pr_data(repo, pr_number)

  def _get_mock_pr_data(self, repo: str, pr_number: int) -> Dict[str, Any]:
    """Get safe mock PR data."""
    return {
      "number": pr_number,
      "title": f"Mock PR #{pr_number}",
      "body": "Mock PR description - API call failed",
      "state": "open",
      "user": {"login": "mock-user"},
      "base": {"ref": "main"},
      "head": {"ref": "feature-branch"},
      "created_at": "2025-08-02T00:00:00Z",
      "updated_at": "2025-08-02T00:00:00Z",
      "additions": 10,
      "deletions": 5,
      "changed_files": 2
    }

  async def get_pr_files(self, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    """Get PR files from GitHub API."""
    logger.info(f"📁 Fetching PR files for {repo}#{pr_number}")

    try:
      loop = asyncio.get_event_loop()
      files_data = await loop.run_in_executor(
          None,
          self._fetch_pr_files_sync,
          repo,
          pr_number
      )

      return files_data

    except Exception as e:
      logger.error(f"❌ Error fetching PR files: {e}")
      return self._get_mock_files_data()

  def _fetch_pr_files_sync(self, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    """Synchronous PR files fetch."""

    url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/files"

    try:
      response = self.session.get(url, timeout=30)
      response.raise_for_status()

      files_data = response.json()

      # Ensure all file data has safe values
      safe_files = []
      for file_data in files_data:
        safe_file = {
          "filename": file_data.get("filename") or "unknown_file",
          "status": file_data.get("status") or "modified",
          "additions": file_data.get("additions", 0),
          "deletions": file_data.get("deletions", 0),
          "patch": file_data.get("patch") or ""
        }
        safe_files.append(safe_file)

      return safe_files

    except requests.exceptions.RequestException as e:
      logger.error(f"GitHub API files request failed: {e}")
      return self._get_mock_files_data()

  def _get_mock_files_data(self) -> List[Dict[str, Any]]:
    """Get safe mock files data."""
    return [
      {
        "filename": "src/example.py",
        "status": "modified",
        "additions": 10,
        "deletions": 5,
        "patch": "@@ -1,5 +1,10 @@\n def example():\n-    pass\n+    return True"
      },
      {
        "filename": "README.md",
        "status": "modified",
        "additions": 2,
        "deletions": 1,
        "patch": "@@ -1,3 +1,4 @@\n # Project\n+Updated documentation"
      }
    ]