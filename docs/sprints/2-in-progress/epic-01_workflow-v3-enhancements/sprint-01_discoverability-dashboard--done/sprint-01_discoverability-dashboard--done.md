---
sprint: 1
title: "Discoverability Dashboard"
epic: 1
status: done
created: 2026-01-06T21:01:11Z
started: 2026-01-06T21:01:11Z
completed: 2026-01-06
hours: null
workflow_version: "3.1.0"


---

# Sprint 1: Discoverability Dashboard

## Overview

| Field | Value |
|-------|-------|
| Sprint | 1 |
| Title | Discoverability Dashboard |
| Epic | 01 - Workflow v3.0 Enhancements |
| Status | Planning |
| Created | 2025-12-30 |
| Started | - |
| Completed | - |

## Goal

Create an interactive workflow status and help system that makes the sprint workflow self-documenting and reduces the learning curve for new developers.

## Background

Current pain point: Developers face a steep learning curve when using the workflow system. Skills and commands exist but aren't discoverable, there's no central command reference, and it's unclear which agents to use for different tasks. This creates friction and slows down both onboarding and day-to-day development.

The workflow system has 29+ skills and 5+ specialized agents, but without a help system, developers must read documentation or ask for guidance to discover capabilities.

## Requirements

### Functional Requirements

- [ ] Create `/workflow-help` command that displays all available commands
- [ ] Show current workflow phase and what actions are available
- [ ] Display agent recommendations based on current context
- [ ] Provide visual progress indicators for sprint status
- [ ] Link to relevant playbook patterns from status output
- [ ] Make status output actionable (show next steps)

### Non-Functional Requirements

- [ ] Help output must be concise and scannable (fit in one screen)
- [ ] Status display should use visual indicators (progress bars, icons)
- [ ] Response time < 1 second for both commands
- [ ] Work correctly whether or not a sprint is active

## Dependencies

- **Sprints**: None (foundational sprint)
- **External**: None
- **Parallelization**: ✅ Can run in parallel with Sprint 2 (Automated Lifecycle Management) - different code areas, no conflicts

## Scope

### In Scope

- `/workflow-help` skill implementation
- Enhanced `/sprint-status` output with progress visualization
- Agent recommendation system based on phase
- Quick links to playbook patterns
- Command reference documentation

### Out of Scope

- Interactive tutorial/walkthrough (future enhancement)
- Auto-complete for commands (IDE feature)
- Web-based dashboard (CLI-focused)
- Telemetry/usage tracking (covered in Sprint 5)

## Technical Approach

1. **Command Reference System**: Create structured data file mapping commands to descriptions, usage, and examples
2. **Context-Aware Recommendations**: Use sprint state JSON to determine current phase and recommend relevant agents/commands
3. **Visual Progress**: Calculate completion percentage based on sprint steps and render ASCII progress bar
4. **Playbook Integration**: Map common patterns to sprint phases for contextual help

Files to create/modify:
- `.claude/skills/workflow-help.md` - New help command implementation
- Update `.claude/hooks/validate_step.py` - Add recommendation output
- `docs/workflow-command-reference.json` - Structured command data

## Tasks

### Phase 1: Planning
- [ ] Review current workflow help/status implementations
- [ ] Design `/workflow-help` output format
- [ ] Design enhanced `/sprint-status` output format
- [ ] Create command reference structure schema

### Phase 2: Implementation
- [ ] Create `workflow-command-reference.json` data file
- [ ] Implement `/workflow-help` skill
- [ ] Enhance `/sprint-status` with progress visualization
- [ ] Add agent recommendations to status output
- [ ] Add playbook pattern links
- [ ] Create examples in docs/

### Phase 3: Validation
- [ ] Test `/workflow-help` in various contexts
- [ ] Test `/sprint-status` with active sprint
- [ ] Test `/sprint-status` without active sprint
- [ ] Verify recommendations are accurate
- [ ] Get user feedback on output format

### Phase 4: Documentation
- [ ] Add usage examples to Epic README
- [ ] Update CLAUDE.md with new commands
- [ ] Create dialog example showing discoverability improvements

## Acceptance Criteria

- [ ] `/workflow-help` displays all available commands with descriptions
- [ ] `/sprint-status` shows visual progress bar and current phase
- [ ] Recommendations shown are contextually relevant
- [ ] New developer can discover commands without reading full docs
- [ ] All tests passing
- [ ] Code reviewed and refactored

## Expected Output Example

```
$ /sprint-status

Sprint 1: Discoverability Dashboard
Status: Phase 2.2 - Implementation
Progress: [=====>    ] 50% (6/12 tasks)

NEXT ACTIONS:
  /sprint-next           Advance to step 2.3 (Tests)

RECOMMENDED AGENTS:
  • product-engineer    Implement features
  • test-runner         Run test suite

PLAYBOOK PATTERNS:
  • Self-Documenting Systems
  • Progressive Disclosure

Run /workflow-help for full command reference
```

## Open Questions

- Should `/workflow-help` show all commands or just contextual ones?
- What's the right level of detail for agent descriptions?
- Should we add emoji/colors to the output? (probably not per CLAUDE.md)

## Notes

**Priority**: High (foundational improvement)
**Estimated Effort**: 2-3 hours
**Success Metric**: 60% reduction in onboarding time (60 min → 20 min)

Based on Plan agent analysis Priority 1 from vericorr workflow review.
