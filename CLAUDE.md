# Global Claude Code Instructions

## Sprint Workflow System

This is a **3-layer workflow enforcement system** for consistent sprint execution across all projects.

### Quick Start

```bash
# Start a new sprint
/sprint-start <N>

# Check current progress
/sprint-status

# Advance to next step after completing current
/sprint-next

# Complete sprint (runs pre-flight checklist)
/sprint-complete

# Abort if needed
/sprint-abort <reason>
```

### How It Works

1. **Slash Commands** - Entry points that guide workflow execution
2. **State File** - `.claude/sprint-state.json` tracks progress per project
3. **Steps Definition** - `~/.claude/sprint-steps.json` defines the workflow

### Phases Overview

| Phase | Name | Steps | Description |
|-------|------|-------|-------------|
| 1 | Planning | 1.1-1.4 | Read sprint, design architecture, clarify requirements |
| 2 | Test-First Implementation | 2.1-2.4 | TDD: write tests, implement, run tests, fix failures |
| 3 | Validation & Refactoring | 3.1-3.4 | Verify migrations, quality review, refactor, re-test |
| 4 | Documentation | 4.1 | Generate dialog examples |
| 5 | Commit | 5.1 | Stage and commit changes |
| 6 | Completion | 6.1-6.4 | Update sprint file, checklist, close sprint |

### Key Features

- **DRY Architecture Design** - Plan agent designs code structure before implementation
- **Mandatory Clarification** - Must ask user questions before starting implementation
- **Post-Implementation Refactoring** - Clean up code after tests pass
- **Pre-Flight Checklist** - 9 items must pass before sprint completion

### Project Setup

For a project to use this workflow, it needs:

1. Sprint planning files organized by status:
   ```
   docs/sprints/
   ├── 0-backlog/      # Future sprints
   ├── 1-todo/         # Ready to start
   ├── 2-in-progress/  # Currently active
   ├── 3-done/         # Completed
   ├── 4-blocked/      # Waiting on dependencies
   ├── 5-abandoned/    # Cancelled/abandoned
   └── 6-archived/     # Archived completed sprints
   ```
2. The state file `.claude/sprint-state.json` (created by `/sprint-start`)

### Enforcement Rules

- Cannot skip steps - must complete current before advancing
- Cannot commit before Phase 5
- Cannot complete without all checklist items passing
- Every step recorded with timestamp for audit trail

### CRITICAL: Use Slash Commands for ALL Sprint Operations

**NEVER manually:**
- Create sprint folders or files
- Edit `docs/sprints/registry.json`
- Edit `.claude/sprint-*-state.json`
- Move or rename sprint files
- Update sprint status in YAML frontmatter
- Call `scripts/sprint_lifecycle.py` directly

**ALWAYS use slash commands:**

```bash
/sprint-new "Title"           # Create new sprint (auto-number)
/sprint-new "Title" --epic=N  # Create sprint in epic
/sprint-start <N>             # Start sprint, create state file
/sprint-status                # Check progress
/sprint-next                  # Advance to next step
/sprint-complete <N>          # Complete with postmortem, tags, etc.
```

**What the slash commands handle:**

| Command | Creates/Updates |
|---------|----------------|
| `/sprint-new` | Sprint folder, markdown file, registry entry |
| `/sprint-start` | State file, YAML frontmatter (status, started) |
| `/sprint-complete` | Postmortem, --done suffix, registry, git tag |

**The slash commands invoke skills that use `scripts/sprint_lifecycle.py` internally.** You should NEVER call the script directly - always use the slash command.

## Sprint Types

The workflow supports 6 sprint types with different quality gates to reduce false failures and enable experimental work:

| Type | Coverage | Key Requirements |
|------|----------|-----------------|
| fullstack | 75% | Integration tests recommended |
| backend | 85% | Integration tests required |
| frontend | 70% | Visual regression tests |
| research | 30% | Documentation mandatory |
| spike | 0% | Documentation mandatory |
| infrastructure | 60% | Smoke tests required |

### Usage

Add to sprint frontmatter:
```yaml
---
sprint: 42
type: backend
coverage_threshold: 80  # Optional override
# Justification: Higher threshold due to critical validation logic
---
```

### Default Behavior

- Sprints without a `type` field default to `fullstack` (75% coverage)
- A warning will be logged for sprints missing the type field

### Coverage Override

You can override the default coverage threshold with justification:

```yaml
coverage_threshold: 65
# Justification: Integrating with external API, some paths not testable locally
```

**Rules**:
- Justification comment required (must include "Justification:")
- Valid range: 0-100%
- Self-service (no approval needed)

### Choosing the Right Type

See `docs/patterns/sprint-type-classification.md` for detailed guidance including:
- Decision tree for choosing sprint type
- Examples of each type
- Common scenarios and recommendations
- Override best practices

## Knowledge Base

Architecture patterns, playbooks, standards, and workflow documentation live in `knowledge/`. See [knowledge/README.md](knowledge/README.md) for the full index.

Key references:
- **Patterns** — `knowledge/patterns/` — Reusable architecture recipes (provider pattern, domain layering, etc.)
- **Playbooks** — `knowledge/playbooks/` — Step-by-step guides (project bootstrap, deployment, data sources)
- **Standards** — `knowledge/standards/` — Coding conventions and quality standards
- **Workflows** — `knowledge/workflows/` — Process docs (sprint lifecycle, migrations, postmortems)
- **ADR Synthesis** — `knowledge/ADR-SYNTHESIS.md` — 49 architecture decision records
