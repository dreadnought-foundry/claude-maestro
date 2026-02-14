"""
Context builder for sprint automation.

Generates structured context briefs for upcoming sprints by reading
prior sprint data, postmortems, and project configuration. Outputs
a markdown document that can be fed into a sprint prompt to give
Claude full project awareness.

Usage:
    From command line:
        python -m sprint_automation build-context 21

    From Python code:
        from sprint_automation.context import build_context
        brief = build_context(21)
"""

from .builder import build_context

__all__ = [
    "build_context",
]
