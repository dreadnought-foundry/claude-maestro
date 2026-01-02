---
sprint: 5
title: "Analytics & Insights"
epic: 1
type: backend
status: in-progress
created: 2026-01-02T12:47:18Z
started: 2026-01-02T12:47:18Z
completed: null
hours: null
workflow_version: "3.1.0"

---

# Sprint 5: Analytics & Insights

## Overview

| Field | Value |
|-------|-------|
| Sprint | 5 |
| Title | Analytics & Insights |
| Epic | 01 - Workflow v3.0 Enhancements |
| Status | Planning |
| Created | 2025-12-30 |
| Started | - |
| Completed | - |

## Goal

Track and visualize workflow metrics to enable data-driven improvements and achieve 15% faster workflow velocity through bottleneck identification and optimization.

## Background

Current pain point: No visibility into workflow efficiency. We don't track agent execution times, phase breakdowns, coverage deltas, or context token usage. Without metrics, we can't identify bottlenecks, measure improvement velocity, or optimize agent usage.

Questions we can't answer today:
- Which workflow phases take the longest?
- Which agents are most/least efficient?
- How does coverage change per sprint?
- What's the average time to complete each sprint type?
- Are we getting faster over time?

This sprint adds comprehensive tracking and a `/sprint-analytics` command for insights.

## Requirements

### Functional Requirements

- [ ] Expand `.claude/sprint-state.json` to track agent executions with timing
- [ ] Track phase timings (planning, implementation, validation, documentation)
- [ ] Track coverage delta (before/after sprint)
- [ ] Track context tokens used per agent
- [ ] Track files modified per agent
- [ ] Create `/sprint-analytics [N]` command to display metrics
- [ ] Show timing breakdown by phase
- [ ] Compare sprint to historical averages
- [ ] Identify slowest phases and suggest optimizations
- [ ] Enhance sprint registry with analytics metadata
- [ ] Support analytics across all sprint types

### Non-Functional Requirements

- [ ] State file size must remain manageable (< 100KB per sprint)
- [ ] Analytics computation must be < 2 seconds
- [ ] Historical data must be archived after 90 days
- [ ] Analytics must work for incomplete sprints (in-progress)

## Dependencies

- **Sprints**: Sprint 2 (Automated Lifecycle Management) - needs enhanced state tracking
- **External**: None
- **Parallelization**: ❌ Must run AFTER Sprint 2 completes (depends on state tracking improvements)

## Scope

### In Scope

- Enhanced state tracking (agents, phases, coverage, tokens)
- `/sprint-analytics` command implementation
- Timing breakdown visualization
- Historical comparison and averages
- Bottleneck identification
- Sprint registry enhancement with metrics
- Analytics for all sprint types

### Out of Scope

- Real-time dashboards (CLI-focused)
- Cross-project analytics (single project only)
- Agent performance benchmarking (future)
- Predictive sprint duration estimates (future)
- Web-based analytics visualization (future)

## Technical Approach

1. **Expanded State Tracking** (`.claude/sprint-state.json`):
   ```json
   {
     "agent_executions": [
       {
         "agent": "product-engineer",
         "phase": "2.2",
         "started_at": "2025-12-30T14:30:00Z",
         "completed_at": "2025-12-30T15:45:00Z",
         "duration_seconds": 4500,
         "files_modified": 5,
         "context_tokens_used": 12500
       }
     ],
     "phase_timings": {
       "1_planning": 1800,  // seconds
       "2_implementation": 3600,
       "3_validation": 900
     },
     "coverage_delta": {
       "before": 73.2,
       "after": 78.5,
       "delta": +5.3
     }
   }
   ```

2. **Analytics Command** (`/sprint-analytics [N]`):
   - Parse sprint state JSON
   - Calculate phase percentages
   - Compare to registry averages
   - Identify slowest phases
   - Suggest optimizations

3. **Sprint Registry Enhancement** (`scripts/build-sprint-registry.py`):
   ```python
   {
     "sprint_258": {
       "duration_hours": 1.75,
       "agents_used": ["Plan", "product-engineer", "quality-engineer"],
       "phase_breakdown": {
         "planning": 0.25,
         "implementation": 1.0,
         "validation": 0.35,
         "documentation": 0.15
       },
       "test_count": 38,
       "coverage_improvement": 5.3
     }
   }
   ```

Files to create/modify:
- `.claude/sprint-state.schema.json` (add analytics fields)
- `.claude/skills/sprint-analytics.md` (new command)
- `scripts/build-sprint-registry.py` (add metrics aggregation)
- `scripts/analytics_engine.py` (new - analytics computation)

## Tasks

### Phase 1: Planning
- [ ] Review current state tracking in Sprint 2
- [ ] Design expanded state schema for analytics
- [ ] Design analytics computation algorithms
- [ ] Plan visualization format (ASCII graphs, tables)

### Phase 2: Implementation
- [ ] Update sprint state schema with analytics fields
- [ ] Create `scripts/analytics_engine.py` for computations
- [ ] Implement `/sprint-analytics` command
- [ ] Add agent execution tracking to state updates
- [ ] Add phase timing tracking
- [ ] Add coverage delta calculation
- [ ] Enhance `build-sprint-registry.py` with metrics
- [ ] Create historical comparison logic

### Phase 3: Validation
- [ ] Test analytics with completed sprint data
- [ ] Test analytics with in-progress sprint
- [ ] Test historical comparison across sprint types
- [ ] Verify performance (< 2 second computation)
- [ ] Test state file size limits
- [ ] Integration test with sample sprint history

### Phase 4: Documentation
- [ ] Document analytics data model
- [ ] Create guide for interpreting analytics
- [ ] Add examples of analytics output
- [ ] Document optimization recommendations

## Acceptance Criteria

- [ ] Agent executions tracked with timing data
- [ ] Phase timings captured automatically
- [ ] Coverage delta calculated per sprint
- [ ] `/sprint-analytics` shows timing breakdown
- [ ] Historical comparison to averages
- [ ] Bottleneck identification and suggestions
- [ ] Works for all sprint types
- [ ] All tests passing
- [ ] Code reviewed and refactored

## Expected Analytics Output

```
$ /sprint-analytics 258

Sprint 258: Unified Platform Users & Access Control
Type: fullstack
Duration: 1.75 hours
Status: completed

PHASE BREAKDOWN:
Planning       [██░░░░░░░░] 14% (0.25h)
Implementation [████████░░] 57% (1.00h)
Validation     [███░░░░░░░] 20% (0.35h)
Documentation  [█░░░░░░░░░]  9% (0.15h)

AGENTS USED:
• Plan              0.25h (planning)
• product-engineer  1.00h (implementation)
• quality-engineer  0.35h (validation)

METRICS:
Coverage:     73.2% → 78.5% (+5.3%)
Tests added:  38
Files touched: 12

COMPARISON TO AVERAGES (fullstack sprints):
Duration:     1.75h vs 2.1h avg (17% faster ✓)
Coverage:     +5.3% vs +4.2% avg (better ✓)

INSIGHTS:
✓ Planning phase efficient (14% vs 20% avg)
⚠ Implementation phase took 57% (consider breaking into smaller tasks)
✓ Good coverage improvement

SUGGESTIONS:
• Consider parallel agent execution for implementation
• Current velocity: on track for sprint completion
```

## Open Questions

- Should we track individual file-level metrics?
- How should we handle sprints that span multiple days?
- Should we alert if a sprint is taking longer than average?

## Notes

**Priority**: Medium (enables continuous improvement)
**Estimated Effort**: 5-7 hours
**Success Metric**: Achieve 15% faster workflow velocity over 10 sprints

Based on Plan agent analysis Priority 5 from vericorr workflow review.

**Sequential Execution**: Must run AFTER Sprint 2 completes (Week 3) - depends on enhanced state tracking.

**Future Enhancements**:
- Predictive duration estimates
- Agent efficiency benchmarking
- Cross-project analytics
- Automated optimization suggestions
