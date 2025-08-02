"""
Utility functions for diff service.
"""

import time
from contextlib import contextmanager


@contextmanager
def measure_time():
  """Context manager to measure execution time."""

  class Timer:
    def __init__(self):
      self.start_time = None
      self.end_time = None
      self.elapsed_ms = None

  timer = Timer()
  timer.start_time = time.time()

  try:
    yield timer
  finally:
    timer.end_time = time.time()
    timer.elapsed_ms = int((timer.end_time - timer.start_time) * 1000)