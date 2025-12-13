---
description: "Archive a completed epic and all its sprints"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Archive Epic: $ARGUMENTS

Archive a completed epic by moving it from done to archived.

## Instructions

### 1. Parse Arguments

Parse $ARGUMENTS to get the epic number:
- Example: "3" or "03" or "epic-03"
- Extract just the number

If no epic number provided, show error:
```
Error: No epic specified.
Usage: /epic-archive <epic-number>
Example: /epic-archive 3
```

### 2. Find Epic Folder

Search for the epic in the done folder:
```bash
find docs/sprints/3-done -type d -name "epic-{NN}_*" 2>/dev/null
```

Format the number with leading zero if needed (e.g., "3" → "03").

### 3. Verify Epic Location

**If found in `3-done/`:** Proceed with archiving.

**If found in `2-in-progress/`:**
```
Error: Epic {NN} is still in progress.

Complete the epic first: /epic-complete {NN}
```

**If found in `6-archived/`:**
```
Epic {NN} is already archived at:
  docs/sprints/6-archived/epic-{NN}_name/
```

**If not found:**
```
Error: Epic {NN} not found.

Check available epics with: /epic-list
```

### 4. Move Epic Folder to Archived

```bash
# Move entire folder from done to archived
mv docs/sprints/3-done/epic-{NN}_* docs/sprints/6-archived/
```

### 5. Update Epic File Status

Read `_epic.md` in the epic folder and update:

**YAML frontmatter:**
```yaml
---
epic: N
title: "<title>"
status: archived
started: <original started date>
completed: <original completed date>
archived_at: <current ISO 8601 date>
total_hours: <preserved>
---
```

**Markdown table (if present):**
- Set `| **Status** |` to `Archived`

### 6. Note Related State Files

Check for sprint state files related to this epic:
```bash
ls .claude/sprint-*-state.json
```

List any that correspond to sprints in this epic. These are preserved for reference.

### 7. Report Success

```
Epic {NN}: <Title> - ARCHIVED
═══════════════════════════════════════════════

Location: docs/sprints/6-archived/epic-{NN}_name/

Files archived:
  ✓ sprint-XX_title--done.md
  ✓ sprint-YY_title--done.md
  ✗ sprint-ZZ_title--aborted.md
  - _epic.md

Total: X sprint files + 1 epic file

Epic status updated to: archived
Archived at: <date>

State files preserved:
  - .claude/sprint-XX-state.json
  - .claude/sprint-YY-state.json
```

---

## Usage

```
/epic-archive <epic-number>
```

Examples:
```
/epic-archive 3
/epic-archive 08
```
