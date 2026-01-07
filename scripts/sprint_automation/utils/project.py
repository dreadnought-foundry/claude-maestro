"""
Project-level utility functions for sprint automation.

Provides functions for finding sprint files, checking epic membership,
and other project-level operations.
"""

import re
from pathlib import Path
from typing import Optional, Tuple

from ..constants import POSTMORTEM_SUFFIX


def find_sprint_file(sprint_num: int, project_root: Path) -> Optional[Path]:
    """
    Find sprint file by number in any status directory.

    Args:
        sprint_num: Sprint number to find
        project_root: Project root path

    Returns:
        Path to sprint file if found, None otherwise

    Example:
        >>> find_sprint_file(2, Path("/project"))
        Path("/project/docs/sprints/2-in-progress/sprint-02_title.md")
    """
    sprints_dir = project_root / "docs" / "sprints"
    pattern = f"sprint-{sprint_num:02d}_*"

    # Search in all status directories and epic folders
    for status_dir in sprints_dir.glob("*"):
        if not status_dir.is_dir():
            continue

        # Check direct children (standalone sprints)
        for sprint_file in status_dir.glob(f"{pattern}.md"):
            # Exclude postmortem files
            if POSTMORTEM_SUFFIX not in sprint_file.name:
                return sprint_file

        # Check in epic folders (sprints may be in subdirectories)
        for sprint_file in status_dir.glob(f"**/{pattern}.md"):
            # Exclude postmortem files
            if POSTMORTEM_SUFFIX not in sprint_file.name:
                return sprint_file

    return None


def is_epic_sprint(sprint_path: Path) -> Tuple[bool, Optional[int]]:
    """
    Check if sprint is part of an epic.

    Args:
        sprint_path: Path to sprint file

    Returns:
        Tuple of (is_epic, epic_number)

    Example:
        >>> is_epic_sprint(Path("docs/sprints/2-in-progress/epic-01_name/sprint-02_title.md"))
        (True, 1)
    """
    # Check if path contains epic-NN_ pattern
    for part in sprint_path.parts:
        match = re.match(r"epic-(\d+)_", part)
        if match:
            return True, int(match.group(1))

    return False, None


def find_epic_folder(epic_num: int, project_root: Path) -> Optional[Path]:
    """
    Find epic folder by number in any status directory.

    Args:
        epic_num: Epic number to find
        project_root: Project root path

    Returns:
        Path to epic folder if found, None otherwise

    Example:
        >>> find_epic_folder(1, Path("/project"))
        Path("/project/docs/sprints/2-in-progress/epic-01_name")
    """
    sprints_dir = project_root / "docs" / "sprints"
    pattern = f"epic-{epic_num:02d}_*"

    # Search in all status directories
    for status_dir in sprints_dir.glob("*"):
        if not status_dir.is_dir():
            continue

        # Check for epic folder
        for epic_folder in status_dir.glob(pattern):
            if epic_folder.is_dir():
                return epic_folder

    return None


def get_sprints_dir(project_root: Path) -> Path:
    """
    Get the sprints directory for a project.

    Args:
        project_root: Project root path

    Returns:
        Path to sprints directory
    """
    return project_root / "docs" / "sprints"


def get_registry_path(project_root: Path) -> Path:
    """
    Get the registry file path for a project.

    Args:
        project_root: Project root path

    Returns:
        Path to registry.json
    """
    return project_root / "docs" / "sprints" / "registry.json"
