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
from .unified_state import (
    UNIFIED_STATE_VERSION,
    STATE_FILE_NAME,
    find_project_root as find_project_root_unified,
    get_state_path,
    load_state as load_unified_state,
    save_state as save_unified_state,
    get_task,
    upsert_task,
    delete_task,
    get_tasks_by_pipeline,
    get_active_tasks,
    create_maestro_task,
    create_autonomous_task,
    update_maestro_progress,
    update_autonomous_progress,
    complete_task,
    fail_task,
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
    # unified_state
    "UNIFIED_STATE_VERSION",
    "STATE_FILE_NAME",
    "find_project_root_unified",
    "get_state_path",
    "load_unified_state",
    "save_unified_state",
    "get_task",
    "upsert_task",
    "delete_task",
    "get_tasks_by_pipeline",
    "get_active_tasks",
    "create_maestro_task",
    "create_autonomous_task",
    "update_maestro_progress",
    "update_autonomous_progress",
    "complete_task",
    "fail_task",
]
