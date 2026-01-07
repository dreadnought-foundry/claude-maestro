"""
Epic automation module.

Provides epic lifecycle management including creation, status tracking,
completion, and archiving.
"""

from .lifecycle import (
    archive_epic,
    complete_epic,
    create_epic,
    reset_epic,
    start_epic,
)
from .status import add_to_epic, get_epic_status, list_epics

__all__ = [
    # lifecycle
    "archive_epic",
    "complete_epic",
    "create_epic",
    "reset_epic",
    "start_epic",
    # status
    "add_to_epic",
    "get_epic_status",
    "list_epics",
]
