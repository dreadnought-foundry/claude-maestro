# Technical Proposal: Maestro Integration with Auto-Claude

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Draft

---

## Executive Summary

This proposal outlines integrating Maestro's workflow enforcement capabilities into Auto-Claude's autonomous multi-agent framework. The integration adds structured quality gates, sprint-type-aware coverage thresholds, and workflow state tracking to Auto-Claude's powerful parallel execution engine.

**Key Value**: Auto-Claude excels at *execution* (parallel agents, autonomous builds). Maestro excels at *process enforcement* (quality gates, step progression, postmortems). Together they create a system that builds fast AND builds right.

---

## Problem Statement

### Current Auto-Claude Gaps

1. **No coverage variance by work type** - A research spike shouldn't require the same coverage as a backend service
2. **No enforced workflow progression** - Agents can skip validation steps
3. **No structured postmortems** - Learnings aren't captured systematically
4. **No sprint/epic hierarchy** - Work organization relies entirely on external tools (Linear)

### What Maestro Adds

| Capability | Impact |
|------------|--------|
| Sprint types with coverage gates | Reduces false failures on experimental work |
| 6-phase workflow with 14 steps | Ensures consistent quality across all work |
| Pre-flight checklist (9 items) | Catches issues before merge |
| Postmortem generation | Captures learnings for continuous improvement |
| Epic/sprint hierarchy | Self-contained work organization |

---

## Integration Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        AUTO-CLAUDE                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Agent 1   │  │   Agent 2   │  │   Agent N   │              │
│  │  (worktree) │  │  (worktree) │  │  (worktree) │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    QA PIPELINE                             │  │
│  │  ┌─────────┐  ┌─────────────────┐  ┌──────────────────┐   │  │
│  │  │ Existing│  │ MAESTRO QUALITY │  │ Existing         │   │  │
│  │  │ Checks  │→ │ GATE ADAPTER    │→ │ Merge Logic      │   │  │
│  │  └─────────┘  └────────┬────────┘  └──────────────────┘   │  │
│  │                        │                                   │  │
│  └────────────────────────┼───────────────────────────────────┘  │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                     MAESTRO CORE                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐  │
│  │ Sprint Type    │  │ Workflow State │  │ Postmortem         │  │
│  │ Registry       │  │ Manager        │  │ Generator          │  │
│  │                │  │                │  │                    │  │
│  │ - fullstack    │  │ - Phase track  │  │ - Metrics collect  │  │
│  │ - backend      │  │ - Step enforce │  │ - Learning capture │  │
│  │ - frontend     │  │ - Checklist    │  │ - Pattern extract  │  │
│  │ - research     │  │                │  │                    │  │
│  │ - spike        │  │                │  │                    │  │
│  │ - infra        │  │                │  │                    │  │
│  └────────────────┘  └────────────────┘  └────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. Maestro Quality Gate Adapter

A new module in Auto-Claude's QA pipeline that:
- Reads sprint type from spec metadata
- Applies type-specific coverage thresholds
- Runs Maestro's 9-item pre-flight checklist
- Blocks merge if gates fail

```python
# apps/backend/qa/maestro_adapter.py

class MaestroQualityGate:
    """Adapter between Auto-Claude QA and Maestro quality gates."""

    COVERAGE_THRESHOLDS = {
        "fullstack": 75,
        "backend": 85,
        "frontend": 70,
        "research": 30,
        "spike": 0,
        "infrastructure": 60,
    }

    def validate(self, spec: Spec, coverage: float) -> ValidationResult:
        sprint_type = spec.metadata.get("type", "fullstack")
        threshold = self.COVERAGE_THRESHOLDS.get(sprint_type, 75)

        if coverage < threshold:
            return ValidationResult(
                passed=False,
                reason=f"Coverage {coverage}% below {sprint_type} threshold {threshold}%"
            )

        return self.run_preflight_checklist(spec)

    def run_preflight_checklist(self, spec: Spec) -> ValidationResult:
        """Run Maestro's 9-item pre-flight checklist."""
        checklist = [
            self.check_tests_pass,
            self.check_coverage_met,
            self.check_no_lint_errors,
            self.check_no_type_errors,
            self.check_migrations_valid,
            self.check_docs_updated,
            self.check_no_debug_code,
            self.check_no_secrets,
            self.check_changelog_updated,
        ]

        failures = []
        for check in checklist:
            result = check(spec)
            if not result.passed:
                failures.append(result.reason)

        return ValidationResult(
            passed=len(failures) == 0,
            failures=failures
        )
```

#### 2. Sprint Type Detection

Auto-Claude specs gain a `type` field that maps to Maestro sprint types:

```json
// spec_contract.json (extended)
{
  "spec": {
    "title": "string",
    "description": "string",
    "type": {
      "enum": ["fullstack", "backend", "frontend", "research", "spike", "infrastructure"],
      "default": "fullstack"
    },
    "coverage_override": {
      "threshold": "number",
      "justification": "string"
    }
  }
}
```

#### 3. Workflow State Bridge

Syncs Auto-Claude's task state with Maestro's workflow phases:

```python
# apps/backend/integrations/maestro_state.py

class MaestroStateBridge:
    """Bridges Auto-Claude task state with Maestro workflow phases."""

    PHASE_MAPPING = {
        # Auto-Claude stage → Maestro phase
        "planning": "1.1",      # Read sprint file
        "discovery": "1.2",     # Architecture design
        "implementation": "2.2", # Implementation
        "testing": "2.3",       # Run tests
        "validation": "3.1",    # Verify migrations
        "review": "3.2",        # Quality review
        "merge": "5.1",         # Commit
    }

    def sync_state(self, task_id: str, auto_claude_stage: str):
        """Update Maestro state file when Auto-Claude progresses."""
        maestro_phase = self.PHASE_MAPPING.get(auto_claude_stage)
        if maestro_phase:
            state_file = self.get_state_file(task_id)
            state_file.update_phase(maestro_phase)
            state_file.record_timestamp()

    def can_proceed(self, task_id: str, target_stage: str) -> bool:
        """Check if Maestro workflow allows proceeding to target stage."""
        state = self.get_state_file(task_id)
        return state.current_phase_complete()
```

#### 4. Postmortem Generator

Generates Maestro-style postmortems after Auto-Claude completes a spec:

```python
# apps/backend/qa/postmortem.py

class PostmortemGenerator:
    """Generates Maestro-format postmortems from Auto-Claude execution data."""

    def generate(self, spec: Spec, execution_data: ExecutionData) -> Postmortem:
        return Postmortem(
            summary=self.build_summary(execution_data),
            agent_work=self.extract_agent_contributions(execution_data),
            what_went_well=self.analyze_successes(execution_data),
            what_could_improve=self.analyze_issues(execution_data),
            patterns_discovered=self.extract_patterns(execution_data),
            learnings=self.generate_learnings(execution_data),
            action_items=self.suggest_actions(execution_data),
        )

    def build_summary(self, data: ExecutionData) -> dict:
        return {
            "started": data.start_time,
            "completed": data.end_time,
            "duration_hours": data.duration_hours,
            "tests_added": data.test_count,
            "coverage_delta": data.coverage_after - data.coverage_before,
            "files_changed": len(data.modified_files),
            "agents_used": len(data.agent_sessions),
        }
```

---

## Implementation Approach

### Phase 1: Foundation (Week 1-2)

**Goal**: Add sprint type awareness to Auto-Claude specs

| Task | Description | Files |
|------|-------------|-------|
| 1.1 | Extend spec_contract.json with type field | `apps/backend/spec_contract.json` |
| 1.2 | Add coverage threshold lookup | `apps/backend/qa/coverage.py` |
| 1.3 | Update spec validation for type | `apps/backend/spec/validate_spec.py` |
| 1.4 | Add CLI flag for sprint type | `apps/backend/cli/` |

**Acceptance Criteria**:
- [ ] Specs accept `type` field with 6 valid values
- [ ] Coverage validation uses type-specific thresholds
- [ ] Default to `fullstack` (75%) when type not specified
- [ ] Unit tests for all threshold values

### Phase 2: Quality Gates (Week 2-3)

**Goal**: Integrate Maestro's pre-flight checklist into QA pipeline

| Task | Description | Files |
|------|-------------|-------|
| 2.1 | Create MaestroQualityGate adapter | `apps/backend/qa/maestro_adapter.py` |
| 2.2 | Implement 9-item checklist | `apps/backend/qa/preflight_checklist.py` |
| 2.3 | Hook into existing QA pipeline | `apps/backend/qa/pipeline.py` |
| 2.4 | Add checklist bypass for spike type | `apps/backend/qa/maestro_adapter.py` |

**Acceptance Criteria**:
- [ ] QA pipeline runs all 9 checklist items
- [ ] Failures block merge with clear error messages
- [ ] Spike type skips coverage check
- [ ] Research type requires docs check

### Phase 3: State Synchronization (Week 3-4)

**Goal**: Bridge Auto-Claude task state with Maestro workflow phases

| Task | Description | Files |
|------|-------------|-------|
| 3.1 | Create state bridge module | `apps/backend/integrations/maestro_state.py` |
| 3.2 | Map Auto-Claude stages to Maestro phases | `apps/backend/integrations/phase_mapping.py` |
| 3.3 | Add state file read/write | `apps/backend/integrations/state_file.py` |
| 3.4 | Emit state change events | `apps/backend/core/events.py` |

**Acceptance Criteria**:
- [ ] State file created when spec starts
- [ ] Phase updates on each stage transition
- [ ] Timestamps recorded for audit trail
- [ ] State persists across agent restarts

### Phase 4: Postmortem Generation (Week 4-5)

**Goal**: Auto-generate postmortems after spec completion

| Task | Description | Files |
|------|-------------|-------|
| 4.1 | Create postmortem generator | `apps/backend/qa/postmortem.py` |
| 4.2 | Collect agent execution metrics | `apps/backend/agents/metrics.py` |
| 4.3 | Pattern extraction from changes | `apps/backend/analysis/patterns.py` |
| 4.4 | Postmortem file output | `apps/backend/qa/postmortem_writer.py` |

**Acceptance Criteria**:
- [ ] Postmortem generated on spec completion
- [ ] Includes all Maestro postmortem sections
- [ ] Agent contributions tracked per session
- [ ] Output in Markdown format

### Phase 5: Epic/Sprint Hierarchy (Week 5-6)

**Goal**: Add optional Maestro-style work organization

| Task | Description | Files |
|------|-------------|-------|
| 5.1 | Add epic grouping to specs | `apps/backend/spec/epic.py` |
| 5.2 | Registry for completed work | `apps/backend/spec/registry.py` |
| 5.3 | Epic completion detection | `apps/backend/spec/epic_lifecycle.py` |
| 5.4 | CLI commands for epic management | `apps/backend/cli/epic_commands.py` |

**Acceptance Criteria**:
- [ ] Specs can be grouped into epics
- [ ] Registry tracks all completed specs
- [ ] Epic auto-completes when all specs done
- [ ] CLI supports epic create/list/complete

---

## Technical Details

### File Locations

```
apps/backend/
├── integrations/
│   └── maestro/
│       ├── __init__.py
│       ├── adapter.py          # Main integration point
│       ├── state_bridge.py     # Workflow state sync
│       ├── phase_mapping.py    # Stage → phase mapping
│       └── config.py           # Maestro settings
├── qa/
│   ├── maestro_gate.py         # Quality gate adapter
│   ├── preflight_checklist.py  # 9-item checklist
│   └── postmortem.py           # Postmortem generator
└── spec/
    └── types.py                # Sprint type definitions
```

### Configuration

```yaml
# .auto-claude/maestro.yaml
maestro:
  enabled: true

  quality_gates:
    enforce_coverage: true
    enforce_checklist: true
    block_on_failure: true

  sprint_types:
    fullstack:
      coverage: 75
      checklist: full
    backend:
      coverage: 85
      checklist: full
      require_integration_tests: true
    frontend:
      coverage: 70
      checklist: full
    research:
      coverage: 30
      checklist: docs_only
      require_documentation: true
    spike:
      coverage: 0
      checklist: minimal
    infrastructure:
      coverage: 60
      checklist: full
      require_smoke_tests: true

  postmortem:
    auto_generate: true
    include_agent_metrics: true
    extract_patterns: true

  workflow:
    sync_state: true
    enforce_phases: false  # Start with tracking only
```

### API Surface

```python
# Public API for integration

from maestro_integration import MaestroGate, PostmortemGenerator

# In QA pipeline
gate = MaestroGate(config)
result = gate.validate(spec, coverage_report)
if not result.passed:
    raise QualityGateFailure(result.failures)

# After completion
postmortem = PostmortemGenerator().generate(spec, execution_data)
postmortem.write_to_file(output_path)
```

---

## Migration Strategy

### For Existing Auto-Claude Users

1. **Week 1**: Release with Maestro disabled by default
2. **Week 2**: Enable quality gates in "warn only" mode
3. **Week 3**: Enable quality gates in "block" mode for new specs
4. **Week 4**: Full enforcement for all specs

### Backwards Compatibility

- Specs without `type` field default to `fullstack`
- Existing QA checks run before Maestro gates
- All Maestro features can be disabled via config
- No changes to existing CLI commands

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Specs passing QA on first attempt | Unknown | 85% |
| Coverage variance by work type | None | 6 types |
| Postmortems generated | 0% | 100% |
| Average rework cycles | Unknown | -30% |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Slows down autonomous execution | High | Make gates async, cache results |
| Users reject additional requirements | Medium | Gradual rollout, easy disable |
| State sync conflicts | Medium | Maestro state is secondary/advisory |
| Postmortem data incomplete | Low | Best-effort collection, degrade gracefully |

---

## Open Questions

1. **Linear integration**: Should Maestro state sync to Linear, or replace it?
2. **Multi-agent conflicts**: How to handle when agents disagree on phase completion?
3. **Custom sprint types**: Should users be able to define their own types?
4. **Rollback behavior**: What happens to Maestro state if Auto-Claude rolls back?

---

## Next Steps

1. [ ] Review proposal with Auto-Claude maintainers
2. [ ] Create fork for proof-of-concept
3. [ ] Implement Phase 1 (sprint types) as MVP
4. [ ] Gather feedback on quality gate integration points
5. [ ] Refine based on real-world testing

---

## Appendix A: Maestro Sprint Types Reference

| Type | Coverage | Checklist | Special Requirements |
|------|----------|-----------|---------------------|
| fullstack | 75% | Full (9 items) | Integration tests recommended |
| backend | 85% | Full | Integration tests required |
| frontend | 70% | Full | Visual regression tests |
| research | 30% | Docs only (3 items) | Documentation mandatory |
| spike | 0% | Minimal (1 item) | Documentation mandatory |
| infrastructure | 60% | Full | Smoke tests required |

## Appendix B: Maestro Pre-Flight Checklist

1. All tests pass
2. Coverage meets threshold for sprint type
3. No lint errors
4. No type errors (if typed language)
5. Database migrations valid and reversible
6. Documentation updated (if applicable)
7. No debug/console statements in production code
8. No secrets or credentials in code
9. Changelog updated (if applicable)
