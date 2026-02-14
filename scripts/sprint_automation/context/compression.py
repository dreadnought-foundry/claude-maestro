"""
Tiered compression strategies for sprint context.

Applies different levels of detail to sprint data based on
relevance to the target sprint:
  - Tier 1 (full): Same-epic sprints, immediately prior sprint
  - Tier 2 (summary): Recent sprints in other epics
  - Tier 3 (one-liner): Old or unrelated sprints
"""

import re
from pathlib import Path
from typing import Dict, List, Optional


def estimate_tokens(text: str) -> int:
    """Approximate token count. 1 token ~ 4 characters."""
    return len(text) // 4


def extract_postmortem_summary(content: str) -> str:
    """
    Extract key sections from a postmortem file.

    Pulls 'What went well', 'What could improve', and 'Key metrics'
    sections, skipping boilerplate.

    Args:
        content: Full postmortem markdown content

    Returns:
        Condensed summary string
    """
    sections = []

    # Extract specific sections by header
    targets = [
        "what went well",
        "what could improve",
        "key metrics",
        "blockers encountered",
        "technical insights",
    ]

    lines = content.split("\n")
    current_section = None
    current_lines: List[str] = []

    for line in lines:
        header_match = re.match(r"^##\s+(.+)", line)
        if header_match:
            # Save previous section if it was a target
            if current_section and current_lines:
                sections.append(f"**{current_section}**")
                sections.extend(current_lines)
                sections.append("")

            header_text = header_match.group(1).strip().lower()
            current_section = None
            current_lines = []

            for target in targets:
                if target in header_text:
                    current_section = header_match.group(1).strip()
                    break
        elif current_section:
            stripped = line.strip()
            # Skip TODO placeholders and HTML comments
            if stripped and not stripped.startswith("TODO") and not stripped.startswith("<!--"):
                current_lines.append(line)

    # Don't forget last section
    if current_section and current_lines:
        sections.append(f"**{current_section}**")
        sections.extend(current_lines)

    return "\n".join(sections).strip()


def extract_sprint_summary(content: str) -> str:
    """
    Extract goal and key requirements from a sprint spec file.

    Pulls the Goal section and requirement headers (not full details).

    Args:
        content: Full sprint markdown content

    Returns:
        Condensed summary string
    """
    sections = []
    lines = content.split("\n")
    in_goal = False
    in_requirements = False
    goal_lines: List[str] = []

    for line in lines:
        header_match = re.match(r"^##\s+(.+)", line)
        subheader_match = re.match(r"^###\s+(.+)", line)

        if header_match:
            header_text = header_match.group(1).strip().lower()
            if "goal" in header_text:
                in_goal = True
                in_requirements = False
                continue
            elif "requirements" in header_text or "requirement" in header_text:
                in_goal = False
                in_requirements = True
                continue
            else:
                # Save goal if we were collecting it
                if in_goal and goal_lines:
                    sections.append("**Goal:** " + " ".join(
                        l.strip() for l in goal_lines if l.strip()
                    ))
                in_goal = False
                in_requirements = False
                goal_lines = []

        if in_goal:
            goal_lines.append(line)
        elif in_requirements and subheader_match:
            sections.append(f"- {subheader_match.group(1).strip()}")

    # Capture goal if file ended during goal section
    if in_goal and goal_lines:
        sections.append("**Goal:** " + " ".join(
            l.strip() for l in goal_lines if l.strip()
        ))

    return "\n".join(sections).strip()


def extract_decisions(content: str) -> List[str]:
    """
    Extract key decisions from a sprint spec or postmortem.

    Looks for patterns like "Decision:", "Chose X over Y",
    or items in a 'Key Decisions' section.

    Args:
        content: Markdown content to scan

    Returns:
        List of decision strings
    """
    decisions = []
    lines = content.split("\n")
    in_decisions = False

    for line in lines:
        header_match = re.match(r"^##\s+(.+)", line)
        if header_match:
            header_text = header_match.group(1).strip().lower()
            in_decisions = "decision" in header_text
            continue

        if in_decisions:
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* "):
                decisions.append(stripped[2:])

    return decisions


def compress_tier1(
    sprint_num: int,
    sprint_content: str,
    postmortem_content: Optional[str],
) -> str:
    """
    Tier 1: Full detail for highly relevant sprints.

    Includes full postmortem and sprint summary.

    Args:
        sprint_num: Sprint number
        sprint_content: Full sprint spec content
        postmortem_content: Full postmortem content (if exists)

    Returns:
        Formatted tier 1 context block
    """
    parts = [f"#### Sprint {sprint_num}"]

    # Full sprint summary (goal + requirements)
    summary = extract_sprint_summary(sprint_content)
    if summary:
        parts.append(summary)

    # Full postmortem details
    if postmortem_content:
        pm_summary = extract_postmortem_summary(postmortem_content)
        if pm_summary:
            parts.append("")
            parts.append(pm_summary)

    return "\n".join(parts)


def compress_tier2(
    sprint_num: int,
    title: str,
    sprint_content: str,
    postmortem_content: Optional[str],
) -> str:
    """
    Tier 2: Summary for moderately relevant sprints.

    Includes goal and key metrics only.

    Args:
        sprint_num: Sprint number
        title: Sprint title
        sprint_content: Full sprint spec content
        postmortem_content: Full postmortem content (if exists)

    Returns:
        Formatted tier 2 context block
    """
    parts = [f"- **Sprint {sprint_num}: {title}**"]

    # Just the goal
    summary = extract_sprint_summary(sprint_content)
    if summary:
        # Take only the goal line
        for line in summary.split("\n"):
            if line.startswith("**Goal:**"):
                parts.append(f"  {line}")
                break

    # Key metrics from postmortem if available
    if postmortem_content:
        for line in postmortem_content.split("\n"):
            if "files changed" in line.lower() or "tests:" in line.lower():
                parts.append(f"  {line.strip()}")

    return "\n".join(parts)


def compress_tier3(sprint_num: int, title: str, status: str) -> str:
    """
    Tier 3: One-liner for old/unrelated sprints.

    Args:
        sprint_num: Sprint number
        title: Sprint title
        status: Sprint status

    Returns:
        Single-line summary
    """
    return f"- Sprint {sprint_num}: {title} ({status})"
