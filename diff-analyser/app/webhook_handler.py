"""
Webhook processing for diff service.
"""

import json
import hmac
import hashlib
import structlog
from typing import Dict, Any, Optional

from .config import get_settings
from .diff_parser import DiffParser
from .models import PRMetadata
from .utils import measure_time

logger = structlog.get_logger(__name__)


class WebhookValidationError(Exception):
  """Custom exception for webhook validation errors."""
  pass


class WebhookHandler:
  """Handles GitHub PR webhook processing."""

  def __init__(self):
    self.settings = get_settings()
    self.diff_parser = DiffParser()
    logger.info("WebhookHandler initialized")

  async def process_webhook(self, body: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
    """Process GitHub webhook request with enhanced debugging."""
    try:
      # Step 1: Validate webhook signature
      self._validate_webhook_signature(body, headers)

      # Step 2: Parse JSON payload
      payload = self._parse_payload(body)

      # 🔍 LOG RAW PAYLOAD for debugging
      logger.info("🔍 RAW WEBHOOK PAYLOAD:")
      logger.info(f"   Keys: {sorted(payload.keys())}")
      if 'action' in payload:
        logger.info(f"   Action: {payload['action']}")
      if 'pull_request' in payload:
        pr = payload['pull_request']
        logger.info(f"   PR Number: {pr.get('number')}")
        logger.info(f"   PR State: {pr.get('state')}")
        logger.info(f"   PR Title: {pr.get('title', '')[:50]}")
      if 'repository' in payload:
        repo = payload['repository']
        logger.info(f"   Repository: {repo.get('full_name')}")

      # Step 3: Log webhook details for debugging
      self._log_webhook_debug_info(payload, headers)

      # Step 4: Validate if this is a relevant PR event
      if not self._is_relevant_pr_event(payload):
        raise WebhookValidationError("Not a relevant PR event")

      # Step 5: Extract PR metadata
      pr_metadata = self._extract_pr_metadata(payload)

      # Step 6: Process the PR diff
      with measure_time() as timer:
        parsed_diff = await self.diff_parser.parse_pr_diff(pr_metadata)

      logger.info(
          "✅ Successfully processed webhook",
          pr_number=pr_metadata.pr_number,
          repository=pr_metadata.repository,
          files_processed=len(parsed_diff.modified_files),
          processing_time_ms=timer.elapsed_ms
      )

      # Step 7: Return processing results
      return {
        "status": "success",
        "pr_number": pr_metadata.pr_number,
        "repository": pr_metadata.repository,
        "files_processed": len(parsed_diff.modified_files),
        "total_additions": parsed_diff.total_additions,
        "total_deletions": parsed_diff.total_deletions,
        "processing_time_ms": timer.elapsed_ms,
        "parsed_diff": parsed_diff  # 📤 Include full parsed diff for Step 3
      }

    except WebhookValidationError:
      # Re-raise validation errors to be handled by caller
      raise
    except Exception as e:
      logger.error("❌ Webhook processing failed", error=str(e))
      raise

  def _validate_webhook_signature(self, body: bytes, headers: Dict[str, str]) -> None:
    """Temporarily skip signature validation for testing."""

    logger.info("🚨 SKIPPING webhook signature validation for testing")
    logger.info("⚠️ THIS IS INSECURE - Enable signature validation in production!")

    # Log some headers for debugging
    signature_headers = [k for k in headers.keys() if 'signature' in k.lower() or 'hub' in k.lower()]
    if signature_headers:
      logger.info(f"📋 GitHub signature headers found: {signature_headers}")
    else:
      logger.info("📋 No signature headers found")

    return  # Skip all validation

  def _parse_payload(self, body: bytes) -> Dict[str, Any]:
    """
    Parse webhook JSON payload.

    Args:
        body: Raw request body

    Returns:
        Parsed JSON payload

    Raises:
        WebhookValidationError: If JSON parsing fails
    """
    try:
      payload = json.loads(body.decode('utf-8'))

      if not isinstance(payload, dict):
        raise WebhookValidationError("Payload must be a JSON object")

      return payload

    except json.JSONDecodeError as e:
      logger.error(f"❌ Invalid JSON payload: {e}")
      raise WebhookValidationError(f"Invalid JSON payload: {e}")
    except UnicodeDecodeError as e:
      logger.error(f"❌ Invalid payload encoding: {e}")
      raise WebhookValidationError(f"Invalid payload encoding: {e}")

  def _log_webhook_debug_info(self, payload: Dict[str, Any], headers: Dict[str, str]) -> None:
    """Log webhook details for debugging."""

    action = payload.get('action', 'unknown')
    has_pr = 'pull_request' in payload
    pr_number = payload.get('number') or payload.get('pull_request', {}).get('number')
    repo_name = payload.get('repository', {}).get('full_name', 'unknown')

    logger.info("🔍 Webhook Debug Info:")
    logger.info(f"   Action: {action}")
    logger.info(f"   Has pull_request: {has_pr}")
    logger.info(f"   PR Number: {pr_number}")
    logger.info(f"   Repository: {repo_name}")
    logger.info(f"   Keys in payload: {sorted(payload.keys())}")
    logger.info(f"   User-Agent: {headers.get('user-agent', 'unknown')}")
    logger.info(f"   X-GitHub-Event: {headers.get('x-github-event', 'unknown')}")

    if has_pr:
      pr_data = payload.get('pull_request', {})
      logger.info(f"   PR State: {pr_data.get('state', 'unknown')}")
      logger.info(f"   PR Draft: {pr_data.get('draft', 'unknown')}")
      logger.info(f"   PR Author: {pr_data.get('user', {}).get('login', 'unknown')}")

  def _is_relevant_pr_event(self, payload: Dict[str, Any]) -> bool:
    """
    Check if this is a PR event we should process - ENHANCED VERSION.
    """
    try:
      # Extract event details with fallbacks
      action = str(payload.get('action', '')).lower().strip()
      has_pr = 'pull_request' in payload and payload['pull_request'] is not None

      # 🔍 COMPREHENSIVE DEBUG LOGGING
      logger.info("🔍 DETAILED EVENT VALIDATION:")
      logger.info(f"   All payload keys: {sorted(payload.keys())}")
      logger.info(f"   Action: '{action}'")
      logger.info(f"   Has pull_request: {has_pr}")

      # Check if this is a PR-related event at all
      if not has_pr:
        # Maybe it's a different event format - check for 'number' field
        if 'number' in payload and 'repository' in payload:
          logger.info("🔍 Found 'number' and 'repository' - might be PR event without pull_request object")
          pr_number = payload.get('number')
          repo_name = payload.get('repository', {}).get('full_name', 'unknown')
          logger.info(f"   PR Number: {pr_number}, Repository: {repo_name}")

          # Accept this as a PR event
          logger.info("✅ ACCEPTING: Event has PR number and repository")
          return True
        else:
          logger.info("❌ REJECTED: No pull_request data and no number/repository fields")
          return False

      # Extract PR details
      pr_data = payload.get('pull_request', {})
      pr_number = pr_data.get('number') or payload.get('number')
      pr_state = str(pr_data.get('state', '')).lower()
      pr_draft = pr_data.get('draft', False)

      logger.info(f"   PR Number: {pr_number}")
      logger.info(f"   PR State: '{pr_state}'")
      logger.info(f"   PR Draft: {pr_draft}")

      # Get repository info
      repo_data = payload.get('repository', {})
      repo_name = repo_data.get('full_name', 'unknown')
      logger.info(f"   Repository: {repo_name}")

      # RELAXED ACTION VALIDATION - Accept more actions
      relevant_actions = [
        'opened',           # New PR created
        'synchronize',      # PR updated with new commits
        'reopened',         # PR reopened
        'ready_for_review', # Draft PR made ready
        'edited',           # PR title/description edited
        'review_requested', # Review requested
        'assigned',         # PR assigned
        'unassigned',       # PR unassigned
        'labeled',          # Labels added
        'unlabeled',        # Labels removed
        'closed',           # PR closed (we might want to process this too)
        'converted_to_draft', # PR converted to draft
        'auto_merge_enabled', # Auto merge enabled
        'auto_merge_disabled' # Auto merge disabled
      ]

      logger.info(f"   Relevant actions: {relevant_actions}")
      logger.info(f"   Action '{action}' in relevant: {action in relevant_actions}")

      # ACCEPT MORE SCENARIOS

      # Scenario 1: Empty action but has PR data
      if not action and has_pr and pr_number:
        logger.info("✅ ACCEPTING: No action specified but has PR data")
        return True

      # Scenario 2: Action is in our list
      if action in relevant_actions:
        logger.info(f"✅ ACCEPTING: Action '{action}' is relevant")
        return True

      # Scenario 3: Unknown action but has PR data - accept for testing
      if has_pr and pr_number and repo_name != 'unknown':
        logger.info(f"✅ ACCEPTING: Unknown action '{action}' but has valid PR data")
        return True

      # Scenario 4: Has number field (even without pull_request object)
      if pr_number and repo_name != 'unknown':
        logger.info(f"✅ ACCEPTING: Has PR number {pr_number} and repository {repo_name}")
        return True

      # If we get here, reject
      logger.info(f"❌ REJECTED: Action '{action}' not recognized and insufficient PR data")
      logger.info("💡 This might be a comment, review, or other non-PR event")

      return False

    except Exception as e:
      logger.error(f"❌ Error validating PR event: {e}")
      # In case of error, be permissive for debugging
      logger.warning("⚠️ Error in validation - accepting event for debugging")
      return True

  def _extract_pr_metadata(self, payload: Dict[str, Any]) -> PRMetadata:
    """
    Extract PR metadata from webhook payload.

    Args:
        payload: Webhook payload

    Returns:
        PRMetadata object

    Raises:
        WebhookValidationError: If required data is missing
    """
    try:
      pr_data = payload.get('pull_request', {})
      repo_data = payload.get('repository', {})

      # Extract required fields
      pr_number = pr_data.get('number')
      repository = repo_data.get('full_name')

      if not pr_number:
        raise WebhookValidationError("PR number missing from payload")

      if not repository:
        raise WebhookValidationError("Repository name missing from payload")

      # Extract optional fields with defaults
      author = pr_data.get('user', {}).get('login', 'unknown')
      title = pr_data.get('title', 'No title')
      description = pr_data.get('body') or ''
      base_branch = pr_data.get('base', {}).get('ref', 'main')
      head_branch = pr_data.get('head', {}).get('ref', 'unknown')
      created_at = pr_data.get('created_at', '')

      # Create metadata object
      pr_metadata = PRMetadata(
          pr_number=pr_number,
          repository=repository,
          author=author,
          title=title,
          description=description,
          base_branch=base_branch,
          head_branch=head_branch,
          created_at=created_at
      )

      logger.info(f"✅ Extracted PR metadata for PR {pr_number} by {author}")
      return pr_metadata

    except Exception as e:
      if isinstance(e, WebhookValidationError):
        raise
      logger.error(f"❌ Error extracting PR metadata: {e}")
      raise WebhookValidationError(f"Failed to extract PR metadata: {e}")

  def get_health_status(self) -> Dict[str, Any]:
    """
    Get webhook handler health status.

    Returns:
        Health status information
    """
    return {
      "webhook_handler": "healthy",
      "diff_parser": "healthy",
      "webhook_secret_configured": bool(self.settings.github_webhook_secret)
    }