#!/usr/bin/env python3
"""
Sprint lifecycle automation utilities.

Automates sprint file movements, registry updates, git tagging, and epic completion detection
to eliminate manual overhead in sprint completion workflow.

Functions:
    find_project_root() -> Path: Locate project root containing .claude/
    move_to_done(sprint_num, dry_run=False) -> Path: Move sprint file to done with --done suffix
    update_registry(sprint_num, status, dry_run=False, **metadata) -> None: Update sprint registry
    check_epic_completion(epic_num) -> tuple[bool, str]: Detect if epic ready to complete
    create_git_tag(sprint_num, title, dry_run=False) -> None: Create and push git tag

Usage:
    python scripts/sprint_lifecycle.py --help

    # From Python code:
    from scripts.sprint_lifecycle import move_to_done, update_registry, create_git_tag

    new_path = move_to_done(2)
    update_registry(2, status='done', hours=6)
    create_git_tag(2, "Automated Lifecycle Management")
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


class SprintLifecycleError(Exception):
    """Base exception for sprint lifecycle operations."""
    pass


class GitError(SprintLifecycleError):
    """Git operation failed."""
    pass


class FileOperationError(SprintLifecycleError):
    """File operation failed."""
    pass


class ValidationError(SprintLifecycleError):
    """Validation check failed."""
    pass


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


def _backup_file(file_path: Path) -> Path:
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


def _restore_file(backup_path: Path) -> None:
    """
    Restore file from backup.

    Args:
        backup_path: Path to backup file
    """
    original_path = Path(str(backup_path).replace(".bak", ""))
    shutil.move(backup_path, original_path)


def _cleanup_backup(backup_path: Path) -> None:
    """
    Remove backup file after successful operation.

    Args:
        backup_path: Path to backup file
    """
    if backup_path.exists():
        backup_path.unlink()


def _find_sprint_file(sprint_num: int, project_root: Path) -> Optional[Path]:
    """
    Find sprint file by number in any status directory.

    Args:
        sprint_num: Sprint number to find
        project_root: Project root path

    Returns:
        Path to sprint file if found, None otherwise

    Example:
        >>> _find_sprint_file(2, Path("/project"))
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
            return sprint_file

        # Check in epic folders (sprints may be in subdirectories)
        for sprint_file in status_dir.glob(f"**/{pattern}.md"):
            return sprint_file

    return None


def _is_epic_sprint(sprint_path: Path) -> Tuple[bool, Optional[int]]:
    """
    Check if sprint is part of an epic.

    Args:
        sprint_path: Path to sprint file

    Returns:
        Tuple of (is_epic, epic_number)

    Example:
        >>> _is_epic_sprint(Path("docs/sprints/2-in-progress/epic-01_name/sprint-02_title.md"))
        (True, 1)
    """
    # Check if path contains epic-NN_ pattern
    for part in sprint_path.parts:
        match = re.match(r"epic-(\d+)_", part)
        if match:
            return True, int(match.group(1))

    return False, None


def _update_yaml_frontmatter(file_path: Path, updates: dict) -> None:
    """
    Update YAML frontmatter in markdown file.

    Args:
        file_path: Path to markdown file
        updates: Dict of frontmatter keys to update

    Example:
        >>> _update_yaml_frontmatter(path, {"status": "done", "completed": "2025-12-30"})
    """
    with open(file_path, 'r') as f:
        content = f.read()

    # Parse frontmatter
    if not content.startswith('---\n'):
        raise ValidationError(f"File {file_path} missing YAML frontmatter")

    parts = content.split('---\n', 2)
    if len(parts) < 3:
        raise ValidationError(f"File {file_path} has malformed YAML frontmatter")

    frontmatter = parts[1]
    body = parts[2]

    # Update frontmatter lines
    lines = frontmatter.split('\n')
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

    with open(file_path, 'w') as f:
        f.write(new_content)


def move_to_done(sprint_num: int, dry_run: bool = False) -> Path:
    """
    Move sprint file to done status with --done suffix.

    For epic sprints: Renames with --done suffix, keeps in epic folder
    For standalone sprints: Moves to 3-done/_standalone/ with --done suffix

    Updates YAML frontmatter: status=done, completed=timestamp

    Args:
        sprint_num: Sprint number to move
        dry_run: If True, only show what would happen without making changes

    Returns:
        Path to new location of sprint file

    Raises:
        FileOperationError: If sprint file not found or move fails
        ValidationError: If sprint already marked done

    Example:
        >>> new_path = move_to_done(2)
        >>> print(new_path)
        /project/docs/sprints/2-in-progress/epic-01_name/sprint-02_title--done.md
    """
    project_root = find_project_root()
    sprint_file = _find_sprint_file(sprint_num, project_root)

    if not sprint_file:
        raise FileOperationError(
            f"Sprint {sprint_num} not found in any status directory. "
            f"Searched in {project_root}/docs/sprints/"
        )

    # Check if already done
    if "--done" in sprint_file.name:
        raise ValidationError(
            f"Sprint {sprint_num} already marked as done: {sprint_file}"
        )

    is_epic, epic_num = _is_epic_sprint(sprint_file)

    if dry_run:
        if is_epic:
            if sprint_file.parent.name.startswith("sprint-"):
                # Sprint in subdirectory
                sprint_subdir = sprint_file.parent
                new_dir_name = sprint_subdir.name + "--done"
                new_name = sprint_file.name.replace(".md", "--done.md")
                print(f"[DRY RUN] Would rename epic sprint subdirectory and file:")
                print(f"  From: {sprint_file}")
                print(f"  Dir:  {sprint_subdir.name} → {new_dir_name}")
                print(f"  File: {sprint_file.name} → {new_name}")
                new_path = sprint_subdir.with_name(new_dir_name) / new_name
            else:
                # Sprint directly in epic folder
                new_name = sprint_file.name.replace(".md", "--done.md")
                new_path = sprint_file.with_name(new_name)
                print(f"[DRY RUN] Would rename epic sprint:")
                print(f"  From: {sprint_file}")
                print(f"  To:   {new_path}")
        else:
            standalone_dir = project_root / "docs" / "sprints" / "3-done" / "_standalone"
            new_name = sprint_file.name.replace(".md", "--done.md")
            new_path = standalone_dir / new_name
            print(f"[DRY RUN] Would move standalone sprint:")
            print(f"  From: {sprint_file}")
            print(f"  To:   {new_path}")
        return new_path

    # Backup original file
    backup = _backup_file(sprint_file)

    try:
        # Update YAML frontmatter
        _update_yaml_frontmatter(sprint_file, {
            "status": "done",
            "completed": datetime.now().strftime("%Y-%m-%d")
        })

        if is_epic:
            # Epic sprint: rename with --done suffix in place
            # If sprint is in a subdirectory (sprint-NN_name/sprint-NN_name.md),
            # move it up to the epic folder and rename the subdirectory
            if sprint_file.parent.name.startswith("sprint-"):
                # Sprint is in a subdirectory - move file up and rename dir
                sprint_subdir = sprint_file.parent
                new_name = sprint_file.name.replace(".md", "--done.md")
                new_dir_name = sprint_subdir.name + "--done"
                new_subdir = sprint_subdir.with_name(new_dir_name)

                # Rename the subdirectory
                sprint_subdir.rename(new_subdir)

                # Update path to new location
                new_path = new_subdir / sprint_file.name
                new_path_with_done = new_path.with_name(new_name)
                new_path.rename(new_path_with_done)
                new_path = new_path_with_done
            else:
                # Sprint is directly in epic folder
                new_name = sprint_file.name.replace(".md", "--done.md")
                new_path = sprint_file.with_name(new_name)
                sprint_file.rename(new_path)
        else:
            # Standalone sprint: move to 3-done/_standalone/
            standalone_dir = project_root / "docs" / "sprints" / "3-done" / "_standalone"
            standalone_dir.mkdir(parents=True, exist_ok=True)

            new_name = sprint_file.name.replace(".md", "--done.md")
            new_path = standalone_dir / new_name

            # Move file
            shutil.move(str(sprint_file), str(new_path))

        # Cleanup backup
        _cleanup_backup(backup)

        return new_path

    except Exception as e:
        # Restore from backup on failure
        _restore_file(backup)
        raise FileOperationError(f"Failed to move sprint {sprint_num}: {e}") from e


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
    registry_path = project_root / "docs" / "sprints" / "registry.json"

    # Load or create registry
    if registry_path.exists():
        with open(registry_path) as f:
            registry = json.load(f)
    else:
        registry = {"version": "1.0", "nextSprintNumber": 1, "nextEpicNumber": 1, "sprints": {}, "epics": {}}

    next_num = registry.get("nextSprintNumber", 1)

    if dry_run:
        print(f"[DRY RUN] Next sprint number: {next_num}")
        print(f"[DRY RUN] Would increment to: {next_num + 1}")
        return next_num

    # Increment counter
    registry["nextSprintNumber"] = next_num + 1

    # Save registry
    backup = None
    if registry_path.exists():
        backup = _backup_file(registry_path)

    try:
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        if backup:
            _cleanup_backup(backup)

        return next_num

    except Exception as e:
        if backup:
            _restore_file(backup)
        raise FileOperationError(f"Failed to update sprint counter: {e}") from e


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
    registry_path = project_root / "docs" / "sprints" / "registry.json"

    # Load or create registry
    if registry_path.exists():
        with open(registry_path) as f:
            registry = json.load(f)
    else:
        registry = {"version": "1.0", "nextSprintNumber": 1, "nextEpicNumber": 1, "sprints": {}, "epics": {}}

    next_num = registry.get("nextEpicNumber", 1)

    if dry_run:
        print(f"[DRY RUN] Next epic number: {next_num}")
        print(f"[DRY RUN] Would increment to: {next_num + 1}")
        return next_num

    # Increment counter
    registry["nextEpicNumber"] = next_num + 1

    # Save registry
    backup = None
    if registry_path.exists():
        backup = _backup_file(registry_path)

    try:
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        if backup:
            _cleanup_backup(backup)

        return next_num

    except Exception as e:
        if backup:
            _restore_file(backup)
        raise FileOperationError(f"Failed to update epic counter: {e}") from e


def register_new_sprint(title: str, epic: Optional[int] = None, dry_run: bool = False, **metadata) -> int:
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
    registry_path = project_root / "docs" / "sprints" / "registry.json"

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
        **metadata
    }

    # Save registry
    backup = _backup_file(registry_path)

    try:
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        _cleanup_backup(backup)

        return sprint_num

    except Exception as e:
        _restore_file(backup)
        raise FileOperationError(f"Failed to register sprint: {e}") from e


def register_new_epic(title: str, sprint_count: int = 0, dry_run: bool = False, **metadata) -> int:
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
    registry_path = project_root / "docs" / "sprints" / "registry.json"

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
        **metadata
    }

    # Save registry
    backup = _backup_file(registry_path)

    try:
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        _cleanup_backup(backup)

        return epic_num

    except Exception as e:
        _restore_file(backup)
        raise FileOperationError(f"Failed to register epic: {e}") from e


def update_registry(sprint_num: int, status: str, dry_run: bool = False, **metadata) -> None:
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
    registry_path = project_root / "docs" / "sprints" / "registry.json"

    # Create registry if doesn't exist
    if not registry_path.exists():
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry = {"version": "1.0", "sprints": {}, "epics": {}}
    else:
        with open(registry_path) as f:
            registry = json.load(f)

    # Ensure structure exists
    if "sprints" not in registry:
        registry["sprints"] = {}

    sprint_key = str(sprint_num)

    if dry_run:
        # Load registry to check epic membership for dry-run output
        if registry_path.exists():
            with open(registry_path) as f:
                registry = json.load(f)
            epic_num = registry.get("sprints", {}).get(sprint_key, {}).get("epic")
        else:
            epic_num = None

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

    # Backup and save
    backup = None
    if registry_path.exists():
        backup = _backup_file(registry_path)

    try:
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        if backup:
            _cleanup_backup(backup)

    except Exception as e:
        if backup:
            _restore_file(backup)
        raise FileOperationError(f"Failed to update registry: {e}") from e


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
    sprint_files = list(epic_folder.glob("sprint-*/*.md")) + list(epic_folder.glob("sprint-*.md"))

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

        if "--done" in file_name or "--done" in dir_name:
            done_count += 1
        elif "--aborted" in file_name or "--aborted" in dir_name:
            aborted_count += 1
        else:
            active_sprints.append(f"{dir_name}/{file_name}" if dir_name.startswith("sprint-") else file_name)

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


def check_git_clean() -> bool:
    """
    Check if git working directory is clean.

    Returns:
        True if working directory is clean, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        return len(result.stdout.strip()) == 0
    except subprocess.CalledProcessError:
        return False


def create_git_tag(sprint_num: int, title: str, dry_run: bool = False, auto_push: bool = True) -> None:
    """
    Create git tag for sprint completion and optionally push to remote.

    Tag format: sprint-{N}
    Message format: Sprint {N}: {title}

    Args:
        sprint_num: Sprint number
        title: Sprint title
        dry_run: If True, only show what would happen
        auto_push: If True, push tag to remote after creation

    Raises:
        GitError: If git operations fail
        ValidationError: If working tree is dirty

    Example:
        >>> create_git_tag(2, "Automated Lifecycle Management", auto_push=True)
    """
    # Validate git status
    if not check_git_clean():
        raise ValidationError(
            "Git working directory is dirty. Commit or stash changes before creating tag."
        )

    tag_name = f"sprint-{sprint_num}"
    tag_message = f"Sprint {sprint_num}: {title}"

    if dry_run:
        print(f"[DRY RUN] Would create git tag:")
        print(f"  Tag: {tag_name}")
        print(f"  Message: {tag_message}")
        if auto_push:
            print(f"  Auto-push: Yes (git push origin {tag_name})")
        return

    try:
        # Create annotated tag
        subprocess.run(
            ["git", "tag", "-a", tag_name, "-m", tag_message],
            check=True,
            capture_output=True,
            text=True
        )

        print(f"✓ Created git tag: {tag_name}")

        # Push tag if requested
        if auto_push:
            subprocess.run(
                ["git", "push", "origin", tag_name],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✓ Pushed tag to remote: {tag_name}")

    except subprocess.CalledProcessError as e:
        raise GitError(
            f"Failed to create/push git tag '{tag_name}': {e.stderr}"
        ) from e


def start_sprint(sprint_num: int, dry_run: bool = False) -> dict:
    """
    Start a sprint: move to in-progress, create state file, update YAML.

    Args:
        sprint_num: Sprint number to start
        dry_run: If True, preview changes without executing

    Returns:
        Dict with start summary

    Raises:
        FileOperationError: If sprint file not found
        ValidationError: If sprint already started or in wrong state

    Example:
        >>> summary = start_sprint(3)
        >>> print(summary['status'])  # 'started'
    """
    project_root = find_project_root()

    # Find sprint in backlog or todo
    sprint_file = None
    for folder in ["0-backlog", "1-todo"]:
        search_path = project_root / "docs" / "sprints" / folder
        if search_path.exists():
            found = list(search_path.glob(f"**/sprint-{sprint_num:02d}_*.md"))
            if found:
                sprint_file = found[0]
                break

    if not sprint_file:
        raise FileOperationError(
            f"Sprint {sprint_num} not found in backlog or todo folders"
        )

    # Check if sprint is in an epic
    is_epic, epic_num = _is_epic_sprint(sprint_file)

    # Read YAML frontmatter
    with open(sprint_file) as f:
        content = f.read()

    import re
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not yaml_match:
        raise ValidationError(f"Sprint {sprint_num} missing YAML frontmatter")

    yaml_content = yaml_match.group(1)
    title_match = re.search(r'^title:\s*(.+)$', yaml_content, re.MULTILINE)

    if not title_match:
        raise ValidationError(f"Sprint {sprint_num} missing title")

    title = title_match.group(1).strip().strip('"')

    if dry_run:
        print(f"[DRY RUN] Would start sprint {sprint_num}:")
        print(f"  Title: {title}")
        print(f"  Epic: {epic_num if is_epic else 'standalone'}")
        print(f"  1. Move to 2-in-progress/")
        print(f"  2. Update YAML (status=in-progress, started=<now>)")
        print(f"  3. Create state file .claude/sprint-{sprint_num}-state.json")
        return {"status": "dry-run", "sprint_num": sprint_num}

    # Move to in-progress
    in_progress_dir = project_root / "docs" / "sprints" / "2-in-progress"
    in_progress_dir.mkdir(parents=True, exist_ok=True)

    if is_epic:
        # Keep in epic folder structure
        epic_folder_name = sprint_file.parent.name if "epic-" in sprint_file.parent.name else sprint_file.parent.parent.name
        new_parent = in_progress_dir / epic_folder_name
        new_parent.mkdir(parents=True, exist_ok=True)

        if sprint_file.parent.name.startswith("sprint-"):
            # Sprint in subdirectory
            new_sprint_dir = new_parent / sprint_file.parent.name
            new_sprint_dir.mkdir(parents=True, exist_ok=True)
            new_path = new_sprint_dir / sprint_file.name
        else:
            new_path = new_parent / sprint_file.name
    else:
        # Standalone sprint
        new_path = in_progress_dir / sprint_file.name

    # Update YAML frontmatter
    started_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    _update_yaml_frontmatter(sprint_file, {
        "status": "in-progress",
        "started": started_time
    })

    # Move file
    shutil.move(str(sprint_file), str(new_path))
    print(f"✓ Moved to: {new_path}")

    # Create state file
    state_file = project_root / ".claude" / f"sprint-{sprint_num}-state.json"
    state = {
        "sprint_number": sprint_num,
        "sprint_file": str(new_path.relative_to(project_root)),
        "sprint_title": title,
        "status": "in_progress",
        "current_phase": 1,
        "current_step": "1.1",
        "started_at": started_time,
        "workflow_version": "3.0",
        "completed_steps": []
    }

    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"✓ State file created: {state_file.name}")

    summary = {
        "status": "started",
        "sprint_num": sprint_num,
        "title": title,
        "file_path": str(new_path),
        "epic": epic_num if is_epic else None
    }

    print(f"\n{'='*60}")
    print(f"Sprint {sprint_num}: {title} - STARTED ✓")
    print(f"{'='*60}")
    print(f"File: {new_path.relative_to(project_root)}")
    if is_epic:
        print(f"Epic: {epic_num}")
    print(f"Next: Begin Phase 1 (Planning)")
    print(f"{'='*60}")

    return summary


def abort_sprint(sprint_num: int, reason: str, dry_run: bool = False) -> dict:
    """
    Abort a sprint: rename with --aborted suffix, update state.

    Args:
        sprint_num: Sprint number to abort
        reason: Reason for aborting
        dry_run: If True, preview changes without executing

    Returns:
        Dict with abort summary

    Raises:
        FileOperationError: If sprint file not found
        ValidationError: If sprint already aborted

    Example:
        >>> summary = abort_sprint(4, "Requirements changed")
        >>> print(summary['status'])  # 'aborted'
    """
    project_root = find_project_root()
    sprint_file = _find_sprint_file(sprint_num, project_root)

    if not sprint_file:
        raise FileOperationError(
            f"Sprint {sprint_num} not found"
        )

    # Check if already aborted
    if "--aborted" in sprint_file.name:
        raise ValidationError(
            f"Sprint {sprint_num} already aborted: {sprint_file}"
        )

    # Read YAML for metadata
    with open(sprint_file) as f:
        content = f.read()

    import re
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not yaml_match:
        raise ValidationError(f"Sprint {sprint_num} missing YAML frontmatter")

    yaml_content = yaml_match.group(1)
    title_match = re.search(r'^title:\s*(.+)$', yaml_content, re.MULTILINE)
    started_match = re.search(r'^started:\s*(.+)$', yaml_content, re.MULTILINE)

    title = title_match.group(1).strip().strip('"') if title_match else "Unknown"

    # Calculate hours if started
    hours = None
    if started_match:
        started_str = started_match.group(1).strip()
        # Only calculate hours if started is not null
        if started_str and started_str.lower() != 'null':
            started = datetime.fromisoformat(started_str.replace('Z', '+00:00'))
            aborted = datetime.now().astimezone()
            hours = round((aborted - started).total_seconds() / 3600, 1)

    if dry_run:
        print(f"[DRY RUN] Would abort sprint {sprint_num}:")
        print(f"  Title: {title}")
        print(f"  Reason: {reason}")
        print(f"  Hours: {hours if hours else 'N/A'}")
        print(f"  1. Update YAML (status=aborted, reason, hours)")
        print(f"  2. Rename with --aborted suffix")
        print(f"  3. Update state file")
        return {"status": "dry-run", "sprint_num": sprint_num}

    # Update YAML frontmatter
    aborted_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    updates = {
        "status": "aborted",
        "aborted_at": aborted_time,
        "abort_reason": reason
    }
    if hours:
        updates["hours"] = hours

    _update_yaml_frontmatter(sprint_file, updates)

    # Rename with --aborted suffix
    if sprint_file.parent.name.startswith("sprint-"):
        # Sprint in subdirectory
        sprint_subdir = sprint_file.parent
        new_dir_name = sprint_subdir.name + "--aborted"
        new_subdir = sprint_subdir.with_name(new_dir_name)
        sprint_subdir.rename(new_subdir)

        new_name = sprint_file.name.replace(".md", "--aborted.md")
        new_path = new_subdir / new_name
        (new_subdir / sprint_file.name).rename(new_path)
    else:
        # Sprint file directly in folder
        new_name = sprint_file.name.replace(".md", "--aborted.md")
        new_path = sprint_file.with_name(new_name)
        sprint_file.rename(new_path)

    print(f"✓ Renamed to: {new_path.name}")

    # Update state file
    state_file = project_root / ".claude" / f"sprint-{sprint_num}-state.json"
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        state["status"] = "aborted"
        state["aborted_at"] = aborted_time
        state["abort_reason"] = reason
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"✓ State file updated")

    # Update registry
    update_registry(sprint_num, status="aborted", abort_reason=reason, hours=hours if hours else 0)
    print(f"✓ Registry updated")

    summary = {
        "status": "aborted",
        "sprint_num": sprint_num,
        "title": title,
        "reason": reason,
        "hours": hours,
        "file_path": str(new_path)
    }

    print(f"\n{'='*60}")
    print(f"Sprint {sprint_num}: {title} - ABORTED")
    print(f"{'='*60}")
    print(f"Reason: {reason}")
    print(f"Hours before abort: {hours if hours else 'N/A'}")
    print(f"File: {new_path.name}")
    print(f"{'='*60}")

    return summary


def start_epic(epic_num: int, dry_run: bool = False) -> dict:
    """
    Start an epic: move from backlog/todo to in-progress, update YAML.

    Args:
        epic_num: Epic number to start
        dry_run: If True, preview changes without executing

    Returns:
        Dict with start summary

    Raises:
        FileOperationError: If epic folder not found
        ValidationError: If epic already started

    Example:
        >>> summary = start_epic(3)
        >>> print(summary['status'])  # 'started'
    """
    project_root = find_project_root()

    # Find epic in backlog or todo
    epic_folder = None
    epic_num_str = f"{epic_num:02d}"

    for folder in ["0-backlog", "1-todo"]:
        search_path = project_root / "docs" / "sprints" / folder
        if search_path.exists():
            found = list(search_path.glob(f"epic-{epic_num_str}_*"))
            if found and found[0].is_dir():
                epic_folder = found[0]
                break

    if not epic_folder:
        raise FileOperationError(
            f"Epic {epic_num} not found in backlog or todo folders"
        )

    # Find _epic.md file
    epic_file = epic_folder / "_epic.md"
    if not epic_file.exists():
        raise FileOperationError(
            f"Epic {epic_num} missing _epic.md file"
        )

    # Read title from YAML
    with open(epic_file) as f:
        content = f.read()

    import re
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not yaml_match:
        raise ValidationError(f"Epic {epic_num} missing YAML frontmatter")

    yaml_content = yaml_match.group(1)
    title_match = re.search(r'^title:\s*(.+)$', yaml_content, re.MULTILINE)
    title = title_match.group(1).strip().strip('"') if title_match else "Unknown"

    # Count sprints in epic
    sprint_files = list(epic_folder.glob("**/sprint-*.md"))
    sprint_count = len(sprint_files)

    if dry_run:
        print(f"[DRY RUN] Would start epic {epic_num}:")
        print(f"  Title: {title}")
        print(f"  Sprints: {sprint_count}")
        print(f"  1. Move to 2-in-progress/")
        print(f"  2. Update YAML (status=in-progress, started=<now>)")
        return {"status": "dry-run", "epic_num": epic_num}

    # Move to in-progress
    in_progress_dir = project_root / "docs" / "sprints" / "2-in-progress"
    in_progress_dir.mkdir(parents=True, exist_ok=True)

    new_epic_folder = in_progress_dir / epic_folder.name
    epic_folder.rename(new_epic_folder)

    # Update YAML frontmatter
    epic_file = new_epic_folder / "_epic.md"
    started_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    _update_yaml_frontmatter(epic_file, {
        "status": "in-progress",
        "started": started_time
    })

    summary = {
        "epic_num": epic_num,
        "title": title,
        "status": "started",
        "sprint_count": sprint_count,
        "new_path": str(new_epic_folder)
    }

    print(f"\n{'='*60}")
    print(f"Epic {epic_num}: {title} - STARTED")
    print(f"{'='*60}")
    print(f"Location: {new_epic_folder}")
    print(f"Sprints: {sprint_count}")
    print(f"{'='*60}")

    return summary


def complete_epic(epic_num: int, dry_run: bool = False) -> dict:
    """
    Complete an epic: verify all sprints done/aborted, move to done, calculate stats.

    Args:
        epic_num: Epic number to complete
        dry_run: If True, preview changes without executing

    Returns:
        Dict with completion summary

    Raises:
        FileOperationError: If epic folder not found
        ValidationError: If epic has unfinished sprints

    Example:
        >>> summary = complete_epic(3)
        >>> print(summary['total_hours'])  # 42.5
    """
    project_root = find_project_root()
    epic_num_str = f"{epic_num:02d}"

    # Find epic in in-progress
    in_progress_dir = project_root / "docs" / "sprints" / "2-in-progress"
    found = list(in_progress_dir.glob(f"epic-{epic_num_str}_*"))

    if not found or not found[0].is_dir():
        raise FileOperationError(
            f"Epic {epic_num} not found in in-progress folder"
        )

    epic_folder = found[0]
    epic_file = epic_folder / "_epic.md"

    if not epic_file.exists():
        raise FileOperationError(
            f"Epic {epic_num} missing _epic.md file"
        )

    # Read title from YAML
    with open(epic_file) as f:
        content = f.read()

    import re
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not yaml_match:
        raise ValidationError(f"Epic {epic_num} missing YAML frontmatter")

    yaml_content = yaml_match.group(1)
    title_match = re.search(r'^title:\s*(.+)$', yaml_content, re.MULTILINE)
    title = title_match.group(1).strip().strip('"') if title_match else "Unknown"

    # Check all sprints are finished
    sprint_files = list(epic_folder.glob("**/sprint-*.md"))
    done_sprints = []
    aborted_sprints = []
    unfinished_sprints = []
    blocked_sprints = []

    for sprint_file in sprint_files:
        name = sprint_file.name
        if "--done" in name:
            done_sprints.append(name)
        elif "--aborted" in name:
            aborted_sprints.append(name)
        elif "--blocked" in name:
            blocked_sprints.append(name)
        else:
            unfinished_sprints.append(name)

    if unfinished_sprints or blocked_sprints:
        error_msg = f"Cannot complete epic {epic_num} - has unfinished sprints:\n"
        if unfinished_sprints:
            error_msg += "\nIn Progress/Pending:\n"
            for sprint in unfinished_sprints:
                error_msg += f"  - {sprint}\n"
        if blocked_sprints:
            error_msg += "\nBlocked:\n"
            for sprint in blocked_sprints:
                error_msg += f"  - {sprint}\n"
        raise ValidationError(error_msg.strip())

    # Calculate total hours
    total_hours = 0.0
    for sprint_file in sprint_files:
        with open(sprint_file) as f:
            sprint_content = f.read()
        yaml_match = re.search(r'^---\n(.*?)\n---', sprint_content, re.DOTALL)
        if yaml_match:
            hours_match = re.search(r'^hours:\s*([0-9.]+)', yaml_match.group(1), re.MULTILINE)
            if hours_match:
                total_hours += float(hours_match.group(1))

    if dry_run:
        print(f"[DRY RUN] Would complete epic {epic_num}:")
        print(f"  Title: {title}")
        print(f"  Done: {len(done_sprints)}")
        print(f"  Aborted: {len(aborted_sprints)}")
        print(f"  Total hours: {total_hours:.1f}")
        print(f"  1. Move to 3-done/")
        print(f"  2. Update YAML (status=done, completed=<now>, total_hours)")
        return {"status": "dry-run", "epic_num": epic_num}

    # Move to done
    done_dir = project_root / "docs" / "sprints" / "3-done"
    done_dir.mkdir(parents=True, exist_ok=True)

    new_epic_folder = done_dir / epic_folder.name
    epic_folder.rename(new_epic_folder)

    # Update YAML frontmatter
    epic_file = new_epic_folder / "_epic.md"
    completed_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    _update_yaml_frontmatter(epic_file, {
        "status": "done",
        "completed": completed_time,
        "total_hours": total_hours
    })

    summary = {
        "epic_num": epic_num,
        "title": title,
        "status": "done",
        "done_count": len(done_sprints),
        "aborted_count": len(aborted_sprints),
        "total_hours": total_hours,
        "new_path": str(new_epic_folder)
    }

    print(f"\n{'='*60}")
    print(f"Epic {epic_num}: {title} - COMPLETE")
    print(f"{'='*60}")
    print(f"Location: {new_epic_folder}")
    print(f"Sprints completed: {len(done_sprints)}")
    print(f"Sprints aborted: {len(aborted_sprints)}")
    print(f"Total hours: {total_hours:.1f}")
    print(f"{'='*60}")

    return summary


def archive_epic(epic_num: int, dry_run: bool = False) -> dict:
    """
    Archive an epic: move from done to archived, update YAML.

    Args:
        epic_num: Epic number to archive
        dry_run: If True, preview changes without executing

    Returns:
        Dict with archive summary

    Raises:
        FileOperationError: If epic folder not found in done
        ValidationError: If epic not yet complete

    Example:
        >>> summary = archive_epic(3)
        >>> print(summary['status'])  # 'archived'
    """
    project_root = find_project_root()
    epic_num_str = f"{epic_num:02d}"

    # Find epic in done
    done_dir = project_root / "docs" / "sprints" / "3-done"
    found = list(done_dir.glob(f"epic-{epic_num_str}_*"))

    if not found or not found[0].is_dir():
        raise FileOperationError(
            f"Epic {epic_num} not found in done folder. Complete it first with /epic-complete"
        )

    epic_folder = found[0]
    epic_file = epic_folder / "_epic.md"

    if not epic_file.exists():
        raise FileOperationError(
            f"Epic {epic_num} missing _epic.md file"
        )

    # Read title from YAML
    with open(epic_file) as f:
        content = f.read()

    import re
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not yaml_match:
        raise ValidationError(f"Epic {epic_num} missing YAML frontmatter")

    yaml_content = yaml_match.group(1)
    title_match = re.search(r'^title:\s*(.+)$', yaml_content, re.MULTILINE)
    title = title_match.group(1).strip().strip('"') if title_match else "Unknown"

    # Count sprint files
    sprint_files = list(epic_folder.glob("**/sprint-*.md"))
    file_count = len(sprint_files)

    if dry_run:
        print(f"[DRY RUN] Would archive epic {epic_num}:")
        print(f"  Title: {title}")
        print(f"  Files: {file_count} sprints + 1 epic")
        print(f"  1. Move to 6-archived/")
        print(f"  2. Update YAML (status=archived, archived_at=<now>)")
        return {"status": "dry-run", "epic_num": epic_num}

    # Move to archived
    archived_dir = project_root / "docs" / "sprints" / "6-archived"
    archived_dir.mkdir(parents=True, exist_ok=True)

    new_epic_folder = archived_dir / epic_folder.name
    epic_folder.rename(new_epic_folder)

    # Update YAML frontmatter
    epic_file = new_epic_folder / "_epic.md"
    archived_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    _update_yaml_frontmatter(epic_file, {
        "status": "archived",
        "archived_at": archived_time
    })

    summary = {
        "epic_num": epic_num,
        "title": title,
        "status": "archived",
        "file_count": file_count,
        "new_path": str(new_epic_folder)
    }

    print(f"\n{'='*60}")
    print(f"Epic {epic_num}: {title} - ARCHIVED")
    print(f"{'='*60}")
    print(f"Location: {new_epic_folder}")
    print(f"Files: {file_count} sprints + 1 epic")
    print(f"{'='*60}")

    return summary


def block_sprint(sprint_num: int, reason: str, dry_run: bool = False) -> dict:
    """
    Block a sprint: rename with --blocked suffix, update state.

    Args:
        sprint_num: Sprint number to block
        reason: Reason for blocking
        dry_run: If True, preview changes without executing

    Returns:
        Dict with block summary

    Raises:
        FileOperationError: If sprint file not found
        ValidationError: If sprint already blocked

    Example:
        >>> summary = block_sprint(4, "Waiting for API access")
        >>> print(summary['status'])  # 'blocked'
    """
    project_root = find_project_root()
    sprint_file = _find_sprint_file(sprint_num, project_root)

    if not sprint_file:
        raise FileOperationError(
            f"Sprint {sprint_num} not found"
        )

    # Check if already blocked
    if "--blocked" in sprint_file.name:
        raise ValidationError(
            f"Sprint {sprint_num} already blocked: {sprint_file}"
        )

    # Read YAML for metadata
    with open(sprint_file) as f:
        content = f.read()

    import re
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not yaml_match:
        raise ValidationError(f"Sprint {sprint_num} missing YAML frontmatter")

    yaml_content = yaml_match.group(1)
    title_match = re.search(r'^title:\s*(.+)$', yaml_content, re.MULTILINE)
    started_match = re.search(r'^started:\s*(.+)$', yaml_content, re.MULTILINE)

    title = title_match.group(1).strip().strip('"') if title_match else "Unknown"

    # Calculate hours worked so far
    hours = None
    if started_match:
        started_str = started_match.group(1).strip()
        if started_str and started_str.lower() != 'null':
            started = datetime.fromisoformat(started_str.replace('Z', '+00:00'))
            blocked = datetime.now().astimezone()
            hours = round((blocked - started).total_seconds() / 3600, 1)

    if dry_run:
        print(f"[DRY RUN] Would block sprint {sprint_num}:")
        print(f"  Title: {title}")
        print(f"  Reason: {reason}")
        print(f"  Hours so far: {hours if hours else 'N/A'}")
        print(f"  1. Update YAML (status=blocked, blocker, hours_before_block)")
        print(f"  2. Rename with --blocked suffix")
        print(f"  3. Update state file")
        return {"status": "dry-run", "sprint_num": sprint_num}

    # Update YAML frontmatter
    blocked_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    updates = {
        "status": "blocked",
        "blocked_at": blocked_time,
        "blocker": reason
    }
    if hours:
        updates["hours_before_block"] = hours

    _update_yaml_frontmatter(sprint_file, updates)

    # Rename with --blocked suffix
    if sprint_file.parent.name.startswith("sprint-"):
        # Sprint in subdirectory
        sprint_subdir = sprint_file.parent
        new_dir_name = sprint_subdir.name + "--blocked"
        new_subdir = sprint_subdir.with_name(new_dir_name)
        sprint_subdir.rename(new_subdir)

        new_name = sprint_file.name.replace(".md", "--blocked.md")
        new_path = new_subdir / new_name
    else:
        # Sprint file directly in folder
        new_name = sprint_file.name.replace(".md", "--blocked.md")
        new_path = sprint_file.with_name(new_name)
        sprint_file.rename(new_path)

    # Update state file
    state_file = project_root / ".claude" / f"sprint-{sprint_num}-state.json"
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        state["status"] = "blocked"
        state["blocked_at"] = blocked_time
        state["blocker"] = reason
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

    summary = {
        "sprint_num": sprint_num,
        "title": title,
        "status": "blocked",
        "reason": reason,
        "hours": hours,
        "new_path": str(new_path)
    }

    print(f"\n{'='*60}")
    print(f"Sprint {sprint_num}: {title} - BLOCKED")
    print(f"{'='*60}")
    print(f"Blocker: {reason}")
    print(f"Hours before block: {hours if hours else 'N/A'}")
    print(f"File: {new_path.name}")
    print(f"To resume: /sprint-resume {sprint_num}")
    print(f"{'='*60}")

    return summary


def resume_sprint(sprint_num: int, dry_run: bool = False) -> dict:
    """
    Resume a blocked sprint: remove --blocked suffix, update state.

    Args:
        sprint_num: Sprint number to resume
        dry_run: If True, preview changes without executing

    Returns:
        Dict with resume summary

    Raises:
        FileOperationError: If sprint file not found
        ValidationError: If sprint not blocked

    Example:
        >>> summary = resume_sprint(4)
        >>> print(summary['status'])  # 'resumed'
    """
    project_root = find_project_root()
    sprint_file = _find_sprint_file(sprint_num, project_root)

    if not sprint_file:
        raise FileOperationError(
            f"Sprint {sprint_num} not found"
        )

    # Check if sprint is blocked
    if "--blocked" not in sprint_file.name:
        raise ValidationError(
            f"Sprint {sprint_num} is not blocked. Current state: {sprint_file.name}"
        )

    # Read YAML for metadata
    with open(sprint_file) as f:
        content = f.read()

    import re
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not yaml_match:
        raise ValidationError(f"Sprint {sprint_num} missing YAML frontmatter")

    yaml_content = yaml_match.group(1)
    title_match = re.search(r'^title:\s*(.+)$', yaml_content, re.MULTILINE)
    blocker_match = re.search(r'^blocker:\s*(.+)$', yaml_content, re.MULTILINE)
    hours_match = re.search(r'^hours_before_block:\s*([0-9.]+)', yaml_content, re.MULTILINE)

    title = title_match.group(1).strip().strip('"') if title_match else "Unknown"
    blocker = blocker_match.group(1).strip().strip('"') if blocker_match else "Unknown"
    hours_before = float(hours_match.group(1)) if hours_match else None

    if dry_run:
        print(f"[DRY RUN] Would resume sprint {sprint_num}:")
        print(f"  Title: {title}")
        print(f"  Was blocked by: {blocker}")
        print(f"  Hours before block: {hours_before if hours_before else 'N/A'}")
        print(f"  1. Update YAML (status=in-progress, resumed_at, previous_blocker)")
        print(f"  2. Remove --blocked suffix")
        print(f"  3. Update state file")
        return {"status": "dry-run", "sprint_num": sprint_num}

    # Update YAML frontmatter
    resumed_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    updates = {
        "status": "in-progress",
        "resumed_at": resumed_time,
        "previous_blocker": blocker
    }
    # Remove blocked-specific fields
    updates["blocker"] = None
    updates["blocked_at"] = None

    _update_yaml_frontmatter(sprint_file, updates)

    # Remove --blocked suffix
    if sprint_file.parent.name.startswith("sprint-") and "--blocked" in sprint_file.parent.name:
        # Sprint in subdirectory
        sprint_subdir = sprint_file.parent
        new_dir_name = sprint_subdir.name.replace("--blocked", "")
        new_subdir = sprint_subdir.with_name(new_dir_name)
        sprint_subdir.rename(new_subdir)

        new_name = sprint_file.name.replace("--blocked", "")
        new_path = new_subdir / new_name
    else:
        # Sprint file directly in folder
        new_name = sprint_file.name.replace("--blocked", "")
        new_path = sprint_file.with_name(new_name)
        sprint_file.rename(new_path)

    # Update state file
    state_file = project_root / ".claude" / f"sprint-{sprint_num}-state.json"
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        state["status"] = "in-progress"
        state["resumed_at"] = resumed_time
        state["previous_blocker"] = blocker
        # Remove blocked fields
        state.pop("blocker", None)
        state.pop("blocked_at", None)
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

    summary = {
        "sprint_num": sprint_num,
        "title": title,
        "status": "resumed",
        "previous_blocker": blocker,
        "hours_before_block": hours_before,
        "new_path": str(new_path)
    }

    print(f"\n{'='*60}")
    print(f"Sprint {sprint_num}: {title} - RESUMED")
    print(f"{'='*60}")
    print(f"Previously blocked by: {blocker}")
    print(f"Hours before block: {hours_before if hours_before else 'N/A'}")
    print(f"File: {new_path.name}")
    print(f"Use /sprint-next {sprint_num} to continue")
    print(f"{'='*60}")

    return summary


def get_sprint_status(sprint_num: int) -> dict:
    """
    Get current sprint status and progress.

    Args:
        sprint_num: Sprint number to check

    Returns:
        Dict with sprint status information

    Raises:
        FileOperationError: If sprint or state file not found

    Example:
        >>> status = get_sprint_status(4)
        >>> print(status['status'])  # 'in-progress'
    """
    project_root = find_project_root()

    # Read state file
    state_file = project_root / ".claude" / f"sprint-{sprint_num}-state.json"
    if not state_file.exists():
        raise FileOperationError(
            f"No state file for sprint {sprint_num}. Sprint may not be started."
        )

    with open(state_file) as f:
        state = json.load(f)

    # Find sprint file
    sprint_file = _find_sprint_file(sprint_num, project_root)
    if not sprint_file:
        raise FileOperationError(f"Sprint {sprint_num} file not found")

    # Read YAML frontmatter
    with open(sprint_file) as f:
        content = f.read()

    import re
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    yaml_data = {}
    if yaml_match:
        yaml_content = yaml_match.group(1)
        for line in yaml_content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                yaml_data[key.strip()] = value.strip()

    status = {
        "sprint_num": sprint_num,
        "title": yaml_data.get("title", "Unknown").strip('"'),
        "status": state.get("status", yaml_data.get("status", "Unknown")),
        "workflow_version": state.get("workflow_version", "1.0"),
        "started": yaml_data.get("started"),
        "completed": yaml_data.get("completed"),
        "current_step": state.get("current_step"),
        "sprint_file": str(sprint_file)
    }

    # Display status
    print(f"\n{'='*60}")
    print(f"Sprint {sprint_num}: {status['title']}")
    print(f"{'='*60}")
    print(f"Status: {status['status']}")
    print(f"Workflow: v{status['workflow_version']}")
    if status['started']:
        print(f"Started: {status['started']}")
    if status['current_step']:
        print(f"Current step: {status['current_step']}")
    print(f"File: {sprint_file.name}")
    print(f"{'='*60}")

    return status


def get_epic_status(epic_num: int) -> dict:
    """
    Get detailed epic status with sprint progress.

    Args:
        epic_num: Epic number to check

    Returns:
        Dict with epic status information

    Raises:
        FileOperationError: If epic not found

    Example:
        >>> status = get_epic_status(1)
        >>> print(status['progress'])  # 0.6 (60%)
    """
    project_root = find_project_root()
    epic_num_str = f"{epic_num:02d}"

    # Find epic folder
    epic_folder = None
    for folder in ["0-backlog", "1-todo", "2-in-progress", "3-done", "6-archived"]:
        search_path = project_root / "docs" / "sprints" / folder
        if search_path.exists():
            found = list(search_path.glob(f"epic-{epic_num_str}_*"))
            if found and found[0].is_dir():
                epic_folder = found[0]
                break

    if not epic_folder:
        raise FileOperationError(f"Epic {epic_num} not found")

    epic_file = epic_folder / "_epic.md"
    if not epic_file.exists():
        raise FileOperationError(f"Epic {epic_num} missing _epic.md")

    # Read epic file
    with open(epic_file) as f:
        content = f.read()

    import re
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    yaml_data = {}
    if yaml_match:
        yaml_content = yaml_match.group(1)
        for line in yaml_content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                yaml_data[key.strip()] = value.strip()

    title = yaml_data.get("title", "Unknown").strip('"')
    status = yaml_data.get("status", "Unknown")

    # Count sprints
    sprint_files = list(epic_folder.glob("**/sprint-*.md"))
    total = len(sprint_files)
    done = len([f for f in sprint_files if "--done" in f.name])
    aborted = len([f for f in sprint_files if "--aborted" in f.name])
    blocked = len([f for f in sprint_files if "--blocked" in f.name])
    in_progress = total - done - aborted - blocked

    progress = done / total if total > 0 else 0

    epic_status = {
        "epic_num": epic_num,
        "title": title,
        "status": status,
        "location": epic_folder.parent.name,
        "total_sprints": total,
        "done": done,
        "in_progress": in_progress,
        "blocked": blocked,
        "aborted": aborted,
        "progress": progress
    }

    # Display status
    print(f"\n{'='*60}")
    print(f"Epic {epic_num}: {title}")
    print(f"{'='*60}")
    print(f"Status: {status}")
    print(f"Location: {epic_folder.parent.name}")
    print(f"Sprints: {done}/{total} done ({progress*100:.0f}%)")
    if in_progress > 0:
        print(f"  In progress: {in_progress}")
    if blocked > 0:
        print(f"  Blocked: {blocked}")
    if aborted > 0:
        print(f"  Aborted: {aborted}")
    print(f"{'='*60}")

    return epic_status


def list_epics() -> list:
    """
    List all epics with their progress.

    Returns:
        List of dicts with epic information

    Example:
        >>> epics = list_epics()
        >>> for epic in epics:
        ...     print(f"Epic {epic['epic_num']}: {epic['progress']*100:.0f}%")
    """
    project_root = find_project_root()
    sprints_dir = project_root / "docs" / "sprints"

    if not sprints_dir.exists():
        print("No sprints directory found")
        return []

    # Find all epic folders
    epic_folders = []
    for folder in ["0-backlog", "1-todo", "2-in-progress", "3-done", "6-archived"]:
        folder_path = sprints_dir / folder
        if folder_path.exists():
            for epic_dir in folder_path.glob("epic-*"):
                if epic_dir.is_dir():
                    epic_folders.append(epic_dir)

    epics = []
    for epic_folder in sorted(epic_folders):
        # Extract epic number
        import re
        match = re.search(r'epic-(\d+)', epic_folder.name)
        if not match:
            continue

        epic_num = int(match.group(1))

        # Read epic file
        epic_file = epic_folder / "_epic.md"
        if not epic_file.exists():
            continue

        with open(epic_file) as f:
            content = f.read()

        yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        title = "Unknown"
        if yaml_match:
            yaml_content = yaml_match.group(1)
            title_match = re.search(r'^title:\s*(.+)$', yaml_content, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip().strip('"')

        # Count sprints
        sprint_files = list(epic_folder.glob("**/sprint-*.md"))
        total = len(sprint_files)
        done = len([f for f in sprint_files if "--done" in f.name])

        progress = done / total if total > 0 else 0

        epics.append({
            "epic_num": epic_num,
            "title": title,
            "total": total,
            "done": done,
            "progress": progress,
            "location": epic_folder.parent.name
        })

    # Display list
    print(f"\n{'='*60}")
    print("Epics:")
    print(f"{'='*60}")
    for epic in epics:
        bar_length = 10
        filled = int(epic['progress'] * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        location_marker = {
            "0-backlog": "📦",
            "1-todo": "📋",
            "2-in-progress": "⚙️",
            "3-done": "✅",
            "6-archived": "📁"
        }.get(epic['location'], "  ")

        print(f"  {location_marker} {epic['epic_num']:02d}. {epic['title'][:40]:<40} [{bar}] {epic['progress']*100:3.0f}%  ({epic['done']}/{epic['total']} sprints)")
    print(f"{'='*60}")
    print(f"Total: {len(epics)} epics")
    print(f"{'='*60}")

    return epics


def recover_sprint(sprint_num: int, dry_run: bool = False) -> dict:
    """
    Recover a sprint file that ended up in the wrong location.

    Args:
        sprint_num: Sprint number to recover
        dry_run: If True, preview changes without executing

    Returns:
        Dict with recovery summary

    Raises:
        FileOperationError: If sprint file not found
        ValidationError: If sprint is already in correct location

    Example:
        >>> summary = recover_sprint(4)
        >>> print(summary['new_path'])
    """
    project_root = find_project_root()
    sprint_file = _find_sprint_file(sprint_num, project_root)

    if not sprint_file:
        raise FileOperationError(f"Sprint {sprint_num} not found")

    # Determine correct location
    is_epic, epic_num = _is_epic_sprint(sprint_file)
    has_done_suffix = "--done" in sprint_file.name

    # Determine expected location
    if not has_done_suffix:
        raise ValidationError(
            f"Sprint {sprint_num} is not complete (no --done suffix). Nothing to recover."
        )

    if is_epic:
        # Epic sprint - should be in epic folder (either in-progress or done depending on epic status)
        expected_parent = sprint_file.parent
        if not expected_parent.name.startswith("epic-"):
            expected_parent = expected_parent.parent

        # Check if we need to move
        if "3-done" in str(sprint_file) and "2-in-progress" in str(expected_parent):
            # Epic sprint in wrong location
            correct_path = expected_parent / sprint_file.name
        else:
            raise ValidationError(f"Sprint {sprint_num} is already in correct location")
    else:
        # Standalone sprint - should be in 3-done
        correct_folder = project_root / "docs" / "sprints" / "3-done"
        correct_path = correct_folder / sprint_file.name

        if sprint_file.parent == correct_folder:
            raise ValidationError(f"Sprint {sprint_num} is already in correct location")

    if dry_run:
        print(f"[DRY RUN] Would recover sprint {sprint_num}:")
        print(f"  From: {sprint_file}")
        print(f"  To: {correct_path}")
        return {"status": "dry-run", "sprint_num": sprint_num}

    # Move file
    correct_path.parent.mkdir(parents=True, exist_ok=True)
    sprint_file.rename(correct_path)

    # Update state file if exists
    state_file = project_root / ".claude" / f"sprint-{sprint_num}-state.json"
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        state["sprint_file"] = str(correct_path)
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

    summary = {
        "sprint_num": sprint_num,
        "old_path": str(sprint_file),
        "new_path": str(correct_path)
    }

    print(f"\n{'='*60}")
    print(f"Sprint {sprint_num} - RECOVERED")
    print(f"{'='*60}")
    print(f"From: {sprint_file}")
    print(f"To: {correct_path}")
    print(f"{'='*60}")

    return summary


def add_to_epic(sprint_num: int, epic_num: int, dry_run: bool = False) -> dict:
    """
    Add an existing sprint to an epic.

    Args:
        sprint_num: Sprint number to add
        epic_num: Epic number to add sprint to
        dry_run: If True, preview changes without executing

    Returns:
        Dict with operation summary

    Raises:
        FileOperationError: If sprint or epic not found
        ValidationError: If sprint already in epic

    Example:
        >>> summary = add_to_epic(81, 10)
        >>> print(summary['epic_title'])
    """
    project_root = find_project_root()

    # Find sprint file
    sprint_file = _find_sprint_file(sprint_num, project_root)
    if not sprint_file:
        raise FileOperationError(f"Sprint {sprint_num} not found")

    # Check if already in epic
    is_epic, current_epic = _is_epic_sprint(sprint_file)
    if is_epic:
        raise ValidationError(
            f"Sprint {sprint_num} is already in epic {current_epic}"
        )

    # Find epic folder
    epic_num_str = f"{epic_num:02d}"
    epic_folder = None
    for folder in ["0-backlog", "1-todo", "2-in-progress"]:
        search_path = project_root / "docs" / "sprints" / folder
        if search_path.exists():
            found = list(search_path.glob(f"epic-{epic_num_str}_*"))
            if found and found[0].is_dir():
                epic_folder = found[0]
                break

    if not epic_folder:
        raise FileOperationError(f"Epic {epic_num} not found")

    epic_file = epic_folder / "_epic.md"
    if not epic_file.exists():
        raise FileOperationError(f"Epic {epic_num} missing _epic.md")

    # Read epic title
    with open(epic_file) as f:
        content = f.read()

    import re
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    epic_title = "Unknown"
    if yaml_match:
        title_match = re.search(r'^title:\s*(.+)$', yaml_match.group(1), re.MULTILINE)
        if title_match:
            epic_title = title_match.group(1).strip().strip('"')

    # Read sprint title
    with open(sprint_file) as f:
        sprint_content = f.read()

    sprint_yaml = re.search(r'^---\n(.*?)\n---', sprint_content, re.DOTALL)
    sprint_title = "Unknown"
    if sprint_yaml:
        title_match = re.search(r'^title:\s*(.+)$', sprint_yaml.group(1), re.MULTILINE)
        if title_match:
            sprint_title = title_match.group(1).strip().strip('"')

    new_path = epic_folder / sprint_file.name

    if dry_run:
        print(f"[DRY RUN] Would add sprint {sprint_num} to epic {epic_num}:")
        print(f"  Sprint: {sprint_title}")
        print(f"  Epic: {epic_title}")
        print(f"  Move to: {new_path}")
        print(f"  Update YAML: epic={epic_num}")
        return {"status": "dry-run", "sprint_num": sprint_num, "epic_num": epic_num}

    # Move sprint file
    sprint_file.rename(new_path)

    # Update sprint YAML
    _update_yaml_frontmatter(new_path, {"epic": epic_num})

    summary = {
        "sprint_num": sprint_num,
        "sprint_title": sprint_title,
        "epic_num": epic_num,
        "epic_title": epic_title,
        "new_path": str(new_path)
    }

    print(f"\n{'='*60}")
    print(f"Sprint {sprint_num} added to Epic {epic_num}")
    print(f"{'='*60}")
    print(f"Sprint: {sprint_title}")
    print(f"Epic: {epic_title}")
    print(f"New location: {new_path}")
    print(f"{'='*60}")

    return summary


def create_project(target_path: Optional[str] = None, dry_run: bool = False) -> dict:
    """
    Initialize a new project with the complete sprint workflow system.

    Copies commands, scripts, agents, hooks, and configuration from the master
    template to set up a new project.

    Args:
        target_path: Target directory path (defaults to current directory)
        dry_run: If True, preview changes without executing

    Returns:
        Dict with initialization summary

    Raises:
        FileOperationError: If target doesn't exist or master template not found
        ValidationError: If project already initialized

    Example:
        >>> summary = create_project("/path/to/new/project")
        >>> print(summary['status'])  # 'initialized'
    """
    import os

    # 1. Determine target path
    if target_path:
        target = Path(target_path).resolve()
    else:
        target = Path.cwd().resolve()

    # 2. Validate target
    if not target.exists():
        raise FileOperationError(f"Directory not found: {target}")

    # Check if already initialized
    if (target / ".claude" / "sprint-steps.json").exists():
        raise ValidationError(
            f"Project already initialized at {target}\n"
            f"Use /project-update to sync changes instead."
        )

    # 3. Define source paths
    master_project = Path.home() / "Development" / "Dreadnought" / "claude-maestro"
    global_claude = Path.home() / ".claude"
    template_path = global_claude / "templates" / "project"

    # Validate master project exists
    if not master_project.exists():
        raise FileOperationError(
            f"Master project not found at {master_project}\n"
            f"Cannot initialize without template source."
        )

    if dry_run:
        print(f"[DRY RUN] Would initialize project at: {target}")
        print(f"\nWould create structure:")
        print(f"  ├── commands/ (from {master_project}/commands/)")
        print(f"  ├── scripts/ (from {master_project}/scripts/)")
        print(f"  ├── .claude/")
        print(f"  │   ├── agents/ (global + template)")
        print(f"  │   ├── hooks/ (global + template)")
        print(f"  │   ├── settings.json")
        print(f"  │   ├── sprint-steps.json")
        print(f"  │   └── WORKFLOW_VERSION")
        print(f"  ├── docs/sprints/")
        print(f"  │   ├── 0-backlog/")
        print(f"  │   ├── 1-todo/")
        print(f"  │   ├── 2-in-progress/")
        print(f"  │   ├── 3-done/")
        print(f"  │   ├── 4-blocked/")
        print(f"  │   ├── 5-aborted/")
        print(f"  │   ├── 6-archived/")
        print(f"  │   └── registry.json")
        print(f"  ├── CLAUDE.md")
        print(f"  └── .gitignore (updated)")
        return {"status": "dry-run", "target": str(target)}

    # 4. Create directory structure
    print(f"→ Creating directory structure...")
    dirs_to_create = [
        target / ".claude" / "agents",
        target / ".claude" / "hooks",
        target / "commands",
        target / "scripts",
        target / "docs" / "sprints" / "0-backlog",
        target / "docs" / "sprints" / "1-todo",
        target / "docs" / "sprints" / "2-in-progress",
        target / "docs" / "sprints" / "3-done",
        target / "docs" / "sprints" / "4-blocked",
        target / "docs" / "sprints" / "5-aborted",
        target / "docs" / "sprints" / "6-archived",
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

    print(f"✓ Created directory structure")

    # 5. Copy commands from master project
    print(f"→ Copying commands...")
    command_count = 0
    if (master_project / "commands").exists():
        for cmd_file in (master_project / "commands").glob("*.md"):
            shutil.copy2(cmd_file, target / "commands" / cmd_file.name)
            command_count += 1
    print(f"✓ Copied {command_count} command files")

    # 6. Copy scripts from master project
    print(f"→ Copying scripts...")
    if (master_project / "scripts").exists():
        for script_file in (master_project / "scripts").iterdir():
            if script_file.is_file():
                dest = target / "scripts" / script_file.name
                shutil.copy2(script_file, dest)
                # Make Python scripts executable
                if script_file.suffix == ".py":
                    dest.chmod(0o755)
    print(f"✓ Copied automation scripts")

    # 7. Copy agents (global + template)
    print(f"→ Copying agents...")
    agent_count = 0

    # Copy global agents
    if (global_claude / "agents").exists():
        for agent_file in (global_claude / "agents").glob("*.md"):
            shutil.copy2(agent_file, target / ".claude" / "agents" / agent_file.name)
            agent_count += 1

    # Copy template agents
    if (template_path / ".claude" / "agents").exists():
        for agent_file in (template_path / ".claude" / "agents").glob("*.md"):
            shutil.copy2(agent_file, target / ".claude" / "agents" / agent_file.name)
            agent_count += 1

    print(f"✓ Copied {agent_count} agents")

    # 8. Copy hooks (global + template)
    print(f"→ Copying hooks...")
    hook_count = 0

    # Copy global hooks
    if (global_claude / "hooks").exists():
        for hook_file in (global_claude / "hooks").glob("*.py"):
            dest = target / ".claude" / "hooks" / hook_file.name
            shutil.copy2(hook_file, dest)
            dest.chmod(0o755)
            hook_count += 1

    # Copy template hooks
    if (template_path / ".claude" / "hooks").exists():
        for hook_file in (template_path / ".claude" / "hooks").glob("*.py"):
            dest = target / ".claude" / "hooks" / hook_file.name
            shutil.copy2(hook_file, dest)
            dest.chmod(0o755)
            hook_count += 1

    print(f"✓ Copied {hook_count} hooks")

    # 9. Copy configuration files
    print(f"→ Copying configuration...")

    # Copy sprint-steps.json
    if (template_path / ".claude" / "sprint-steps.json").exists():
        shutil.copy2(
            template_path / ".claude" / "sprint-steps.json",
            target / ".claude" / "sprint-steps.json"
        )

    # Copy settings.json
    if (template_path / ".claude" / "settings.json").exists():
        shutil.copy2(
            template_path / ".claude" / "settings.json",
            target / ".claude" / "settings.json"
        )

    # Copy WORKFLOW_VERSION
    if (master_project / "WORKFLOW_VERSION").exists():
        shutil.copy2(
            master_project / "WORKFLOW_VERSION",
            target / ".claude" / "WORKFLOW_VERSION"
        )

    print(f"✓ Copied configuration files")

    # 10. Copy CLAUDE.md (don't overwrite if exists)
    print(f"→ Copying CLAUDE.md...")
    if not (target / "CLAUDE.md").exists():
        if (template_path / "CLAUDE.md").exists():
            shutil.copy2(template_path / "CLAUDE.md", target / "CLAUDE.md")
            print(f"✓ Created CLAUDE.md")
        else:
            print(f"⚠ Template CLAUDE.md not found, skipping")
    else:
        print(f"✓ CLAUDE.md already exists, skipping")

    # 11. Create sprint registry
    print(f"→ Creating sprint registry...")
    registry = {
        "counters": {
            "next_sprint": 1,
            "next_epic": 1
        },
        "sprints": {},
        "epics": {}
    }

    registry_path = target / "docs" / "sprints" / "registry.json"
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)

    print(f"✓ Created sprint registry")

    # 12. Update .gitignore
    print(f"→ Updating .gitignore...")
    gitignore_path = target / ".gitignore"
    gitignore_entries = [
        "# Sprint workflow state files",
        ".claude/sprint-*-state.json",
        ".claude/product-state.json"
    ]

    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if "sprint-.*-state.json" not in content:
            with open(gitignore_path, 'a') as f:
                f.write("\n")
                f.write("\n".join(gitignore_entries))
                f.write("\n")
            print(f"✓ Updated .gitignore")
        else:
            print(f"✓ .gitignore already configured")
    else:
        with open(gitignore_path, 'w') as f:
            f.write("\n".join(gitignore_entries))
            f.write("\n")
        print(f"✓ Created .gitignore")

    # Read workflow version
    workflow_version = "unknown"
    if (target / ".claude" / "WORKFLOW_VERSION").exists():
        workflow_version = (target / ".claude" / "WORKFLOW_VERSION").read_text().strip()

    # 13. Report success
    print(f"\n{'='*70}")
    print(f"✅ Project workflow initialized at: {target}")
    print(f"{'='*70}")
    print(f"\nCreated structure:")
    print(f"├── commands/             ({command_count} command files)")
    print(f"├── scripts/              (automation)")
    print(f"├── .claude/")
    print(f"│   ├── agents/           ({agent_count} agents)")
    print(f"│   ├── hooks/            ({hook_count} hooks)")
    print(f"│   ├── settings.json")
    print(f"│   ├── sprint-steps.json")
    print(f"│   └── WORKFLOW_VERSION")
    print(f"├── docs/sprints/")
    print(f"│   ├── 0-backlog/")
    print(f"│   ├── 1-todo/")
    print(f"│   ├── 2-in-progress/")
    print(f"│   ├── 3-done/")
    print(f"│   ├── 4-blocked/")
    print(f"│   ├── 5-aborted/")
    print(f"│   ├── 6-archived/")
    print(f"│   └── registry.json")
    print(f"└── CLAUDE.md")
    print(f"\nNext steps:")
    print(f"1. Review and customize CLAUDE.md for your project")
    print(f"2. Create your first sprint: /sprint-new \"Initial Setup\"")
    print(f"3. Start working: /sprint-start 1")
    print(f"\nTo sync future updates: /project-update")
    print(f"Workflow version: {workflow_version}")
    print(f"{'='*70}")

    return {
        "status": "initialized",
        "target": str(target),
        "command_count": command_count,
        "agent_count": agent_count,
        "hook_count": hook_count,
        "workflow_version": workflow_version
    }


def complete_sprint(sprint_num: int, dry_run: bool = False) -> dict:
    """
    Complete a sprint with full automation: pre-flight checks, file movement,
    registry update, git commit, and tag creation.

    Args:
        sprint_num: Sprint number to complete
        dry_run: If True, preview changes without executing

    Returns:
        Dict with completion summary

    Raises:
        FileOperationError: If sprint file not found or operations fail
        ValidationError: If pre-flight checks fail
        GitError: If git operations fail

    Example:
        >>> summary = complete_sprint(2)
        >>> print(summary['status'])  # 'completed'
    """
    project_root = find_project_root()
    sprint_file = _find_sprint_file(sprint_num, project_root)

    if not sprint_file:
        raise FileOperationError(
            f"Sprint {sprint_num} not found. Use /sprint-start {sprint_num} first."
        )

    # 1. Verify postmortem exists
    with open(sprint_file) as f:
        content = f.read()
        if "## Postmortem" not in content:
            raise ValidationError(
                f"Sprint {sprint_num} missing postmortem section.\n"
                f"Run: /sprint-postmortem {sprint_num} first"
            )

    # 2. Read YAML frontmatter for metadata
    import re
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not yaml_match:
        raise ValidationError(f"Sprint {sprint_num} missing YAML frontmatter")

    yaml_content = yaml_match.group(1)
    title_match = re.search(r'^title:\s*(.+)$', yaml_content, re.MULTILINE)
    started_match = re.search(r'^started:\s*(.+)$', yaml_content, re.MULTILINE)

    if not title_match:
        raise ValidationError(f"Sprint {sprint_num} missing title in YAML")
    if not started_match:
        raise ValidationError(f"Sprint {sprint_num} missing started timestamp")

    title = title_match.group(1).strip().strip('"')
    started_str = started_match.group(1).strip()

    # 3. Calculate hours
    from datetime import datetime
    started = datetime.fromisoformat(started_str.replace('Z', '+00:00'))
    completed = datetime.now().astimezone()
    hours = round((completed - started).total_seconds() / 3600, 1)

    if dry_run:
        print(f"[DRY RUN] Would complete sprint {sprint_num}:")
        print(f"  Title: {title}")
        print(f"  Hours: {hours}")
        print(f"  1. Move file with --done suffix")
        print(f"  2. Update registry (status=done, hours={hours})")
        print(f"  3. Commit changes")
        print(f"  4. Create and push git tag: sprint-{sprint_num}")
        print(f"  5. Check epic completion")
        return {"status": "dry-run", "sprint_num": sprint_num, "hours": hours}

    # 4. Move sprint file to done
    print(f"→ Moving sprint {sprint_num} to done...")
    new_path = move_to_done(sprint_num, dry_run=False)
    print(f"✓ Moved to: {new_path}")

    # 5. Update registry
    print(f"→ Updating registry...")
    update_registry(
        sprint_num,
        status="done",
        dry_run=False,
        completed=completed.strftime("%Y-%m-%d"),
        hours=hours
    )
    print(f"✓ Registry updated")

    # 6. Commit changes
    print(f"→ Committing changes...")
    try:
        commit_msg = (
            f"feat(sprint-{sprint_num}): complete sprint - {title}\n\n"
            f"- Duration: {hours} hours\n"
            f"- Marked with --done suffix\n"
            f"- Updated registry\n\n"
            f"🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\n"
            f"Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
        )
        subprocess.run(
            ["git", "add", "-A"],
            check=True,
            capture_output=True,
            text=True
        )
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ Changes committed")
    except subprocess.CalledProcessError as e:
        raise GitError(f"Failed to commit changes: {e.stderr}") from e

    # 7. Create and push git tag
    print(f"→ Creating git tag...")
    create_git_tag(sprint_num, title, dry_run=False, auto_push=True)

    # 8. Check epic completion
    is_epic, epic_num = _is_epic_sprint(new_path)
    if is_epic and epic_num:
        print(f"→ Checking epic {epic_num} completion...")
        is_complete, message = check_epic_completion(epic_num)
        print(message)
        if is_complete:
            print(f"\n💡 Epic {epic_num} is ready! Run: /epic-complete {epic_num}")

    # 9. Update state file
    state_file = project_root / ".claude" / f"sprint-{sprint_num}-state.json"
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        state["status"] = "complete"
        state["completed_at"] = completed.isoformat()
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"✓ State file updated")

    # 10. Success summary
    summary = {
        "status": "completed",
        "sprint_num": sprint_num,
        "title": title,
        "hours": hours,
        "file_path": str(new_path),
        "tag": f"sprint-{sprint_num}",
        "epic": epic_num if is_epic else None
    }

    print(f"\n{'='*60}")
    print(f"Sprint {sprint_num}: {title} - COMPLETE ✓")
    print(f"{'='*60}")
    print(f"Duration: {hours} hours")
    print(f"File: {new_path.name}")
    print(f"Tag: sprint-{sprint_num} (pushed to remote)")
    if is_epic:
        print(f"Epic: {epic_num}")
    print(f"{'='*60}")

    return summary


def main():
    """CLI interface for sprint lifecycle utilities."""
    parser = argparse.ArgumentParser(
        description="Sprint lifecycle automation utilities (creation → execution → completion)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # === CREATION COMMANDS ===

    # next-sprint-number command
    next_sprint_parser = subparsers.add_parser("next-sprint-number", help="Get next sprint number")
    next_sprint_parser.add_argument("--dry-run", action="store_true", help="Preview without incrementing")

    # next-epic-number command
    next_epic_parser = subparsers.add_parser("next-epic-number", help="Get next epic number")
    next_epic_parser.add_argument("--dry-run", action="store_true", help="Preview without incrementing")

    # register-sprint command
    register_sprint_parser = subparsers.add_parser("register-sprint", help="Register new sprint")
    register_sprint_parser.add_argument("title", help="Sprint title")
    register_sprint_parser.add_argument("--epic", type=int, help="Epic number (optional)")
    register_sprint_parser.add_argument("--estimated-hours", type=float, help="Estimated hours")
    register_sprint_parser.add_argument("--dry-run", action="store_true", help="Preview without registering")

    # register-epic command
    register_epic_parser = subparsers.add_parser("register-epic", help="Register new epic")
    register_epic_parser.add_argument("title", help="Epic title")
    register_epic_parser.add_argument("--sprint-count", type=int, default=0, help="Number of sprints")
    register_epic_parser.add_argument("--estimated-hours", type=float, help="Estimated hours")
    register_epic_parser.add_argument("--dry-run", action="store_true", help="Preview without registering")

    # === LIFECYCLE COMMANDS ===

    # start-sprint command
    start_parser = subparsers.add_parser("start-sprint", help="Start a sprint (move to in-progress)")
    start_parser.add_argument("sprint_num", type=int, help="Sprint number")
    start_parser.add_argument("--dry-run", action="store_true", help="Preview without executing")

    # abort-sprint command
    abort_parser = subparsers.add_parser("abort-sprint", help="Abort a sprint")
    abort_parser.add_argument("sprint_num", type=int, help="Sprint number")
    abort_parser.add_argument("reason", help="Reason for aborting")
    abort_parser.add_argument("--dry-run", action="store_true", help="Preview without executing")

    # block-sprint command
    block_parser = subparsers.add_parser("block-sprint", help="Block a sprint (mark as blocked)")
    block_parser.add_argument("sprint_num", type=int, help="Sprint number")
    block_parser.add_argument("reason", help="Reason for blocking")
    block_parser.add_argument("--dry-run", action="store_true", help="Preview without executing")

    # resume-sprint command
    resume_parser = subparsers.add_parser("resume-sprint", help="Resume a blocked sprint")
    resume_parser.add_argument("sprint_num", type=int, help="Sprint number")
    resume_parser.add_argument("--dry-run", action="store_true", help="Preview without executing")

    # start-epic command
    start_epic_parser = subparsers.add_parser("start-epic", help="Start an epic (move to in-progress)")
    start_epic_parser.add_argument("epic_num", type=int, help="Epic number")
    start_epic_parser.add_argument("--dry-run", action="store_true", help="Preview without executing")

    # complete-epic command
    complete_epic_parser = subparsers.add_parser("complete-epic", help="Complete an epic (move to done)")
    complete_epic_parser.add_argument("epic_num", type=int, help="Epic number")
    complete_epic_parser.add_argument("--dry-run", action="store_true", help="Preview without executing")

    # archive-epic command
    archive_epic_parser = subparsers.add_parser("archive-epic", help="Archive an epic (move to archived)")
    archive_epic_parser.add_argument("epic_num", type=int, help="Epic number")
    archive_epic_parser.add_argument("--dry-run", action="store_true", help="Preview without executing")

    # === COMPLETION COMMANDS ===

    # complete-sprint command
    complete_parser = subparsers.add_parser("complete-sprint", help="Complete sprint with full automation")
    complete_parser.add_argument("sprint_num", type=int, help="Sprint number")
    complete_parser.add_argument("--dry-run", action="store_true", help="Preview without executing")

    # move-to-done command
    move_parser = subparsers.add_parser("move-to-done", help="Move sprint to done status")
    move_parser.add_argument("sprint_num", type=int, help="Sprint number")
    move_parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")

    # update-registry command
    registry_parser = subparsers.add_parser("update-registry", help="Update sprint registry")
    registry_parser.add_argument("sprint_num", type=int, help="Sprint number")
    registry_parser.add_argument("--status", required=True, help="Sprint status")
    registry_parser.add_argument("--completed", help="Completion date (YYYY-MM-DD)")
    registry_parser.add_argument("--hours", type=float, help="Hours spent")
    registry_parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")

    # check-epic command
    epic_parser = subparsers.add_parser("check-epic", help="Check if epic is complete")
    epic_parser.add_argument("epic_num", type=int, help="Epic number")

    # create-tag command
    tag_parser = subparsers.add_parser("create-tag", help="Create git tag for sprint")
    tag_parser.add_argument("sprint_num", type=int, help="Sprint number")
    tag_parser.add_argument("title", help="Sprint title")
    tag_parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    tag_parser.add_argument("--no-push", action="store_true", help="Don't auto-push tag to remote")

    # === QUERY COMMANDS ===

    # sprint-status command
    sprint_status_parser = subparsers.add_parser("sprint-status", help="Get sprint status and progress")
    sprint_status_parser.add_argument("sprint_num", type=int, help="Sprint number")

    # epic-status command
    epic_status_parser = subparsers.add_parser("epic-status", help="Get epic status with sprint progress")
    epic_status_parser.add_argument("epic_num", type=int, help="Epic number")

    # list-epics command
    list_epics_parser = subparsers.add_parser("list-epics", help="List all epics with progress")

    # recover-sprint command
    recover_parser = subparsers.add_parser("recover-sprint", help="Recover sprint file in wrong location")
    recover_parser.add_argument("sprint_num", type=int, help="Sprint number")
    recover_parser.add_argument("--dry-run", action="store_true", help="Preview without executing")

    # add-to-epic command
    add_epic_parser = subparsers.add_parser("add-to-epic", help="Add sprint to epic")
    add_epic_parser.add_argument("sprint_num", type=int, help="Sprint number")
    add_epic_parser.add_argument("epic_num", type=int, help="Epic number")
    add_epic_parser.add_argument("--dry-run", action="store_true", help="Preview without executing")

    # === PROJECT SETUP COMMANDS ===

    # create-project command
    create_project_parser = subparsers.add_parser("create-project", help="Initialize new project with workflow")
    create_project_parser.add_argument("target_path", nargs="?", help="Target directory (default: current)")
    create_project_parser.add_argument("--dry-run", action="store_true", help="Preview without executing")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # === CREATION COMMAND HANDLERS ===

        if args.command == "next-sprint-number":
            num = get_next_sprint_number(dry_run=args.dry_run)
            if not args.dry_run:
                print(f"✓ Next sprint number: {num}")
                print(f"✓ Counter incremented to: {num + 1}")

        elif args.command == "next-epic-number":
            num = get_next_epic_number(dry_run=args.dry_run)
            if not args.dry_run:
                print(f"✓ Next epic number: {num}")
                print(f"✓ Counter incremented to: {num + 1}")

        elif args.command == "register-sprint":
            metadata = {}
            if args.estimated_hours:
                metadata["estimatedHours"] = args.estimated_hours

            sprint_num = register_new_sprint(
                args.title,
                epic=args.epic,
                dry_run=args.dry_run,
                **metadata
            )
            if not args.dry_run:
                print(f"✓ Registered sprint {sprint_num}: {args.title}")
                if args.epic:
                    print(f"  Part of Epic {args.epic}")

        elif args.command == "register-epic":
            metadata = {}
            if args.estimated_hours:
                metadata["estimatedHours"] = args.estimated_hours

            epic_num = register_new_epic(
                args.title,
                sprint_count=args.sprint_count,
                dry_run=args.dry_run,
                **metadata
            )
            if not args.dry_run:
                print(f"✓ Registered epic {epic_num}: {args.title}")
                print(f"  Planned sprints: {args.sprint_count}")

        # === LIFECYCLE COMMAND HANDLERS ===

        elif args.command == "start-sprint":
            result = start_sprint(args.sprint_num, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"✓ Started sprint {result['sprint_num']}: {result['title']}")
                print(f"  Moved to: {result['new_path']}")
                print(f"  State file: {result['state_file']}")

        elif args.command == "abort-sprint":
            result = abort_sprint(args.sprint_num, args.reason, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"✓ Aborted sprint {result['sprint_num']}: {result['title']}")
                print(f"  Reason: {args.reason}")
                print(f"  New path: {result['new_path']}")
                if result.get('hours'):
                    print(f"  Hours worked: {result['hours']:.1f}")

        elif args.command == "block-sprint":
            result = block_sprint(args.sprint_num, args.reason, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"✓ Blocked sprint {result['sprint_num']}: {result['title']}")
                print(f"  Reason: {args.reason}")
                print(f"  New path: {result['new_path']}")
                if result.get('hours'):
                    print(f"  Hours worked: {result['hours']:.1f}")

        elif args.command == "resume-sprint":
            result = resume_sprint(args.sprint_num, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"✓ Resumed sprint {result['sprint_num']}: {result['title']}")
                print(f"  Previously blocked by: {result['previous_blocker']}")
                print(f"  New path: {result['new_path']}")

        elif args.command == "start-epic":
            result = start_epic(args.epic_num, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"✓ Started epic {result['epic_num']}: {result['title']}")
                print(f"  Moved to: {result['new_path']}")
                print(f"  Sprints: {result['sprint_count']}")

        elif args.command == "complete-epic":
            result = complete_epic(args.epic_num, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"✓ Completed epic {result['epic_num']}: {result['title']}")
                print(f"  Moved to: {result['new_path']}")
                print(f"  Sprints completed: {result['done_count']}")
                print(f"  Sprints aborted: {result['aborted_count']}")
                print(f"  Total hours: {result['total_hours']:.1f}")

        elif args.command == "archive-epic":
            result = archive_epic(args.epic_num, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"✓ Archived epic {result['epic_num']}: {result['title']}")
                print(f"  Moved to: {result['new_path']}")
                print(f"  Files: {result['file_count']} sprints + 1 epic")

        # === COMPLETION COMMAND HANDLERS ===

        elif args.command == "complete-sprint":
            complete_sprint(args.sprint_num, dry_run=args.dry_run)

        elif args.command == "move-to-done":
            new_path = move_to_done(args.sprint_num, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"✓ Moved sprint {args.sprint_num} to: {new_path}")

        elif args.command == "update-registry":
            metadata = {}
            if args.completed:
                metadata["completed"] = args.completed
            if args.hours:
                metadata["hours"] = args.hours

            update_registry(args.sprint_num, args.status, dry_run=args.dry_run, **metadata)
            if not args.dry_run:
                print(f"✓ Updated registry for sprint {args.sprint_num}")

        elif args.command == "check-epic":
            is_complete, message = check_epic_completion(args.epic_num)
            print(message)
            sys.exit(0 if is_complete else 1)

        elif args.command == "create-tag":
            create_git_tag(
                args.sprint_num,
                args.title,
                dry_run=args.dry_run,
                auto_push=not args.no_push
            )

        # === QUERY COMMAND HANDLERS ===

        elif args.command == "sprint-status":
            get_sprint_status(args.sprint_num)

        elif args.command == "epic-status":
            get_epic_status(args.epic_num)

        elif args.command == "list-epics":
            list_epics()

        elif args.command == "recover-sprint":
            result = recover_sprint(args.sprint_num, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"✓ Recovered sprint {result['sprint_num']}")

        elif args.command == "add-to-epic":
            result = add_to_epic(args.sprint_num, args.epic_num, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"✓ Added sprint {result['sprint_num']} to epic {result['epic_num']}")

        # === PROJECT SETUP COMMAND HANDLERS ===

        elif args.command == "create-project":
            target = getattr(args, 'target_path', None)
            result = create_project(target_path=target, dry_run=args.dry_run)
            # Output is handled by create_project() function

    except SprintLifecycleError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
