# Recipe: Documentation Approach

**Category**: workflow
**Version**: 1.0
**Last Updated**: 2025-12-13
**Purpose**: Define how CorrData approaches documentation

## Philosophy

> "Documentation is a love letter to your future self."
> — Damian Conway

Our documentation follows these principles:

1. **Living Documentation** - Docs evolve with code, never static
2. **Single Source of Truth** - One authoritative location per topic
3. **Progressive Disclosure** - High-level first, details available
4. **Machine-Readable** - Structured for AI agents to consume
5. **Human-First** - But always readable by humans

## Documentation Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Documentation Layers                        │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  EXTERNAL (Customer-Facing)          mintlify-docs/            │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  • Product guides                                     │     │
│  │  • API reference                                      │     │
│  │  • MCP integration                                    │     │
│  │  • Playbook (selected recipes)                        │     │
│  │                                                       │     │
│  │  Hosted: Mintlify (docs.corrdata.com)                │     │
│  └──────────────────────────────────────────────────────┘     │
│                            ▲                                   │
│                            │ sync-playbook-to-mintlify.sh     │
│                            │                                   │
│  INTERNAL (Development)              POC/docs/                 │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  /architecture/     ADRs, system design              │     │
│  │  /playbook/         Battle-tested recipes            │     │
│  │  /sprints/          Sprint planning and tracking     │     │
│  │  /examples/         Dialog examples, scenarios       │     │
│  │  /research/         Research reports                 │     │
│  │  /business/         Business docs, emails            │     │
│  │  /guides/           Internal how-tos                 │     │
│  │  /security/         Security documentation           │     │
│  │  /planning/         Roadmaps, future work            │     │
│  │                                                       │     │
│  │  Stored: Git repository (POC/docs/)                  │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  AGENT INSTRUCTIONS                  ~/.claude/                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  /commands/         Slash command definitions        │     │
│  │  /skills/           Skill definitions                │     │
│  │  /templates/        Document templates               │     │
│  │  sprint-steps.json  Workflow configuration           │     │
│  │  CLAUDE.md          Project instructions             │     │
│  │                                                       │     │
│  │  Stored: User home (~/.claude/) or project root      │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Document Types

### Architecture Decision Records (ADRs)

**Location**: `docs/architecture/decisions/ADR-NNN-*.md`

**Purpose**: Record significant architectural decisions with context

**Template**:
```markdown
# ADR-NNN: Title

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing?

## Consequences
What becomes easier or more difficult because of this change?
```

**When to Create**:
- New technology choice
- Significant pattern change
- Integration approach
- Security decision

### Sprint Planning Files

**Location**: `docs/sprints/{status}/{epic}/sprint-NNN_title.md`

**Status Folders**:
- `0-backlog/` - Future work
- `1-todo/` - Ready to start
- `2-in-progress/` - Currently active
- `3-blocked/` - Waiting on external
- `4-done/` - Completed

**Template**: Uses `~/.claude/templates/sprint-template.md`

**Contents**:
- Goal and background
- Tasks by phase
- Model schema (if applicable)
- Acceptance criteria
- Team strategy (added during sprint)
- Postmortem (added after completion)

### Playbook Recipes

**Location**: `docs/playbook/{category}/{recipe}.md`

**Categories**:
- `workflows/` - Development processes
- `patterns/` - Reusable code patterns
- `integrations/` - External system integration
- `playbooks/` - Troubleshooting guides

**Template**: Uses `docs/playbook/_TEMPLATE.md`

**Required Sections**:
- Context (when to use/not use)
- Ingredients (prerequisites)
- Steps (detailed instructions)
- Learnings (from real sprints)
- Anti-patterns (what NOT to do)

### Dialog Examples

**Location**: `docs/examples/dialog_sprint-NNN_feature.md`

**Purpose**: Show real MCP/API interactions for training and reference

**Created By**: `skill:generate-dialog` or manually after significant features

### Research Reports

**Location**: `docs/research/RR-NNN_topic.md`

**Purpose**: Document research into external data sources, APIs, standards

**When to Create**:
- Evaluating new data source
- Investigating API integration
- Analyzing industry standards

## Documentation Workflow

### During Sprint

```
/sprint-start N
    │
    ├─ Plan agent updates sprint file with Team Strategy
    │
    ▼
[Implementation]
    │
    ├─ Code changes trigger inline documentation
    │   - Docstrings for new functions
    │   - Type hints
    │   - Comments for complex logic
    │
    ▼
/sprint-complete N
    │
    ├─ Postmortem added to sprint file
    ├─ Dialog example created (if significant feature)
    └─ Playbook recipes updated with learnings
```

### After Sprint

1. **Update Playbook**: Add learnings to relevant recipes
2. **Create ADR**: If architectural decision was made
3. **Sync to Mintlify**: If external-facing content changed

### Quarterly Review

1. Review all playbook recipes for accuracy
2. Archive outdated ADRs
3. Update roadmap documentation
4. Sync major updates to Mintlify

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| ADR | `ADR-NNN-kebab-case.md` | `ADR-025-sprint-workflow-enforcement.md` |
| Sprint | `sprint-NNN_kebab-case.md` | `sprint-91_assets-equipment-regions.md` |
| Research | `RR-NNN_kebab-case.md` | `RR-001_epa-dmr-discharge-monitoring-reports.md` |
| Dialog | `dialog_sprint-NNN_feature.md` | `dialog_sprint-36_dmr-foundation.md` |
| Recipe | `kebab-case.md` | `sprint-workflow-v2.md` |

## CLAUDE.md Instructions

The `CLAUDE.md` file in each project root provides AI-specific instructions:

**Global** (`~/.claude/CLAUDE.md`):
- Workflow system overview
- Universal commands reference
- Cross-project patterns

**Project** (`POC/CLAUDE.md`):
- Project structure
- Code standards
- Database configuration
- Sprint workflow usage

## Mintlify Sync

Selected internal docs are synced to Mintlify for external sharing:

```bash
# Sync playbook recipes
./scripts/sync-playbook-to-mintlify.sh

# Preview locally
cd /Volumes/Foundry/Development/CorrData/mintlify-docs
npx mintlify dev

# Deploy (automatic on push to main)
git push origin main
```

**What Gets Synced**:
- Playbook recipes (curated)
- API documentation
- MCP integration guides
- Product guides

**What Stays Internal**:
- Sprint files
- Business documents
- Research reports
- Internal playbooks

## Anti-Patterns

### Don't: Document in Code Comments Only

**Why it's bad**: Comments get stale, not searchable, no structure

**Instead**: Use proper doc files, link from code comments

---

### Don't: Create Documentation Without Context

**Why it's bad**: Readers don't know when to use it

**Instead**: Always include "When to use" and "When NOT to use"

---

### Don't: Skip Postmortems

**Why it's bad**: Learnings lost, mistakes repeated

**Instead**: Every sprint gets a postmortem, even small ones

---

### Don't: Let Mintlify Drift from Internal Docs

**Why it's bad**: Customers see outdated info

**Instead**: Run sync script after significant changes

## Maintenance

### Weekly
- Review sprint postmortems for playbook updates
- Update recipes with new learnings

### Monthly
- Audit playbook index for completeness
- Check Mintlify sync status

### Quarterly
- Full playbook review
- ADR cleanup
- Roadmap updates

## Related Recipes

- [Development Infrastructure](./development-infrastructure.md) - Full setup documentation
- [Sprint Workflow v2.0](./sprint-workflow-v2.md) - How sprints generate docs

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-13 | Initial documentation approach |
