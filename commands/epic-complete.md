---
description: "Complete an epic - move it to done after all sprints finished"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Complete Epic

Move an epic from in-progress to done status after verifying all sprints are complete.

## Instructions

### 1. Parse Arguments

Parse `$ARGUMENTS` to get the epic number:
- Example: "3" or "03" or "epic-03"
- Extract just the number

If no epic number provided, show error:
```
Error: No epic specified.
Usage: /epic-complete <epic-number>
Example: /epic-complete 8
```

### 2. Find Epic Folder

Search for the epic in in-progress folder:
```bash
find docs/sprints/2-in-progress -type d -name "epic-{NN}_*" 2>/dev/null
```

Format the number with leading zero if needed (e.g., "3" → "03").

### 3. Verify Epic Exists and Is In-Progress

If no folder found in `2-in-progress/`:
```
Error: Epic {NN} not found in in-progress.

Check epic location with: /epic-status {NN}
```

If epic already in `3-done/`:
```
Epic {NN} is already complete.

Location: docs/sprints/3-done/epic-{NN}_name/

To archive: /epic-archive {NN}
```

### 4. Check All Sprints Are Finished

List all sprint files in the epic folder:
```bash
ls docs/sprints/2-in-progress/epic-{NN}_*/sprint-*.md
```

**Valid statuses for completion:**
- `--done` suffix: Sprint completed successfully
- `--aborted` suffix: Sprint was cancelled (still counts as finished)

**Blocking statuses:**
- No suffix (pending or in-progress)
- `--blocked` suffix

If any sprints are not finished:
```
Error: Cannot complete epic {NN} - has unfinished sprints:

In Progress / Pending:
  - sprint-XX_title.md
  - sprint-YY_title.md

Blocked:
  - sprint-ZZ_title--blocked.md

Complete or abort these sprints first:
  /sprint-complete <N>  or  /sprint-abort <N> <reason>
```

### 5. Calculate Epic Statistics

Count sprints by status:
- Done: count of `*--done.md` files
- Aborted: count of `*--aborted.md` files

Read each sprint file to sum up hours:
- Total hours = sum of all `hours:` from YAML frontmatter

### 6. Move Epic Folder to Done

```bash
# Get the epic folder name
EPIC_FOLDER=$(basename <found-path>)

# Move entire folder to done
mv docs/sprints/2-in-progress/epic-{NN}_* docs/sprints/3-done/
```

### 7. Update Epic File Status

Read `_epic.md` in the epic folder and update:

**YAML frontmatter:**
```yaml
---
epic: N
title: "<title>"
status: done
started: <original started date>
completed: <current ISO 8601 date>
total_hours: <sum of all sprint hours>
---
```

**Markdown table (if present):**
- Set `| **Status** |` to `Done`
- Set `| **Completed** |` to current date

**Sprint table:**
- Update each sprint's status column to match their suffix

### 8. Report Success

```
Epic {NN}: <Title> - COMPLETE
═══════════════════════════════════════════════

Location: docs/sprints/3-done/epic-{NN}_name/

Summary:
  - Sprints completed: X
  - Sprints aborted: Y
  - Total hours: Z.ZZ

Sprints:
  ✓ sprint-XX_title--done.md
  ✓ sprint-YY_title--done.md
  ✗ sprint-ZZ_title--aborted.md

Epic status updated to: done

Next steps:
  - Archive when ready: /epic-archive {NN}
  - Start another epic: /epic-start <epic-number>
```

---

## Usage

```
/epic-complete <epic-number>
```

Examples:
```
/epic-complete 8
/epic-complete 10
```
