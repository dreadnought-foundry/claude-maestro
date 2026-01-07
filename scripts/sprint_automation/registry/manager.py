"""
Registry management for sprint automation.

Provides functions for updating sprint registry entries and
checking epic completion status.
"""

import json
from pathlib import Path
from typing import Tuple

from ..constants import STATUS_DONE, STATUS_ABORTED
from ..exceptions import FileOperationError
from ..utils.file_ops import (
    backup_file,
    cleanup_backup,
    restore_file,
    find_project_root,
)
from ..utils.project import get_registry_path


def load_registry(project_root: Path) -> dict:
    """
    Load registry from file or create empty structure.

    Args:
        project_root: Project root path

    Returns:
        Registry dictionary
    """
    registry_path = get_registry_path(project_root)

    if not registry_path.exists():
        return {"version": "1.0", "sprints": {}, "epics": {}}

    with open(registry_path) as f:
        return json.load(f)


def save_registry(project_root: Path, registry: dict) -> None:
    """
    Save registry to file with backup.

    Args:
        project_root: Project root path
        registry: Registry dictionary to save

    Raises:
        FileOperationError: If save fails
    """
    registry_path = get_registry_path(project_root)
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    backup = None
    if registry_path.exists():
        backup = backup_file(registry_path)

    try:
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)

        if backup:
            cleanup_backup(backup)

    except Exception as e:
        if backup:
            restore_file(backup)
        raise FileOperationError(f"Failed to save registry: {e}") from e


def update_registry(
    sprint_num: int, status: str, dry_run: bool = False, **metadata
) -> None:
    """
    Update sprint registry with completion metadata.

    Args:
        sprint_num: Sprint number to update
        status: New status (typically 'done')
        dry_run: If True, only show what would be updated
        **metadata: Additional fields to update (completed, hours, etc.)

    Raises:
        FileOperationError: If registry update fails

    Example:
        >>> update_registry(2, status='done', completed='2025-12-30', hours=6)
    """
    project_root = find_project_root()

    # Load or create registry
    registry = load_registry(project_root)

    # Ensure structure exists
    if "sprints" not in registry:
        registry["sprints"] = {}

    sprint_key = str(sprint_num)

    if dry_run:
        epic_num = registry.get("sprints", {}).get(sprint_key, {}).get("epic")

        print(f"[DRY RUN] Would update registry for sprint {sprint_num}:")
        print(f"  status: {status}")
        for key, value in metadata.items():
            print(f"  {key}: {value}")

        if status == "done" and epic_num:
            print(f"  Would also increment Epic {epic_num} completedSprints count")

        return

    # Update sprint entry
    if sprint_key not in registry["sprints"]:
        registry["sprints"][sprint_key] = {}

    registry["sprints"][sprint_key]["status"] = status
    registry["sprints"][sprint_key].update(metadata)

    # If sprint is part of an epic and being marked done, update epic's completedSprints count
    if status == "done" and "epics" in registry:
        epic_num = registry["sprints"][sprint_key].get("epic")
        if epic_num:
            epic_key = str(epic_num)
            if epic_key in registry["epics"]:
                # Increment completed sprints count
                current_count = registry["epics"][epic_key].get("completedSprints", 0)
                registry["epics"][epic_key]["completedSprints"] = current_count + 1

    # Save registry
    save_registry(project_root, registry)


def check_epic_completion(epic_num: int) -> Tuple[bool, str]:
    """
    Check if epic is ready to be completed (all sprints finished).

    Args:
        epic_num: Epic number to check

    Returns:
        Tuple of (is_complete, message)
        - is_complete: True if all sprints are done or aborted
        - message: Status message for user

    Example:
        >>> is_complete, msg = check_epic_completion(1)
        >>> if is_complete:
        >>>     print(f"Epic ready! {msg}")
    """
    project_root = find_project_root()
    sprints_dir = project_root / "docs" / "sprints"

    # Find epic folder
    epic_pattern = f"epic-{epic_num:02d}_*"
    epic_folder = None

    for status_dir in sprints_dir.glob("*"):
        if not status_dir.is_dir():
            continue
        for folder in status_dir.glob(epic_pattern):
            if folder.is_dir():
                epic_folder = folder
                break
        if epic_folder:
            break

    if not epic_folder:
        return False, f"Epic {epic_num} not found"

    # List all sprint files in epic folder (may be in subdirectories)
    sprint_files = list(epic_folder.glob("sprint-*/*.md")) + list(
        epic_folder.glob("sprint-*.md")
    )

    if not sprint_files:
        return False, f"Epic {epic_num} has no sprint files"

    # Count by status
    done_count = 0
    aborted_count = 0
    active_sprints = []

    for sprint_file in sprint_files:
        # Check both file name and parent directory for --done/--aborted suffix
        file_name = sprint_file.name
        dir_name = sprint_file.parent.name

        if STATUS_DONE in file_name or STATUS_DONE in dir_name:
            done_count += 1
        elif STATUS_ABORTED in file_name or STATUS_ABORTED in dir_name:
            aborted_count += 1
        else:
            active_sprints.append(
                f"{dir_name}/{file_name}"
                if dir_name.startswith("sprint-")
                else file_name
            )

    total = len(sprint_files)
    finished = done_count + aborted_count

    if finished == total:
        return True, (
            f"Epic {epic_num} is complete!\n"
            f"  Total sprints: {total}\n"
            f"  Done: {done_count}\n"
            f"  Aborted: {aborted_count}\n\n"
            f"Run: /epic-complete {epic_num}"
        )
    else:
        return False, (
            f"Epic {epic_num} is not complete yet\n"
            f"  Total sprints: {total}\n"
            f"  Done: {done_count}\n"
            f"  Aborted: {aborted_count}\n"
            f"  Remaining: {len(active_sprints)}\n\n"
            f"Unfinished sprints:\n" + "\n".join(f"  - {s}" for s in active_sprints)
        )
