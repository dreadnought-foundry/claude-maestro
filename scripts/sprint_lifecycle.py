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

    except SprintLifecycleError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
