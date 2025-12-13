---
description: "Start an epic - move it to in-progress"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Start Epic

Move an epic from backlog/todo to in-progress status.

## Instructions

### 1. Parse Arguments

Parse `$ARGUMENTS` to get the epic number:
- Example: "3" or "03" or "epic-03"
- Extract just the number

If no epic number provided, show error:
```
Error: No epic specified.
Usage: /epic-start <epic-number>
Example: /epic-start 8
```

### 2. Find Epic Folder

Search for the epic in backlog and todo folders:
```bash
find docs/sprints/0-backlog docs/sprints/1-todo -type d -name "epic-{NN}_*" 2>/dev/null
```

Format the number with leading zero if needed (e.g., "3" → "03").

### 3. Verify Epic Exists

If no folder found:
```
Error: Epic {NN} not found in backlog or todo.

Check available epics with: /epic-list
```

If epic already in `2-in-progress/`:
```
Epic {NN} is already in progress.

Location: docs/sprints/2-in-progress/epic-{NN}_name/

Use /epic-status {NN} to see current sprint status.
```

### 4. Move Epic Folder to In-Progress

```bash
# Get the epic folder name
EPIC_FOLDER=$(basename <found-path>)

# Move entire folder to in-progress
mv docs/sprints/{0-backlog,1-todo}/epic-{NN}_* docs/sprints/2-in-progress/
```

### 5. Update Epic File Status

Read `_epic.md` in the epic folder and update:

**YAML frontmatter:**
```yaml
---
epic: N
title: "<title>"
status: in-progress
started: <current ISO 8601 date>
---
```

**Markdown table (if present):**
- Set `| **Status** |` to `In Progress`
- Set `| **Started** |` to current date

### 6. Report Success

```
Epic {NN}: <Title> - STARTED
═══════════════════════════════════════════════

Location: docs/sprints/2-in-progress/epic-{NN}_name/

Sprints in this epic:
  - sprint-XX_title.md
  - sprint-YY_title.md
  - sprint-ZZ_title.md

Total: X sprints

Next steps:
1. Start a sprint: /sprint-start <sprint-number>
2. Check epic status: /epic-status {NN}
```

---

## Usage

```
/epic-start <epic-number>
```

Examples:
```
/epic-start 8
/epic-start 10
```
