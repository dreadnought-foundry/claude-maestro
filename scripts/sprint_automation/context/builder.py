"""
Context builder for sprint prompts.

Reads prior sprint data, postmortems, registry, and project config
to generate a structured context brief. The brief gives Claude full
awareness of what has been built, what decisions were made, and what
the current project state is before starting a new sprint.

Usage:
    brief = build_context(21)
    print(brief)  # Structured markdown ready for sprint prompt
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..constants import POSTMORTEM_SUFFIX
from ..exceptions import FileOperationError, ValidationError
from ..utils.file_ops import find_project_root
from ..utils.project import find_sprint_file, get_registry_path, get_sprints_dir
from .compression import (
    compress_tier1,
    compress_tier2,
    compress_tier3,
    estimate_tokens,
)

# Default token budget for the context brief
DEFAULT_TOKEN_BUDGET = 8000


def _load_registry(project_root: Path) -> Dict:
    """Load the sprint/epic registry."""
    registry_path = get_registry_path(project_root)
    if not registry_path.exists():
        raise FileOperationError(f"Registry not found at {registry_path}")

    with open(registry_path) as f:
        return json.load(f)


def _find_postmortem(sprint_num: int, project_root: Path) -> Optional[str]:
    """
    Find and read a sprint's postmortem file.

    Searches all sprint directories for a matching postmortem.

    Args:
        sprint_num: Sprint number
        project_root: Project root path

    Returns:
        Postmortem content string, or None if not found
    """
    sprints_dir = get_sprints_dir(project_root)
    pattern = f"sprint-{sprint_num}*{POSTMORTEM_SUFFIX}"

    # Search recursively
    for pm_file in sprints_dir.rglob(pattern):
        if pm_file.is_file():
            return pm_file.read_text()

    # Also check for postmortem section embedded in sprint file
    sprint_file = _find_sprint_file_extended(sprint_num, project_root)
    if sprint_file and sprint_file.exists():
        content = sprint_file.read_text()
        if "## Postmortem" in content or "### What went well" in content:
            # Extract postmortem section from the end of the file
            lines = content.split("\n")
            pm_start = None
            for i, line in enumerate(lines):
                if re.match(r"^##\s+Postmortem", line):
                    pm_start = i
                    break
            if pm_start is not None:
                return "\n".join(lines[pm_start:])

    return None


def _find_sprint_file_extended(sprint_num: int, project_root: Path) -> Optional[Path]:
    """
    Find sprint file with extended search.

    Extends the base find_sprint_file to also check for sprint.md
    inside sprint-named directories (a common Maestro pattern).

    Args:
        sprint_num: Sprint number
        project_root: Project root path

    Returns:
        Path to sprint file if found, None otherwise
    """
    # Try the standard finder first
    result = find_sprint_file(sprint_num, project_root)
    if result:
        return result

    # Fallback: look for sprint.md inside sprint-NN_ directories
    sprints_dir = get_sprints_dir(project_root)
    dir_pattern = f"sprint-{sprint_num:02d}_*"

    for status_dir in sprints_dir.glob("*"):
        if not status_dir.is_dir():
            continue

        # Check direct children directories
        for sprint_dir in status_dir.glob(dir_pattern):
            if sprint_dir.is_dir():
                sprint_md = sprint_dir / "sprint.md"
                if sprint_md.exists():
                    return sprint_md

        # Check inside epic folders and _standalone
        for sprint_dir in status_dir.glob(f"**/{dir_pattern}"):
            if sprint_dir.is_dir():
                sprint_md = sprint_dir / "sprint.md"
                if sprint_md.exists():
                    return sprint_md

    return None


def _read_sprint_content(sprint_num: int, project_root: Path) -> Optional[str]:
    """Read a sprint's spec file content."""
    sprint_file = _find_sprint_file_extended(sprint_num, project_root)
    if sprint_file and sprint_file.exists():
        return sprint_file.read_text()
    return None


def _read_claude_md(project_root: Path) -> Optional[str]:
    """Read the project's CLAUDE.md file."""
    claude_md = project_root / "CLAUDE.md"
    if claude_md.exists():
        return claude_md.read_text()
    return None


def _extract_project_summary(claude_md_content: str) -> str:
    """
    Extract key project info from CLAUDE.md.

    Pulls tech stack, team structure, code standards — not the
    workflow docs (which are Maestro's, not the project's).

    Args:
        claude_md_content: Full CLAUDE.md content

    Returns:
        Condensed project summary
    """
    sections = []
    lines = claude_md_content.split("\n")
    capture = False
    capture_depth = 0

    # Sections we want to capture from the project's CLAUDE.md
    target_sections = [
        "tech stack",
        "team structure",
        "code standards",
        "testing requirements",
        "deployment",
        "environment variables",
        "design reference",
    ]

    # Sections to skip (Maestro workflow docs)
    skip_sections = [
        "workflow system",
        "sprint workflow",
        "quick start",
        "how it works",
        "phases overview",
        "key features",
        "project setup",
        "enforcement rules",
        "sprint types",
        "sprint directories",
        "epic management",
    ]

    for line in lines:
        h2_match = re.match(r"^##\s+(.+)", line)
        h3_match = re.match(r"^###\s+(.+)", line)

        if h2_match:
            header = h2_match.group(1).strip().lower()
            # Check if this is a section to skip
            if any(skip in header for skip in skip_sections):
                capture = False
                continue
            # Check if it matches a target or is project-specific
            if any(target in header for target in target_sections):
                capture = True
                capture_depth = 2
                sections.append(line)
                continue
            # Any h2 that starts with "project:" is project-specific
            if "project" in header:
                capture = True
                capture_depth = 2
                sections.append(line)
                continue
            capture = False

        elif h3_match and capture:
            header = h3_match.group(1).strip().lower()
            if any(skip in header for skip in skip_sections):
                continue
            sections.append(line)

        elif capture:
            sections.append(line)

    return "\n".join(sections).strip()


def _assign_tiers(
    target_sprint: int,
    registry: Dict,
) -> Dict[int, int]:
    """
    Assign compression tiers to completed sprints.

    Tier assignment rules:
      - Tier 1: Same epic as target, or immediately prior sprint
      - Tier 2: Different epic but recent (within last 5 sprints)
      - Tier 3: Everything else

    Args:
        target_sprint: The sprint number about to start
        registry: Full registry data

    Returns:
        Dict mapping sprint_num -> tier (1, 2, or 3)
    """
    sprints = registry.get("sprints", {})
    target_data = sprints.get(str(target_sprint), {})
    target_epic = target_data.get("epic")

    tiers = {}
    completed_sprints = sorted(
        [
            int(num)
            for num, data in sprints.items()
            if data.get("status") == "done" and int(num) != target_sprint
        ]
    )

    if not completed_sprints:
        return tiers

    # Most recent sprint is always tier 1
    most_recent = completed_sprints[-1]

    for sprint_num in completed_sprints:
        sprint_data = sprints[str(sprint_num)]
        sprint_epic = sprint_data.get("epic")

        if sprint_num == most_recent:
            tiers[sprint_num] = 1
        elif target_epic and sprint_epic == target_epic:
            # Same epic = tier 1
            tiers[sprint_num] = 1
        elif sprint_num >= target_sprint - 5:
            # Recent sprint = tier 2
            tiers[sprint_num] = 2
        else:
            # Old/unrelated = tier 3
            tiers[sprint_num] = 3

    return tiers


def build_context(
    target_sprint: int,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    output_file: Optional[str] = None,
) -> str:
    """
    Build a structured context brief for an upcoming sprint.

    Reads all available project data and generates a markdown document
    with tiered compression to fit within a token budget.

    Args:
        target_sprint: Sprint number about to start
        token_budget: Maximum approximate tokens for the brief
        output_file: Optional path to write brief to (default: .claude/sprint-N-context.md)

    Returns:
        Formatted markdown context brief

    Raises:
        FileOperationError: If project root or registry not found
        ValidationError: If target sprint not found in registry
    """
    project_root = find_project_root()
    registry = _load_registry(project_root)

    sprints = registry.get("sprints", {})
    epics = registry.get("epics", {})

    # Validate target sprint exists
    if str(target_sprint) not in sprints:
        raise ValidationError(
            f"Sprint {target_sprint} not found in registry. "
            f"Available: {', '.join(sorted(sprints.keys(), key=int))}"
        )

    target_data = sprints[str(target_sprint)]
    target_epic = target_data.get("epic")

    # Start building the brief
    parts: List[str] = []

    # Header
    parts.append(f"# Context Brief - Sprint {target_sprint}: {target_data['title']}")
    parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    parts.append("")

    # Project summary from CLAUDE.md
    claude_md = _read_claude_md(project_root)
    if claude_md:
        project_summary = _extract_project_summary(claude_md)
        if project_summary:
            parts.append("## Project Configuration")
            parts.append(project_summary)
            parts.append("")

    # Project state overview
    total_sprints = len(sprints)
    done_sprints = sum(1 for s in sprints.values() if s.get("status") == "done")
    parts.append("## Project State")
    parts.append(f"- {done_sprints}/{total_sprints} sprints completed")

    if epics:
        parts.append(f"- {len(epics)} epics defined")
        for epic_num, epic_data in sorted(epics.items(), key=lambda x: int(x[0])):
            status = epic_data.get("status", "unknown")
            title = epic_data.get("title", "Untitled")
            completed = epic_data.get("completedSprints", 0)
            total = epic_data.get("totalSprints", 0)
            parts.append(f"  - Epic {epic_num}: {title} ({completed}/{total} sprints, {status})")

    if target_epic:
        epic_data = epics.get(str(target_epic), {})
        parts.append(f"- **Current epic**: {target_epic} - {epic_data.get('title', 'Unknown')}")

    parts.append("")

    # Assign compression tiers
    tiers = _assign_tiers(target_sprint, registry)

    # Separate sprints by tier
    tier1_sprints = sorted([s for s, t in tiers.items() if t == 1])
    tier2_sprints = sorted([s for s, t in tiers.items() if t == 2])
    tier3_sprints = sorted([s for s, t in tiers.items() if t == 3])

    # Tier 1: Full detail
    if tier1_sprints:
        parts.append("## Relevant Prior Work (Full Detail)")
        parts.append("")

        for sprint_num in tier1_sprints:
            sprint_content = _read_sprint_content(sprint_num, project_root)
            postmortem_content = _find_postmortem(sprint_num, project_root)
            sprint_data = sprints[str(sprint_num)]

            if sprint_content:
                block = compress_tier1(sprint_num, sprint_content, postmortem_content)
            else:
                block = compress_tier3(
                    sprint_num, sprint_data.get("title", "Unknown"), "done"
                )

            parts.append(block)
            parts.append("")

            # Check token budget
            current_tokens = estimate_tokens("\n".join(parts))
            if current_tokens > token_budget * 0.7:
                # Demote remaining tier 1 to tier 2
                remaining = tier1_sprints[tier1_sprints.index(sprint_num) + 1:]
                tier2_sprints = sorted(remaining + tier2_sprints)
                break

    # Tier 2: Summaries
    if tier2_sprints:
        parts.append("## Other Recent Work (Summary)")
        parts.append("")

        for sprint_num in tier2_sprints:
            sprint_content = _read_sprint_content(sprint_num, project_root)
            postmortem_content = _find_postmortem(sprint_num, project_root)
            sprint_data = sprints[str(sprint_num)]

            if sprint_content:
                block = compress_tier2(
                    sprint_num,
                    sprint_data.get("title", "Unknown"),
                    sprint_content,
                    postmortem_content,
                )
            else:
                block = compress_tier3(
                    sprint_num, sprint_data.get("title", "Unknown"), "done"
                )

            parts.append(block)

            # Check budget
            current_tokens = estimate_tokens("\n".join(parts))
            if current_tokens > token_budget * 0.85:
                # Demote remaining to tier 3
                remaining_idx = tier2_sprints.index(sprint_num) + 1
                tier3_sprints = sorted(
                    tier2_sprints[remaining_idx:] + tier3_sprints
                )
                break

        parts.append("")

    # Tier 3: One-liners
    if tier3_sprints:
        parts.append("## Other Completed Sprints")
        parts.append("")

        for sprint_num in tier3_sprints:
            sprint_data = sprints[str(sprint_num)]
            parts.append(
                compress_tier3(
                    sprint_num,
                    sprint_data.get("title", "Unknown"),
                    sprint_data.get("status", "unknown"),
                )
            )

        parts.append("")

    # Target sprint spec (always included in full, outside token budget)
    target_content = _read_sprint_content(target_sprint, project_root)
    if target_content:
        parts.append("## Target Sprint Spec")
        parts.append("")
        parts.append(target_content)

    brief = "\n".join(parts)

    # Write to file
    if output_file is None:
        output_path = project_root / ".claude" / f"sprint-{target_sprint}-context.md"
    else:
        output_path = Path(output_file)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(brief)

    # Print summary
    total_tokens = estimate_tokens(brief)
    print(f"\n{'='*60}")
    print(f"CONTEXT BRIEF GENERATED")
    print(f"{'='*60}")
    print(f"Target:      Sprint {target_sprint}: {target_data['title']}")
    print(f"Output:      {output_path}")
    print(f"Tokens:      ~{total_tokens:,} (budget: {token_budget:,})")
    print(f"Tier 1:      {len(tier1_sprints)} sprints (full detail)")
    print(f"Tier 2:      {len(tier2_sprints)} sprints (summary)")
    print(f"Tier 3:      {len(tier3_sprints)} sprints (one-liner)")
    print(f"{'='*60}")

    return brief
