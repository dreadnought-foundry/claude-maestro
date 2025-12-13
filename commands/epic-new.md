---
description: "Create a new epic to group related sprints"
allowed-tools: [Read, Write, Glob, Bash]
---

# Create Epic: $ARGUMENTS

Create a new epic file for organizing related sprints.

## Instructions

### 1. Parse Arguments

Parse $ARGUMENTS to get the epic title:
- Example: "Mobile Field Application"

If no title provided, ask the user for one.

### 2. Find Next Epic Number

Use Glob to find existing epics:
```
docs/epics/epic-*.md
```

Determine the next available epic number.

### 3. Create Slug

Convert title to slug:
- Lowercase
- Replace spaces with hyphens
- Remove special characters
- Example: "Mobile Field Application" → "mobile-field-application"

### 4. Create Epic File

Create `docs/epics/epic-{NN}_{slug}.md` using this template:

```markdown
# Epic {NN}: {Title}

## Overview

{To be filled in - describe the strategic initiative}

## Success Criteria

- [ ] {Define measurable outcomes}

## Sprints

| Sprint | Title | Status |
|--------|-------|--------|
| -- | TBD | planned |

## Backlog

- [ ] {Add unassigned tasks}

## Notes

Created: {TODAY}
```

### 5. Report

Output:
```
Created: docs/epics/epic-{NN}_{slug}.md

Next steps:
1. Fill in the Overview and Success Criteria
2. Add existing sprints to the Sprints table
3. Use /sprint-new "<title>" --epic={NN} to create new sprints
```
