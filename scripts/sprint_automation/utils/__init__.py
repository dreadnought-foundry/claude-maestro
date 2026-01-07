"""
Utility functions for sprint automation.

This package provides common utilities for file operations,
git operations, state management, and project-level functions.
"""

from .file_ops import (
    backup_file,
    cleanup_backup,
    find_project_root,
    restore_file,
    update_yaml_frontmatter,
)
from .git_ops import check_git_clean, create_git_tag
from .project import (
    find_epic_folder,
    find_sprint_file,
    get_registry_path,
    get_sprints_dir,
    is_epic_sprint,
)
from .state import (
    create_state,
    delete_state,
    load_state,
    load_workflow_steps,
    save_state,
    state_exists,
    update_state,
)

__all__ = [
    # file_ops
    "backup_file",
    "cleanup_backup",
    "find_project_root",
    "restore_file",
    "update_yaml_frontmatter",
    # git_ops
    "check_git_clean",
    "create_git_tag",
    # project
    "find_epic_folder",
    "find_sprint_file",
    "get_registry_path",
    "get_sprints_dir",
    "is_epic_sprint",
    # state
    "create_state",
    "delete_state",
    "load_state",
    "load_workflow_steps",
    "save_state",
    "state_exists",
    "update_state",
]
