"""
Sprint postmortem generation.

Generates postmortem analysis after sprint completion.
"""

import json
import re

from ..exceptions import FileOperationError, ValidationError
from ..utils.file_ops import find_project_root
from ..utils.project import find_sprint_file


def generate_postmortem(sprint_num: int, dry_run: bool = False) -> dict:
    """
    Generate postmortem analysis as a separate file linked from sprint.

    Creates sprint-{N}_postmortem.md with metrics, learnings, and analysis.
    Adds link to postmortem from the sprint file.

    Args:
        sprint_num: Sprint number to generate postmortem for
        dry_run: If True, preview without creating files

    Returns:
        Dict with summary of postmortem generation

    Raises:
        FileOperationError: If sprint file not found
        ValidationError: If sprint is not complete

    Example:
        >>> generate_postmortem(4)
        >>> # Creates: sprint-4_postmortem.md
        >>> # Links from: sprint-4_feature-name--done.md
    """
    project_root = find_project_root()

    # Find sprint file
    sprint_file = find_sprint_file(sprint_num, project_root)
    if not sprint_file:
        raise FileOperationError(f"Sprint {sprint_num} file not found")

    # Read sprint YAML frontmatter
    with open(sprint_file) as f:
        content = f.read()

    yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not yaml_match:
        raise ValidationError(f"Sprint {sprint_num} has no YAML frontmatter")

    yaml_content = yaml_match.group(1)
    title_match = re.search(r"^title:\s*(.+)$", yaml_content, re.MULTILINE)
    sprint_title = (
        title_match.group(1).strip().strip('"')
        if title_match
        else f"Sprint {sprint_num}"
    )

    # Read state file if exists
    state_file = project_root / ".claude" / f"sprint-{sprint_num}-state.json"
    metrics = {}
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)

        # Calculate duration
        started = state.get("started_at")
        completed = state.get("completed_at")
        if started and completed:
            from datetime import datetime

            start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            complete_dt = datetime.fromisoformat(completed.replace("Z", "+00:00"))
            duration = complete_dt - start_dt
            metrics["duration_hours"] = round(duration.total_seconds() / 3600, 1)
            metrics["started_at"] = started
            metrics["completed_at"] = completed

        metrics["completed_steps"] = len(state.get("completed_steps", []))

    # Create postmortem file in same directory as sprint
    postmortem_file = sprint_file.parent / f"sprint-{sprint_num}_postmortem.md"

    # Generate postmortem content
    postmortem_content = f"""# Sprint {sprint_num} Postmortem: {sprint_title}

## Metrics

| Metric | Value |
|--------|-------|
| Sprint Number | {sprint_num} |
| Started | {metrics.get('started_at', 'N/A')} |
| Completed | {metrics.get('completed_at', 'N/A')} |
| Duration | {metrics.get('duration_hours', 'N/A')} hours |
| Steps Completed | {metrics.get('completed_steps', 'N/A')} |
| Files Changed | TODO: Run `git diff --stat` |
| Tests Added | TODO: Count test functions |
| Coverage Delta | TODO: Compare coverage |

## What Went Well

<!-- What worked well during this sprint? -->

- TODO: Add positives

## What Could Improve

<!-- What could be done better next time? -->

- TODO: Add improvements

## Blockers Encountered

<!-- Were there any blockers or unexpected challenges? -->

- TODO: Document blockers

## Technical Insights

<!-- What did we learn technically? -->

- TODO: Add technical learnings

## Process Insights

<!-- What did we learn about our process? -->

- TODO: Add process learnings

## Patterns Discovered

<!-- Any reusable code patterns worth documenting? -->

```
TODO: Add code patterns
```

## Action Items for Next Sprint

- [ ] TODO: Add follow-up tasks

## Notes

<!-- Any other observations or context -->

TODO: Add additional notes
"""

    summary = {
        "sprint_num": sprint_num,
        "postmortem_file": str(postmortem_file),
        "sprint_file": str(sprint_file),
        "dry_run": dry_run,
        "metrics": metrics,
    }

    print(f"\n{'='*60}")
    print(f"GENERATE POSTMORTEM FOR SPRINT {sprint_num}")
    print(f"{'='*60}")
    print(f"Sprint: {sprint_title}")
    if metrics:
        print(f"Duration: {metrics.get('duration_hours', 'N/A')} hours")
        print(f"Steps: {metrics.get('completed_steps', 'N/A')}")
    print(f"Postmortem file: {postmortem_file.name}")

    if dry_run:
        print("\n[DRY RUN] Would create:")
        print(f"  - {postmortem_file}")
        print(f"{'='*60}")
        return summary

    # Write postmortem file
    with open(postmortem_file, "w") as f:
        f.write(postmortem_content)

    print(f"\n✓ Created postmortem file: {postmortem_file.name}")
    print(f"{'='*60}")

    return summary
