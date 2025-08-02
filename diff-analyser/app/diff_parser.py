"""
Core diff parsing logic for diff service.
"""

import logging
from typing import List
from .models import PRMetadata, FileDiff, ParsedDiff
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class DiffParser:
  """Core diff parsing logic."""

  def __init__(self):
    self.github_client = GitHubClient()
    logger.info("DiffParser initialized")

  async def parse_pr_diff(self, pr_metadata: PRMetadata) -> ParsedDiff:
    """
    Parse PR diff and extract relevant information.

    Args:
        pr_metadata: PR metadata

    Returns:
        ParsedDiff object with processed data
    """
    logger.info(f"🔍 Starting diff parsing for PR {pr_metadata.pr_number}")

    try:
      # Fetch PR files from GitHub API
      files_data = await self.github_client.get_pr_files(
          pr_metadata.repository,
          pr_metadata.pr_number
      )

      # Parse files into FileDiff objects
      modified_files = []
      total_additions = 0
      total_deletions = 0

      for file_data in files_data:
        file_diff = FileDiff(
            file_path=file_data.get("filename", ""),
            change_type=file_data.get("status", "modified"),
            additions=file_data.get("additions", 0),
            deletions=file_data.get("deletions", 0),
            patch=file_data.get("patch", "")
        )
        modified_files.append(file_diff)
        total_additions += file_diff.additions
        total_deletions += file_diff.deletions

      # Create parsed diff result
      parsed_diff = ParsedDiff(
          pr_metadata=pr_metadata,
          modified_files=modified_files,
          commit_messages=[f"Changes in PR {pr_metadata.pr_number}"],
          total_additions=total_additions,
          total_deletions=total_deletions
      )

      logger.info(
          f"✅ Successfully parsed diff for PR {pr_metadata.pr_number} - "
          f"Files: {len(modified_files)}, +{total_additions}/-{total_deletions}"
      )
      return parsed_diff

    except Exception as e:
      logger.error(f"❌ Error parsing diff for PR {pr_metadata.pr_number}: {e}")

      # Return minimal parsed diff on error
      mock_file_diff = FileDiff(
          file_path="error/mock.py",
          change_type="modified",
          additions=0,
          deletions=0,
          patch="Error occurred during parsing"
      )

      return ParsedDiff(
          pr_metadata=pr_metadata,
          modified_files=[mock_file_diff],
          commit_messages=["Error parsing commits"],
          total_additions=0,
          total_deletions=0
      )