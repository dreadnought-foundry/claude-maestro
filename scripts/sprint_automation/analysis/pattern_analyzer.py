"""
Anti-pattern detector for sprint postmortems.

Mines completed sprint postmortems for recurring issues and surfaces
them as early warnings before planning starts. Runs externally via CLI
to avoid context window impact.

Usage:
    python -m sprint_automation.analysis.pattern_analyzer [--limit N] [--json]
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

from ..utils.file_ops import find_project_root


def _extract_postmortem_section(content: str, heading: str) -> list[str]:
    """Extract bullet items from a postmortem subsection."""
    pattern = rf"###\s+{re.escape(heading)}\s*\n(.*?)(?=\n###|\n##|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return []

    section = match.group(1).strip()
    items = []
    for line in section.split("\n"):
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            text = line[2:].strip()
            # Strip action item tags like [done], [backlog], etc.
            text = re.sub(r"`?\[(?:done|sprint|backlog|pattern)\]`?\s*", "", text)
            if text and not text.startswith("TODO"):
                items.append(text)
    return items


def _normalize_issue(text: str) -> str:
    """Normalize issue text for fuzzy grouping."""
    text = text.lower().strip()
    text = re.sub(r"sprint\s+\d+", "sprint N", text)
    text = re.sub(r"\b\d+\b", "N", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _find_completed_sprints(project_root: Path, limit: int = 10) -> list[Path]:
    """Find the most recent completed sprint files with postmortems."""
    sprints_dir = project_root / "docs" / "sprints" / "3-done"
    if not sprints_dir.exists():
        return []

    sprint_files = []
    for f in sprints_dir.glob("**/*--done.md"):
        if "_postmortem" in f.name or "_epic" in f.name:
            continue
        sprint_files.append(f)

    # Sort by modification time (most recent first)
    sprint_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return sprint_files[:limit]


def _group_similar_issues(issues: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Group similar issues by normalized text, return {normalized: [originals]}."""
    groups: dict[str, list[str]] = {}
    for original, source in issues:
        key = _normalize_issue(original)
        # Merge keys that share 3+ consecutive words
        merged = False
        for existing_key in list(groups.keys()):
            existing_words = set(existing_key.split())
            new_words = set(key.split())
            overlap = existing_words & new_words
            if len(overlap) >= 3:
                groups[existing_key].append(f"{original} (from {source})")
                merged = True
                break
        if not merged:
            groups[key] = [f"{original} (from {source})"]
    return groups


def analyze_patterns(
    project_root: Optional[Path] = None,
    limit: int = 10,
    as_json: bool = False,
) -> dict:
    """
    Analyze postmortem history for recurring issues.

    Reads the last N completed sprint postmortems, extracts "What Could Improve"
    and "Action Items" sections, groups similar issues, and returns any that
    appear in 2+ sprints as anti-pattern warnings.

    Args:
        project_root: Project root (auto-detected if None)
        limit: Number of recent sprints to analyze
        as_json: If True, return raw dict; if False, also print human-readable output

    Returns:
        Dict with keys:
            - recurring_issues: [{issue, count, sprints, examples}]
            - sprints_analyzed: int
            - unresolved_action_items: [{item, source_sprint}]
    """
    if project_root is None:
        project_root = find_project_root()

    sprint_files = _find_completed_sprints(project_root, limit)

    if not sprint_files:
        result = {
            "recurring_issues": [],
            "sprints_analyzed": 0,
            "unresolved_action_items": [],
        }
        if not as_json:
            print("No completed sprints found. Skipping pattern analysis.")
        return result

    # Collect issues from each sprint
    improvement_issues: list[tuple[str, str]] = []
    unresolved_items: list[dict] = []

    for sprint_file in sprint_files:
        content = sprint_file.read_text()

        # Extract sprint number from filename
        num_match = re.search(r"sprint-(\d+)", sprint_file.name)
        sprint_label = f"Sprint {num_match.group(1)}" if num_match else sprint_file.stem

        # Mine "What Could Improve"
        improvements = _extract_postmortem_section(content, "What Could Improve")
        for item in improvements:
            improvement_issues.append((item, sprint_label))

        # Mine unresolved action items (unchecked boxes)
        action_items = _extract_postmortem_section(content, "Action Items")
        for item in action_items:
            if not item.startswith("[x]") and not item.startswith("[X]"):
                unresolved_items.append({"item": item, "source_sprint": sprint_label})

    # Group and find recurring issues (2+ occurrences)
    grouped = _group_similar_issues(improvement_issues)
    recurring = []
    for normalized, examples in grouped.items():
        if len(examples) >= 2:
            recurring.append(
                {
                    "issue": examples[0].split(" (from ")[0],
                    "count": len(examples),
                    "examples": examples,
                }
            )

    # Sort by frequency
    recurring.sort(key=lambda x: x["count"], reverse=True)

    result = {
        "recurring_issues": recurring,
        "sprints_analyzed": len(sprint_files),
        "unresolved_action_items": unresolved_items[:10],
    }

    if not as_json:
        _print_report(result)

    return result


def _print_report(result: dict) -> None:
    """Print human-readable pattern analysis report."""
    analyzed = result["sprints_analyzed"]
    recurring = result["recurring_issues"]
    unresolved = result["unresolved_action_items"]

    print(f"\n{'='*60}")
    print(f"ANTI-PATTERN ANALYSIS ({analyzed} sprints analyzed)")
    print(f"{'='*60}")

    if recurring:
        print(f"\nRecurring Issues ({len(recurring)} detected):")
        for issue in recurring:
            print(f"  [{issue['count']}x] {issue['issue']}")
            for ex in issue["examples"][:3]:
                print(f"       - {ex}")
    else:
        print("\nNo recurring issues detected.")

    if unresolved:
        print(f"\nUnresolved Action Items ({len(unresolved)}):")
        for item in unresolved[:5]:
            print(f"  - {item['item']} ({item['source_sprint']})")
    else:
        print("\nNo unresolved action items.")

    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze sprint postmortem patterns")
    parser.add_argument("--limit", type=int, default=10, help="Number of recent sprints to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--project-root", type=str, default=None, help="Project root path")
    args = parser.parse_args()

    root = Path(args.project_root) if args.project_root else None
    result = analyze_patterns(project_root=root, limit=args.limit, as_json=args.json)

    if args.json:
        print(json.dumps(result, indent=2))
        sys.exit(0)

    sys.exit(0 if not result["recurring_issues"] else 1)
