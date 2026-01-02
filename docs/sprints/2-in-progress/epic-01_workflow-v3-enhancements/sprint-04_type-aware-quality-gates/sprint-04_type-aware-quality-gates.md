# Sprint 4: Type-Aware Quality Gates

## Overview

| Field | Value |
|-------|-------|
| Sprint | 4 |
| Title | Type-Aware Quality Gates |
| Epic | 01 - Workflow v3.0 Enhancements |
| Status | Planning |
| Created | 2025-12-30 |
| Started | - |
| Completed | - |

## Goal

Customize quality requirements based on sprint type to reduce false gate failures from 20% to 5% and make research/spike work feasible within the workflow.

## Background

Current pain point: The 75% coverage gate is one-size-fits-all. Research/spike sprints shouldn't require 75% coverage, integration-heavy sprints may need higher thresholds, and there's no differentiation between unit/integration coverage requirements.

For example, a research sprint exploring a proof-of-concept should focus on documentation and learnings, not coverage. But currently, it would fail the quality gate. This creates friction and discourages experimental work.

## Requirements

### Functional Requirements

- [ ] Add `type` field to sprint frontmatter (fullstack, backend, frontend, research, spike, infrastructure)
- [ ] Add optional `coverage_threshold` override in sprint frontmatter
- [ ] Create dynamic quality gate configuration based on sprint type
- [ ] Implement type-specific requirements (coverage, integration tests, e2e tests, documentation)
- [ ] Update pre-flight checklist to adapt based on sprint type
- [ ] Research sprints require 30% coverage + documentation
- [ ] Backend sprints require 85% coverage + integration tests
- [ ] Frontend sprints require 70% coverage + visual regression
- [ ] Spike sprints require 0% coverage + documentation
- [ ] Infrastructure sprints require 60% coverage + smoke tests

### Non-Functional Requirements

- [ ] Sprint type must be specified in frontmatter (validation error if missing)
- [ ] Type-specific gates must be clearly documented
- [ ] Overrides must require justification comment
- [ ] Validation must happen before sprint can advance from planning

## Dependencies

- **Sprints**: None
- **External**: None
- **Parallelization**: ✅ Can run in parallel with Sprint 3 (Interface Contract Validation) - different workflow phases, no conflicts

## Scope

### In Scope

- Sprint type classification system
- Type-aware quality gate configuration
- Dynamic pre-flight checklist adaptation
- Coverage threshold customization
- Documentation requirements by type
- Integration into sprint validation

### Out of Scope

- Automatic type detection (manual classification required)
- Historical sprint type migration (apply to new sprints only)
- Per-file coverage requirements (project-level only)
- Custom quality gate plugins (future enhancement)

## Technical Approach

1. **Sprint Frontmatter Enhancement**:
   ```yaml
   ---
   sprint: 260
   type: fullstack  # Options: fullstack, backend, frontend, research, spike, infrastructure
   coverage_threshold: 75  # Optional override
   ---
   ```

2. **Quality Gate Configuration**:
   ```python
   # .claude/hooks/validate_step.py - enhanced
   QUALITY_GATES = {
     "fullstack": {
       "coverage": 75,
       "integration_tests": True,
       "e2e_tests": False
     },
     "backend": {
       "coverage": 85,
       "integration_tests": True
     },
     "frontend": {
       "coverage": 70,
       "visual_regression": True
     },
     "research": {
       "coverage": 30,
       "documentation": True  # Mandatory
     },
     "spike": {
       "coverage": 0,
       "documentation": True  # Mandatory
     },
     "infrastructure": {
       "coverage": 60,
       "smoke_tests": True
     }
   }
   ```

3. **Pre-Flight Checklist Adaptation**:
   - Research sprints skip coverage gate
   - Frontend sprints add visual regression check
   - Backend sprints require integration tests
   - Spike sprints require learnings documentation

4. **Validation**:
   - Check sprint type is valid enum
   - If override specified, require justification comment
   - Validate before advancing from planning phase

Files to create/modify:
- `.claude/hooks/validate_step.py` (add type-aware gates)
- `.claude/sprint-state.schema.json` (add sprint_type field)
- `CLAUDE.md` (document sprint types and gates)
- `docs/patterns/sprint-type-classification.md` (guidance on choosing types)

## Tasks

### Phase 1: Planning
- [ ] Review current quality gate implementation
- [ ] Design sprint type classification schema
- [ ] Map quality requirements to each sprint type
- [ ] Design override mechanism with justification

### Phase 2: Implementation
- [ ] Update sprint state schema with `sprint_type` field
- [ ] Implement type-aware quality gates in `validate_step.py`
- [ ] Add sprint type validation
- [ ] Implement dynamic pre-flight checklist
- [ ] Add coverage threshold override logic
- [ ] Update CLAUDE.md with sprint type documentation
- [ ] Create sprint type classification guide

### Phase 3: Validation
- [ ] Test each sprint type validates correctly
- [ ] Test coverage thresholds by type
- [ ] Test override mechanism with justification
- [ ] Test validation catches missing sprint type
- [ ] Test pre-flight checklist adaptation
- [ ] Integration test with sample sprints of each type

### Phase 4: Documentation
- [ ] Document all sprint types and their requirements
- [ ] Create decision tree for choosing sprint type
- [ ] Add examples of each sprint type
- [ ] Update workflow docs with type-aware gates

## Acceptance Criteria

- [ ] Sprint type can be specified in frontmatter
- [ ] Quality gates adapt based on sprint type
- [ ] Research sprints pass with 30% coverage + docs
- [ ] Spike sprints pass with 0% coverage + docs
- [ ] Backend sprints require 85% coverage
- [ ] Override mechanism works with justification
- [ ] Pre-flight checklist adapts to sprint type
- [ ] All tests passing
- [ ] Code reviewed and refactored

## Sprint Type Reference

| Type | Coverage | Special Requirements |
|------|----------|---------------------|
| fullstack | 75% | Integration tests recommended |
| backend | 85% | Integration tests required |
| frontend | 70% | Visual regression tests |
| research | 30% | Documentation mandatory |
| spike | 0% | Documentation mandatory |
| infrastructure | 60% | Smoke tests required |

## Open Questions

- Should we allow custom sprint types or restrict to enum?
- What happens if sprint type changes mid-sprint?
- Should override require approval or just justification?

## Notes

**Priority**: Medium-High (reduces friction, enables experimental work)
**Estimated Effort**: 3-4 hours
**Success Metric**: Reduce false quality gate failures from 20% to 5%

Based on Plan agent analysis Priority 4 from vericorr workflow review.

**Parallel Execution**: Can run simultaneously with Sprint 3 in separate terminal (Week 2).

**Example Usage**:
```yaml
---
sprint: 265
type: research
coverage_threshold: 25  # Override to 25% with justification below
# Justification: Exploring ML model architecture, code is experimental
---
```
