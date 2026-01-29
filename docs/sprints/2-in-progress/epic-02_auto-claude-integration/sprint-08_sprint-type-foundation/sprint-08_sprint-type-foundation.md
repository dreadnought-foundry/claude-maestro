---
sprint: 8
title: "Sprint Type Foundation"
type: backend
epic: 2
status: planning
created: 2026-01-29T14:33:54Z
started: null
completed: null
hours: null
workflow_version: "3.1.0"
---

# Sprint 8: Sprint Type Foundation

## Overview

| Field | Value |
|-------|-------|
| Sprint | 8 |
| Title | Sprint Type Foundation |
| Type | backend |
| Epic | 2 |
| Status | Planning |
| Created | 2026-01-29 |
| Started | - |
| Completed | - |

## Goal

Add sprint type awareness to Auto-Claude specs, enabling type-specific coverage thresholds.

## Background

Auto-Claude currently applies uniform quality standards regardless of work type. A research spike shouldn't require 85% coverage like a production backend service. By adding sprint types (fullstack, backend, frontend, research, spike, infrastructure), we enable appropriate quality gates for different kinds of work.

This is the foundation sprint for the Maestro integration - all subsequent sprints depend on this type system.

## Requirements

### Functional Requirements

- [ ] Extend `spec_contract.json` with `type` field accepting 6 values
- [ ] Add `coverage_override` field with threshold and justification
- [ ] Create coverage threshold lookup by sprint type
- [ ] Update spec validation to recognize and validate type field
- [ ] Add CLI flag `--type` for spec creation

### Non-Functional Requirements

- [ ] Backwards compatible - specs without type default to "fullstack"
- [ ] Clear error messages when invalid type specified
- [ ] Type validation at spec parse time, not runtime

## Dependencies

- **Sprints**: None (foundation sprint)
- **External**: Fork of Auto-Claude repository

## Scope

### In Scope

- spec_contract.json schema extension
- Coverage threshold constants
- Spec validation for type field
- CLI integration for --type flag
- Unit tests for all 6 type thresholds

### Out of Scope

- Quality gate enforcement (Sprint 9)
- State synchronization (Sprint 10)
- Postmortem generation (Sprint 11)

## Technical Approach

1. Fork Auto-Claude repository
2. Extend spec_contract.json with type enum and coverage_override object
3. Create `apps/backend/spec/types.py` with threshold constants
4. Modify `apps/backend/spec/validate_spec.py` to validate type
5. Update CLI in `apps/backend/cli/` to accept --type flag

## Tasks

### Phase 1: Planning
- [ ] Fork Auto-Claude repository
- [ ] Set up development environment
- [ ] Review existing spec_contract.json structure
- [ ] Design type schema extension

### Phase 2: Implementation
- [ ] Write tests for type validation
- [ ] Write tests for coverage threshold lookup
- [ ] Extend spec_contract.json with type field
- [ ] Create types.py with COVERAGE_THRESHOLDS constant
- [ ] Update validate_spec.py for type validation
- [ ] Add --type CLI flag

### Phase 3: Validation
- [ ] Run existing Auto-Claude test suite
- [ ] Verify backwards compatibility with typeless specs
- [ ] Test all 6 sprint types

### Phase 4: Documentation
- [ ] Document type field in spec_contract.json
- [ ] Add examples for each sprint type
- [ ] Update CLI help text

## Acceptance Criteria

- [ ] Specs accept `type` field with values: fullstack, backend, frontend, research, spike, infrastructure
- [ ] Coverage thresholds: fullstack=75%, backend=85%, frontend=70%, research=30%, spike=0%, infrastructure=60%
- [ ] Specs without type default to "fullstack" (75%)
- [ ] `coverage_override` allows custom threshold with required justification
- [ ] CLI `--type` flag works for spec creation
- [ ] All tests passing with 85% coverage (backend sprint)
- [ ] Code reviewed

## Notes

Created: 2026-01-29
Target Files:
- `apps/backend/spec_contract.json`
- `apps/backend/spec/types.py` (new)
- `apps/backend/spec/validate_spec.py`
- `apps/backend/cli/`
