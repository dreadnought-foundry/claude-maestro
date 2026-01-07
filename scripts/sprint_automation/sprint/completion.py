"""
Sprint completion operations.

Handles sprint completion workflow including moving files to done status
and running the complete sprint process.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
import re
import shutil

from ..exceptions import FileOperationError, ValidationError, GitError
from ..utils.file_ops import (
    backup_file,
    cleanup_backup,
    restore_file,
    update_yaml_frontmatter,
    find_project_root,
)
from ..utils.project import find_sprint_file, is_epic_sprint
from ..utils.git_ops import create_git_tag
from ..registry.manager import update_registry, check_epic_completion
from .postmortem import generate_postmortem


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
    sprint_file = find_sprint_file(sprint_num, project_root)

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

    is_epic, epic_num = is_epic_sprint(sprint_file)

    if dry_run:
        if is_epic:
            if sprint_file.parent.name.startswith("sprint-"):
                # Sprint in subdirectory
                sprint_subdir = sprint_file.parent
                new_dir_name = sprint_subdir.name + "--done"
                new_name = sprint_file.name.replace(".md", "--done.md")
                print("[DRY RUN] Would rename epic sprint subdirectory and file:")
                print(f"  From: {sprint_file}")
                print(f"  Dir:  {sprint_subdir.name} → {new_dir_name}")
                print(f"  File: {sprint_file.name} → {new_name}")
                new_path = sprint_subdir.with_name(new_dir_name) / new_name
            else:
                # Sprint directly in epic folder
                new_name = sprint_file.name.replace(".md", "--done.md")
                new_path = sprint_file.with_name(new_name)
                print("[DRY RUN] Would rename epic sprint:")
                print(f"  From: {sprint_file}")
                print(f"  To:   {new_path}")
        else:
            standalone_dir = (
                project_root / "docs" / "sprints" / "3-done" / "_standalone"
            )
            new_name = sprint_file.name.replace(".md", "--done.md")
            new_path = standalone_dir / new_name
            print("[DRY RUN] Would move standalone sprint:")
            print(f"  From: {sprint_file}")
            print(f"  To:   {new_path}")
        return new_path

    # Backup original file
    backup = backup_file(sprint_file)

    try:
        # Update YAML frontmatter
        update_yaml_frontmatter(
            sprint_file,
            {"status": "done", "completed": datetime.now().strftime("%Y-%m-%d")},
        )

        # YAML update succeeded, cleanup backup before directory operations
        # This prevents .bak files from being moved with directory renames
        cleanup_backup(backup)
        backup = None  # Mark as cleaned up

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
            standalone_dir = (
                project_root / "docs" / "sprints" / "3-done" / "_standalone"
            )
            standalone_dir.mkdir(parents=True, exist_ok=True)

            new_name = sprint_file.name.replace(".md", "--done.md")
            new_path = standalone_dir / new_name

            # Move file
            shutil.move(str(sprint_file), str(new_path))

        return new_path

    except Exception as e:
        # Restore from backup on failure (only if not already cleaned up)
        if backup and backup.exists():
            restore_file(backup)
        raise FileOperationError(f"Failed to move sprint {sprint_num}: {e}") from e


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
    sprint_file = find_sprint_file(sprint_num, project_root)

    if not sprint_file:
        raise FileOperationError(
            f"Sprint {sprint_num} not found. Use /sprint-start {sprint_num} first."
        )

    # 1. Generate postmortem if not exists
    postmortem_file = sprint_file.parent / f"sprint-{sprint_num}_postmortem.md"
    if not postmortem_file.exists():
        print("→ Generating postmortem...")
        generate_postmortem(sprint_num, dry_run=dry_run)
        if not dry_run:
            print("✓ Postmortem generated")

    with open(sprint_file) as f:
        content = f.read()

    # 2. Read YAML frontmatter for metadata

    yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not yaml_match:
        raise ValidationError(f"Sprint {sprint_num} missing YAML frontmatter")

    yaml_content = yaml_match.group(1)
    title_match = re.search(r"^title:\s*(.+)$", yaml_content, re.MULTILINE)
    started_match = re.search(r"^started:\s*(.+)$", yaml_content, re.MULTILINE)

    if not title_match:
        raise ValidationError(f"Sprint {sprint_num} missing title in YAML")
    if not started_match:
        raise ValidationError(f"Sprint {sprint_num} missing started timestamp")

    title = title_match.group(1).strip().strip('"')
    started_str = started_match.group(1).strip()

    # 3. Calculate hours
    from datetime import datetime

    started = datetime.fromisoformat(started_str.replace("Z", "+00:00"))
    completed = datetime.now().astimezone()
    hours = round((completed - started).total_seconds() / 3600, 1)

    if dry_run:
        # Calculate actual paths for dry-run display
        sprint_folder = sprint_file.parent
        new_file_name = sprint_file.name.replace(".md", "--done.md")
        new_folder_name = sprint_folder.name + "--done"
        new_folder = sprint_folder.parent / new_folder_name

        print(f"[DRY RUN] Would complete sprint {sprint_num}:")
        print(f"  Title: {title}")
        print(f"  Hours: {hours}")
        if not postmortem_file.exists():
            print(f"\n  1. Generate postmortem: {postmortem_file.name}")
        else:
            print(f"\n  1. Postmortem exists: {postmortem_file.name}")
        print("\n  2. Rename folder and file with --done suffix:")
        print(f"     {sprint_folder.relative_to(project_root)}/")
        print(f"     → {new_folder.relative_to(project_root)}/")
        print(f"     {sprint_file.name}")
        print(f"     → {new_file_name}")
        print(f"\n  3. Update registry (status=done, hours={hours})")
        print("  4. Commit changes")
        print(f"  5. Create and push git tag: sprint-{sprint_num}")
        print("  6. Check epic completion")
        return {"status": "dry-run", "sprint_num": sprint_num, "hours": hours}

    # 4. Move sprint file to done
    print(f"→ Moving sprint {sprint_num} to done...")
    new_path = move_to_done(sprint_num, dry_run=False)
    print(f"✓ Moved to: {new_path}")

    # 5. Update registry
    print("→ Updating registry...")
    update_registry(
        sprint_num,
        status="done",
        dry_run=False,
        completed=completed.strftime("%Y-%m-%d"),
        hours=hours,
    )
    print("✓ Registry updated")

    # 6. Commit changes
    print("→ Committing changes...")
    try:
        commit_msg = (
            f"feat(sprint-{sprint_num}): complete sprint - {title}\n\n"
            f"- Duration: {hours} hours\n"
            f"- Marked with --done suffix\n"
            f"- Updated registry\n\n"
            f"🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\n"
            f"Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
        )
        subprocess.run(["git", "add", "-A"], check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            check=True,
            capture_output=True,
            text=True,
        )
        print("✓ Changes committed")
    except subprocess.CalledProcessError as e:
        raise GitError(f"Failed to commit changes: {e.stderr}") from e

    # 7. Create and push git tag
    print("→ Creating git tag...")
    create_git_tag(sprint_num, title, dry_run=False, auto_push=True)

    # 8. Check epic completion
    is_epic, epic_num = is_epic_sprint(new_path)
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
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
        print("✓ State file updated")

    # 10. Success summary
    summary = {
        "status": "completed",
        "sprint_num": sprint_num,
        "title": title,
        "hours": hours,
        "file_path": str(new_path),
        "tag": f"sprint-{sprint_num}",
        "epic": epic_num if is_epic else None,
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
