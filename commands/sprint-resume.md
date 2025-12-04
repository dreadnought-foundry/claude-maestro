---
description: "Resume a blocked sprint"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Resume Sprint

Resume a previously blocked sprint.

## Instructions

### 1. Parse Arguments

`$ARGUMENTS` should contain the sprint number.

If `$ARGUMENTS` is empty:
- Use Glob to find sprint files in blocked folder: `docs/sprints/blocked/sprint-*.md`
- If multiple found, list them and ask user which one to resume
- If only one found, use that sprint number
- If none found, report "No blocked sprints to resume."

### 2. Find and Read Sprint File

1. Use Glob to find the sprint file:
   ```
   docs/sprints/blocked/sprint-$ARGUMENTS*.md
   ```

2. Read the sprint file and extract:
   - YAML frontmatter (started, blocked_at, hours_before_block, blocker)
   - Current state from state file

If not found in blocked folder:
```
Sprint {N} is not in blocked status. Use /sprint-status to check its current state.
```

### 3. Confirm with User

```
Resume Sprint N: <title>?

Was blocked: <blocked_at>
Blocker was: <blocker>
Hours before block: <hours>

The sprint will move back to in-progress and you can continue from where you left off.

Type "yes" to confirm.
```

### 4. Update Sprint File Metadata

Update YAML frontmatter:
```yaml
---
sprint: N
title: <title>
status: in-progress
started: <original started timestamp>
resumed_at: <current ISO 8601 timestamp>
hours_before_block: <preserved from before>
previous_blocker: "<blocker reason>"
completed: null
hours: null
---
```

Update the markdown table (if present):
- Set `| **Status** |` to `In Progress`
- Add note: "Resumed on <date> (was blocked: <reason>)"

### 5. Move Sprint File Back to In-Progress

```bash
mv docs/sprints/blocked/sprint-{N}*.md docs/sprints/in-progress/
```

### 6. Update State File

Update `.claude/sprint-{N}-state.json`:

```json
{
  "status": "in_progress",
  "resumed_at": "<current ISO timestamp>",
  "previous_blocker": "<blocker reason>"
}
```

Keep all progress fields intact.

### 7. Update README

Update `docs/sprints/README.md`:
- Remove sprint from Blocked section
- Add sprint back to In Progress section

### 8. Report

```
Sprint N: <title> - RESUMED

Previously blocked by: <blocker>
Hours before block: <hours>

Current progress:
- Phase: X of 6
- Current step: Y.Z

Sprint file moved to: docs/sprints/in-progress/

Use /sprint-next <N> to continue from where you left off.
Use /sprint-status <N> to see full progress details.
```

---

## Usage

```
/sprint-resume <N>
```

Examples:
```
/sprint-resume 35
/sprint-resume 36
```
