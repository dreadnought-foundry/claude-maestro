"""
Sprint Automation Package.

A modular package for managing sprint and epic lifecycles in Claude Code projects.

This package provides:
- Sprint lifecycle management (create, start, complete, abort, block, resume)
- Epic lifecycle management (create, start, complete, archive)
- Registry management with auto-numbering
- State file tracking for workflow enforcement
- Git integration (tags, commits)
- Project initialization
- CLI interface

Usage:
    From command line:
        python -m sprint_automation sprint-create 1 "My Sprint"
        python -m sprint_automation sprint-start 1
        python -m sprint_automation sprint-complete 1

    From Python code:
        from sprint_automation import create_sprint, start_sprint, complete_sprint

        create_sprint(1, "My Sprint")
        start_sprint(1)
        complete_sprint(1)
"""

# Constants
from .constants import (
    FOLDER_ARCHIVED,
    FOLDER_BACKLOG,
    FOLDER_BLOCKED,
    FOLDER_DONE,
    FOLDER_IN_PROGRESS,
    FOLDER_TODO,
    STATUS_ABORTED,
    STATUS_BLOCKED,
    STATUS_DONE,
)

# Exceptions
from .exceptions import (
    FileOperationError,
    GitError,
    SprintLifecycleError,
    ValidationError,
)

# Epic operations
from .epic import (
    add_to_epic,
    archive_epic,
    complete_epic,
    create_epic,
    get_epic_status,
    list_epics,
    reset_epic,
    start_epic,
)

# Project operations
from .project import create_project

# Registry operations
from .registry import (
    check_epic_completion,
    get_next_epic_number,
    get_next_sprint_number,
    load_registry,
    register_new_epic,
    register_new_sprint,
    save_registry,
    update_registry,
)

# Sprint operations
from .sprint import (
    abort_sprint,
    advance_step,
    block_sprint,
    complete_sprint,
    create_sprint,
    generate_postmortem,
    get_sprint_status,
    move_to_done,
    recover_sprint,
    resume_sprint,
    start_sprint,
)

# Analysis
from .analysis import analyze_patterns, capture_baseline, compare_baseline

# Utilities
from .utils import (
    check_git_clean,
    create_git_tag,
    find_epic_folder,
    find_project_root,
    find_sprint_file,
    get_registry_path,
    get_sprints_dir,
    is_epic_sprint,
    update_yaml_frontmatter,
)

__version__ = "1.0.0"

__all__ = [
    # Analysis
    "analyze_patterns",
    "capture_baseline",
    "compare_baseline",
    # Constants
    "FOLDER_ARCHIVED",
    "FOLDER_BACKLOG",
    "FOLDER_BLOCKED",
    "FOLDER_DONE",
    "FOLDER_IN_PROGRESS",
    "FOLDER_TODO",
    "STATUS_ABORTED",
    "STATUS_BLOCKED",
    "STATUS_DONE",
    # Exceptions
    "FileOperationError",
    "GitError",
    "SprintLifecycleError",
    "ValidationError",
    # Epic operations
    "add_to_epic",
    "archive_epic",
    "complete_epic",
    "create_epic",
    "get_epic_status",
    "list_epics",
    "reset_epic",
    "start_epic",
    # Project operations
    "create_project",
    # Registry operations
    "check_epic_completion",
    "get_next_epic_number",
    "get_next_sprint_number",
    "load_registry",
    "register_new_epic",
    "register_new_sprint",
    "save_registry",
    "update_registry",
    # Sprint operations
    "abort_sprint",
    "advance_step",
    "block_sprint",
    "complete_sprint",
    "create_sprint",
    "generate_postmortem",
    "get_sprint_status",
    "move_to_done",
    "recover_sprint",
    "resume_sprint",
    "start_sprint",
    # Utilities
    "check_git_clean",
    "create_git_tag",
    "find_epic_folder",
    "find_project_root",
    "find_sprint_file",
    "get_registry_path",
    "get_sprints_dir",
    "is_epic_sprint",
    "update_yaml_frontmatter",
]
