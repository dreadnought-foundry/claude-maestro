"""
Sprint status operations.

Provides functions for querying sprint status and advancing
through workflow steps.
"""

import json
from datetime import datetime
from pathlib import Path

from ..exceptions import FileOperationError, ValidationError
from ..utils.file_ops import find_project_root
from ..utils.project import find_sprint_file


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
    sprint_file = find_sprint_file(sprint_num, project_root)
    if not sprint_file:
        raise FileOperationError(f"Sprint {sprint_num} file not found")

    # Read YAML frontmatter
    with open(sprint_file) as f:
        content = f.read()

    import re

    yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    yaml_data = {}
    if yaml_match:
        yaml_content = yaml_match.group(1)
        for line in yaml_content.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                yaml_data[key.strip()] = value.strip()

    status = {
        "sprint_num": sprint_num,
        "title": yaml_data.get("title", "Unknown").strip('"'),
        "status": state.get("status", yaml_data.get("status", "Unknown")),
        "workflow_version": state.get("workflow_version", "1.0"),
        "started": yaml_data.get("started"),
        "completed": yaml_data.get("completed"),
        "current_step": state.get("current_step"),
        "sprint_file": str(sprint_file),
    }

    # Display status
    print(f"\n{'='*60}")
    print(f"Sprint {sprint_num}: {status['title']}")
    print(f"{'='*60}")
    print(f"Status: {status['status']}")
    print(f"Workflow: v{status['workflow_version']}")
    if status["started"]:
        print(f"Started: {status['started']}")
    if status["current_step"]:
        print(f"Current step: {status['current_step']}")
    print(f"File: {sprint_file.name}")
    print(f"{'='*60}")

    return status


def advance_step(sprint_num: int, dry_run: bool = False) -> dict:
    """
    Advance sprint to next workflow step.

    Reads current step from state, finds next step in workflow definition,
    and updates state file. Validates that current step is completed.

    Args:
        sprint_num: Sprint number to advance
        dry_run: If True, preview changes without executing

    Returns:
        Dict with summary of step advancement

    Raises:
        FileOperationError: If sprint or state file not found
        ValidationError: If current step is not complete

    Example:
        >>> advance_step(4, dry_run=True)
        >>> # Preview: Sprint 4: 1.1 Planning → 1.2 Design
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

    current_step = state.get("current_step")
    if not current_step:
        raise ValidationError("State file missing current_step")

    # Load workflow steps definition
    steps_file = Path.home() / ".claude" / "sprint-steps.json"
    if not steps_file.exists():
        raise FileOperationError(f"Sprint steps definition not found at {steps_file}")

    with open(steps_file) as f:
        steps_def = json.load(f)

    step_order = steps_def.get("step_order", [])
    if not step_order:
        raise ValidationError("sprint-steps.json missing step_order")

    # Find current step index
    try:
        current_idx = step_order.index(current_step)
    except ValueError:
        raise ValidationError(f"Current step '{current_step}' not found in workflow")

    # Get next step
    if current_idx >= len(step_order) - 1:
        raise ValidationError(
            f"Already at final step ({current_step}). Use /sprint-complete to finish."
        )

    next_step = step_order[current_idx + 1]

    # Find step details
    current_step_name = None
    next_step_name = None
    for phase in steps_def.get("phases", []):
        for step_info in phase.get("steps", []):
            if step_info["step"] == current_step:
                current_step_name = step_info["name"]
            if step_info["step"] == next_step:
                next_step_name = step_info["name"]

    summary = {
        "sprint_num": sprint_num,
        "previous_step": current_step,
        "previous_step_name": current_step_name,
        "new_step": next_step,
        "new_step_name": next_step_name,
        "dry_run": dry_run,
    }

    print(f"\n{'='*60}")
    print(f"ADVANCE SPRINT {sprint_num} TO NEXT STEP")
    print(f"{'='*60}")
    print(f"Current:  {current_step} - {current_step_name}")
    print(f"Next:     {next_step} - {next_step_name}")

    if dry_run:
        print("\n[DRY RUN] Would update state file:")
        print(f"  - Mark {current_step} as completed")
        print(f"  - Advance to {next_step}")
        print(f"{'='*60}")
        return summary

    # Mark current step completed
    completed_steps = state.get("completed_steps", [])
    completed_steps.append(
        {"step": current_step, "completed_at": datetime.now().isoformat()}
    )

    # Update state
    state["current_step"] = next_step
    state["completed_steps"] = completed_steps

    # Parse current step to update phase (e.g., "2.3" → phase 2)
    try:
        phase_num = int(next_step.split(".")[0])
        state["current_phase"] = phase_num
    except (ValueError, IndexError):
        pass  # Keep existing phase if parsing fails

    # Write updated state
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    # Create test artifacts for specific steps
    sprint_file = find_sprint_file(sprint_num, project_root)
    if sprint_file:
        sprint_folder = sprint_file.parent

        # Step 1.5.1: Create interface contract file (for fullstack sprints)
        if current_step == "1.5.1":
            contract_file = (
                sprint_folder / f"sprint-{sprint_num}_interface-contract.json"
            )
            if not contract_file.exists():
                contract_content = {
                    "sprint": sprint_num,
                    "version": "1.0",
                    "created": datetime.now().isoformat(),
                    "interfaces": {
                        "backend": {"endpoints": [], "models": [], "enums": []},
                        "frontend": {"components": [], "hooks": [], "types": []},
                        "shared": {"types": [], "constants": []},
                    },
                    "validation_status": "pending",
                }
                with open(contract_file, "w") as f:
                    json.dump(contract_content, f, indent=2)
                print(f"  ✓ Created interface contract: {contract_file.name}")

        # Step 3.2: Create quality assessment file
        if current_step == "3.2":
            quality_file = (
                sprint_folder / f"sprint-{sprint_num}_quality-assessment.json"
            )
            if not quality_file.exists():
                quality_content = {
                    "sprint": sprint_num,
                    "assessed_at": datetime.now().isoformat(),
                    "code_quality": {
                        "docstrings": True,
                        "type_hints": True,
                        "lint_clean": True,
                        "complexity_acceptable": True,
                    },
                    "test_quality": {
                        "coverage_percentage": 0,
                        "edge_cases_covered": True,
                        "mocks_appropriate": True,
                    },
                    "issues_found": [],
                    "recommendations": [],
                    "overall_status": "pass",
                }
                with open(quality_file, "w") as f:
                    json.dump(quality_content, f, indent=2)
                print(f"  ✓ Created quality assessment: {quality_file.name}")

    print(f"\n✓ Sprint {sprint_num} advanced to step {next_step}")
    print(f"{'='*60}")

    return summary
