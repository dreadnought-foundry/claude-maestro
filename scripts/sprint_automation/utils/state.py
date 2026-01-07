"""
State file operations for sprint automation.

Manages sprint state files that track workflow progress.
State files are stored in .claude/sprint-{N}-state.json
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from ..exceptions import FileOperationError


def get_state_file_path(project_root: Path, sprint_num: int) -> Path:
    """
    Get path to sprint state file.

    Args:
        project_root: Project root path
        sprint_num: Sprint number

    Returns:
        Path to state file
    """
    return project_root / ".claude" / f"sprint-{sprint_num}-state.json"


def load_state(project_root: Path, sprint_num: int) -> Dict:
    """
    Load sprint state from file.

    Args:
        project_root: Project root path
        sprint_num: Sprint number

    Returns:
        State dictionary

    Raises:
        FileOperationError: If state file not found
    """
    state_file = get_state_file_path(project_root, sprint_num)

    if not state_file.exists():
        raise FileOperationError(
            f"No state file for sprint {sprint_num}. Sprint may not be started."
        )

    with open(state_file) as f:
        return json.load(f)


def save_state(project_root: Path, sprint_num: int, state: Dict) -> None:
    """
    Save sprint state to file.

    Args:
        project_root: Project root path
        sprint_num: Sprint number
        state: State dictionary to save
    """
    state_file = get_state_file_path(project_root, sprint_num)
    state_file.parent.mkdir(parents=True, exist_ok=True)

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def create_state(
    project_root: Path,
    sprint_num: int,
    sprint_file: Path,
    title: str,
) -> Dict:
    """
    Create new sprint state file.

    Args:
        project_root: Project root path
        sprint_num: Sprint number
        sprint_file: Path to sprint markdown file
        title: Sprint title

    Returns:
        Created state dictionary
    """
    started_time = datetime.now().isoformat()

    state = {
        "sprint_number": sprint_num,
        "sprint_file": str(sprint_file.relative_to(project_root)),
        "sprint_title": title,
        "status": "in_progress",
        "current_phase": 1,
        "current_step": "1.1",
        "started_at": started_time,
        "workflow_version": "3.0",
        "completed_steps": [],
    }

    save_state(project_root, sprint_num, state)
    print(f"✓ State file created: sprint-{sprint_num}-state.json")

    return state


def update_state(
    project_root: Path,
    sprint_num: int,
    updates: Dict,
) -> Dict:
    """
    Update sprint state with new values.

    Args:
        project_root: Project root path
        sprint_num: Sprint number
        updates: Dictionary of fields to update

    Returns:
        Updated state dictionary
    """
    state = load_state(project_root, sprint_num)
    state.update(updates)
    save_state(project_root, sprint_num, state)
    return state


def delete_state(project_root: Path, sprint_num: int) -> None:
    """
    Delete sprint state file.

    Args:
        project_root: Project root path
        sprint_num: Sprint number
    """
    state_file = get_state_file_path(project_root, sprint_num)
    if state_file.exists():
        state_file.unlink()


def state_exists(project_root: Path, sprint_num: int) -> bool:
    """
    Check if state file exists for sprint.

    Args:
        project_root: Project root path
        sprint_num: Sprint number

    Returns:
        True if state file exists
    """
    state_file = get_state_file_path(project_root, sprint_num)
    return state_file.exists()


def load_workflow_steps() -> Dict:
    """
    Load workflow steps definition from ~/.claude/sprint-steps.json

    Returns:
        Workflow steps dictionary

    Raises:
        FileOperationError: If steps file not found
    """
    steps_file = Path.home() / ".claude" / "sprint-steps.json"
    if not steps_file.exists():
        raise FileOperationError(f"Sprint steps definition not found at {steps_file}")

    with open(steps_file) as f:
        return json.load(f)
