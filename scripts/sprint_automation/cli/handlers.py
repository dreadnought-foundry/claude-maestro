"""
Command handlers for sprint automation CLI.

Maps CLI commands to their corresponding functions.
"""

import sys

from ..sprint import (
    create_sprint,
    start_sprint,
    complete_sprint,
    abort_sprint,
    block_sprint,
    resume_sprint,
    recover_sprint,
    get_sprint_status,
    advance_step,
)
from ..epic import (
    create_epic,
    start_epic,
    complete_epic,
    archive_epic,
    get_epic_status,
    list_epics,
    add_to_epic,
)
from ..project import create_project
from ..registry import update_registry


def handle_command(args) -> int:
    """
    Handle CLI command execution.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        if args.command == "sprint-create":
            create_sprint(
                args.sprint_num,
                args.title,
                sprint_type=args.type,
                epic=args.epic,
                dry_run=args.dry_run,
            )
        elif args.command == "sprint-start":
            start_sprint(args.sprint_num, dry_run=args.dry_run)
        elif args.command == "sprint-complete":
            complete_sprint(args.sprint_num, dry_run=args.dry_run)
        elif args.command == "sprint-abort":
            abort_sprint(args.sprint_num, args.reason, dry_run=args.dry_run)
        elif args.command == "sprint-block":
            block_sprint(args.sprint_num, args.reason, dry_run=args.dry_run)
        elif args.command == "sprint-resume":
            resume_sprint(args.sprint_num, dry_run=args.dry_run)
        elif args.command == "sprint-status":
            get_sprint_status(args.sprint_num)
        elif args.command == "sprint-advance":
            advance_step(args.sprint_num, dry_run=args.dry_run)
        elif args.command == "sprint-recover":
            recover_sprint(args.sprint_num, dry_run=args.dry_run)
        elif args.command == "epic-create":
            create_epic(args.epic_num, args.title, dry_run=args.dry_run)
        elif args.command == "epic-start":
            start_epic(args.epic_num, dry_run=args.dry_run)
        elif args.command == "epic-complete":
            complete_epic(args.epic_num, dry_run=args.dry_run)
        elif args.command == "epic-archive":
            archive_epic(args.epic_num, dry_run=args.dry_run)
        elif args.command == "epic-status":
            get_epic_status(args.epic_num)
        elif args.command == "epic-list":
            list_epics()
        elif args.command == "epic-add-sprint":
            add_to_epic(args.sprint_num, args.epic_num, dry_run=args.dry_run)
        elif args.command == "project-create":
            create_project(target_path=args.path, dry_run=args.dry_run)
        elif args.command == "registry-update":
            update_registry(args.sprint_num, args.status, dry_run=args.dry_run)
        else:
            print(f"Unknown command: {args.command}")
            return 1

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
