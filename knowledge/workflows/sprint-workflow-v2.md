# Recipe: Sprint Workflow v2.2.1

**Category**: workflow
**Version**: 2.2.1
**Last Updated**: 2025-12-14
**Sprints**: Developed from learnings across Sprints 1-106

## Context

**When to use this recipe:**
- Starting any new sprint in CorrData
- Coordinating multiple work streams (backend, frontend, tests)
- When parallel development can speed delivery

**When NOT to use this recipe:**
- Simple one-file fixes (just do them directly)
- Pure research tasks (use Explore agent instead)
- Sprints without `workflow_version: "2.0"` in state (use legacy flow)

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sprint Workflow v2.0                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: Planning (Sequential)                                 │
│  ┌─────┐   ┌──────────┐   ┌─────────┐   ┌──────────────┐       │
│  │Read │ → │Plan+Team │ → │Clarify  │ → │Document      │       │
│  │Sprint│   │Design   │   │Questions│   │Strategy      │       │
│  └─────┘   └──────────┘   └─────────┘   └──────────────┘       │
│                              ↑                                  │
│                         User Gate                               │
│                                                                 │
│  Phase 2: Implementation (PARALLEL)                             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  ┌─────────┐   ┌──────────┐   ┌─────────┐           │      │
│  │  │Backend  │   │Frontend  │   │Tests    │           │      │
│  │  │Agent    │   │Agent     │   │Agent    │           │      │
│  │  └────┬────┘   └────┬─────┘   └────┬────┘           │      │
│  │       │             │              │                 │      │
│  │       └─────────────┼──────────────┘                 │      │
│  │                     ↓                                │      │
│  │              Parent Collects                         │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  Phase 3: Validation (Sequential)                               │
│  ┌─────────┐   ┌──────┐   ┌─────────┐   ┌────────────┐        │
│  │Integrate│ → │Tests │ → │Quality  │ → │User        │        │
│  │Work     │   │+Cover│   │Review   │   │Approval    │        │
│  └─────────┘   └──────┘   └─────────┘   └────────────┘        │
│                                             ↑                   │
│                                        User Gate                │
│                                                                 │
│  Phase 4: Complete (Sequential)                                 │
│  ┌──────┐   ┌────────┐   ┌───────────┐   ┌───────────┐        │
│  │Commit│ → │Move to │ → │Postmortem │ → │Final      │        │
│  │      │   │Done    │   │           │   │Commit     │        │
│  └──────┘   └────────┘   └───────────┘   └───────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Sprint File Lifecycle

Sprints follow a consistent file organization pattern with `--done` suffix to track completion.

### Epic Sprints (Grouped Work)

Epic sprints move **together as a group** when the epic starts:

```
1-todo/epic-N_name/                    2-in-progress/epic-N_name/
├── sprint-A_title.md                  ├── sprint-A_title.md
├── sprint-B_title.md    ─────────►    ├── sprint-B_title--done.md
└── sprint-C_title.md    /epic-start   └── sprint-C_title.md

                                       3-done/epic-N_name/
                         ─────────►    ├── sprint-A_title--done.md
                         /epic-complete├── sprint-B_title--done.md
                         (all --done)  └── sprint-C_title--done.md
```

**Key Rules:**
- `/epic-start N` moves ALL sprints to `2-in-progress/` together
- `/sprint-start N` for epic sprints **requires epic to be started first**
- `/sprint-complete N` adds `--done` suffix but keeps file in epic folder
- `/epic-complete N` only works when ALL sprints have `--done` suffix

### Standalone Sprints

Standalone sprints move individually through the lifecycle:

```
1-todo/                      2-in-progress/               3-done/_standalone/
sprint-X_title.md  ────►    sprint-X_title.md   ────►   sprint-X_title--done.md
               /sprint-start              /sprint-complete
```

**Key Rules:**
- `/sprint-start N` moves standalone sprint to `2-in-progress/`
- `/sprint-complete N` adds `--done` suffix and moves to `3-done/_standalone/`

### File Naming Convention

| State | Suffix | Location |
|-------|--------|----------|
| Todo | (none) | `1-todo/` or `1-todo/epic-N_name/` |
| In Progress | (none) | `2-in-progress/` or `2-in-progress/epic-N_name/` |
| Completed | `--done` | `3-done/_standalone/` or `3-done/epic-N_name/` |
| Aborted | `--aborted` | Same as completed |
| Blocked | `--blocked` | Stays in `2-in-progress/` |

## Ingredients

Before starting, ensure you have:

- [ ] Sprint planning file in `docs/sprints/1-todo/{epic}/sprint-N_*.md`
- [ ] Claude Code with slash commands configured
- [ ] Database running and migrations current
- [ ] No uncommitted changes in working directory

## Steps

### Phase 1: Planning

#### Step 1.1: Start the Sprint

```bash
/sprint-start <N>
```

This will:
1. Find and read the sprint file
2. Move it to `2-in-progress/`
3. Create state file `.claude/sprint-N-state.json`

#### Step 1.2: Plan Agent Designs Team Strategy

The Plan agent will analyze the sprint and determine:

| Decision | Options | How It's Chosen |
|----------|---------|-----------------|
| Sprint Type | backend-only, frontend-only, fullstack, integration, data-layer | Based on files to create/modify |
| Parallelism | Yes/No | Multiple independent work streams |
| TDD Approach | Strict, Flexible, Coverage-based | Complexity of business logic |
| Team Composition | Agent assignments | Based on file types |

**Expected output**: Team strategy with file ownership map

#### Step 1.3: Clarify Requirements (User Gate)

You'll be asked questions about:
- Ambiguous requirements
- Design decisions
- Edge cases
- Preferences

**Answer these carefully** - this is the only planning gate.

#### Step 1.4: Document Strategy

The sprint file is updated with:
```markdown
## Team Strategy

### Agent Assignments
| Agent | Role | Files Owned | Skills |
|-------|------|-------------|--------|
| product-engineer | Backend | src/corrdata/... | run-migrations |
| product-engineer | Frontend | mobile-pwa/... | validate-graphql |
| quality-engineer | Tests | tests/test_sprint*.py | check-coverage |
```

### Phase 2: Implementation (Parallel)

#### Step 2.1-2.3: Parallel Agent Execution

```bash
/sprint-next <N>
```

This spawns parallel agents:

**Backend Agent** receives:
```
You are implementing backend for Sprint N.
Files you own: [list]
Skills: run-migrations, validate-mcp
ONLY modify your files.
Report progress with STATUS: markers.
```

**Frontend Agent** receives:
```
You are implementing frontend for Sprint N.
Files you own: [list]
Skills: validate-graphql
ONLY modify your files.
Report progress with STATUS: markers.
```

**Test Agent** receives:
```
You are implementing tests for Sprint N.
Files you own: tests/test_sprintN_*.py
Skills: check-coverage
Write tests for all acceptance criteria.
```

#### Monitoring Progress

Check agent status anytime:
```bash
/sprint-status <N>
```

Output shows:
```
Sprint N - Phase 2: Implementation

| Agent | Role | Status | Progress | Issues |
|-------|------|--------|----------|--------|
| abc123 | Backend | running | 3/5 tasks | None |
| def456 | Frontend | running | 2/4 tasks | Waiting for API |
| ghi789 | Tests | complete | 5 tests | None |
```

### Phase 3: Validation

#### Step 3.1: Integration

Parent agent:
1. Collects all parallel agent outputs
2. Checks for file conflicts
3. Resolves any integration issues
4. Ensures all pieces fit together

#### Step 3.2: Run Tests

```bash
# Automated by workflow
pytest tests/ --cov=src/corrdata --cov-report=term
```

**Must achieve:**
- All tests passing
- Coverage >= 75%

#### Step 3.3: Quality Review

Quality engineer agent:
1. Runs lint/format (`skill:lint-fix`)
2. Reviews code quality
3. Checks for security issues
4. Validates documentation

#### Step 3.4: User Approval (Final Gate)

You'll see:
```
Sprint N ready for commit.

## Summary
- Files created: 8
- Files modified: 3
- Tests: 12/12 passing
- Coverage: 87%
- Lint: Clean

Approve commit? [Yes/No]
```

### Phase 4: Complete

#### Step 4.1: Git Commit

```bash
# Automated
git add .
git commit -m "feat(sprint-N): {description}

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### Step 4.2: Move Sprint to Done

Sprint file renamed with `--done` suffix and moved:
- **Epic sprints**: `sprint-N_title.md` → `sprint-N_title--done.md` (stays in epic folder)
- **Standalone sprints**: Moved to `3-done/_standalone/sprint-N_title--done.md`

#### Step 4.2b: Create Git Tag

After moving the sprint file, a git tag is created:

```bash
git tag -a "sprint-N" -m "Sprint N: <title>"
```

**Tag Format**: `sprint-N` (e.g., `sprint-42`, `sprint-123`)

Tags enable easy navigation to specific sprint commits:
```bash
# View all sprint tags
git tag -l "sprint-*"

# Checkout specific sprint
git checkout sprint-42

# Compare two sprints
git diff sprint-41..sprint-42
```

**Note**: Tags are local by default. Push to share:
```bash
git push origin sprint-N
```

#### Step 4.3: Postmortem & Action Items

Postmortem is now **auto-generated** during `/sprint-complete`. It captures:
- Duration and metrics
- What went well
- What could improve
- Patterns discovered
- **Tagged action items** (see below)

**Action Item Tags**:

| Tag | Meaning | Destination |
|-----|---------|-------------|
| `[done]` | Already resolved | Marked with link |
| `[sprint]` | Needs dedicated sprint | New todo sprint + backlog |
| `[backlog]` | Future work | `docs/sprints/backlog.md` |
| `[pattern]` | Reusable pattern | Playbook |

**Backlog Integration**:
- Action items are added to `docs/sprints/backlog.md`
- When starting a new sprint, related backlog items are surfaced
- This creates a feedback loop: learnings → backlog → future sprints

#### Step 4.4: Final Commit

Commits the postmortem, action items, and sprint file updates.

## Skills Reference

| Skill | When Invoked | What It Does |
|-------|--------------|--------------|
| `validate-graphql` | Frontend work | Schema validation, GraphQL tests |
| `validate-mcp` | MCP tool changes | Server import, tool tests |
| `check-coverage` | After tests | pytest with coverage threshold |
| `run-migrations` | Database changes | Alembic upgrade verification |
| `lint-fix` | Quality review | Ruff check and format |
| `generate-dialog` | New capabilities | Create dialog example |

## Learnings

### From Sprint 85-88 (Epic 12)
- GraphQL modules benefit from parallel frontend/backend work
- Tests written alongside code find issues faster than tests-first
- Single approval gate reduces context-switching overhead

### From Sprint Workflow Design
- File ownership prevents merge conflicts
- Progress visibility (STATUS markers) helps monitoring
- Postmortems capture learnings that would otherwise be lost

## Anti-Patterns

### Don't: Spawn Agents Without File Ownership

**What it looks like**: Multiple agents modifying `models.py`

**Why it's bad**: Merge conflicts, race conditions, lost work

**Instead**: Plan agent assigns exclusive file ownership

---

### Don't: Skip the Clarification Gate

**What it looks like**: Rushing through planning to start coding

**Why it's bad**: Rework when requirements were ambiguous

**Instead**: Take time to answer questions, even "No questions, looks clear"

---

### Don't: Ignore Agent Progress

**What it looks like**: Running `/sprint-next` and walking away

**Why it's bad**: Blocked agents can't make progress, issues compound

**Instead**: Check `/sprint-status` periodically, address ISSUES immediately

---

### Don't: Skip Action Item Processing

**What it looks like**: Writing postmortem action items without tags

**Why it's bad**: Items get lost, same problems recur in future sprints

**Instead**: Tag every action item (`[done]`, `[sprint]`, `[backlog]`, `[pattern]`) and process them to the appropriate destination. Postmortems are now auto-generated during `/sprint-complete`

## Variations

### For Backend-Only Sprints

- Skip Step 2.2 (Frontend)
- Focus skills: `run-migrations`, `validate-mcp`
- Often faster due to no frontend coordination

### For Integration Sprints

- Minimal new code, mostly wiring
- Coverage-based TDD (hit 75%, timing flexible)
- Extra attention to integration testing

### For Data-Layer Sprints

- Heavy focus on migrations
- May need sequential execution (migration order matters)
- Extra verification of database state

## Related Recipes

- [Epic Planning](./epic-planning.md) - Managing multi-sprint epics
- [Postmortem Process](./postmortem-process.md) - Deep dive on postmortems
- [GraphQL Module Pattern](../patterns/graphql-module.md) - Adding new GraphQL

## Slash Commands Reference

### Sprint Commands

| Command | When to Use |
|---------|-------------|
| `/sprint-new "<title>"` | Create new sprint file |
| `/sprint-start <N>` | Initialize sprint, create state file |
| `/sprint-next <N>` | Advance to next step |
| `/sprint-status <N>` | Check progress, agent status |
| `/sprint-complete <N>` | Run checklist, add `--done` suffix, create `sprint-N` tag |
| `/sprint-postmortem <N>` | Generate postmortem |
| `/sprint-abort <N>` | Cancel sprint, add `--aborted` suffix |
| `/sprint-blocked <N>` | Mark as blocked |
| `/sprint-resume <N>` | Resume blocked sprint |

### Epic Commands

| Command | When to Use |
|---------|-------------|
| `/epic-new "<title>"` | Create new epic folder and file |
| `/epic-start <N>` | Move epic folder to `2-in-progress/` |
| `/epic-status <N>` | View epic progress and sprint status |
| `/epic-complete <N>` | Move epic to `3-done/`, create `epic-N` tag |
| `/epic-list` | List all epics with status |
| `/epic-archive <N>` | Archive completed epic |

### Git Tags

Both sprints and epics create annotated git tags on completion:

| Type | Tag Format | Example |
|------|------------|---------|
| Sprint | `sprint-N` | `sprint-42` |
| Epic | `epic-N` | `epic-8` |

**Useful Commands**:
```bash
# List all workflow tags
git tag -l "sprint-*" "epic-*"

# View tag details
git show sprint-42

# Push all tags to remote
git push origin --tags

# Find commits between epics
git log epic-7..epic-8 --oneline
```

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.2.1 | 2025-12-14 | Git tags on sprint/epic completion (`sprint-N`, `epic-N`) |
| 2.2 | 2025-12-14 | Consistent `--done` suffix for all sprints, epic sprint lifecycle, sprint-start validates epic membership |
| 2.1 | 2025-12-13 | Auto-postmortems, action item tags, backlog integration |
| 2.0 | 2025-12-13 | Parallel agents, skills, single gate, postmortems |
| 1.0 | 2025-12-03 | Original sequential 6-phase workflow |
