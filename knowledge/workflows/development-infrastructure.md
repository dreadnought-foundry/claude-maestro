# Recipe: Development Infrastructure

**Category**: workflow
**Version**: 1.0
**Last Updated**: 2025-12-13
**Purpose**: Document our complete AI-assisted development setup

## Overview

This recipe documents the complete infrastructure for AI-assisted development at CorrData, including agents, skills, slash commands, and how they work together.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Development Infrastructure                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  USER                                                                   │
│    │                                                                    │
│    ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    SLASH COMMANDS                                │   │
│  │  /sprint-start  /sprint-next  /sprint-complete  /epic-*         │   │
│  └─────────────────────────┬───────────────────────────────────────┘   │
│                            │                                            │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      PARENT AGENT                                │   │
│  │  (Claude Code main session)                                      │   │
│  │  - Orchestrates workflow                                         │   │
│  │  - Spawns sub-agents                                             │   │
│  │  - Integrates work                                               │   │
│  └─────────────────────────┬───────────────────────────────────────┘   │
│                            │                                            │
│              ┌─────────────┼─────────────┐                             │
│              ▼             ▼             ▼                              │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                 │
│  │    AGENTS     │ │    AGENTS     │ │    AGENTS     │                 │
│  │ Plan          │ │ product-eng   │ │ quality-eng   │                 │
│  │ Explore       │ │ devops-eng    │ │ test-runner   │                 │
│  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘                 │
│          │                 │                 │                          │
│          └─────────────────┼─────────────────┘                          │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        SKILLS                                    │   │
│  │  validate-graphql  validate-mcp  check-coverage  run-migrations │   │
│  │  lint-fix  generate-dialog  smoke-tests  build-pwa              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Current Inventory

### Agents (Built-in to Claude Code)

| Agent | Purpose | When Used | Spawned By |
|-------|---------|-----------|------------|
| **Plan** | Architecture design, team strategy | Sprint planning (Phase 1) | /sprint-start |
| **Explore** | Codebase exploration, research | Finding files, understanding code | Manual or auto |
| **product-engineer** | Full-stack implementation | Backend/frontend work (Phase 2) | /sprint-next |
| **quality-engineer** | Testing, quality review | Test writing, code review (Phase 2-3) | /sprint-next |
| **test-runner** | Execute tests, analyze failures | Validation (Phase 3) | /sprint-next |
| **devops-engineer** | Infrastructure, deployment | CI/CD, scaling | Manual |
| **chief-executive-architect** | Complex cross-domain problems | Major initiatives | Manual |
| **digital-twin-data-scientist** | Data modeling, pipelines | Data layer work | Manual |

### Skills (Custom Created)

#### Development Skills
| Skill | File | Purpose | Invoked By |
|-------|------|---------|------------|
| **validate-graphql** | `~/.claude/skills/validate-graphql.md` | Schema validation, GraphQL tests | Frontend agent |
| **validate-mcp** | `~/.claude/skills/validate-mcp.md` | MCP server and tool tests | Backend agent |
| **check-coverage** | `~/.claude/skills/check-coverage.md` | pytest with 85% threshold | Test agent |
| **run-migrations** | `~/.claude/skills/run-migrations.md` | Alembic migration verification | Backend agent |
| **lint-fix** | `~/.claude/skills/lint-fix.md` | Ruff linting and formatting | Quality agent |
| **generate-dialog** | `~/.claude/skills/generate-dialog.md` | Create dialog examples | Documentation |
| **smoke-tests** | `~/.claude/skills/smoke-tests.md` | Quick API health verification | Quality agent |
| **build-pwa** | `~/.claude/skills/build-pwa.md` | Build and verify PWA | Frontend agent |

#### DevOps Skills
| Skill | File | Purpose | Invoked By |
|-------|------|---------|------------|
| **deploy-staging** | `~/.claude/skills/deploy-staging.md` | Deploy to staging environment | DevOps agent |
| **deploy-production** | `~/.claude/skills/deploy-production.md` | Deploy to production (with safeguards) | DevOps agent |
| **health-check** | `~/.claude/skills/health-check.md` | Verify deployment health | DevOps/Quality agent |
| **setup-cicd** | `~/.claude/skills/setup-cicd.md` | Configure GitHub Actions workflows | DevOps agent |

### Slash Commands

#### Sprint Workflow
| Command | Description | Phase |
|---------|-------------|-------|
| `/sprint-start <N>` | Initialize sprint, spawn Plan agent | Phase 1 |
| `/sprint-next <N>` | Advance to next step, spawn agents | All phases |
| `/sprint-status <N>` | Check progress, agent status | Any time |
| `/sprint-complete <N>` | Pre-flight checklist, finish | Phase 4 |
| `/sprint-postmortem <N>` | Generate learnings | After completion |
| `/sprint-abort <N>` | Cancel sprint | Any time |
| `/sprint-blocked <N>` | Mark as blocked | Any time |
| `/sprint-resume <N>` | Resume blocked sprint | After unblocked |
| `/sprint-new` | Create new sprint file | Before starting |
| `/sprint-add-to-epic` | Add sprint to epic | Organization |

#### Epic Workflow
| Command | Description |
|---------|-------------|
| `/epic-new` | Create new epic |
| `/epic-start` | Move epic to in-progress |
| `/epic-status` | Show epic details |
| `/epic-complete` | Finish epic |
| `/epic-list` | List all epics |
| `/epic-archive` | Archive completed epic |

#### Product Workflow
| Command | Description |
|---------|-------------|
| `/product-new` | Create product spec |
| `/product-start` | Start product development |
| `/product-next` | Advance product stage |
| `/product-status` | Check product status |
| `/product-approve` | Approve for release |
| `/product-complete` | Mark complete |
| `/product-list` | List products |

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `sprint-steps.json` | `~/.claude/sprint-steps.json` | Workflow phase/step definitions |
| `sprint-template.md` | `~/.claude/templates/sprint-template.md` | Sprint file template |
| State files | `.claude/sprint-N-state.json` | Per-sprint progress tracking |

## Gap Analysis

### Current Gaps (Recommended Additions)

#### Missing Skills

| Skill | Purpose | Priority |
|-------|---------|----------|
| **smoke-tests** | Quick API health check | High |
| **build-pwa** | Build mobile PWA, check for errors | Medium |
| **security-scan** | Basic OWASP vulnerability check | Medium |
| **api-docs-gen** | Generate OpenAPI/GraphQL docs | Low |

#### Agent Coverage

We have good coverage. Consider:
- **documentation-engineer** - Auto-generate and maintain docs (future)
- **security-engineer** - Security-focused reviews (future)

### Recommendation

**Current setup is sufficient for our needs.** Add skills as pain points emerge:
1. If PWA builds break frequently → add `build-pwa` skill
2. If smoke tests are often forgotten → add `smoke-tests` skill
3. If security issues slip through → add `security-scan` skill

## How It All Works Together

### Flow Example: Sprint 91

```
User: /sprint-start 91

Parent Agent:
├─ Reads sprint file
├─ Spawns Plan agent
│   └─ Returns: sprint_type=fullstack, team=[backend, frontend, tests]
├─ Asks clarifying questions
└─ Documents team strategy in sprint file

User: /sprint-next 91

Parent Agent:
├─ Spawns product-engineer (Backend)
│   ├─ Creates models
│   ├─ Invokes skill:run-migrations
│   └─ Invokes skill:validate-mcp
├─ Spawns product-engineer (Frontend)
│   └─ Invokes skill:validate-graphql
└─ Spawns quality-engineer (Tests)
    └─ Invokes skill:check-coverage

[All complete]

Parent Agent:
├─ Integrates work
├─ Runs full test suite
├─ Spawns quality-engineer for review
│   └─ Invokes skill:lint-fix
└─ Asks for user approval

User: Approved

Parent Agent:
├─ Commits changes
├─ Moves sprint to done
├─ Runs postmortem
└─ Final commit
```

## Maintenance

### Adding a New Skill

1. Create file: `~/.claude/skills/{skill-name}.md`
2. Follow template structure (see existing skills)
3. Update `sprint-steps.json` to reference skill
4. Update this documentation

### Adding a New Slash Command

1. Create file: `~/.claude/commands/{command-name}.md`
2. Include frontmatter with description and allowed-tools
3. Document in this recipe

### Upgrading Workflow Version

1. Update `~/.claude/sprint-steps.json`
2. Add backward compatibility check for version field
3. Update slash commands to handle new workflow
4. Document changes in playbook

## Related Recipes

- [VS Code Setup](./vscode-setup.md) - Multi-terminal setup for parallel agents
- [Sprint Workflow v2.0](./sprint-workflow-v2.md) - Detailed sprint execution
- [Documentation Approach](./documentation-approach.md) - How we document

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-13 | Initial documentation of infrastructure |
