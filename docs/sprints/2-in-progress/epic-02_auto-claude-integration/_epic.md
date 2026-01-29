---
epic: 2
title: "Auto-Claude Integration"
status: in-progress
created: 2026-01-29
started: 2026-01-29T14:42:41Z
completed: null

---

# Epic 2: Auto-Claude Integration

## Overview

Integrate Maestro's workflow enforcement capabilities into Auto-Claude's autonomous multi-agent framework. This creates a "Conductor and Orchestra" model where Maestro defines WHAT gets built and HOW GOOD it needs to be, while Auto-Claude handles WHO builds it and executes autonomously with parallel agents.

**Key Value**: Auto-Claude excels at execution (parallel agents, autonomous builds). Maestro excels at process enforcement (quality gates, step progression, postmortems). Together they create a system that builds fast AND builds right.

## Vision Documents

- [Vision Document](../../proposals/maestro-auto-claude-vision.md)
- [Technical Proposal](../../proposals/maestro-auto-claude-integration-proposal.md)

## Success Criteria

- [ ] Auto-Claude specs accept `type` field with 6 sprint types
- [ ] Coverage validation uses type-specific thresholds (spike=0%, backend=85%)
- [ ] Maestro's 9-item pre-flight checklist integrated into Auto-Claude QA pipeline
- [ ] Workflow state syncs between Auto-Claude stages and Maestro phases
- [ ] Postmortems auto-generated after spec completion
- [ ] Optional epic/sprint hierarchy available in Auto-Claude

## Sprints

| Sprint | Title | Status | Depends On |
|--------|-------|--------|------------|
| 8 | Sprint Type Foundation | planned | - |
| 9 | Quality Gate Integration | planned | Sprint 8 |
| 10 | State Synchronization | planned | Sprint 8 |
| 11 | Postmortem Generation | planned | Sprint 10 |
| 12 | Epic Sprint Hierarchy | planned | Sprint 8 |

## Backlog

- [ ] Fork Auto-Claude repository
- [ ] Set up development environment
- [ ] Extend spec_contract.json with type field
- [ ] Create MaestroQualityGate adapter
- [ ] Implement 9-item pre-flight checklist
- [ ] Create state bridge module
- [ ] Map Auto-Claude stages to Maestro phases
- [ ] Build postmortem generator
- [ ] Add epic grouping to specs
- [ ] Write integration tests
- [ ] Documentation and migration guide

## Architecture

```
YOU ──► MAESTRO (define work, set quality bar) ──► AUTO-CLAUDE (parallel execution)
                                                          │
                                                          ▼
                                              MAESTRO QUALITY GATE
                                                          │
                                                          ▼
                                              Postmortem & Learnings
```

## Notes

Created: 2026-01-29
Target Repository: https://github.com/AndyMik90/Auto-Claude.git
