"""
Constants used throughout sprint automation.

This module defines all magic strings, status suffixes, folder names,
and other constants to ensure consistency across the codebase.
"""

# Status suffixes for sprint and epic files
STATUS_DONE = "--done"
STATUS_ABORTED = "--aborted"
STATUS_BLOCKED = "--blocked"

# Sprint status folder names
FOLDER_BACKLOG = "0-backlog"
FOLDER_TODO = "1-todo"
FOLDER_IN_PROGRESS = "2-in-progress"
FOLDER_DONE = "3-done"
FOLDER_BLOCKED = "4-blocked"
FOLDER_ABANDONED = "5-abandoned"
FOLDER_ARCHIVED = "6-archived"

# Special directory names
STANDALONE_DIR = "_standalone"
EPIC_FILE = "_epic.md"

# All status folders in order
STATUS_FOLDERS = [
    FOLDER_BACKLOG,
    FOLDER_TODO,
    FOLDER_IN_PROGRESS,
    FOLDER_DONE,
    FOLDER_BLOCKED,
    FOLDER_ABANDONED,
    FOLDER_ARCHIVED,
]

# Registry file structure
REGISTRY_VERSION = "1.0"
REGISTRY_FILENAME = "registry.json"

# Sprint file patterns
SPRINT_PATTERN = "sprint-{num:02d}_*"
EPIC_PATTERN = "epic-{num:02d}_*"
POSTMORTEM_SUFFIX = "_postmortem.md"

# YAML frontmatter keys
YAML_STATUS = "status"
YAML_COMPLETED = "completed"
YAML_STARTED = "started"
YAML_BLOCKED_REASON = "blocked_reason"
YAML_ABORTED_REASON = "aborted_reason"
YAML_EPIC = "epic"
YAML_SPRINT = "sprint"
YAML_TITLE = "title"

# State file
STATE_FILE = ".claude/sprint-state.json"

# Directory structure
DOCS_DIR = "docs"
SPRINTS_DIR = "sprints"
CLAUDE_DIR = ".claude"
