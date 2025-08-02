"""
FastAPI application entry point for diff service.
"""

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from datetime import datetime
import json

from .config import get_settings
from .webhook_handler import WebhookHandler, WebhookValidationError
from .models import HealthResponse
from .diff_parser import DiffParser
from .github_client import GitHubClient

# Configure structured logging
structlog.configure(
    processors=[
      structlog.stdlib.filter_by_level,
      structlog.stdlib.add_logger_name,
      structlog.stdlib.add_log_level,
      structlog.stdlib.PositionalArgumentsFormatter(),
      structlog.processors.TimeStamper(fmt="iso"),
      structlog.processors.StackInfoRenderer(),
      structlog.processors.format_exc_info,
      structlog.processors.UnicodeDecoder(),
      structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Diff Analyser Service",
    description="GitHub PR webhook processor for AI code analysis pipeline",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize handlers
webhook_handler = WebhookHandler()
diff_parser = DiffParser()
github_client = GitHubClient()


@app.get("/", response_model=dict)
async def root():
  """Root endpoint."""
  return {
    "service": "diff-analyser",
    "version": "1.0.0",
    "status": "running",
    "endpoints": {
      "webhook": "POST /webhook/pr-event",
      "analyze_pr": "POST /api/analyze-pr/{pr_id}",
      "health": "GET /health"
    }
  }


@app.get("/health", response_model=HealthResponse)
async def health_check():
  """Health check endpoint."""
  try:
    return HealthResponse(
        status="healthy",
        service="diff-analyser",
        version="1.0.0"
    )
  except Exception as e:
    logger.error("Health check failed", error=str(e))
    raise HTTPException(status_code=503, detail="Service unhealthy")


# 🚀 API 1: Webhook API (Auto-triggered by GitHub)
@app.post("/webhook/pr-event")
async def handle_pr_webhook(request: Request):
  """Handle GitHub PR webhook events - Auto-triggered by GitHub."""
  global last_webhook_response  # Add this if you want Method 2 as well

  try:
    body = await request.body()
    headers = dict(request.headers)

    # Process webhook
    result = await webhook_handler.process_webhook(body, headers)

    # 📤 Prepare Step 3 payload
    step_3_payload = await _prepare_step_3_payload_from_webhook(result)

    # Create comprehensive response
    response_data = {
      "status": "success",
      "message": "Webhook processed automatically",
      "trigger": "github_webhook",
      "timestamp": datetime.now().isoformat(),
      "webhook_summary": {
        "pr_number": result.get('pr_number'),
        "repository": result.get('repository'),
        "files_processed": result.get('files_processed', 0),
        "total_additions": result.get('total_additions', 0),
        "total_deletions": result.get('total_deletions', 0),
        "processing_time_ms": result.get('processing_time_ms', 0)
      },
      "step_3_payload": step_3_payload,  # 📤 Ready for Yasin's service
      "step_3_ready": True
    }

    # Store for debugging (Method 2)
    last_webhook_response = response_data

    # 📝 Log the Step 3 payload for visibility
    logger.info("🚀 Webhook Response Generated:")
    logger.info(f"   PR: {result.get('pr_number')} from {result.get('repository')}")
    logger.info(f"   Files: {result.get('files_processed', 0)}")
    logger.info(f"   Step 3 Payload Keys: {list(step_3_payload.keys())}")
    logger.info(f"   Step 3 Ready: ✅")

    # 💾 Save to file for debugging (Method 3)
    _save_webhook_response_to_file(response_data)

    return JSONResponse(status_code=200, content=response_data)

  except WebhookValidationError as e:
    error_response = {
      "status": "ignored",
      "reason": str(e),
      "trigger": "github_webhook",
      "timestamp": datetime.now().isoformat(),
      "step_3_ready": False
    }

    last_webhook_response = error_response
    logger.info(f"🚫 Webhook ignored: {e}")
    return JSONResponse(status_code=200, content=error_response)

  except Exception as e:
    error_response = {
      "status": "error",
      "error": str(e),
      "trigger": "github_webhook",
      "timestamp": datetime.now().isoformat(),
      "step_3_ready": False
    }

    last_webhook_response = error_response
    logger.error("❌ Webhook processing failed", error=str(e))
    raise HTTPException(status_code=500, detail="Internal server error")


# Add this new async function to prepare Step 3 payload from webhook
async def _prepare_step_3_payload_from_webhook(webhook_result: dict) -> dict:
  """
  Prepare comprehensive Step 3 payload from webhook processing result.
  This is what Yasin's embedding service needs.
  """

  # Extract basic info
  pr_number = webhook_result.get('pr_number', 0)
  repository = webhook_result.get('repository', '')

  # If we have detailed parsed diff data in the result
  parsed_diff = webhook_result.get('parsed_diff')

  if parsed_diff:
    # Use real parsed diff data
    step_3_payload = {
      "pr_metadata": {
        "pr_number": pr_number,
        "repository": repository,
        "author": parsed_diff.pr_metadata.author,
        "title": parsed_diff.pr_metadata.title,
        "description": parsed_diff.pr_metadata.description,
        "base_branch": parsed_diff.pr_metadata.base_branch,
        "head_branch": parsed_diff.pr_metadata.head_branch,
        "created_at": parsed_diff.pr_metadata.created_at,
        "trigger_type": "github_webhook"
      },
      "modified_files": [
        {
          "file_path": file_diff.file_path,
          "change_type": file_diff.change_type,
          "additions": file_diff.additions,
          "deletions": file_diff.deletions,
          "patch": file_diff.patch,
          "file_extension": _get_file_extension(file_diff.file_path),
          "is_code_file": _is_code_file(file_diff.file_path)
        }
        for file_diff in parsed_diff.modified_files
      ],
      "symbols_for_embedding": await _extract_symbols_for_embedding(parsed_diff.modified_files),
      "commit_messages": parsed_diff.commit_messages,
      "processing_metadata": {
        "total_files": len(parsed_diff.modified_files),
        "code_files": len([f for f in parsed_diff.modified_files if _is_code_file(f.file_path)]),
        "total_additions": parsed_diff.total_additions,
        "total_deletions": parsed_diff.total_deletions,
        "processing_time_ms": webhook_result.get('processing_time_ms', 0),
        "timestamp": datetime.now().isoformat(),
        "service_version": "1.0.0"
      }
    }
  else:
    # Fallback with basic data
    step_3_payload = {
      "pr_metadata": {
        "pr_number": pr_number,
        "repository": repository,
        "trigger_type": "github_webhook"
      },
      "modified_files": [],
      "symbols_for_embedding": [],
      "commit_messages": [],
      "processing_metadata": {
        "total_files": webhook_result.get('files_processed', 0),
        "total_additions": webhook_result.get('total_additions', 0),
        "total_deletions": webhook_result.get('total_deletions', 0),
        "processing_time_ms": webhook_result.get('processing_time_ms', 0),
        "timestamp": datetime.now().isoformat(),
        "service_version": "1.0.0",
        "note": "Limited data - parsed_diff not available"
      }
    }

  return step_3_payload


# Helper functions
def _get_file_extension(file_path: str) -> str:
  """Get file extension."""
  return file_path.split('.')[-1] if '.' in file_path else ''


def _is_code_file(file_path: str) -> bool:
  """Check if file is a code file."""
  code_extensions = {'.py', '.js', '.java', '.ts', '.go', '.cpp', '.c', '.rb', '.php', '.cs', '.jsx', '.tsx'}
  ext = '.' + _get_file_extension(file_path)
  return ext.lower() in code_extensions


async def _extract_symbols_for_embedding(modified_files) -> list:
  """
  Extract symbols (functions, classes) for embedding.
  This is where you'd implement actual code parsing.
  """

  symbols = []

  for file_diff in modified_files:
    if _is_code_file(file_diff.file_path):
      # TODO: Implement actual code parsing to extract functions/classes
      # For now, add mock symbols based on file type

      file_ext = _get_file_extension(file_diff.file_path)

      if file_ext == 'py':
        symbols.append({
          "symbol_name": "example_function",
          "symbol_type": "function",
          "file_path": file_diff.file_path,
          "context": _extract_context_from_patch(file_diff.patch),
          "change_type": file_diff.change_type,
          "language": "python"
        })
      elif file_ext in ['js', 'ts', 'jsx', 'tsx']:
        symbols.append({
          "symbol_name": "exampleFunction",
          "symbol_type": "function",
          "file_path": file_diff.file_path,
          "context": _extract_context_from_patch(file_diff.patch),
          "change_type": file_diff.change_type,
          "language": "javascript"
        })

  return symbols


def _extract_context_from_patch(patch: str) -> str:
  """Extract meaningful context from git patch."""
  if not patch:
    return "No patch content available"

  # Extract added/modified lines (lines starting with +)
  lines = patch.split('\n')
  context_lines = []

  for line in lines:
    if line.startswith('+') and not line.startswith('+++'):
      context_lines.append(line[1:])  # Remove + prefix
    elif line.startswith(' '):  # Context lines
      context_lines.append(line[1:])  # Remove space prefix

  context = '\n'.join(context_lines[:10])  # First 10 lines
  return context if context else "Context extraction failed"


# Add Method 2: Debug endpoint
last_webhook_response = None

@app.get("/debug/last-webhook-response")
async def get_last_webhook_response():
  """Get the JSON response from the last processed webhook."""
  if last_webhook_response:
    return {
      "message": "Last webhook response with Step 3 payload",
      "response": last_webhook_response
    }
  else:
    return {
      "message": "No webhook processed yet - trigger a PR event to see response",
      "response": None
    }


# Add Method 3: File logging
def _save_webhook_response_to_file(response_data: dict):
  """Save webhook response to JSON file."""
  import os

  try:
    # Create logs directory
    os.makedirs("logs", exist_ok=True)

    # Create filename with timestamp and PR info
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pr_info = response_data.get('webhook_summary', {})
    pr_number = pr_info.get('pr_number', 'unknown')

    filename = f"logs/webhook_pr{pr_number}_{timestamp}.json"

    with open(filename, 'w') as f:
      json.dump(response_data, f, indent=2, default=str)

    logger.info(f"💾 Webhook response saved to {filename}")

  except Exception as e:
    logger.error(f"Failed to save webhook response: {e}")


# 🎯 API 2: On-Demand PR Analysis (Called by Ankit's backend)
@app.post("/api/analyze-pr/{pr_id}")
async def analyze_pr_by_id(
    pr_id: int,
    repo: str = Query(..., description="Repository in format 'owner/repo'", example="pooshans/assignment"),
    api_key: str = Query(None, description="API key for authentication (optional)")
):
  """Analyze a specific PR by ID - called on-demand by backend services."""
  try:
    logger.info(f"🔍 On-demand PR analysis requested",
                pr_id=pr_id, repository=repo)

    # Validate inputs
    if not repo or '/' not in repo:
      raise HTTPException(status_code=400, detail="Repository must be in format 'owner/repo'")

    if pr_id <= 0:
      raise HTTPException(status_code=400, detail="PR ID must be a positive integer")

    # Fetch PR data from GitHub API
    pr_data = await github_client.get_pr_data(repo, pr_id)

    # Create PR metadata with safe handling
    try:
      pr_metadata = _create_pr_metadata_from_api(pr_data, repo)
    except Exception as e:
      logger.error(f"Failed to create PR metadata: {e}")
      raise HTTPException(status_code=500, detail=f"Failed to process PR metadata: {str(e)}")

    # Process the PR diff
    try:
      parsed_diff = await diff_parser.parse_pr_diff(pr_metadata)
    except Exception as e:
      logger.error(f"Failed to parse PR diff: {e}")
      raise HTTPException(status_code=500, detail=f"Failed to parse PR diff: {str(e)}")

    # Prepare result
    result = {
      "status": "success",
      "pr_number": pr_id,
      "repository": repo,
      "files_processed": len(parsed_diff.modified_files),
      "total_additions": parsed_diff.total_additions,
      "total_deletions": parsed_diff.total_deletions,
      "trigger": "on_demand_api"
    }

    # Prepare data for Step 3
    step_3_payload = _prepare_step_3_payload(result, parsed_diff)

    logger.info(
        "✅ On-demand analysis completed",
        pr_id=pr_id,
        repository=repo,
        files_processed=len(parsed_diff.modified_files)
    )

    return JSONResponse(
        status_code=200,
        content={
          "status": "success",
          "message": f"PR {pr_id} analyzed successfully",
          "trigger": "on_demand_api",
          "data": result,
          "step_3_payload": step_3_payload,
          "analysis_details": {
            "pr_metadata": pr_metadata.dict(),
            "modified_files": [file.dict() for file in parsed_diff.modified_files],
            "commit_messages": parsed_diff.commit_messages
          }
        }
    )

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"On-demand PR analysis failed",
                 pr_id=pr_id, repository=repo, error=str(e))
    raise HTTPException(
        status_code=500,
        detail=f"Failed to analyze PR {pr_id}: {str(e)}"
    )

# 📊 Helper endpoint to see what Step 3 would receive
@app.get("/api/step-3-preview/{pr_id}")
async def preview_step_3_data(
    pr_id: int,
    repo: str = Query(..., description="Repository in format 'owner/repo'")
):
  """Preview what data would be sent to Step 3 for a specific PR."""
  try:
    # This calls the same logic as the on-demand API
    response = await analyze_pr_by_id(pr_id, repo)
    response_data = response.body.decode() if hasattr(response, 'body') else {}

    # Extract just the Step 3 payload
    if isinstance(response, JSONResponse):
      import json
      full_data = json.loads(response.body.decode())
      return {
        "pr_id": pr_id,
        "repository": repo,
        "step_3_payload": full_data.get("step_3_payload", {}),
        "preview": True
      }

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


# 🔧 Helper Functions
def _prepare_step_3_payload(result: dict, parsed_diff=None) -> dict:
  """Prepare payload for Step 3 (Embedding Service)."""

  base_payload = {
    "pr_metadata": {
      "pr_number": result.get("pr_number"),
      "repository": result.get("repository"),
      "trigger_type": result.get("trigger", "unknown")
    },
    "processing_metadata": {
      "total_files": result.get("files_processed", 0),
      "total_additions": result.get("total_additions", 0),
      "total_deletions": result.get("total_deletions", 0),
      "processing_time_ms": result.get("processing_time_ms", 0)
    }
  }

  if parsed_diff:
    base_payload.update({
      "modified_files": [
        {
          "file_path": file_diff.file_path,
          "change_type": file_diff.change_type,
          "additions": file_diff.additions,
          "deletions": file_diff.deletions,
          "patch": file_diff.patch[:500] + "..." if len(file_diff.patch) > 500 else file_diff.patch
        }
        for file_diff in parsed_diff.modified_files
      ],
      "symbols_for_embedding": [
        # TODO: Extract functions, classes, etc.
        {
          "symbol_name": "example_function",
          "symbol_type": "function",
          "file_path": "src/example.py",
          "context": "Mock context for embedding",
          "change_type": "modified"
        }
      ],
      "commit_messages": parsed_diff.commit_messages
    })

  return base_payload


def _validate_api_key(api_key: str) -> bool:
  """Validate API key (implement your logic here)."""
  # TODO: Implement proper API key validation
  return True  # For now, accept any key


def _create_pr_metadata_from_api(pr_data: dict, repo: str):
  """Create PRMetadata from GitHub API response with safe None handling."""
  from .models import PRMetadata

  # Safe extraction with None handling
  def safe_get(data, *keys, default=""):
    """Safely get nested dict values, handling None."""
    for key in keys:
      if isinstance(data, dict) and key in data:
        data = data[key]
      else:
        return default
    return data if data is not None else default

  return PRMetadata(
      pr_number=pr_data.get("number", 0),
      repository=repo,
      author=safe_get(pr_data, "user", "login", default="unknown"),
      title=safe_get(pr_data, "title", default="No Title"),
      description=safe_get(pr_data, "body", default=""),
      base_branch=safe_get(pr_data, "base", "ref", default="main"),
      head_branch=safe_get(pr_data, "head", "ref", default="unknown"),
      created_at=safe_get(pr_data, "created_at", default="")
  )


@app.get("/metrics")
async def metrics():
  """Prometheus metrics endpoint."""
  if settings.enable_metrics:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
  else:
    raise HTTPException(status_code=404, detail="Metrics disabled")


if __name__ == "__main__":
  uvicorn.run(
      "app.main:app",
      host=settings.service_host,
      port=settings.service_port,
      log_level=settings.log_level.lower(),
      reload=settings.debug_mode
  )