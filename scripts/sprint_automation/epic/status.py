"""
Epic status operations.

Provides functions for querying epic status, listing epics,
and adding sprints to epics.
"""

import re

from ..exceptions import FileOperationError, ValidationError
from ..utils.file_ops import find_project_root, update_yaml_frontmatter
from ..utils.project import find_sprint_file, is_epic_sprint


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

    yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    yaml_data = {}
    if yaml_match:
        yaml_content = yaml_match.group(1)
        for line in yaml_content.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
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
        "progress": progress,
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

        match = re.search(r"epic-(\d+)", epic_folder.name)
        if not match:
            continue

        epic_num = int(match.group(1))

        # Read epic file
        epic_file = epic_folder / "_epic.md"
        if not epic_file.exists():
            continue

        with open(epic_file) as f:
            content = f.read()

        yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        title = "Unknown"
        if yaml_match:
            yaml_content = yaml_match.group(1)
            title_match = re.search(r"^title:\s*(.+)$", yaml_content, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip().strip('"')

        # Count sprints
        sprint_files = list(epic_folder.glob("**/sprint-*.md"))
        total = len(sprint_files)
        done = len([f for f in sprint_files if "--done" in f.name])

        progress = done / total if total > 0 else 0

        epics.append(
            {
                "epic_num": epic_num,
                "title": title,
                "total": total,
                "done": done,
                "progress": progress,
                "location": epic_folder.parent.name,
            }
        )

    # Display list
    print(f"\n{'='*60}")
    print("Epics:")
    print(f"{'='*60}")
    for epic in epics:
        bar_length = 10
        filled = int(epic["progress"] * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        location_marker = {
            "0-backlog": "📦",
            "1-todo": "📋",
            "2-in-progress": "⚙️",
            "3-done": "✅",
            "6-archived": "📁",
        }.get(epic["location"], "  ")

        print(
            f"  {location_marker} {epic['epic_num']:02d}. {epic['title'][:40]:<40} [{bar}] {epic['progress']*100:3.0f}%  ({epic['done']}/{epic['total']} sprints)"
        )
    print(f"{'='*60}")
    print(f"Total: {len(epics)} epics")
    print(f"{'='*60}")

    return epics


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
    sprint_file = find_sprint_file(sprint_num, project_root)
    if not sprint_file:
        raise FileOperationError(f"Sprint {sprint_num} not found")

    # Check if already in epic
    is_epic, current_epic = is_epic_sprint(sprint_file)
    if is_epic:
        raise ValidationError(f"Sprint {sprint_num} is already in epic {current_epic}")

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

    yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    epic_title = "Unknown"
    if yaml_match:
        title_match = re.search(r"^title:\s*(.+)$", yaml_match.group(1), re.MULTILINE)
        if title_match:
            epic_title = title_match.group(1).strip().strip('"')

    # Read sprint title
    with open(sprint_file) as f:
        sprint_content = f.read()

    sprint_yaml = re.search(r"^---\n(.*?)\n---", sprint_content, re.DOTALL)
    sprint_title = "Unknown"
    if sprint_yaml:
        title_match = re.search(r"^title:\s*(.+)$", sprint_yaml.group(1), re.MULTILINE)
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
    update_yaml_frontmatter(new_path, {"epic": epic_num})

    summary = {
        "sprint_num": sprint_num,
        "sprint_title": sprint_title,
        "epic_num": epic_num,
        "epic_title": epic_title,
        "new_path": str(new_path),
    }

    print(f"\n{'='*60}")
    print(f"Sprint {sprint_num} added to Epic {epic_num}")
    print(f"{'='*60}")
    print(f"Sprint: {sprint_title}")
    print(f"Epic: {epic_title}")
    print(f"New location: {new_path}")
    print(f"{'='*60}")

    return summary
