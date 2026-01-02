# Project Instructions

## Workflow System

This project uses an **AI-assisted development workflow** with parallel agents, skills, and slash commands.

**Workflow Version**: See `.claude/WORKFLOW_VERSION` for current version.

### Quick Start

```bash
/sprint-new "Feature Name"    # Create a new sprint
/sprint-start <N>             # Initialize sprint, spawn Plan agent
/sprint-next                  # Advance to next step
/sprint-status                # Check progress and agent status
/sprint-complete              # Pre-flight checklist and finish
/sprint-postmortem            # Capture learnings
```

### How It Works

```
Phase 1: Planning (sequential)
├── Read sprint → Plan agent designs team → Clarify requirements

Phase 2: Implementation (PARALLEL)
├── Backend agent ──┐
├── Frontend agent ─┼── Run simultaneously
└── Test agent ─────┘

Phase 3: Validation (sequential)
├── Integrate → Run tests → Quality review → User approval

Phase 4: Complete (sequential)
├── Commit → Move to done → Postmortem
```

### Key Concepts

- **Agents**: Plan, product-engineer, quality-engineer, test-runner, devops-engineer
- **State Files**: `.claude/sprint-N-state.json` tracks each sprint
- **Sprint Counter**: `docs/sprints/next-sprint.txt` auto-assigns numbers

### Sprint Directories

| Directory | Purpose |
|-----------|---------|
| `docs/sprints/1-todo/` | Planned sprints waiting to start |
| `docs/sprints/2-in-progress/` | Currently active sprints |
| `docs/sprints/3-done/` | Completed sprints |
| `docs/sprints/5-aborted/` | Cancelled/abandoned sprints |

### Workflow Enforcement

The sprint workflow is enforced via hooks. Key rules:
- Cannot skip steps - must complete current before advancing
- Cannot commit without completing sprint
- All sprints require postmortem before completion
- Sprint numbers auto-assigned from counter file

### Epic Management

Group related sprints into epics:

```bash
/epic-new "Epic Name"         # Create new epic
/epic-start <N>               # Start working on epic
/sprint-new "Feature" --epic=N # Add sprint to epic
/epic-complete <N>            # Finish epic when all sprints done
```

---

## Project-Specific Instructions

<!-- Add your project-specific instructions below -->

### Code Standards

- Add your coding standards here

### Testing Requirements

- Add your testing requirements here

### Deployment

- Add your deployment process here
