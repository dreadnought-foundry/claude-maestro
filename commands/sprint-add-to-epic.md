---
description: "Add an existing sprint to an epic"
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

# Add Sprint to Epic

Add an existing sprint file to an epic, moving it and updating all necessary files.

## Instructions

### 1. Parse Arguments

`$ARGUMENTS` should contain: `<sprint-number> <epic-number>`

Examples:
- `81 10` - Add sprint 81 to epic 10
- `82 6` - Add sprint 82 to epic 6

If arguments missing or invalid:
```
Error: Missing arguments.
Usage: /sprint-add-to-epic <sprint-number> <epic-number>
Example: /sprint-add-to-epic 81 10
```

### 2. Find the Sprint File

Search all sprint folders for the sprint file:
```bash
find docs/sprints -name "sprint-{N}_*.md" -o -name "sprint-{N}--*.md"
```

If not found:
```
Error: Sprint {N} not found.

Create it first with /sprint-new or manually.
```

If sprint already has `--done`, `--blocked`, or `--aborted` suffix, preserve it.

### 3. Find the Epic Folder

Search for the epic folder:
```bash
find docs/sprints -type d -name "epic-{NN}_*"
```

Format epic number with leading zero if needed (e.g., "6" → "06").

If not found:
```
Error: Epic {NN} not found.

Create it first with /epic-new or check /epic-list.
```

### 4. Check Sprint Not Already in Epic

If sprint file is already inside an epic folder:
```
Sprint {N} is already in epic {current-epic}.

To move to a different epic, first remove it manually.
```

### 5. Move Sprint File to Epic Folder

```bash
mv <current-sprint-path> <epic-folder-path>/
```

### 6. Update Sprint Frontmatter

Read the sprint file and add/update the `epic` field in YAML frontmatter:

```yaml
---
sprint: N
title: "Sprint Title"
epic: NN  # Add this line
status: todo
...
---
```

### 7. Read Epic File

Read `_epic.md` from the epic folder to get current sprint table.

### 8. Extract Sprint Info

From the sprint file, extract:
- Sprint number
- Title (from frontmatter or filename)
- Status (from frontmatter or filename suffix)

### 9. Add Sprint to Epic's Sprint Table

Find the `## Sprints` section and the sprint table. Add a new row:

```markdown
| {sprint-number} | {title} | {status} |
```

Insert in numerical order if possible, or at the end of the table.

### 10. Report Success

```
Sprint {N}: {Title} added to Epic {NN}: {Epic Title}
═══════════════════════════════════════════════

Sprint file moved to:
  {epic-folder-path}/sprint-{N}_title.md

Updated files:
  ✓ Sprint frontmatter (added epic: {NN})
  ✓ Epic sprint table (added row)

Sprint status: {status}
```

---

## Usage

```
/sprint-add-to-epic <sprint-number> <epic-number>
```

Examples:
```
/sprint-add-to-epic 81 10
/sprint-add-to-epic 82 6
/sprint-add-to-epic 55 7
```

---

## Edge Cases

**Sprint in wrong epic:**
Don't automatically move between epics. Show error and suggest manual move.

**Epic has no sprint table:**
Create the table section:
```markdown
## Sprints

| Sprint | Title | Status |
|--------|-------|--------|
| {N} | {title} | {status} |
```

**Sprint already in table:**
Don't add duplicate. Report that it's already listed.
