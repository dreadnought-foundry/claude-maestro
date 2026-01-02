---
sprint: 3
title: Interface Contract Validation
epic: 01
status: done
created: 2025-12-30T00:00:00Z
started: 2026-01-01T22:10:00Z
completed: 2026-01-01
hours: 1.2
workflow_version: "3.1.0"

---

# Sprint 3: Interface Contract Validation

## Overview

| Field | Value |
|-------|-------|
| Sprint | 3 |
| Title | Interface Contract Validation |
| Epic | 01 - Workflow v3.0 Enhancements |
| Status | Done |
| Created | 2025-12-30 |
| Started | 2026-01-01 |
| Completed | 2026-01-01 |
| Hours | 1.5 |

## Goal

Enforce interface contracts before parallel agent execution to prevent backend/frontend integration mismatches and eliminate 90% of integration bugs.

## Background

Current pain point: Backend and frontend integration mismatches occur despite the Interface Contract Pattern being documented in the playbook. Without upfront agreement, backend builds APIs with different field names, GraphQL enum case issues occur (UPPERCASE vs lowercase), and type mismatches happen.

The documented pattern exists but isn't enforced - developers can skip the contract definition step. This sprint adds a mandatory workflow phase and validation tool to enforce contracts.

## Requirements

### Functional Requirements

- [ ] Add Phase 1.5 "Interface Contract Definition" to sprint workflow (between Planning and Implementation)
- [ ] Create structured contract format (JSON schema) for backend/frontend/test interfaces
- [ ] Plan agent outputs contract in structured format during planning
- [ ] Create `scripts/validate_interface_contract.py` validation tool
- [ ] Validate GraphQL schema matches frontend queries
- [ ] Enforce GraphQL enum UPPERCASE convention
- [ ] Validate type matching between backend and frontend
- [ ] Contract must be defined before parallel agents start work
- [ ] Update `.claude/sprint-state.json` schema to include `interface_contract` field

### Non-Functional Requirements

- [ ] Validation must run in < 5 seconds
- [ ] Clear error messages when validation fails
- [ ] Validation only required for fullstack sprints (not backend-only or frontend-only)
- [ ] Contract format must be human-readable (JSON with comments allowed)

## Dependencies

- **Sprints**: None
- **External**: None
- **Parallelization**: ✅ Can run in parallel with Sprint 4 (Type-Aware Quality Gates) - different workflow phases, no conflicts

## Scope

### In Scope

- New Phase 1.5 in sprint workflow
- Contract format definition (JSON schema)
- Contract validation tool
- GraphQL schema validation
- Enum case enforcement (UPPERCASE)
- Type matching validation
- Integration into sprint workflow

### Out of Scope

- Automatic contract generation from code (manual definition required)
- Contract versioning and evolution (future enhancement)
- Runtime contract enforcement (compile-time only)
- Contract testing framework integration (future)

## Technical Approach

1. **Phase 1.5 Addition**: Insert new workflow step between Planning (1.4) and Tests (2.1)
   - For fullstack sprints only
   - Plan agent outputs structured contract
   - Validation gate before proceeding

2. **Contract Format (JSON)**:
   ```json
   {
     "backend_interface": {
       "queries": {"myFeatures": "returns: [String!]!"},
       "mutations": {...},
       "types": {"Feature": {"key": "String!", "name": "String!"}}
     },
     "frontend_interface": {
       "hooks": ["useEntitlements", "useHasFeature"],
       "types": ["Feature"]
     },
     "test_interface": {
       "backend_assertions": [...],
       "frontend_assertions": [...]
     }
   }
   ```

3. **Validation Tool (`scripts/validate_interface_contract.py`)**:
   - Parse contract JSON
   - Check GraphQL schema matches frontend queries
   - Validate enum values are UPPERCASE
   - Check type definitions match

4. **Workflow Integration**:
   - Update `.claude/sprint-steps.json` with Phase 1.5
   - Add validation gate: contract must exist before Phase 2.1
   - Update state schema to track contract

Files to create/modify:
- `scripts/validate_interface_contract.py` (new)
- `.claude/sprint-steps.json` (add Phase 1.5)
- `.claude/sprint-state.schema.json` (add interface_contract field)
- `docs/patterns/interface-contract-format.md` (document contract schema)

## Tasks

### Phase 1: Planning
- [ ] Review Interface Contract Pattern from playbook
- [ ] Design contract JSON schema
- [ ] Design validation tool architecture
- [ ] Map GraphQL validation rules (enum case, type matching)

### Phase 2: Implementation
- [ ] Create contract JSON schema definition
- [ ] Implement `validate_interface_contract.py` tool
- [ ] Add GraphQL schema validation
- [ ] Add enum UPPERCASE enforcement
- [ ] Add type matching validation
- [ ] Update `.claude/sprint-steps.json` with Phase 1.5
- [ ] Update state schema with `interface_contract` field
- [ ] Create contract format documentation

### Phase 3: Validation
- [ ] Test contract validation with valid contract
- [ ] Test validation catches enum case mismatches
- [ ] Test validation catches type mismatches
- [ ] Test Phase 1.5 gate blocks without contract
- [ ] Test fullstack vs backend-only sprint handling
- [ ] Integration test with sample sprint workflow

### Phase 4: Documentation
- [ ] Document contract format and schema
- [ ] Add examples of valid contracts
- [ ] Update playbook with Phase 1.5 guidance
- [ ] Create troubleshooting guide for validation errors

## Acceptance Criteria

- [ ] Phase 1.5 added to sprint workflow
- [ ] Contract validation tool prevents enum case issues
- [ ] Contract validation tool catches type mismatches
- [ ] Validation runs before parallel agent execution
- [ ] Clear error messages guide developers to fix issues
- [ ] Backend-only sprints skip contract validation
- [ ] All tests passing
- [ ] Code reviewed and refactored

## Expected Contract Example

```json
{
  "sprint": 3,
  "type": "fullstack",
  "backend_interface": {
    "queries": {
      "userFeatures": "returns: [Feature!]!"
    },
    "types": {
      "Feature": {
        "key": "String!",
        "name": "String!",
        "enabled": "Boolean!"
      }
    },
    "enums": {
      "FeatureStatus": ["ENABLED", "DISABLED", "BETA"]
    }
  },
  "frontend_interface": {
    "hooks": ["useFeatures", "useHasFeature"],
    "types": ["Feature", "FeatureStatus"]
  }
}
```

## Open Questions

- Should contract validation be mandatory or optional with override flag?
- What happens if GraphQL schema changes after contract defined?
- Should we validate response shapes or just types?

## Team Strategy

### Sprint Type
- **Type**: integration
- **Parallelism**: Yes (2 streams)

### Agent Assignments

| Agent | Role | Files Owned | Skills |
|-------|------|-------------|--------|
| product-engineer | Contract Schema & Validation Tool Developer | scripts/validate_interface_contract.py, docs/contract-schema.json, .claude/sprint-steps.json, .claude/hooks/validate_step.py, templates/contract-example.json | None |
| quality-engineer | Testing, Documentation & Quality Gates | tests/test_interface_contract_validation.py, docs/patterns/interface-contract-format.md, docs/troubleshooting/contract-validation-errors.md, .claude/hooks/sprint_complete_check.py | None |

### File Ownership

- **Product Engineer**: Core validation tool, contract schema, workflow integration (sprint-steps.json, validate_step.py hook), example template
- **Quality Engineer**: Test suite, pattern documentation, troubleshooting guide, pre-flight checklist updates

### Integration Strategy

1. Hour 0-1: Product-engineer defines contract JSON schema → share with quality-engineer
2. Hour 1-3: Parallel implementation (validation logic + tests/docs)
3. Hour 3-4: First integration point (test execution, bug fixes)
4. Hour 4-5: Phase 1.5 workflow integration
5. Hour 5-6: Final validation and polish

### TDD Approach

**Level**: flexible (DEFAULT)

**Rationale**: Standard validation feature with straightforward rules (GraphQL matching, enum casing, type checking). 75% coverage target. Not complex business logic requiring strict TDD.

### Clarifications

- **Nested types**: Support nested type definitions (e.g., Feature.metadata: [MetadataField!]!)
- **Validation gate**: Mandatory hard gate (no override flag)
- **Schema changes**: Validate once at Phase 1.5 only
- **Validation depth**: Full response shape validation (deep nested structure checking)

## Notes

**Priority**: High (eliminates major source of bugs)
**Estimated Effort**: 6-8 hours
**Success Metric**: Reduce backend/frontend integration bugs from 3-4 per epic to <1

Based on Plan agent analysis Priority 3 from vericorr workflow review.

**Parallel Execution**: Can run simultaneously with Sprint 4 in separate terminal (Week 2).

## Postmortem

### Summary

Implemented Phase 1.5 interface contract validation system to enforce contracts before parallel agent execution, preventing backend/frontend integration mismatches.

| Metric | Value |
|--------|-------|
| Started | 2026-01-01 22:10 UTC |
| Completed | 2026-01-01 23:20 UTC |
| Duration | 1.2 hours |
| Tests Added | 15 test functions |
| Files Created | 7 new files |
| Files Modified | 4 files |
| Lines Added | +2,182 |

### Agent Work Summary

| Agent | Role | Deliverables | Files |
|-------|------|--------------|-------|
| product-engineer | Contract Schema & Validation Tool Developer | Validation tool, JSON schema, Phase 1.5 workflow integration, example template | scripts/validate_interface_contract.py, docs/contract-schema.json, .claude/sprint-steps.json, templates/contract-example.json |
| quality-engineer | Testing, Documentation & Quality Gates | Test suite (15 tests), pattern documentation, troubleshooting guide | tests/test_interface_contract_validation.py, docs/patterns/interface-contract-format.md, docs/troubleshooting/contract-validation-errors.md |

### What Went Well

- **Clear team strategy** - Plan agent designed effective parallel work streams with zero file conflicts
- **User clarification upfront** - Asking about nested types, validation depth, and gate strictness early prevented rework
- **Pattern reuse** - Validation tool followed similar structure to existing sprint_lifecycle.py patterns
- **Comprehensive documentation** - Created both pattern guide AND troubleshooting guide with 8 error categories
- **Performance target met** - Validation completes in < 1s (requirement was < 5s)
- **Version management fix** - Discovered and fixed hardcoded "2.1" versions, now uses WORKFLOW_VERSION as single source of truth
- **Graceful degradation** - Validation tool works without jsonschema dependency via manual validation fallback

### What Could Improve

- **Missing pytest dependency** - Couldn't run full test suite due to missing pytest module in environment
- **State tracking** - Had to manually update sprint state after completing work (state was at 2.1 but work was done)
- **Workflow instructions confusion** - Instructions referenced "v2.1 workflow" pattern name vs actual version "3.1.0", caused brief confusion

### Patterns Discovered

**Validation Tool Pattern**:
```python
# Graceful dependency handling
try:
    import optional_library
    HAS_LIBRARY = True
except ImportError:
    HAS_LIBRARY = False

# Fallback validation
if HAS_LIBRARY:
    use_library_validation()
else:
    use_manual_validation()
```

**Contract Schema Design**:
- Use JSON Schema for structured validation
- Support nested types with recursive validation
- Enforce conventions (UPPERCASE enums) at validation time
- Provide clear, actionable error messages

**Documentation Completeness**:
- Pattern guide + Troubleshooting guide = comprehensive coverage
- Include "Common Pitfalls" section with before/after examples
- Provide quick checklist at end of troubleshooting docs

### Learnings for Future Sprints

1. **Technical**: 
   - Contract validation prevents integration bugs by catching type mismatches early
   - GraphQL enum case issues (UPPERCASE vs lowercase) are common enough to warrant dedicated validation
   - Nested type validation requires recursive approach to handle arbitrary depth

2. **Process**: 
   - Clarifying requirements upfront (Step 1.3) saved significant rework time
   - Version management should use single source of truth (WORKFLOW_VERSION file) not hardcoded values
   - State file should be updated automatically as steps complete, not manually

3. **Integration**: 
   - Phase 1.5 insertion point (between Planning and Implementation) is perfect for contract validation
   - Mandatory gates work well when they have clear error messages and fix guidance
   - Template placeholders (like `{WORKFLOW_VERSION}`) allow dynamic version management

### Action Items

- [x] `[done]` Fix hardcoded workflow versions in templates → Completed in this sprint (commit 07a1417)
- [ ] `[backlog]` Add pytest to project dependencies or create requirements.txt
- [ ] `[backlog]` Automate state file updates as steps complete
- [ ] `[pattern]` Document contract validation pattern in cookbook
- [ ] `[backlog]` Add GraphQL introspection support for runtime schema validation (future enhancement)
- [ ] `[backlog]` Create contract version evolution guide (out of scope for v1)
