"""Development runner script."""

import os
import subprocess
import sys
from pathlib import Path

def main():
  # Set up environment
  os.environ.setdefault("DEBUG", "true")
  os.environ.setdefault("LOG_LEVEL", "INFO")

  # Run the application
  cmd = [
    sys.executable, "-m", "uvicorn",
    "app.main:app",
    "--host", "0.0.0.0",
    "--port", "8000",
    "--reload"
  ]

  subprocess.run(cmd)

if __name__ == "__main__":
  main()