---
description: "Mark sprint as blocked by external dependency"
allowed-tools: [Read, Write, Edit, Bash, Glob, AskUserQuestion]
---

# Block Sprint

Mark a sprint as blocked (paused, waiting on external dependency).

**NOTE**: This workflow supports multiple concurrent sprints. You MUST specify the sprint number.

## Instructions

### 1. Parse Arguments

`$ARGUMENTS` should contain: `<sprint_number> <reason>`

Examples:
- `35 Waiting for API access from vendor`
- `36 Blocked by infrastructure team`

If only a reason is provided (no number):
- Use Glob to find all sprint state files: `.claude/sprint-*-state.json`
- If multiple found, ask user which sprint to block
- If only one found, use that sprint number
- If none found, report "No active sprint to block."

State file path: `.claude/sprint-{N}-state.json`

### 2. Read Current State

Read `.claude/sprint-{N}-state.json` to get current sprint info.

If state file doesn't exist:
```
No active sprint {N} to block. Use /sprint-status to see active sprints.
```

### 3. Confirm with User

Before blocking, confirm:
```
Are you sure you want to mark Sprint N: <title> as BLOCKED?

Current progress:
- Phase: X of 6
- Steps completed: Y
- Current step: Z.W

Blocker: <reason>

This sprint can be resumed later with /sprint-resume <N>.

Type "yes" to confirm, or provide a different action.
```

### 4. Calculate Hours Worked So Far

- Read the `started` timestamp from YAML frontmatter
- Current time minus started time = hours (decimal)
- This tracks time invested before the blocker

### 5. Update Sprint File Metadata

Update YAML frontmatter:
```yaml
---
sprint: N
title: <title>
status: blocked
started: <original timestamp>
blocked_at: <current ISO 8601 timestamp>
hours_before_block: <calculated hours>
blocker: "<reason>"
completed: null
hours: null
---
```

Update the markdown table (if present):
- Set `| **Status** |` to `Blocked`
- Add note: "Blocked on <date>: <reason>"

### 6. Rename Sprint File with `--blocked` Suffix

```bash
# Keep in same epic folder, just rename with --blocked suffix
SPRINT_FILE=$(find docs/sprints -name "sprint-{N}_*.md" -o -name "sprint-{N}*.md" | grep -v "\-\-" | head -1)
mv "$SPRINT_FILE" "${SPRINT_FILE%.md}--blocked.md"
```

**Note**: The file stays in the epic folder. The `--blocked` suffix indicates status.

### 7. Update State File

Update `.claude/sprint-{N}-state.json`:

```json
{
  "status": "blocked",
  "blocked_at": "<current ISO timestamp>",
  "blocker": "<reason>"
}
```

Keep all other fields intact for resumption.

### 8. Update README

Update `docs/sprints/README.md`:
- Add sprint to the Blocked section
- Include hours worked so far and blocker reason

### 9. Report

```
Sprint N: <title> - BLOCKED

Blocker: <reason>
Hours invested so far: <hours>

Progress preserved:
- Phase: X of 6
- Steps completed: <count>
- Current step: <step>

Sprint file renamed to: <filename>--blocked.md
State file preserved at .claude/sprint-{N}-state.json

To resume when blocker is resolved: /sprint-resume <N>
```

---

## Usage

```
/sprint-blocked <N> <reason>
```

Examples:
```
/sprint-blocked 35 Waiting for API access from vendor
/sprint-blocked 36 Blocked by infrastructure team delivery
/sprint-blocked 37 Waiting for design mockups
```
