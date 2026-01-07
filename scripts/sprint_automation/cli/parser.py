"""
Command-line argument parsing for sprint automation.

Defines the argument parser structure for all sprint/epic commands.
"""

import argparse


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for sprint automation.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Sprint lifecycle automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Sprint commands
    sprint_create = subparsers.add_parser("sprint-create", help="Create new sprint")
    sprint_create.add_argument("sprint_num", type=int, help="Sprint number")
    sprint_create.add_argument("title", help="Sprint title")
    sprint_create.add_argument("--type", default="fullstack", help="Sprint type")
    sprint_create.add_argument("--epic", type=int, help="Epic number (optional)")
    sprint_create.add_argument("--dry-run", action="store_true", help="Preview only")

    sprint_start = subparsers.add_parser("sprint-start", help="Start sprint")
    sprint_start.add_argument("sprint_num", type=int, help="Sprint number")
    sprint_start.add_argument("--dry-run", action="store_true", help="Preview only")

    sprint_complete = subparsers.add_parser("sprint-complete", help="Complete sprint")
    sprint_complete.add_argument("sprint_num", type=int, help="Sprint number")
    sprint_complete.add_argument("--dry-run", action="store_true", help="Preview only")

    sprint_abort = subparsers.add_parser("sprint-abort", help="Abort sprint")
    sprint_abort.add_argument("sprint_num", type=int, help="Sprint number")
    sprint_abort.add_argument("reason", help="Abort reason")
    sprint_abort.add_argument("--dry-run", action="store_true", help="Preview only")

    sprint_block = subparsers.add_parser("sprint-block", help="Block sprint")
    sprint_block.add_argument("sprint_num", type=int, help="Sprint number")
    sprint_block.add_argument("reason", help="Block reason")
    sprint_block.add_argument("--dry-run", action="store_true", help="Preview only")

    sprint_resume = subparsers.add_parser("sprint-resume", help="Resume blocked sprint")
    sprint_resume.add_argument("sprint_num", type=int, help="Sprint number")
    sprint_resume.add_argument("--dry-run", action="store_true", help="Preview only")

    sprint_status = subparsers.add_parser("sprint-status", help="Show sprint status")
    sprint_status.add_argument("sprint_num", type=int, help="Sprint number")

    sprint_advance = subparsers.add_parser(
        "sprint-advance", help="Advance to next step"
    )
    sprint_advance.add_argument("sprint_num", type=int, help="Sprint number")
    sprint_advance.add_argument("--dry-run", action="store_true", help="Preview only")

    sprint_recover = subparsers.add_parser(
        "sprint-recover", help="Recover misplaced sprint"
    )
    sprint_recover.add_argument("sprint_num", type=int, help="Sprint number")
    sprint_recover.add_argument("--dry-run", action="store_true", help="Preview only")

    # Epic commands
    epic_create = subparsers.add_parser("epic-create", help="Create new epic")
    epic_create.add_argument("epic_num", type=int, help="Epic number")
    epic_create.add_argument("title", help="Epic title")
    epic_create.add_argument("--dry-run", action="store_true", help="Preview only")

    epic_start = subparsers.add_parser("epic-start", help="Start epic")
    epic_start.add_argument("epic_num", type=int, help="Epic number")
    epic_start.add_argument("--dry-run", action="store_true", help="Preview only")

    epic_complete = subparsers.add_parser("epic-complete", help="Complete epic")
    epic_complete.add_argument("epic_num", type=int, help="Epic number")
    epic_complete.add_argument("--dry-run", action="store_true", help="Preview only")

    epic_archive = subparsers.add_parser("epic-archive", help="Archive completed epic")
    epic_archive.add_argument("epic_num", type=int, help="Epic number")
    epic_archive.add_argument("--dry-run", action="store_true", help="Preview only")

    epic_status = subparsers.add_parser("epic-status", help="Show epic status")
    epic_status.add_argument("epic_num", type=int, help="Epic number")

    subparsers.add_parser("epic-list", help="List all epics")

    epic_add_sprint = subparsers.add_parser(
        "epic-add-sprint", help="Add sprint to epic"
    )
    epic_add_sprint.add_argument("sprint_num", type=int, help="Sprint number")
    epic_add_sprint.add_argument("epic_num", type=int, help="Epic number")
    epic_add_sprint.add_argument("--dry-run", action="store_true", help="Preview only")

    # Project commands
    project_create = subparsers.add_parser("project-create", help="Create new project")
    project_create.add_argument("--path", help="Target path (optional)")
    project_create.add_argument("--dry-run", action="store_true", help="Preview only")

    # Registry commands
    registry_update = subparsers.add_parser("registry-update", help="Update registry")
    registry_update.add_argument("sprint_num", type=int, help="Sprint number")
    registry_update.add_argument("status", help="New status")
    registry_update.add_argument("--dry-run", action="store_true", help="Preview only")

    return parser
