---
description: "List all epics with their status and progress"
allowed-tools: [Read, Glob, Grep]
---

# List All Epics

Show all epics with their completion status.

## Instructions

### 1. Find All Epics

Use Glob to find epic files:
```
docs/epics/epic-*.md
```

### 2. Parse Each Epic

For each epic file, extract:
- Epic number (from filename)
- Title (from # heading)
- Sprint counts:
  - Total sprints (count rows in Sprints table)
  - Completed sprints (rows with "completed" or "done" status)
  - In-progress sprints (rows with "in_progress" or "in-progress" status)

### 3. Calculate Progress

Progress = (Completed / Total) * 100

Create progress bar:
- 10 segments
- Each █ = 10%
- Each ░ = remaining

Example: 60% = `[██████░░░░]`

### 4. Find Unassigned Sprints

Check sprint files in docs/sprints/ folders for sprints not listed in any epic.

### 5. Display Output

Format:
```
Epics:
  01. Core Infrastructure      [████████░░] 80%  (8/10 sprints)
  02. Compliance Reporting     [██████░░░░] 60%  (6/10 sprints)
  03. Web Application          [████░░░░░░] 40%  (4/10 sprints)
  04. Mobile Field App         [██░░░░░░░░] 20%  (1/5 sprints)
  05. Production Deployment    [░░░░░░░░░░] 0%   (0/3 sprints)

  --  Unassigned                            12 sprints

Total: 5 epics, 38 sprints assigned, 12 unassigned
```

### 6. Highlight Active

If there's a current epic in .claude/sprint-state.json, mark it with ← active
