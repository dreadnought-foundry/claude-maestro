"""
Sprint analysis module.

Provides tools for mining sprint history to improve future sprints:
- Pattern analysis across postmortems (anti-pattern detection)
- Test baseline snapshots (pre-existing vs new failure diffing)
"""

from .pattern_analyzer import analyze_patterns
from .test_baseline import capture_baseline, compare_baseline

__all__ = [
    "analyze_patterns",
    "capture_baseline",
    "compare_baseline",
]
