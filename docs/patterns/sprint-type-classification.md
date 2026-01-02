# Sprint Type Classification Guide

## Overview

Sprint types enable quality gates to adapt based on the nature of work being performed. This guide helps you choose the correct sprint type and understand the quality requirements for each.

## Quick Reference

| Type | Coverage | Special Requirements | Use When |
|------|----------|---------------------|----------|
| **fullstack** | 75% | Integration tests recommended | Default; full-stack features with both backend and frontend work |
| **backend** | 85% | Integration tests required | API-only, database schema, backend services, data processing |
| **frontend** | 70% | Visual regression tests | UI-only changes, styling, frontend components, user interactions |
| **research** | 30% | Documentation mandatory | Exploring new approaches, prototyping solutions, feasibility studies |
| **spike** | 0% | Documentation mandatory | Quick proof-of-concept, throwaway code, time-boxed exploration |
| **infrastructure** | 60% | Smoke tests required | DevOps, CI/CD pipelines, build tooling, deployment automation |

## Decision Tree

```
START: What is the primary focus of this sprint?

├─ Building production features?
│  │
│  ├─ Both backend AND frontend work?
│  │  └─> Type: fullstack (75% coverage, integration tests recommended)
│  │
│  ├─ Backend/API work only?
│  │  └─> Type: backend (85% coverage, integration tests required)
│  │
│  └─ Frontend/UI work only?
│     └─> Type: frontend (70% coverage, visual regression tests)
│
├─ Investigating or exploring options?
│  │
│  ├─ Need to keep the code?
│  │  └─> Type: research (30% coverage, documentation mandatory)
│  │
│  └─ Throwaway proof-of-concept?
│     └─> Type: spike (0% coverage, documentation mandatory)
│
└─ Infrastructure or tooling work?
   └─> Type: infrastructure (60% coverage, smoke tests required)
```

## Detailed Type Descriptions

### fullstack

**Coverage**: 75%
**Special Requirements**: Integration tests recommended
**Documentation**: Optional

**When to Use**:
- Building features that span backend and frontend
- Full user-facing functionality with API and UI
- Default choice when work crosses multiple layers

**Quality Focus**:
- Balanced coverage across backend and frontend
- Integration tests to verify API-UI contract
- End-to-end user workflows

**Example**:
```yaml
---
sprint: 42
type: fullstack
title: "User Profile Management"
---
```

**Justification**: Creating user profile API endpoints (backend) and profile editing UI (frontend).

---

### backend

**Coverage**: 85%
**Special Requirements**: Integration tests required
**Documentation**: Optional

**When to Use**:
- API development (REST, GraphQL)
- Database schema changes and migrations
- Backend service logic
- Data processing pipelines
- No frontend changes

**Quality Focus**:
- Highest coverage threshold (critical business logic)
- Integration tests for database operations
- API contract validation
- Service-to-service communication

**Example**:
```yaml
---
sprint: 43
type: backend
title: "Payment Processing Service"
coverage_threshold: 90
# Justification: Financial transaction logic requires maximum test coverage
---
```

**Justification**: Building payment API with zero tolerance for bugs in financial calculations.

---

### frontend

**Coverage**: 70%
**Special Requirements**: Visual regression tests
**Documentation**: Optional

**When to Use**:
- UI component development
- Styling and layout changes
- Frontend state management
- User interaction flows
- No backend changes

**Quality Focus**:
- Component testing (unit and integration)
- Visual regression to catch UI breaks
- Accessibility compliance
- Browser compatibility

**Example**:
```yaml
---
sprint: 44
type: frontend
title: "Dashboard Redesign"
---
```

**Justification**: Updating dashboard UI components with no backend changes.

---

### research

**Coverage**: 30%
**Special Requirements**: Documentation mandatory
**Documentation**: Required

**When to Use**:
- Exploring multiple technical approaches
- Prototyping new features before committing
- Investigating third-party libraries
- Feasibility studies
- Code will be kept (not throwaway)

**Quality Focus**:
- Document findings, pros/cons, recommendations
- Minimal coverage for experimental code
- Focus on learnings over production quality
- Justify recommended approach

**Example**:
```yaml
---
sprint: 45
type: research
title: "GraphQL vs REST API Performance Analysis"
---
```

**Documentation Must Include**:
- Problem statement
- Approaches investigated
- Performance benchmarks
- Pros and cons of each option
- Recommended solution with justification

---

### spike

**Coverage**: 0%
**Special Requirements**: Documentation mandatory
**Documentation**: Required

**When to Use**:
- Quick proof-of-concept (time-boxed)
- Throwaway code to answer specific question
- Rapid prototyping for demos
- Code will NOT be kept in production

**Quality Focus**:
- Document what was learned
- No coverage requirements
- Speed over quality
- Clear outcome documentation

**Example**:
```yaml
---
sprint: 46
type: spike
title: "Can we use WebSockets for real-time updates?"
---
```

**Documentation Must Include**:
- Question being answered
- Approach taken
- Results and findings
- Decision: proceed or pivot?

**Warning**: Never commit spike code to production without refactoring and proper testing.

---

### infrastructure

**Coverage**: 60%
**Special Requirements**: Smoke tests required
**Documentation**: Optional

**When to Use**:
- CI/CD pipeline changes
- Build tooling and scripts
- Deployment automation
- Development environment setup
- Infrastructure as code

**Quality Focus**:
- Smoke tests to verify basic functionality
- Moderate coverage for automation scripts
- Integration tests with external services
- Rollback mechanisms

**Example**:
```yaml
---
sprint: 47
type: infrastructure
title: "Automated Deployment Pipeline"
---
```

**Justification**: Setting up GitHub Actions for automated testing and deployment.

---

## Coverage Threshold Override

You can override the default coverage threshold for any sprint type with proper justification.

### Override Syntax

```yaml
---
sprint: 48
type: backend
coverage_threshold: 80
# Justification: Integration with external API, some code paths not testable locally
---
```

### Override Rules

1. **Justification Required**: Must include comment explaining why override is needed
2. **Format**: `# Justification: <reason>`
3. **Valid Range**: 0-100%
4. **Self-Service**: No approval required, but must be documented

### When to Lower Threshold

- External dependencies not testable locally
- Legacy code integration (gradual improvement)
- Experimental features with high uncertainty
- Time-boxed prototypes that may be discarded

### When to Raise Threshold

- Critical business logic (financial, security)
- Highly reusable utilities or libraries
- Regulated domains (healthcare, finance)
- Core framework or platform code

### Bad Override Examples

```yaml
# BAD: No justification
coverage_threshold: 50
```

```yaml
# BAD: Vague justification
coverage_threshold: 50
# Justification: It's hard to test
```

### Good Override Examples

```yaml
# GOOD: Specific justification for lowering
coverage_threshold: 65
# Justification: Integrating with Stripe API, webhook handlers require live environment
```

```yaml
# GOOD: Specific justification for raising
coverage_threshold: 95
# Justification: Core authentication module, security critical
```

---

## Special Requirements Checklist

Each sprint type has specific checklist items that must pass before completion.

### Common to All Types

- Tests passing
- Git status clean
- No hardcoded secrets

### Type-Specific Additions

**Backend**:
- Integration tests passing
- Database migrations verified
- API contract validated

**Frontend**:
- Visual regression tests passing
- Accessibility checks
- Cross-browser testing

**Research/Spike**:
- Documentation complete
- Findings documented
- Recommendation provided

**Infrastructure**:
- Smoke tests passing
- Rollback procedure tested
- Deployment documented

---

## Choosing the Right Type: Common Scenarios

### Scenario 1: Adding a new API endpoint and consuming it in the UI

**Answer**: `fullstack`
**Reason**: Work spans both backend (API) and frontend (UI)
**Coverage**: 75%
**Tests**: Integration tests for API-UI contract

### Scenario 2: Refactoring database queries for performance

**Answer**: `backend`
**Reason**: Database-only work, no UI changes
**Coverage**: 85%
**Tests**: Integration tests for query correctness

### Scenario 3: Updating button styles across the application

**Answer**: `frontend`
**Reason**: UI-only styling changes
**Coverage**: 70%
**Tests**: Visual regression tests

### Scenario 4: Comparing two state management libraries

**Answer**: `research`
**Reason**: Exploring options before deciding
**Coverage**: 30%
**Documentation**: Must document pros/cons and recommendation

### Scenario 5: Quick test to see if a library can parse our data format

**Answer**: `spike`
**Reason**: Time-boxed, throwaway code
**Coverage**: 0%
**Documentation**: Must document if library works and any issues

### Scenario 6: Adding automated security scanning to CI pipeline

**Answer**: `infrastructure`
**Reason**: CI/CD tooling work
**Coverage**: 60%
**Tests**: Smoke tests to verify scanner runs

---

## FAQ

### What if my sprint doesn't fit any category?

Default to `fullstack` and use coverage override if needed. This provides balanced requirements.

### Can I change sprint type mid-sprint?

Yes, but update the frontmatter immediately. Quality gates will adapt to the new type. Note the change in sprint documentation.

### What happens if I forget to set the type?

The workflow defaults to `fullstack` with a warning. Explicitly setting the type is best practice.

### Can I create a custom sprint type?

No. The six types cover all common scenarios. Use coverage override for edge cases.

### Do research sprints require tests?

Yes, minimal tests (30% coverage) to verify basic functionality. Focus is on documentation, not exhaustive testing.

### Can spike sprints have zero tests?

Yes, spike sprints can have 0% coverage since they're throwaway code. But documentation is mandatory.

### Why does backend have the highest coverage requirement?

Backend code typically contains critical business logic and has fewer external dependencies, making it more testable. Higher coverage reduces bugs in core functionality.

### Why can frontend have lower coverage?

Frontend code often involves visual elements, animations, and browser interactions that are harder to unit test. Visual regression tests compensate for lower coverage.

### What if infrastructure code is hard to test?

Use the override mechanism to lower the threshold (e.g., 40%) with justification. Add comprehensive smoke tests to verify critical paths.

---

## Migration Guide

### Updating Existing Sprints

Existing sprint files without a `type` field will default to `fullstack`. To update:

1. Open the sprint file
2. Add `type: <appropriate-type>` to frontmatter
3. Adjust `coverage_threshold` if needed with justification
4. Commit the change

### Example Migration

**Before**:
```yaml
---
sprint: 35
title: "API Refactoring"
status: in-progress
---
```

**After**:
```yaml
---
sprint: 35
title: "API Refactoring"
type: backend
status: in-progress
coverage_threshold: 80
# Justification: Legacy API with external dependencies, gradual coverage improvement
---
```

---

## Best Practices

1. **Be Honest**: Choose the type that matches the actual work, not the easiest quality gate
2. **Document Overrides**: Always explain why default threshold doesn't fit
3. **Review in Planning**: Validate sprint type during Phase 1 (Planning)
4. **Update if Scope Changes**: If sprint scope shifts, update the type
5. **Use Research for Unknowns**: When uncertain, use research to explore before committing
6. **Spike for Quick Answers**: Time-box spikes to 1-2 hours, then convert to research if continuing

---

## References

- Sprint 4 Specification: `docs/sprints/2-in-progress/epic-01_workflow-v3-enhancements/sprint-04_type-aware-quality-gates/sprint-04_type-aware-quality-gates.md`
- Quality Gates Configuration: `.claude/hooks/validate_step.py`
- Pre-Flight Checklist: `.claude/hooks/sprint_complete_check.py`
- Global Workflow Documentation: `CLAUDE.md`
