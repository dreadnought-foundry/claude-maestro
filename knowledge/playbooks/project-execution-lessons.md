# Recipe: Project Execution Lessons Learned

**Category**: playbook
**Version**: 1.0
**Last Updated**: 2025-12-13
**Sprints**: Retrospective analysis of Sprints 00-109, Epics 01-13

---

## Context

### When to Use This Recipe

- Starting a new AI-assisted development project
- Kicking off a new epic with 5+ sprints
- Retrospective analysis of completed work
- Onboarding new team members to our workflow
- Planning sprint capacity and velocity

### When NOT to Use

- Quick hotfix sprints (use standard sprint template)
- Single-sprint features (overhead exceeds benefit)
- Exploratory research (use research report format)

---

## Executive Summary

Analysis of 109 sprints across 13 epics over 6 weeks of development revealed:

| Metric | Value | Insight |
|--------|-------|---------|
| Total sprints | 109 | High velocity enabled by AI-assisted development |
| Completion rate | 74% | Strong forward momentum |
| Avg sprint duration | 2.9 hours | Small, focused sprints work best |
| Time tracking coverage | 32% | Major gap - affects velocity planning |
| Epic size range | 2-14 sprints | Needs standardization |

**Key Success Factors:**
1. Epic-based organization with dependency tracking
2. Backend-first development order
3. GraphQL as central integration layer
4. Explicit deferred item tracking
5. Test coverage integration in sprints

**Key Failure Patterns:**
1. Missing time tracking (67% of sprints)
2. Late discovery of scope (GraphQL gaps found at Sprint 100)
3. Inconsistent status field values
4. Scattered dependency documentation

---

## Ingredients

### Required Before Starting a New Project

- [ ] Sprint workflow system configured (`.claude/sprint-steps.json`)
- [ ] Slash commands installed (`/sprint-start`, `/sprint-next`, `/sprint-complete`)
- [ ] Epic template with dependency diagram section
- [ ] Sprint template with mandatory time tracking field
- [ ] DEFERRED.md file created in sprints folder
- [ ] Velocity baseline from prior project (or estimate)

### Recommended Tools

- [ ] Pre-commit hooks for sprint validation
- [ ] State file system for concurrent sprints
- [ ] Quality-engineer agent for test coverage
- [ ] Plan agent for architecture design

---

## Learnings by Category

### Epic Organization

#### Sprint 100 Discovery
**Discovery:** Large epics (7+ sprints) benefit from an audit/discovery sprint first.

Epic 12 (Page Integration Audit) started with Sprint 100 which discovered 69 pages needed integration and 19 GraphQL operations were missing. This prevented weeks of blocked work.

**Pattern:** For any epic 7+ sprints:
```
Sprint 0: Discovery/Audit
├── Inventory all affected components
├── Identify dependencies and gaps
├── Size remaining sprints accurately
└── Create dependency diagram
```

#### Epic Size Classes
**Discovery:** Epic sizes varied wildly (2-14 sprints) making planning unpredictable.

**Recommended Classification:**
| Size | Sprints | Characteristics | Example |
|------|---------|-----------------|---------|
| S | 2-3 | Single feature, no dependencies | Epic 09: Missing Pages |
| M | 4-6 | Feature set, 1-2 dependencies | Epic 08: Map Visualization |
| L | 7-10 | Cross-cutting, multiple deps | Epic 02: Compliance |
| XL | 11+ | Platform-level, requires approval | Epic 04: External Data |

### Time Tracking

#### Sprint 87-90 Analysis
**Discovery:** Only 32% of sprints had recorded hours, preventing velocity calculation.

**Impact Examples:**
- Sprint 87: 2 hours (tracked) - Dashboard integration
- Sprint 89: 3 hours (tracked) - Assets pages
- Sprint 45: Unknown (untracked) - AWS Infrastructure (likely 8-10 hours)

**Pattern:** Make time tracking mandatory:
```yaml
# Sprint frontmatter - required fields
hours: null  # Pre-execution: null allowed
             # Post-execution: number required
started: null
completed: null
```

### Backend-Frontend Coordination

#### Epic 12 Dependency Chain
**Discovery:** Frontend sprints blocked when backend incomplete.

```
Sprint 100 (Audit)
    └── Sprint 101 (GraphQL Fixes)
            └── Sprints 87-93 (Frontend Integration)
```

**Pattern:** Always sequence:
1. Backend/API changes (Sprint N)
2. Wait for deployment/verification
3. Frontend integration (Sprint N+1)

**Anti-Pattern:** Starting frontend before backend is stable caused 3 sprint delays in Epic 03.

### GraphQL as Integration Layer

#### Sprint 20 → Sprint 43 Pivot
**Discovery:** REST API layer (Sprint 20) was superseded by GraphQL (Sprint 43).

**Current Hybrid Model (Sprint 107):**
```
REST API (Specialized):
├── Authentication (token flows)
├── File Uploads (multipart)
├── GIS Import (long-running jobs)
├── Mobile Sync (offline-first)
└── Spatial Queries (PostGIS-specific)

GraphQL (Primary):
├── Dashboard queries
├── Asset CRUD
├── Alerts & Events
├── Work Orders
├── Analytics
├── Compliance
└── User/Team management
```

**Lesson:** GraphQL excels at relational data queries; REST better for stateful operations.

### Deferred Work Management

#### Sprint 87-89 Pattern
**Discovery:** Deferred items scattered across sprint files get lost.

**Examples Found:**
- Sprint 87: "Date range filtering deferred to Sprint 108"
- Sprint 89: "Pipeline detail page deferred to Sprint 90"
- Sprint 109: "Customer rename deferred - incomplete"

**Pattern:** Centralize deferred work:
```markdown
# docs/sprints/DEFERRED.md

## Active Deferred Items

| Original Sprint | Item | Target Sprint | Status |
|-----------------|------|---------------|--------|
| 87 | Date range filtering | 108 | Pending |
| 87 | ComplianceCalendar real data | 103 | Pending |
| 89 | Pipeline detail page | 90 | ✅ Done |
```

### Test Coverage

#### Sprint 99 Model
**Discovery:** Dedicated test sprints (Sprint 99: Comprehensive UI Tests) work better than per-sprint testing for large epics.

**Testing Strategy by Epic Size:**
| Epic Size | Strategy | Example |
|-----------|----------|---------|
| S (2-3) | Test-per-sprint | Epic 09 |
| M (4-6) | Test-per-phase | Epic 08 |
| L (7-10) | Dedicated test sprint at 70% | Epic 12 (Sprint 99) |
| XL (11+) | Multiple test checkpoints | Epic 04 |

**Coverage Threshold:** 85% minimum (established Sprint 42+)

### Demo Data

#### Sprint 44, 64 Pattern
**Discovery:** Demo data generation blocks UI testing and documentation.

**Lesson:** Schedule demo data sprint early:
```
Epic Start
├── Sprint 1: Core backend
├── Sprint 2: Demo data generation ← Early!
├── Sprint 3-N: Feature development
└── Sprint N+1: Documentation (needs demo data)
```

---

## Anti-Patterns

### 1. **Late Scope Discovery**
**Problem:** Discovering missing API operations at 70% completion
**Example:** Epic 12 - Sprint 100 found 19 missing GraphQL operations
**Instead:** Run discovery/audit sprint FIRST for epics 7+ sprints

### 2. **Inconsistent Status Values**
**Problem:** Using "done", "complete", "finished" interchangeably
**Example:** Mix of statuses in state files and frontmatter
**Instead:** Standardize: `[todo, in-progress, done, blocked, aborted]`

### 3. **Missing Dependency Links**
**Problem:** Sprint files don't reference what they depend on
**Example:** Sprint 87-93 depend on Sprint 101 but don't document it
**Instead:** Add `depends_on: [101]` to sprint frontmatter

### 4. **Frontend Before Backend**
**Problem:** Starting UI work before API is stable
**Example:** Epic 03 had 3 sprint delays from API changes
**Instead:** Sequence backend → deploy → frontend

### 5. **Scope Creep in Large Epics**
**Problem:** 14-sprint epics grow secondary tasks
**Example:** Epic 04 External Data expanded beyond initial scope
**Instead:** Cap epics at 10 sprints; split if larger

### 6. **Untracked Time**
**Problem:** 67% of sprints have no hours recorded
**Impact:** Cannot calculate velocity or estimate future work
**Instead:** Require `hours` field on sprint completion

---

## Variations

### Greenfield Project

For new projects with no existing codebase:

1. **Epic 0: Foundation** (always first)
   - Sprint 0.1: Project scaffolding
   - Sprint 0.2: CI/CD pipeline
   - Sprint 0.3: Database schema
   - Sprint 0.4: Auth system

2. **Time Buffer:** Add 20% to estimates (learning curve)

3. **Dependency Order:**
   ```
   Database → API → Frontend → Mobile
   ```

### Brownfield/Integration Project

For projects integrating with existing systems:

1. **Discovery Sprint:** Map existing APIs, data formats, constraints

2. **Adapter Pattern:** Create integration layer sprints early
   - External API adapter
   - Data transformation
   - Error handling

3. **Time Buffer:** Add 40% (unknown unknowns in existing systems)

### Rapid Prototyping

For POC/demo projects with time pressure:

1. **Skip:** Comprehensive testing, full documentation
2. **Keep:** Core functionality, demo data, basic error handling
3. **Document:** Technical debt explicitly in DEFERRED.md

---

## Verification

### Epic Completion Checklist

Before marking an epic complete:

- [ ] All sprints in epic are status: done
- [ ] Time tracked for all sprints (hours field populated)
- [ ] Deferred items documented in DEFERRED.md
- [ ] Test coverage meets 85% threshold
- [ ] Demo data available for all features
- [ ] Documentation updated (if customer-facing)
- [ ] ADR created for architectural decisions
- [ ] Epic file updated with completion metrics

### Sprint Completion Checklist

From workflow enforcement system:

- [ ] Tests passing
- [ ] Migrations verified (if applicable)
- [ ] Sample data generated (if applicable)
- [ ] MCP tools tested (if applicable)
- [ ] Dialog example created (if applicable)
- [ ] Sprint file updated with completion timestamp
- [ ] Code has docstrings (if new modules)
- [ ] No hardcoded secrets
- [ ] Git status clean (committed)

---

## Metrics Template

Track these for each project:

```markdown
## Project Metrics: [Project Name]

### Velocity
- Total sprints: X
- Total hours: Y
- Avg sprint duration: Z hours
- Sprints per week: W

### Quality
- Test coverage: X%
- Bugs found post-completion: N
- Sprints requiring rework: M

### Planning Accuracy
- Estimated hours: X
- Actual hours: Y
- Variance: Z%

### Epic Performance
| Epic | Est Sprints | Actual | Variance |
|------|-------------|--------|----------|
| ... | ... | ... | ... |
```

---

## Related Recipes

- [Sprint Workflow v2.0](../workflows/sprint-workflow-v2.md) - Parallel agent execution
- [Development Infrastructure](../workflows/development-infrastructure.md) - Tools and skills inventory
- [Documentation Approach](../workflows/documentation-approach.md) - Doc standards

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-13 | Initial version from Sprint 00-109 retrospective |

---

## Appendix: Quick Reference

### Sprint Duration Estimates

| Sprint Type | Typical Hours | Example |
|-------------|---------------|---------|
| Infrastructure/DevOps | 6-10 | AWS setup, CI/CD |
| Data Integration | 4-8 | External APIs, import |
| Frontend Page | 2-4 | Dashboard, list views |
| API/Backend | 3-5 | GraphQL operations |
| Testing | 3-8 | Test suite, coverage |
| Documentation | 2-4 | Docs, examples |
| Quick Fix | 0.5-2 | Bug fixes, polish |

### Epic Planning Formula

```
Estimated Epic Duration =
  (Sprint Count × 3 hours) × Size Multiplier × Risk Factor

Where:
- Size Multiplier: S=1.0, M=1.1, L=1.2, XL=1.4
- Risk Factor: Greenfield=1.2, Brownfield=1.4, Integration=1.5
```

### Status State Machine

```
todo ──→ in-progress ──→ done
              │
              ├──→ blocked ──→ in-progress
              │
              └──→ aborted
```

### Dependency Notation

```yaml
# Sprint frontmatter
depends_on:
  - sprint-101  # Must complete before this sprint starts
  - sprint-99   # Test coverage must exist

blocks:
  - sprint-87   # This sprint blocks sprint-87
  - sprint-88
```
