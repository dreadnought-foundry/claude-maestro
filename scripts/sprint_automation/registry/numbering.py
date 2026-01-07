"""
Auto-numbering for sprints and epics.

Manages automatic assignment of sprint and epic numbers
through the registry counter system.
"""

import json
from datetime import datetime
from typing import Optional

from ..exceptions import FileOperationError
from ..utils.file_ops import (
    backup_file,
    cleanup_backup,
    restore_file,
    find_project_root,
)
from ..utils.project import get_registry_path
from .manager import load_registry, save_registry


def get_next_sprint_number(dry_run: bool = False) -> int:
    """
    Get next available sprint number and increment counter in registry.

    Args:
        dry_run: If True, return next number without incrementing

    Returns:
        Next sprint number

    Example:
        >>> next_num = get_next_sprint_number()
        >>> print(next_num)
        6
    """
    project_root = find_project_root()
    registry = load_registry(project_root)

    next_num = registry.get("nextSprintNumber", 1)

    if dry_run:
        print(f"[DRY RUN] Next sprint number: {next_num}")
        print(f"[DRY RUN] Would increment to: {next_num + 1}")
        return next_num

    # Increment counter
    registry["nextSprintNumber"] = next_num + 1

    # Save registry
    save_registry(project_root, registry)

    return next_num


def get_next_epic_number(dry_run: bool = False) -> int:
    """
    Get next available epic number and increment counter in registry.

    Args:
        dry_run: If True, return next number without incrementing

    Returns:
        Next epic number

    Example:
        >>> next_num = get_next_epic_number()
        >>> print(next_num)
        2
    """
    project_root = find_project_root()
    registry = load_registry(project_root)

    next_num = registry.get("nextEpicNumber", 1)

    if dry_run:
        print(f"[DRY RUN] Next epic number: {next_num}")
        print(f"[DRY RUN] Would increment to: {next_num + 1}")
        return next_num

    # Increment counter
    registry["nextEpicNumber"] = next_num + 1

    # Save registry
    save_registry(project_root, registry)

    return next_num


def register_new_sprint(
    title: str, epic: Optional[int] = None, dry_run: bool = False, **metadata
) -> int:
    """
    Register a new sprint in registry with auto-assigned number.

    Args:
        title: Sprint title
        epic: Optional epic number this sprint belongs to
        dry_run: If True, show what would be registered
        **metadata: Additional metadata (estimatedHours, created, etc.)

    Returns:
        Assigned sprint number

    Example:
        >>> sprint_num = register_new_sprint("User Authentication", epic=2, estimatedHours=5)
        >>> print(sprint_num)
        6
    """
    # Get next sprint number
    sprint_num = get_next_sprint_number(dry_run=dry_run)

    if dry_run:
        print(f"[DRY RUN] Would register sprint {sprint_num}:")
        print(f"  title: {title}")
        print(f"  epic: {epic}")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        return sprint_num

    project_root = find_project_root()
    registry_path = get_registry_path(project_root)

    # Load registry
    with open(registry_path) as f:
        registry = json.load(f)

    # Ensure structure exists
    if "sprints" not in registry:
        registry["sprints"] = {}

    # Register sprint
    sprint_key = str(sprint_num)
    registry["sprints"][sprint_key] = {
        "title": title,
        "status": "planning",
        "epic": epic,
        "created": datetime.now().strftime("%Y-%m-%d"),
        "started": None,
        "completed": None,
        "hours": None,
        **metadata,
    }

    # Save registry
    backup = backup_file(registry_path)

    try:
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)

        cleanup_backup(backup)

        return sprint_num

    except Exception as e:
        restore_file(backup)
        raise FileOperationError(f"Failed to register sprint: {e}") from e


def register_new_epic(
    title: str, sprint_count: int = 0, dry_run: bool = False, **metadata
) -> int:
    """
    Register a new epic in registry with auto-assigned number.

    Args:
        title: Epic title
        sprint_count: Number of sprints planned for this epic
        dry_run: If True, show what would be registered
        **metadata: Additional metadata (estimatedHours, etc.)

    Returns:
        Assigned epic number

    Example:
        >>> epic_num = register_new_epic("User Management", sprint_count=5, estimatedHours=25)
        >>> print(epic_num)
        2
    """
    # Get next epic number
    epic_num = get_next_epic_number(dry_run=dry_run)

    if dry_run:
        print(f"[DRY RUN] Would register epic {epic_num}:")
        print(f"  title: {title}")
        print(f"  sprint_count: {sprint_count}")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        return epic_num

    project_root = find_project_root()
    registry_path = get_registry_path(project_root)

    # Load registry
    with open(registry_path) as f:
        registry = json.load(f)

    # Ensure structure exists
    if "epics" not in registry:
        registry["epics"] = {}

    # Register epic
    epic_key = str(epic_num)
    registry["epics"][epic_key] = {
        "title": title,
        "status": "planning",
        "created": datetime.now().strftime("%Y-%m-%d"),
        "started": None,
        "completed": None,
        "totalSprints": sprint_count,
        "completedSprints": 0,
        **metadata,
    }

    # Save registry
    backup = backup_file(registry_path)

    try:
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)

        cleanup_backup(backup)

        return epic_num

    except Exception as e:
        restore_file(backup)
        raise FileOperationError(f"Failed to register epic: {e}") from e
