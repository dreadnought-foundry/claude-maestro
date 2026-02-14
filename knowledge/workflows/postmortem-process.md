# Recipe: Postmortem Process

**Category**: workflow
**Version**: 1.0
**Last Updated**: 2025-12-13
**Sprints**: Refined from Sprint 91 learnings

## Context

**When to use this recipe:**
- After completing any sprint (auto-generated during `/sprint-complete`)
- When reviewing past sprint outcomes
- When deciding what to work on next

**Why postmortems matter:**
- Capture learnings while context is fresh
- Create feedback loop for continuous improvement
- Surface action items that might otherwise be forgotten
- Build institutional knowledge across sprints

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Postmortem Flow                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Sprint Complete                                                │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────┐                                                │
│  │ Generate    │  Auto during /sprint-complete                  │
│  │ Postmortem  │                                                │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │ Tag Action  │  [done] [sprint] [backlog] [pattern]          │
│  │ Items       │                                                │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ├──────────────┬──────────────┬──────────────┐         │
│         ▼              ▼              ▼              ▼         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │ [done]    │  │ [sprint]  │  │ [backlog] │  │ [pattern] │   │
│  │ Mark done │  │ Create    │  │ Add to    │  │ Add to    │   │
│  │ with link │  │ todo      │  │ backlog   │  │ playbook  │   │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │
│                       │              │              │           │
│                       ▼              ▼              ▼           │
│                ┌─────────────────────────────────────────┐     │
│                │         docs/sprints/backlog.md         │     │
│                └─────────────────────────────────────────┘     │
│                                    │                            │
│                                    ▼                            │
│                          ┌─────────────────┐                   │
│                          │ /sprint-start   │                   │
│                          │ surfaces items  │                   │
│                          └─────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Postmortem Structure

Every postmortem should include these sections:

### Summary
One sentence describing what the sprint accomplished.

```markdown
### Summary
Sprint 91 integrated Equipment pages with GraphQL and added "Demo Only" banners
to Regions pages after discovering Regions have no backend support.
```

### Duration & Metrics

```markdown
### Duration & Metrics
- **Duration**: 2.5 hours
- **Tests Written**: 26 (backend: 13, frontend: 13)
- **Files Created**: 6
- **Files Modified**: 4
```

### What Went Well
Capture positive outcomes for future reference.

```markdown
### What Went Well
- **Pattern reuse**: Equipment queries followed Sprint 89/90 patterns
- **Early discovery**: Plan agent identified backend gap before implementation
- **Clean pivot**: User clarification enabled quick scope adjustment
```

**Good examples**:
- "Pattern reuse from Sprint X saved 30% implementation time"
- "TDD caught edge case that would have been a production bug"
- "Parallel agents reduced total time by running frontend/backend simultaneously"

### What Could Improve
Be honest - this is how we get better.

```markdown
### What Could Improve
- **Missing hook discovered late**: use-debounce.ts wasn't in initial plan
- **Gap not documented**: No prior docs indicated Regions lacked backend
```

**Good examples**:
- "Migration order wasn't planned, caused rollback during testing"
- "Test coverage goal was 85% but only achieved 72% - need to address"
- "Agent coordination gap: frontend waited 20 min for backend API"

### Patterns Discovered
Reusable approaches worth documenting.

```markdown
### Patterns Discovered
- **Demo Banner pattern**: For pages with frontend but no backend, add visible banner
- **Follow-up sprint creation**: When scope reduced, immediately create follow-up sprint
```

### Action Items
**Every item must be tagged.**

```markdown
### Action Items
- [x] `[done]` Created Sprint 116 for Regions backend → [Sprint 116](path/to/sprint)
- [ ] `[sprint]` Add authentication to API endpoints → Sprint 117
- [ ] `[backlog]` Audit other pages for backend gaps
- [ ] `[pattern]` Document GraphQL transform pattern in playbook
```

## Action Item Tags

| Tag | When to Use | Destination |
|-----|-------------|-------------|
| `[done]` | Item already resolved during sprint | Mark complete with link |
| `[sprint]` | Needs dedicated sprint (significant work) | Create sprint file, add to backlog |
| `[backlog]` | Future work, not urgent | Add to backlog.md |
| `[pattern]` | Reusable code or process pattern | Add to playbook |

### Decision Guide

```
Is the action item already complete?
  └─ Yes → [done] with link to resolution
  └─ No → Continue...

Does it require more than 2 hours of focused work?
  └─ Yes → [sprint] - Create a todo sprint
  └─ No → Continue...

Is it a reusable pattern or process improvement?
  └─ Yes → [pattern] - Document in playbook
  └─ No → [backlog] - Track for future
```

## Backlog Integration

### Adding to Backlog

When processing `[backlog]` or `[sprint]` items, add them to `docs/sprints/backlog.md`:

```markdown
### From Sprint 91 (Equipment & Regions)

- [ ] `[backlog]` Audit other pages for similar backend gaps
- [ ] `[backlog]` Add architecture doc noting supported asset types
- [x] `[sprint]` Regions backend support → [Sprint 116](path)
```

### Surfacing at Sprint Start

When `/sprint-start` runs, it checks the backlog for related items:

```
Backlog items related to Sprint 92:

- [ ] [backlog] Audit other pages for backend gaps (from Sprint 91)
- [ ] [backlog] Document asset type support (from Sprint 91)

Consider addressing these during this sprint if scope allows.
```

### Resolving Backlog Items

When an item is addressed:
1. Mark it `[x]` in the backlog
2. Add to "Resolved Items" table with date and resolution
3. Link to the sprint or commit that resolved it

## Anti-Patterns

### Don't: Write vague action items

**Bad**: "Fix the bug"
**Good**: "`[backlog]` Fix null pointer in RiskScoreCalculator when asset has no measurements"

### Don't: Skip tags

**Bad**: "- [ ] Add tests for edge cases"
**Good**: "- [ ] `[backlog]` Add tests for edge cases in risk calculation"

### Don't: Let backlog grow indefinitely

- Review backlog monthly
- Promote items sitting > 30 days to sprints or remove
- Archive resolved items to keep list manageable

### Don't: Duplicate effort

Before creating a `[sprint]` item, check if similar sprint already exists in todo.

## Examples

### Sprint 91 Postmortem (Real Example)

```markdown
## Postmortem

### Summary
Sprint 91 integrated Equipment pages with GraphQL and added "Demo Only" banners
to Regions pages after discovering Regions have no backend support.

### Duration & Metrics
- **Duration**: 2.5 hours
- **Tests Written**: 26 (13 backend, 13 frontend)
- **Files Created**: 6
- **Files Modified**: 4

### What Went Well
- **Pattern reuse**: Equipment queries and transforms followed existing patterns
  from Sprint 89/90, making implementation straightforward
- **Early discovery**: Plan agent identified the Regions backend gap before
  implementation started, avoiding wasted effort
- **Clean scope pivot**: User clarification ("Equipment Only") allowed quick
  decision to defer Regions backend
- **DemoBanner component**: Reusable component created for future pages with mock data

### What Could Improve
- **Missing hook discovered late**: The `use-debounce.ts` hook wasn't created
  until TypeScript compilation failed
- **Regions gap not documented**: No prior documentation indicated Regions
  lacked backend support

### Patterns Discovered
- **Demo Banner pattern**: For pages where frontend exists but backend support
  is missing, add a visible banner rather than hiding the page
- **Follow-up sprint creation**: When scope is reduced, immediately create a
  follow-up sprint to capture deferred work

### Action Items
- [x] `[done]` Created Sprint 116 for Regions backend support
- [ ] `[backlog]` Consider auditing other pages for similar backend gaps
- [ ] `[backlog]` Add architecture doc noting which asset types are supported
```

## Related Recipes

- [Sprint Workflow v2](./sprint-workflow-v2.md) - Full sprint workflow
- [Epic Planning](./epic-planning.md) - Managing multi-sprint work

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-13 | Initial version with action item tags and backlog integration |
