---
sprint: 7
title: Modular Automation Architecture
status: planning
workflow_version: "3.1"
epic: 1
created: 2026-01-01
started: null
completed: null
hours: null
---

# Sprint 7: Modular Automation Architecture

## Overview

| Field | Value |
|-------|-------|
| Sprint | 7 |
| Title | Modular Automation Architecture |
| Epic | 01 - Workflow v3.0 Enhancements |
| Status | Planning |
| Created | 2026-01-01 |
| Started | - |
| Completed | - |

## Goal

Refactor `scripts/sprint_lifecycle.py` (3,325 lines) into a modular package architecture with focused modules (<600 lines each), built in parallel and atomically cut over with zero downtime.

## Background

Sprint 2 delivered comprehensive automation covering 19 CLI commands for sprint/epic lifecycle management. The implementation consolidated all functionality in a single 3,325-line file (`sprint_lifecycle.py`). While this works, it creates maintainability challenges:

- **Large File Size**: 3,325 lines is difficult to navigate and understand
- **Mixed Concerns**: Registry, file operations, git operations, CLI parsing all in one file
- **Limited Reusability**: Hard to import specific functionality without pulling in everything
- **Testing Complexity**: Mocking becomes harder as file grows
- **Future Extensibility**: Adding new commands or features increases complexity

This sprint refactors into a modular package architecture while maintaining 100% backward compatibility and 84% test coverage.

## Team Strategy

### Sprint Type
- **Type**: refactoring
- **Parallelism**: No (single-agent, phased implementation)

### Agent Assignments

| Agent | Role | Files Owned | Skills |
|-------|------|-------------|--------|
| product-engineer | Refactoring engineer | scripts/sprint_automation/ (create)<br>scripts/sprint_lifecycle.py (modify to facade)<br>tests/test_*.py (reorganize) | None |

### File Ownership

```
scripts/sprint_automation/            → product-engineer (create all)
scripts/sprint_lifecycle.py           → product-engineer (convert to facade)
scripts/sprint_lifecycle_v2.py        → product-engineer (temporary parallel build)
tests/test_*.py                       → product-engineer (reorganize into modules)
```

### Integration Strategy

Parallel build with atomic cutover:
1. Build new modular package alongside existing file
2. Implement in `sprint_lifecycle_v2.py` calling new package
3. Run comparison tests (v1 vs v2 outputs)
4. Atomic swap when v2 validated
5. Cleanup temporary files

### TDD Approach

**Level**: Flexible (refactoring with existing test coverage)

**Justification**: We have 84% test coverage (144 tests) on existing code. Refactoring should maintain this coverage while reorganizing tests to match new module structure.

**Testing Strategy**:
- Maintain 84% coverage minimum (1,328/1,585 statements)
- Reorganize tests to match module structure
- Add comparison tests (v1 vs v2 output validation)
- Integration tests for all 19 CLI commands
- Coverage target: 85%+ (improve during refactoring)

### User Clarifications

Based on discussion:
- ✅ Build in parallel (sprint_lifecycle_v2.py + sprint_automation/)
- ✅ Atomic cutover after validation
- ✅ Maintain backward compatibility (existing imports still work)
- ✅ Use existing test coverage for validation

## Requirements

### Functional Requirements

- [ ] Create `scripts/sprint_automation/` package with 14 modules
- [ ] Maintain 100% backward compatibility (all existing imports work)
- [ ] All 19 CLI commands produce identical output (v1 vs v2)
- [ ] All 144 existing tests pass with new architecture
- [ ] Module size limit: <600 lines per file

### Non-Functional Requirements

- [ ] Test coverage: ≥84% (maintain current level)
- [ ] No performance regression (CLI commands same speed)
- [ ] Zero downtime cutover (atomic file swap)
- [ ] Documentation updated for new architecture

## Dependencies

- **Sprints**: Sprint 2 (Automated Lifecycle Management) - DONE
- **External**: None
- **Parallelization**: Must run solo (can't parallel with other Epic 01 sprints)

## Scope

### In Scope

- Refactor into modular package (14 files)
- Reorganize tests to match modules
- Create backward-compatible facade
- Update documentation
- Comparison testing (v1 vs v2)
- Atomic cutover

### Out of Scope

- Changing functionality (pure refactoring)
- Adding new commands
- Performance optimization beyond maintaining current speed
- Changing CLI interface

## Technical Approach

### Module Structure

```
scripts/sprint_automation/
├── __init__.py              # Public API exports
├── exceptions.py            # Custom exceptions
├── utils/
│   ├── file_ops.py          # File operations
│   ├── git_ops.py           # Git operations
│   └── project.py           # Project utilities
├── registry/
│   ├── manager.py           # Registry CRUD
│   └── numbering.py         # Auto-numbering
├── sprint/
│   ├── lifecycle.py         # Sprint lifecycle
│   ├── status.py            # Status queries
│   └── postmortem.py        # Postmortem generation
├── epic/
│   ├── lifecycle.py         # Epic lifecycle
│   └── status.py            # Epic queries
├── project/
│   └── creation.py          # Project creation
└── cli/
    ├── parser.py            # Argument parsing
    └── handlers.py          # Command handlers
```

### Parallel Build Strategy

1. **Phase 1-7**: Build `sprint_automation/` package incrementally
2. **Interim**: Create `sprint_lifecycle_v2.py` facade using new package
3. **Validation**: Compare outputs between v1 and v2
4. **Cutover**: Atomic swap when validated
5. **Cleanup**: Remove v1 backup and v2 temporary

### Backward Compatibility

Existing code using:
```python
from scripts.sprint_lifecycle import start_sprint, complete_sprint
```

Will continue to work via facade pattern in updated `sprint_lifecycle.py`:
```python
from sprint_automation import *
```

## Tasks

### Phase 1: Package Structure (1-2 hours)
- [ ] Create `scripts/sprint_automation/` directory
- [ ] Create all `__init__.py` files
- [ ] Create `exceptions.py` with custom exceptions
- [ ] Verify existing tests still pass

### Phase 2: Extract Utilities (2-3 hours)
- [ ] Create `utils/file_ops.py` with file operation functions
- [ ] Create `utils/git_ops.py` with git functions
- [ ] Create `utils/project.py` with project utilities
- [ ] Update `__init__.py` to re-export utilities
- [ ] Run tests

### Phase 3: Extract Registry (2-3 hours)
- [ ] Create `registry/manager.py` with RegistryManager class
- [ ] Create `registry/numbering.py` with auto-numbering
- [ ] Update imports
- [ ] Run tests

### Phase 4: Extract Sprint/Epic Lifecycle (3-4 hours)
- [ ] Create `sprint/lifecycle.py` with SprintLifecycle class
- [ ] Create `sprint/status.py` with status queries
- [ ] Create `sprint/postmortem.py` with postmortem generation
- [ ] Create `epic/lifecycle.py` with EpicLifecycle class
- [ ] Create `epic/status.py` with epic queries
- [ ] Update imports
- [ ] Run full test suite

### Phase 5: Extract CLI (1-2 hours)
- [ ] Create `cli/parser.py` with argument parser
- [ ] Create `cli/handlers.py` with command handlers
- [ ] Create `sprint_lifecycle_v2.py` using new CLI
- [ ] Test all 19 commands

### Phase 6: Comparison Testing (1-2 hours)
- [ ] Create comparison test suite
- [ ] Run all 19 commands with both v1 and v2
- [ ] Verify outputs match (diff comparison)
- [ ] Verify state files match
- [ ] Verify registry updates match

### Phase 7: Reorganize Tests (2-3 hours)
- [ ] Split `test_sprint_automation.py` into module-specific tests
- [ ] Create `test_utils_file_ops.py`
- [ ] Create `test_registry_manager.py`
- [ ] Create `test_sprint_lifecycle.py`
- [ ] Create `test_cli.py`
- [ ] Verify 84%+ coverage maintained

### Phase 8: Cutover (30 minutes)
- [ ] Backup v1: `mv sprint_lifecycle.py sprint_lifecycle_v1_backup.py`
- [ ] Promote v2: `mv sprint_lifecycle_v2.py sprint_lifecycle.py`
- [ ] Run full test suite
- [ ] Test all 19 CLI commands
- [ ] Verify existing imports still work

### Phase 9: Documentation (1 hour)
- [ ] Update `docs/AUTOMATION_USAGE.md` with new architecture
- [ ] Add architecture diagram
- [ ] Document module responsibilities
- [ ] Update import examples

## Acceptance Criteria

- [ ] All 144 existing tests passing
- [ ] Test coverage ≥84% (maintain or improve)
- [ ] All 19 CLI commands produce identical output (v1 vs v2)
- [ ] Backward-compatible imports work
- [ ] No module >600 lines
- [ ] Documentation updated
- [ ] Comparison tests validate equivalence
- [ ] Zero test failures after cutover

## Open Questions

None - architecture design complete, implementation plan validated.

## Notes

**Priority**: High (technical debt reduction, enables future Epic 01 work)
**Estimated Effort**: 12-17.5 hours
**Success Metric**: Reduce largest module from 3,325 lines to <600 lines

**Refactoring Benefits**:
- Maintainability: Easier to find and modify code
- Testability: Test modules in isolation
- Reusability: Import only needed components
- Extensibility: Add new commands without growing monolith

**Risk Mitigation**:
- Parallel build (no risk to production)
- Comparison testing (validates equivalence)
- Atomic cutover (instant rollback if needed)
- High test coverage (84% catches regressions)

**Source**: Refactoring plan from conversation after Sprint 2 completion
