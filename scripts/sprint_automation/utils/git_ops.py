"""
Git operation utilities for sprint automation.

Provides git-related functionality including status checks
and tag creation.
"""

import subprocess

from ..exceptions import GitError, ValidationError


def check_git_clean() -> bool:
    """
    Check if git working directory is clean.

    Returns:
        True if working directory is clean, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )
        return len(result.stdout.strip()) == 0
    except subprocess.CalledProcessError:
        return False


def create_git_tag(
    sprint_num: int, title: str, dry_run: bool = False, auto_push: bool = True
) -> None:
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
        print("[DRY RUN] Would create git tag:")
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
            text=True,
        )

        print(f"✓ Created git tag: {tag_name}")

        # Push tag if requested
        if auto_push:
            subprocess.run(
                ["git", "push", "origin", tag_name],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"✓ Pushed tag to remote: {tag_name}")

    except subprocess.CalledProcessError as e:
        raise GitError(f"Failed to create/push git tag '{tag_name}': {e.stderr}") from e
