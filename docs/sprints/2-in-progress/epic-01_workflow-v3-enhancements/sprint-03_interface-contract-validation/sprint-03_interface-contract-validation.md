# Sprint 3: Interface Contract Validation

## Overview

| Field | Value |
|-------|-------|
| Sprint | 3 |
| Title | Interface Contract Validation |
| Epic | 01 - Workflow v3.0 Enhancements |
| Status | Planning |
| Created | 2025-12-30 |
| Started | - |
| Completed | - |

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

## Notes

**Priority**: High (eliminates major source of bugs)
**Estimated Effort**: 6-8 hours
**Success Metric**: Reduce backend/frontend integration bugs from 3-4 per epic to <1

Based on Plan agent analysis Priority 3 from vericorr workflow review.

**Parallel Execution**: Can run simultaneously with Sprint 4 in separate terminal (Week 2).
