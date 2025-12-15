---
description: "Sync workflow updates from master environment to project"
allowed-tools: [Read, Write, Bash, Glob]
---

# Update Project Workflow

Sync workflow updates from the master environment (`~/.claude/`) to the current project.

## Instructions

### 1. Determine Target Project

Parse $ARGUMENTS:
- If empty, use current working directory
- If a path is provided, use that path

```bash
TARGET_PATH="${ARGUMENTS:-$(pwd)}"
```

### 2. Validate Project Setup

Check that the project has been initialized:

```bash
ls -la "$TARGET_PATH/.claude" 2>/dev/null
```

If `.claude/` doesn't exist:
```
ERROR: Project not initialized with workflow system.
Run /project-create first to initialize.
```

### 3. Backup Current Files (Optional)

Create a backup before updating:

```bash
BACKUP_DIR="$TARGET_PATH/.claude/.backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r "$TARGET_PATH/.claude/commands" "$BACKUP_DIR/" 2>/dev/null || true
cp -r "$TARGET_PATH/.claude/hooks" "$BACKUP_DIR/" 2>/dev/null || true
cp "$TARGET_PATH/.claude/sprint-steps.json" "$BACKUP_DIR/" 2>/dev/null || true
```

### 4. Compare and Update Commands

Sync commands from master, tracking changes:

```bash
# Get list of master commands
MASTER_COMMANDS=$(ls ~/.claude/commands/*.md 2>/dev/null)

# Track changes
ADDED=()
UPDATED=()
UNCHANGED=()

for cmd in $MASTER_COMMANDS; do
  filename=$(basename "$cmd")
  target="$TARGET_PATH/.claude/commands/$filename"

  if [ ! -f "$target" ]; then
    # New command
    cp "$cmd" "$target"
    ADDED+=("$filename")
  elif ! diff -q "$cmd" "$target" > /dev/null 2>&1; then
    # Changed command
    cp "$cmd" "$target"
    UPDATED+=("$filename")
  else
    UNCHANGED+=("$filename")
  fi
done
```

### 5. Update Hooks

Sync hooks from master:

```bash
# Copy updated hooks
for hook in ~/.claude/hooks/*.py; do
  filename=$(basename "$hook")
  target="$TARGET_PATH/.claude/hooks/$filename"

  if [ ! -f "$target" ]; then
    cp "$hook" "$target"
    echo "Added: hooks/$filename"
  elif ! diff -q "$hook" "$target" > /dev/null 2>&1; then
    cp "$hook" "$target"
    echo "Updated: hooks/$filename"
  fi
done
```

### 6. Update Configuration Files

Sync workflow configuration:

```bash
# Update sprint-steps.json if master has newer version
if [ -f ~/.claude/sprint-steps.json ]; then
  if [ ! -f "$TARGET_PATH/.claude/sprint-steps.json" ]; then
    cp ~/.claude/sprint-steps.json "$TARGET_PATH/.claude/"
    echo "Added: sprint-steps.json"
  elif ! diff -q ~/.claude/sprint-steps.json "$TARGET_PATH/.claude/sprint-steps.json" > /dev/null 2>&1; then
    cp ~/.claude/sprint-steps.json "$TARGET_PATH/.claude/"
    echo "Updated: sprint-steps.json"
  fi
fi

# Update schema if exists
if [ -f ~/.claude/sprint-state.schema.json ]; then
  cp ~/.claude/sprint-state.schema.json "$TARGET_PATH/.claude/" 2>/dev/null
fi
```

### 7. Preserve Project-Specific Files

These files should NOT be overwritten (project-specific):
- `.claude/settings.json` - Project settings
- `.claude/mcp.json` - MCP configuration
- `.claude/sprint-*-state.json` - Sprint state files
- `.claude/product-state.json` - Product state
- `CLAUDE.md` - Project instructions (user customized)

### 8. Report Changes

Generate a summary of changes:

```
Project workflow updated: $TARGET_PATH

Changes from master (~/.claude/):

Commands:
  Added:    [list of new commands]
  Updated:  [list of changed commands]
  Unchanged: [count] commands

Hooks:
  Added:    [list of new hooks]
  Updated:  [list of changed hooks]

Configuration:
  [sprint-steps.json status]

Preserved (not overwritten):
  - .claude/settings.json
  - .claude/mcp.json
  - .claude/sprint-*-state.json
  - CLAUDE.md

Backup created at: $BACKUP_DIR (if created)

Note: Review any updated commands for breaking changes.
```

### 9. Version Tracking (Optional)

If master has a version file, track it:

```bash
# Check workflow version
if [ -f ~/.claude/WORKFLOW_VERSION ]; then
  cp ~/.claude/WORKFLOW_VERSION "$TARGET_PATH/.claude/"
  echo "Workflow version: $(cat ~/.claude/WORKFLOW_VERSION)"
fi
```

## Flags

- `--dry-run` - Show what would be changed without making changes
- `--force` - Overwrite all files including project-specific ones (use with caution)
- `--no-backup` - Skip creating backup

## Examples

```bash
# Update current project
/project-update

# Update specific project
/project-update /path/to/project

# Preview changes without applying
/project-update --dry-run

# Force update everything
/project-update --force
```
