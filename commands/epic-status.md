---
description: "Show detailed status of an epic"
allowed-tools: [Read, Glob, Grep]
---

# Epic Status: $ARGUMENTS

Show detailed status for epic **$ARGUMENTS**.

## Instructions

### 1. Determine Epic Number

Parse $ARGUMENTS:
- If a number is provided, use that epic
- If empty, check .claude/sprint-state.json for currentEpic
- If no current epic, show error: "No epic specified. Use /epic-status <N>"

### 2. Find Epic File

Use Glob to find:
```
docs/epics/epic-{NN}_*.md
```

If not found, show error: "Epic {NN} not found"

### 3. Parse Epic File

Extract:
- Title (from # heading)
- Overview (content under ## Overview)
- Success Criteria (checkboxes under ## Success Criteria)
- Sprints table (under ## Sprints)
- Backlog items (checkboxes under ## Backlog)

### 4. Enhance Sprint Status

For each sprint in the table, check actual status from sprint files:
- Look in docs/sprints/3-done/ for completed
- Look in docs/sprints/2-in-progress/ for in progress
- Look in docs/sprints/1-todo/ for planned
- Look in docs/sprints/4-blocked/ for blocked

### 5. Calculate Progress

- Total sprints
- Completed count
- In-progress count
- Blocked count
- Percentage complete

### 6. Display Output

Format:
```
Epic {NN}: {Title}
═══════════════════════════════════════════════

Overview:
{Overview text}

Progress: [████████░░] 80% (8/10 sprints)

Success Criteria:
  [x] Criterion 1
  [x] Criterion 2
  [ ] Criterion 3

Sprints:
  [x] 01: Core Data Layer
  [x] 02: MCP Server
  [x] 03: Graph Intelligence
  [→] 15: Geospatial Enrichment  ← in progress
  [ ] 16: Real Data Integration
  [!] 20: REST API Layer  ← blocked

Backlog:
  - Task 1
  - Task 2
  - Task 3

Notes:
{Notes content if any}
```

Legend:
- [x] = completed
- [→] = in progress
- [ ] = planned/todo
- [!] = blocked
