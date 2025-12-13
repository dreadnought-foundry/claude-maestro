---
description: "Create a new sprint planning file from template"
allowed-tools: [Read, Write, Glob, Bash]
---

# Create Sprint $ARGUMENTS

Create a new sprint planning file for Sprint **$ARGUMENTS**.

## Instructions

### 1. Determine Sprint Number, Title, and Epic

Parse $ARGUMENTS:
- If just a number (e.g., "5"), prompt user for title
- If "5 Feature Name", use "5" as number and "Feature Name" as title
- If includes "--epic=N", extract epic number N and remove from title
- Example: "53 Photo Capture --epic=3" → Sprint 53, Title "Photo Capture", Epic 3

Epic is optional - sprints can exist without an epic.

### 2. Check for Existing Sprints

Use Glob to find existing sprints:
```
docs/sprints/sprint-*.md
```

Verify the sprint number doesn't already exist.

### 3. Create Sprint Directory (if needed)

```bash
mkdir -p docs/sprints
```

### 4. Create Sprint File

Create `docs/sprints/sprint-{NN}_{slug}.md` where:
- `{NN}` is zero-padded sprint number (01, 02, etc.)
- `{slug}` is lowercase, hyphenated title (e.g., "user-authentication")

Use this template:

```markdown
# Sprint {N}: {Title}

## Overview

| Field | Value |
|-------|-------|
| Sprint | {N} |
| Title | {Title} |
| Epic | {Epic number or "None"} |
| Status | Planning |
| Created | {TODAY} |
| Started | - |
| Completed | - |

## Goal

{One sentence describing what this sprint accomplishes}

## Background

{Why is this needed? What problem does it solve?}

## Requirements

### Functional Requirements

- [ ] {Requirement 1}
- [ ] {Requirement 2}
- [ ] {Requirement 3}

### Non-Functional Requirements

- [ ] {Performance, security, or other constraints}

## Dependencies

- **Sprints**: {List any sprints that must be completed first, or "None"}
- **External**: {External dependencies like APIs, libraries, etc.}

## Scope

### In Scope

- {What's included}

### Out of Scope

- {What's explicitly NOT included}

## Technical Approach

{High-level description of how this will be implemented}

## Tasks

### Phase 1: Planning
- [ ] Review requirements with stakeholder
- [ ] Design code architecture
- [ ] Clarify any ambiguous requirements

### Phase 2: Implementation
- [ ] Write tests
- [ ] Implement feature
- [ ] Fix any test failures

### Phase 3: Validation
- [ ] Verify migrations (if applicable)
- [ ] Quality review
- [ ] Refactoring

### Phase 4: Documentation
- [ ] Create dialog example (if applicable)
- [ ] Update relevant docs

## Acceptance Criteria

- [ ] {Criterion 1 - how do we know this is done?}
- [ ] {Criterion 2}
- [ ] All tests passing
- [ ] Code reviewed and refactored

## Open Questions

- {Any questions that need answers before or during implementation}

## Notes

{Any additional context, links, references}
```

### 5. Update Epic File (if epic specified)

If --epic=N was provided:
1. Find the epic file: `docs/epics/epic-{NN}_*.md`
2. Add a new row to the Sprints table:
   ```
   | {Sprint} | {Title} | planned |
   ```
3. If epic file not found, warn user but still create sprint

### 6. Report

Output:
```
Created: docs/sprints/sprint-{NN}_{slug}.md
Epic: {Epic number and title, or "None (standalone sprint)"}

Next steps:
1. Fill in the sprint details (Goal, Requirements, etc.)
2. Run /sprint-start {N} when ready to begin
```
