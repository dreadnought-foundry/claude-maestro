"""
Registry management for sprint automation.

This package manages the sprint/epic registry, including
auto-numbering and status tracking.
"""

from .manager import (
    check_epic_completion,
    load_registry,
    save_registry,
    update_registry,
)
from .numbering import (
    get_next_epic_number,
    get_next_sprint_number,
    register_new_epic,
    register_new_sprint,
)

__all__ = [
    # manager
    "check_epic_completion",
    "load_registry",
    "save_registry",
    "update_registry",
    # numbering
    "get_next_epic_number",
    "get_next_sprint_number",
    "register_new_epic",
    "register_new_sprint",
]
