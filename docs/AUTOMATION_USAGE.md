# Sprint Lifecycle Automation - Usage Guide

## Overview

The sprint lifecycle automation system provides command-line tools for managing sprints and epics with auto-numbering, registry tracking, and atomic file operations.

## Quick Start

### Creating a New Sprint

```bash
# Auto-assign sprint number and register in registry
python3 scripts/sprint_lifecycle.py register-sprint "Feature Name" --epic 1 --estimated-hours 5

# Or use the /sprint-new command (recommended)
/sprint-new "Feature Name" --epic=1 --estimated-hours=5
```

### Creating a New Epic

```bash
# Auto-assign epic number
python3 scripts/sprint_lifecycle.py register-epic "Epic Title" --sprint-count 5 --estimated-hours 20

# Or use the /epic-new command (recommended)
/epic-new "Epic Title"
```

### Completing a Sprint

```bash
# Preview what will happen (dry-run)
python3 scripts/sprint_lifecycle.py move-to-done 2 --dry-run

# Execute the move
python3 scripts/sprint_lifecycle.py move-to-done 2

# Update registry with completion metadata
python3 scripts/sprint_lifecycle.py update-registry 2 --status done --completed 2026-01-01 --hours 4.5

# Create git tag
python3 scripts/sprint_lifecycle.py create-tag 2 "Sprint Title"

# Check if epic is complete
python3 scripts/sprint_lifecycle.py check-epic 1

# Or use the /sprint-complete command (recommended)
/sprint-complete 2
```

## Detailed Command Reference

### `register-sprint`

Auto-assign next available sprint number and register in registry.

```bash
python3 scripts/sprint_lifecycle.py register-sprint "Sprint Title" [OPTIONS]

Options:
  --epic N              Link sprint to epic N
  --estimated-hours H   Set estimated hours
  --dry-run             Preview without executing
```

**Example:**
```bash
$ python3 scripts/sprint_lifecycle.py register-sprint "User Authentication" --epic 2 --estimated-hours 8
Registered sprint 7: User Authentication
Linked to Epic 2
Registry updated: nextSprintNumber -> 8
```

### `register-epic`

Auto-assign next available epic number and register in registry.

```bash
python3 scripts/sprint_lifecycle.py register-epic "Epic Title" [OPTIONS]

Options:
  --sprint-count N      Number of sprints planned
  --estimated-hours H   Total estimated hours
  --dry-run             Preview without executing
```

**Example:**
```bash
$ python3 scripts/sprint_lifecycle.py register-epic "Mobile App v2.0" --sprint-count 6 --estimated-hours 30
Registered epic 3: Mobile App v2.0
Planned sprints: 6
Registry updated: nextEpicNumber -> 4
```

### `next-sprint-number`

Query the next available sprint number without registering.

```bash
python3 scripts/sprint_lifecycle.py next-sprint-number --dry-run

Output:
[DRY RUN] Next sprint number: 7
[DRY RUN] Would increment to: 8
```

### `next-epic-number`

Query the next available epic number without registering.

```bash
python3 scripts/sprint_lifecycle.py next-epic-number --dry-run

Output:
[DRY RUN] Next epic number: 3
[DRY RUN] Would increment to: 4
```

### `move-to-done`

Move sprint file to done status with `--done` suffix.

**Behavior:**
- **Epic sprints**: Renames subdirectory and file in place with `--done` suffix
  - `sprint-02_name/sprint-02_name.md` → `sprint-02_name--done/sprint-02_name--done.md`
- **Standalone sprints**: Moves to `docs/sprints/3-done/_standalone/`

```bash
python3 scripts/sprint_lifecycle.py move-to-done SPRINT_NUM [--dry-run]

Examples:
# Preview the move
python3 scripts/sprint_lifecycle.py move-to-done 2 --dry-run

# Execute the move
python3 scripts/sprint_lifecycle.py move-to-done 2
```

### `update-registry`

Update sprint metadata in registry.json.

```bash
python3 scripts/sprint_lifecycle.py update-registry SPRINT_NUM [OPTIONS]

Options:
  --status STATUS       Sprint status (done, in-progress, etc.)
  --completed DATE      Completion date (YYYY-MM-DD)
  --hours HOURS         Actual hours spent
  --dry-run             Preview without executing
```

**Example:**
```bash
python3 scripts/sprint_lifecycle.py update-registry 2 \
  --status done \
  --completed 2026-01-01 \
  --hours 5.5
```

**Special Behavior:**
- When status is set to "done" and sprint has an epic, automatically increments epic's `completedSprints` counter

### `create-tag`

Create annotated git tag for sprint completion.

```bash
python3 scripts/sprint_lifecycle.py create-tag SPRINT_NUM "Sprint Title" [--dry-run]

Tag format: sprint-NN-slug
Tag message: Completed Sprint NN: Title

Auto-pushes tag to remote origin.
```

### `check-epic`

Check if an epic is ready for completion.

```bash
python3 scripts/sprint_lifecycle.py check-epic EPIC_NUM

Output:
Epic 1 is complete! All sprints are done or aborted.
  Total sprints: 5
  Done: 4
  Aborted: 1
  Remaining: 0

OR

Epic 1 is not complete yet
  Total sprints: 5
  Done: 3
  Aborted: 0
  Remaining: 2

Unfinished sprints:
  - sprint-04_feature/sprint-04_feature.md
  - sprint-05_enhancement/sprint-05_enhancement.md
```

## Workflow Integration

### Full Sprint Lifecycle

```bash
# 1. Create sprint with auto-numbering
/sprint-new "User Profile Page" --epic=2 --estimated-hours=6

# Output: Created Sprint 8 in docs/sprints/2-in-progress/epic-02_...

# 2. Work on the sprint...
/sprint-start 8

# 3. Complete the sprint
/sprint-complete 8

# This internally calls:
#   - move-to-done 8
#   - update-registry 8 --status done --completed <date> --hours <actual>
#   - create-tag 8 "User Profile Page"
#   - check-epic 2
```

### Epic Lifecycle

```bash
# 1. Create epic with auto-numbering
/epic-new "Mobile Application"

# Output: Created Epic 3

# 2. Create sprints for the epic
/sprint-new "Login Screen" --epic=3 --estimated-hours=4
/sprint-new "Dashboard" --epic=3 --estimated-hours=6
/sprint-new "Settings" --epic=3 --estimated-hours=3

# 3. Work on sprints...
/sprint-start 9
/sprint-complete 9

/sprint-start 10
/sprint-complete 10

# 4. Check epic status
python3 scripts/sprint_lifecycle.py check-epic 3

# 5. Complete epic when all sprints done
/epic-complete 3
```

## Dry-Run Mode

**All operations support `--dry-run`** to preview changes without executing:

```bash
# Preview sprint creation
python3 scripts/sprint_lifecycle.py register-sprint "Test" --dry-run

# Preview file move
python3 scripts/sprint_lifecycle.py move-to-done 2 --dry-run

# Preview registry update
python3 scripts/sprint_lifecycle.py update-registry 2 --status done --dry-run
```

## Error Handling

### Atomic Operations

All file operations use backup → execute → cleanup pattern:

```
1. Create backup of original file
2. Execute operation (move, rename, update)
3. If success: cleanup backup
4. If failure: restore from backup
```

### Custom Exceptions

- `ValidationError`: Invalid input or preconditions not met
- `FileOperationError`: File operation failed (with automatic rollback)

### Example Error

```bash
$ python3 scripts/sprint_lifecycle.py move-to-done 99
Error: Sprint file not found for sprint 99 in any status directory
```

## Registry Format

The `docs/sprints/registry.json` file tracks all sprints and epics:

```json
{
  "version": "1.0",
  "generated": "2026-01-01T00:00:00Z",
  "nextSprintNumber": 8,
  "nextEpicNumber": 3,
  "sprints": {
    "7": {
      "title": "User Authentication",
      "status": "done",
      "epic": 2,
      "created": "2026-01-01",
      "started": "2026-01-02",
      "completed": "2026-01-05",
      "hours": 8.5,
      "estimatedHours": 8.0,
      "workflowVersion": "3.0",
      "file": "docs/sprints/3-done/epic-02_auth/sprint-07_user-auth--done.md"
    }
  },
  "epics": {
    "2": {
      "title": "Authentication System",
      "status": "in-progress",
      "created": "2026-01-01",
      "completedSprints": 1,
      "totalSprints": 3,
      "estimatedHours": 20
    }
  }
}
```

## Hook Integration

The automation is whitelisted in the PreToolUse hook to bypass manual operation gates:

```python
# In ~/.claude/hooks/pre_tool_use.py
if 'scripts/sprint_lifecycle.py' in command:
    return {'continue': True}  # Bypass gate for automation
```

This allows automation to perform file operations while blocking manual `mv` commands.

See `docs/HOOK_STRATEGY.md` for details.

## Troubleshooting

### Sprint not found

**Problem:** `Sprint file not found for sprint N`

**Solution:** Check which status directory the sprint is in:
```bash
find docs/sprints -name "*sprint-0N*"
```

### Registry out of sync

**Problem:** nextSprintNumber doesn't match actual sprints

**Solution:** Manually edit `docs/sprints/registry.json` and set `nextSprintNumber` to one more than highest sprint number

### Epic counter not incrementing

**Problem:** Epic's `completedSprints` not updating

**Solution:** Ensure you're using `update-registry` with `--status done`, which triggers the epic counter increment

## Advanced Usage

### Scripting with Python API

```python
from scripts.sprint_lifecycle import (
    get_next_sprint_number,
    register_new_sprint,
    move_to_done,
    update_registry
)

# Get next sprint number
next_num = get_next_sprint_number(dry_run=True)

# Register a sprint
sprint_num = register_new_sprint(
    title="Feature Name",
    epic=1,
    estimatedHours=5
)

# Complete workflow
move_to_done(sprint_num)
update_registry(sprint_num, status="done", hours=4.5)
```

### Batch Operations

```bash
# Register multiple sprints for an epic
for title in "Feature A" "Feature B" "Feature C"; do
  python3 scripts/sprint_lifecycle.py register-sprint "$title" --epic 2 --estimated-hours 4
done

# Check status of all epics
for epic in 1 2 3; do
  echo "Epic $epic:"
  python3 scripts/sprint_lifecycle.py check-epic $epic
  echo
done
```

## See Also

- `docs/HOOK_STRATEGY.md` - Hook architecture and security model
- `commands/sprint-complete.md` - Sprint completion workflow
- `commands/sprint-new.md` - Sprint creation workflow
- `commands/epic-new.md` - Epic creation workflow
- `tests/test_sprint_lifecycle.py` - Test suite examples
