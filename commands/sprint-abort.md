---
description: "Abort current sprint with reason"
allowed-tools: [Read, Write, Edit, Glob]
---

# Abort Sprint

Mark a sprint as aborted and preserve state for reference.

**NOTE**: This workflow supports multiple concurrent sprints. You MUST specify the sprint number.

## Instructions

### 1. Parse Arguments

`$ARGUMENTS` should contain: `<sprint_number> <reason>`

Examples:
- `34 Requirements changed, need to re-plan`
- `35 Blocked by external dependency`

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
Are you sure you want to abort Sprint N: <title>?

Current progress:
- Phase: X of 6
- Steps completed: Y
- Current step: Z.W

Reason for abort: <reason>

Type "yes" to confirm abort, or provide a different action.
```

### 4. Update State File

If user confirms, update `.claude/sprint-{N}-state.json`:

```json
{
  "status": "aborted",
  "completed_at": "<current ISO timestamp>",
  "abort_reason": "<reason>"
}
```

Keep all other fields intact for audit trail.

### 5. Update Sprint File

Edit the sprint planning file:
- Set Status: "Aborted"
- Add note: "Aborted on <date>: <reason>"

### 6. Report

```
Sprint N: <title> - ABORTED

Reason: <reason>

Progress preserved:
- Steps completed: <list>
- Current step was: <step>

State file preserved at .claude/sprint-{N}-state.json for reference.

To start a new sprint: /sprint-start <N>
To resume this sprint: Manually edit state file and set status to "in_progress"
```

---

## Usage

```
/sprint-abort <N> <reason>
```

Examples:
```
/sprint-abort 34 Requirements changed, need to re-plan
/sprint-abort 35 Blocked by external dependency
/sprint-abort 36 User requested pivot to different priority
```
