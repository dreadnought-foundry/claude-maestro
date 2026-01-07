"""
Main entry point for sprint automation CLI.

Allows running the package as a module:
    python -m sprint_automation sprint-create 1 "My Sprint"
"""

import sys

from .cli import create_parser, handle_command


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return handle_command(args)


if __name__ == "__main__":
    sys.exit(main())
