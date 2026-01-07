"""
Sprint automation module.

Provides complete sprint lifecycle management including creation,
status tracking, completion, and postmortem generation.
"""

from .completion import complete_sprint, move_to_done
from .lifecycle import (
    abort_sprint,
    block_sprint,
    create_sprint,
    recover_sprint,
    resume_sprint,
    start_sprint,
)
from .postmortem import generate_postmortem
from .status import advance_step, get_sprint_status

__all__ = [
    # completion
    "complete_sprint",
    "move_to_done",
    # lifecycle
    "abort_sprint",
    "block_sprint",
    "create_sprint",
    "recover_sprint",
    "resume_sprint",
    "start_sprint",
    # postmortem
    "generate_postmortem",
    # status
    "advance_step",
    "get_sprint_status",
]
