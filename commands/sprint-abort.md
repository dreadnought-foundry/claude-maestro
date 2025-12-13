---
description: "Abort current sprint (cancelled, won't be completed)"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Abort Sprint

Mark a sprint as aborted (cancelled, won't be completed).

**NOTE**: If the sprint is temporarily blocked and will resume later, use `/sprint-blocked` instead.

## Instructions

### 1. Parse Arguments

`$ARGUMENTS` should contain: `<sprint_number> <reason>`

Examples:
- `34 Requirements changed, need to re-plan`
- `36 Feature no longer needed`

If only a reason is provided (no number):
- Use Glob to find all sprint state files: `.claude/sprint-*-state.json`
- If multiple found, ask user which sprint to abort
- If only one found, use that sprint number
- If none found, report "No active sprint to abort."

State file path: `.claude/sprint-{N}-state.json`

### 2. Read Current State

Read `.claude/sprint-{N}-state.json` to get current sprint info.

If state file doesn't exist:
```
No active sprint {N} to abort. Use /sprint-status to see active sprints.
```

### 3. Confirm with User

Before aborting, confirm:
```
Are you sure you want to ABORT Sprint N: <title>?

This means the sprint is CANCELLED and won't be completed.
If this is a temporary blocker, use /sprint-blocked instead.

Current progress:
- Phase: X of 6
- Steps completed: Y
- Current step: Z.W

Reason for abort: <reason>

Type "yes" to confirm abort.
```

### 4. Calculate Hours Worked

- Read the `started` timestamp from YAML frontmatter
- Current time minus started time = hours (decimal)
- This tracks time invested even for cancelled sprints

### 5. Update Sprint File Metadata

Update YAML frontmatter:
```yaml
---
sprint: N
title: <title>
status: aborted
started: <original timestamp>
aborted_at: <current ISO 8601 timestamp>
hours: <calculated hours>
abort_reason: "<reason>"
completed: null
---
```

Update the markdown table (if present):
- Set `| **Status** |` to `Aborted`
- Add note: "Aborted on <date>: <reason>"

### 6. Rename Sprint File with `--aborted` Suffix

```bash
# Keep in same epic folder, just rename with --aborted suffix
SPRINT_FILE=$(find docs/sprints -name "sprint-{N}_*.md" -o -name "sprint-{N}*.md" | grep -v "\-\-" | head -1)
mv "$SPRINT_FILE" "${SPRINT_FILE%.md}--aborted.md"
```

**Note**: The file stays in the epic folder. The `--aborted` suffix indicates status.

### 7. Update State File

Update `.claude/sprint-{N}-state.json`:

```json
{
  "status": "aborted",
  "aborted_at": "<current ISO timestamp>",
  "abort_reason": "<reason>"
}
```

Keep all other fields intact for audit trail.

### 8. Update README

Update `docs/sprints/README.md`:
- Add sprint to the Aborted section
- Include hours worked and reason

### 9. Report

```
Sprint N: <title> - ABORTED

Reason: <reason>
Hours invested: <hours>

Progress at abort:
- Phase: X of 6
- Steps completed: <count>
- Current step was: <step>

Sprint file renamed to: <filename>--aborted.md
State file preserved at .claude/sprint-{N}-state.json for reference.

To start a new sprint: /sprint-start <N>
```

---

## Usage

```
/sprint-abort <N> <reason>
```

Examples:
```
/sprint-abort 34 Requirements changed, need to re-plan
/sprint-abort 36 Feature no longer needed after customer feedback
/sprint-abort 37 Superseded by sprint 38
```
