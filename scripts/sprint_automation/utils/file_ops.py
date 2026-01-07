"""
File operation utilities for sprint automation.

Provides safe file operations with backup/restore capabilities
and YAML frontmatter manipulation.
"""

import json
import shutil
from pathlib import Path

from ..exceptions import FileOperationError, ValidationError


def find_project_root() -> Path:
    """
    Find project root by walking up directory tree to find .claude/ directory.

    Returns:
        Path: Absolute path to project root

    Raises:
        FileOperationError: If project root cannot be found

    Example:
        >>> root = find_project_root()
        >>> print(root)
        /Users/name/project
    """
    current = Path.cwd().resolve()

    # Walk up directory tree
    for parent in [current] + list(current.parents):
        if (parent / ".claude").exists():
            return parent

    raise FileOperationError(
        "Could not find project root. Expected .claude/ directory. "
        "Are you in a Claude Code project?"
    )


def backup_file(file_path: Path) -> Path:
    """
    Create backup of file before modification.

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file
    """
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    shutil.copy2(file_path, backup_path)
    return backup_path


def restore_file(backup_path: Path) -> None:
    """
    Restore file from backup.

    Args:
        backup_path: Path to backup file
    """
    original_path = Path(str(backup_path).replace(".bak", ""))
    shutil.move(backup_path, original_path)


def cleanup_backup(backup_path: Path) -> None:
    """
    Remove backup file after successful operation.

    Args:
        backup_path: Path to backup file
    """
    if backup_path.exists():
        backup_path.unlink()


def update_yaml_frontmatter(file_path: Path, updates: dict) -> None:
    """
    Update YAML frontmatter in markdown file.

    Args:
        file_path: Path to markdown file
        updates: Dict of frontmatter keys to update

    Example:
        >>> update_yaml_frontmatter(path, {"status": "done", "completed": "2025-12-30"})
    """
    with open(file_path, "r") as f:
        content = f.read()

    # Parse frontmatter
    if not content.startswith("---\n"):
        raise ValidationError(f"File {file_path} missing YAML frontmatter")

    parts = content.split("---\n", 2)
    if len(parts) < 3:
        raise ValidationError(f"File {file_path} has malformed YAML frontmatter")

    frontmatter = parts[1]
    body = parts[2]

    # Update frontmatter lines
    lines = frontmatter.split("\n")
    updated_keys = set()

    for i, line in enumerate(lines):
        for key, value in updates.items():
            if line.startswith(f"{key}:"):
                if value is None:
                    lines[i] = f"{key}: null"
                elif isinstance(value, str):
                    lines[i] = f"{key}: {value}"
                else:
                    lines[i] = f"{key}: {json.dumps(value)}"
                updated_keys.add(key)

    # Add missing keys
    for key, value in updates.items():
        if key not in updated_keys:
            if value is None:
                lines.append(f"{key}: null")
            elif isinstance(value, str):
                lines.append(f"{key}: {value}")
            else:
                lines.append(f"{key}: {json.dumps(value)}")

    # Reconstruct file
    new_content = f"---\n{chr(10).join(lines)}\n---\n{body}"

    with open(file_path, "w") as f:
        f.write(new_content)
