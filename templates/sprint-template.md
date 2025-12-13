---
sprint: {N}
title: "{TITLE}"
status: todo
workflow_version: "2.1"
epic: {EPIC_NUMBER}
type: {TYPE}  # backend-only, frontend-only, fullstack, integration, data-layer
created: {DATE}
started: null
completed: null
hours: null
---

# Sprint {N}: {TITLE}

## Overview

| Field | Value |
|-------|-------|
| Sprint | {N} |
| Title | {TITLE} |
| Epic | {EPIC_NUMBER} - {EPIC_NAME} |
| Type | {TYPE} |
| Workflow | v2.0 |
| Status | Todo |
| Created | {DATE} |

## Goal

{One sentence describing what this sprint accomplishes}

## Background

{Context, dependencies, and why this work is needed}

## Tasks

### Phase 1: {First logical grouping}
- [ ] Task 1
- [ ] Task 2

### Phase 2: {Second logical grouping}
- [ ] Task 3
- [ ] Task 4

## Model Schema (if applicable)

```python
# New models or schema changes
```

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests pass with >= 75% coverage
- [ ] No lint errors

---

## Team Strategy

*Populated by Plan agent during sprint start*

### Sprint Type
- **Type**: {backend-only|frontend-only|fullstack|integration|data-layer}
- **Parallelism**: {yes|no}

### Agent Assignments

| Agent | Role | Files Owned | Skills |
|-------|------|-------------|--------|
| product-engineer | Backend | src/corrdata/... | run-migrations, validate-mcp |
| product-engineer | Frontend | mobile-pwa/... | validate-graphql |
| quality-engineer | Tests | tests/test_sprint{N}_*.py | check-coverage |

### File Ownership

```
# Backend agent owns:
src/corrdata/db/models.py (modify)
src/corrdata/api/graphql/... (create/modify)
alembic/versions/... (create)

# Frontend agent owns:
mobile-pwa/src/pages/... (create/modify)
mobile-pwa/src/components/... (create/modify)

# Test agent owns:
tests/test_sprint{N}_*.py (create)
```

### Integration Strategy

1. **Merge Order**: Backend → Tests → Frontend
2. **Conflict Resolution**: Parent agent resolves any overlapping changes
3. **Validation Sequence**: Migrations → Backend tests → Frontend tests → Full suite

### TDD Approach

- [ ] **Strict TDD** (tests before code) - Use for: {complex logic, risk scoring}
- [x] **Flexible TDD** (tests alongside code) - Default for this sprint
- [ ] **Coverage-based** (tests after, hit 75%) - Use for: {simple CRUD}

---

## Postmortem

*Populated after sprint completion*

### Summary

| Metric | Value |
|--------|-------|
| Started | {timestamp} |
| Completed | {timestamp} |
| Duration | {hours} |
| Tests Added | {count} |
| Coverage Delta | {+X%} |
| Files Changed | {count} |

### Agent Work Summary

| Agent | Tasks Completed | Files Created/Modified | Time |
|-------|-----------------|----------------------|------|
| Plan | Architecture design | - | - |
| product-engineer (backend) | {tasks} | {files} | - |
| product-engineer (frontend) | {tasks} | {files} | - |
| quality-engineer | {tasks} | {files} | - |

### What Went Well

- {Positive outcome 1}
- {Positive outcome 2}

### What Could Improve

- {Issue 1 and potential solution}
- {Issue 2 and potential solution}

### Patterns Discovered

```
# Reusable patterns identified during this sprint
# These should be added to docs/patterns/ if broadly applicable
```

### Learnings for Future Sprints

1. **Technical**: {Technical insight}
2. **Process**: {Process improvement}
3. **Integration**: {Integration lesson}

### Action Items

- [ ] Add pattern X to docs/patterns/
- [ ] Update epic learnings in _epic.md
- [ ] Create follow-up sprint for {deferred item}
