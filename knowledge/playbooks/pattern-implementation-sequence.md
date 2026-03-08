# Pattern Implementation Sequence

**Category**: playbook
**Version**: 1.0
**Last Updated**: 2026-01-02

---

## Context

### When to Use This Guide

- Planning which patterns to implement and in what order
- Wondering "should I add X feature now or later?"
- Team member asking "where do I start after the bootstrap?"
- Deciding priorities for your first epic

### When NOT to Use

- You've already established your core patterns
- Quick prototype or POC (skip most patterns)
- Following a specific feature roadmap (use that instead)

---

##

 Overview

Not all patterns are created equal. Some are **foundational** (must have first), others are **evolutionary** (add when needed), and some are **advanced** (only if you need them).

This guide maps the patterns from our playbook and the vericorr project into the order you should implement them, with decision trees for when to add each one.

---

## The Golden Rule

**Backend → API → Frontend → Advanced Features**

Always build in this order:
1. Data models (backend)
2. API/GraphQL (interface layer)
3. Frontend pages (UI)
4. Advanced features (search, real-time, etc.)

---

## Implementation Phases

### Phase 0: Foundation (Epic 0)

**Must have before any features. Do this during bootstrap.**

| Pattern | ADR | When | Sprint Estimate |
|---------|-----|------|-----------------|
| Three-Layer Database | ADR-001 | Always | Included in template |
| SQLAlchemy 2.0 | ADR-011 | Always | Included in template |
| UUID Identifiers | ADR-005 | Always | Included in template |
| Alembic Migrations | ADR-010 | Always | Included in template |
| FastAPI + GraphQL | ADR-002, 019, 038 | Always | Included in template |
| Environment Config | ADR-016 | Always | Included in template |
| Testing Strategy | ADR-014, 044 | Always | Included in template |

**Output:** Working backend + frontend talking to each other.

**Reference:** See [project-bootstrap-guide.md](./project-bootstrap-guide.md)

---

### Phase 1: Authentication & Multi-Tenancy (Epic 1)

**Add before first real feature. Critical for production apps.**

| Pattern | ADR | When | Decision |
|---------|-----|------|----------|
| Multi-Tenant Security | ADR-037, 060 | Multi-org app | ✅ If serving multiple customers<br>❌ If single org/personal app |
| Auth (Cognito/Auth0) | - | Any production app | ✅ Always for real users<br>❌ Skip for internal tools |
| Role-Based Access | ADR-060 | Different user types | ✅ If admin vs user roles<br>❌ If everyone has same access |

**Sprints:**
1. Sprint 1: Database models (User, Tenant, Role)
2. Sprint 2: Auth provider integration (Cognito/Auth0)
3. Sprint 3: Frontend auth flows (login, logout, protected routes)
4. Sprint 4: Role-based permissions

**Decision Tree:**

```
Do you have multiple organizations/customers?
├─ YES → Multi-tenant (Tenant model + tenant_uuid on everything)
└─ NO → Single tenant (skip Tenant model)

Do you have different user roles (admin, viewer, etc.)?
├─ YES → Role-based access (Role model + permissions)
└─ NO → Simple auth (just User model)
```

**Example:** claude-maestro uses simple auth (no multi-tenancy, single user system).

---

### Phase 2: Core Domain Features (Epic 2-5)

**Your actual application features. Build in backend-first order.**

#### For Each Feature:

**Sprint Pattern:**
1. **Database Sprint:** Add models, migrations
2. **GraphQL Sprint:** Add queries/mutations
3. **Frontend Sprint:** Add pages/components
4. **Test Sprint:** (if epic > 7 sprints)

**Example: Task Management Feature**

```
Epic 02: Task Management
├── Sprint 01: Task models (Project, Task, Comment)
├── Sprint 02: GraphQL schema (queries + mutations)
├── Sprint 03: Project list page
├── Sprint 04: Project detail + task list
├── Sprint 05: Task creation form
└── Sprint 06: Task detail + comments
```

**Reference:** See claude-maestro epic-01 structure

---

### Phase 3: External Data Integration (Epic 4+)

**Add when you need to integrate external APIs or data sources.**

| Pattern | ADR | When | Sprint Estimate |
|---------|-----|------|-----------------|
| Provider Pattern | ADR-012, 032 | External APIs | 1 sprint per provider |
| File-Based Caching | ADR-017 | Slow external APIs | Add with provider |
| Data Provider Factory | ADR-032 | Multiple providers | 1 sprint (with first provider) |

**Decision:** Do you call external APIs (weather, maps, payment, etc.)?
- ✅ YES → Implement provider pattern
- ❌ NO → Skip

**Example from vericorr:**
- Sprint 25: PHMSA data provider
- Sprint 26: File caching for PHMSA
- Sprint 27: Provider factory (allows mock vs real)

**Sprint Structure:**
```
Sprint N: External API Integration
├── Phase 1: Provider interface (abstract)
├── Phase 2: Real implementation (API calls)
├── Phase 3: Mock implementation (testing)
├── Phase 4: Factory (selector between mock/real)
└── Phase 5: Caching layer (optional)
```

---

### Phase 4: Advanced Database Features (As Needed)

**Only add if your domain needs them.**

| Pattern | ADR | When | Decision |
|---------|-----|------|----------|
| PostGIS (Spatial) | ADR-008 | Maps, locations, geo queries | ✅ Asset tracking, delivery routes<br>❌ Standard CRUD app |
| TimescaleDB | ADR-007 | Time-series metrics | ✅ IoT data, analytics dashboards<br>❌ Standard records |
| Neo4j Graph | ADR-003 | Complex relationships | ✅ Social networks, dependencies<br>❌ Simple parent-child |

**Decision Tree:**

```
Do you have location data (lat/lng, addresses)?
├─ YES → PostGIS
│   └─ Enable in docker-compose.yml (already configured)
└─ NO → Skip

Do you collect metrics over time (temperature, counts, etc.)?
├─ YES → TimescaleDB
│   └─ Change postgres image to timescale/timescaledb-ha:pg15
└─ NO → Skip

Do you have complex many-to-many relationships (graph-like)?
├─ YES → Consider Neo4j
│   └─ Add neo4j service to docker-compose.yml
└─ NO → Skip (SQLAlchemy handles most cases)
```

**Reference:** vericorr uses all three (spatial assets, time-series measurements, relationship graphs).

---

### Phase 5: Frontend Enhancements (As Needed)

**Add better UX as you grow.**

| Pattern | ADR | When | Sprint Estimate |
|---------|-----|------|-----------------|
| Real-Time Updates | - | Live data needed | 2-3 sprints |
| Offline Support (PWA) | ADR-021 | Mobile/unreliable network | 2-3 sprints |
| Advanced Components | - | Complex UI needs | Per component |

**Decision:**

```
Do users need to see live updates (chat, dashboards)?
├─ YES → WebSockets + GraphQL subscriptions
└─ NO → Skip (polling is fine)

Will users work offline or on poor networks?
├─ YES → PWA with service workers
└─ NO → Skip (standard web app)
```

**Reference:** vericorr implemented PWA (Epic 06) after core features were done.

---

### Phase 6: Production Infrastructure (Before Launch)

**Required before real users.**

| Pattern | ADR | When | Sprint Estimate |
|---------|-----|------|-----------------|
| ECS/Fargate Deployment | ADR-039, 041, 049 | AWS deployment | 3-4 sprints |
| Observability | ADR-040 | Production monitoring | 1-2 sprints |
| CI/CD Pipeline | ADR-053, 054 | Automated deployments | 2-3 sprints |
| Secret Management | ADR-042 | Production secrets | 1 sprint |

**Epic Structure:**
```
Epic: Production Deployment
├── Sprint 1: AWS infrastructure (VPC, RDS, ECS)
├── Sprint 2: Container images + task definitions
├── Sprint 3: Load balancer + domain setup
├── Sprint 4: CI/CD pipeline (GitHub Actions)
├── Sprint 5: Monitoring (CloudWatch + alarms)
└── Sprint 6: Secret management (Secrets Manager)
```

**Reference:** vericorr Epic 05 (Production Deployment), 6 sprints.

---

## Pattern Decision Matrix

Quick reference for "should I add this pattern now?"

| Pattern | Add When | Skip If |
|---------|----------|---------|
| **Three-Layer DB** | Always (foundation) | Never skip |
| **Multi-Tenant** | Multiple customers | Single org |
| **Provider Pattern** | External APIs | No external data |
| **PostGIS** | Location/maps | No geo data |
| **TimescaleDB** | Time-series | No metrics |
| **Neo4j** | Complex graphs | Simple relations |
| **WebSockets** | Real-time updates | Polling works |
| **PWA** | Offline support | Always-online app |
| **MCP Server** | LLM integration | No AI features |

---

## Epic Sizing Guidance

Based on vericorr project analysis:

| Epic Type | Sprints | Example |
|-----------|---------|---------|
| **Foundation** | 3-5 | Project setup, auth, core models |
| **Feature Set (Small)** | 2-4 | Single domain model with CRUD |
| **Feature Set (Medium)** | 5-8 | Multiple related models + UI |
| **Feature Set (Large)** | 9-12 | Complex domain with relationships |
| **External Integration** | 6-10 | Provider pattern + multiple sources |
| **Production Deployment** | 5-7 | AWS infra + CI/CD + monitoring |

**Rule of thumb:** If planning > 10 sprints, split into 2 epics.

---

## Recommended First Year Roadmap

For a typical SaaS application:

### Quarter 1: Foundation + Core Features
```
Epic 00: Foundation (3-4 sprints)
├── Bootstrap from template
├── Authentication
└── Multi-tenancy (if needed)

Epic 01: First Domain Feature (5-7 sprints)
├── Core models
├── GraphQL API
├── Basic UI
└── Tests

Epic 02: Second Domain Feature (5-7 sprints)
└── (Same pattern)
```

### Quarter 2: Integration + Enhancement
```
Epic 03: External Data Integration (6-8 sprints)
├── Provider pattern
├── First integration
└── Caching

Epic 04: Advanced Features (5-7 sprints)
├── Search
├── Filtering
└── Exports
```

### Quarter 3: Mobile + Real-Time
```
Epic 05: Mobile PWA (6-8 sprints)
├── Offline support
├── Service workers
└── Mobile-optimized UI

Epic 06: Real-Time Features (4-6 sprints)
└── WebSockets + subscriptions
```

### Quarter 4: Production Hardening
```
Epic 07: Production Deployment (5-7 sprints)
Epic 08: Monitoring & Scaling (3-5 sprints)
```

**Total:** ~60-80 sprints in first year (vericorr did 109 sprints in 6 weeks with AI assistance).

---

## Anti-Patterns

### ❌ Don't Do This

**1. Frontend Before Backend**
```
❌ WRONG ORDER:
Sprint 1: Build task list UI
Sprint 2: Build GraphQL API
Sprint 3: Connect them
(UI has to be rebuilt when API changes)

✅ CORRECT ORDER:
Sprint 1: Task models + migrations
Sprint 2: GraphQL schema
Sprint 3: Task list UI (uses stable API)
```

**2. Advanced Features Too Early**
```
❌ WRONG:
Epic 1: Real-time WebSockets
Epic 2: Basic CRUD operations
(Premature optimization)

✅ CORRECT:
Epic 1: Basic CRUD
Epic 2: More features
Epic 5: Real-time (after core is proven)
```

**3. Skipping Tests**
```
❌ WRONG:
"We'll add tests later"
(Later never comes)

✅ CORRECT:
75-85% coverage from Sprint 1
Flexible TDD: tests alongside code
```

---

## Pattern Implementation Sprints

Reference sprints from vericorr showing pattern implementation:

| Pattern | Sprint # | Files | Notes |
|---------|----------|-------|-------|
| GraphQL Schema | 10-15 | schema.py, types.py, resolvers.py | Foundation |
| Provider Pattern | 25 | providers/base.py, providers/real.py | Reusable |
| Multi-Tenant | 8-9 | models.py (Tenant), middleware | Add early |
| PostGIS | 18 | models.py (geometry columns) | When needed |
| PWA | 55-60 | service-worker.js, manifest.json | Later phase |
| MCP Server | 18, 24 | mcp/server.py, tools/ | If LLM needed |

---

## Verification Checklist

Before moving to next phase:

**Phase 0 Complete:**
- [ ] Template running locally
- [ ] Can query GraphQL
- [ ] Frontend displays data
- [ ] Tests passing

**Phase 1 Complete:**
- [ ] Users can log in
- [ ] Protected routes work
- [ ] Roles enforced (if applicable)

**Phase 2 Complete:**
- [ ] Core features working
- [ ] GraphQL types match models
- [ ] Frontend pages functional
- [ ] 75%+ test coverage

**Phase 3+ (As Applicable):**
- [ ] External APIs integrated
- [ ] Advanced DB features working
- [ ] Production deployment ready

---

## Related Playbooks

- [Project Bootstrap Guide](./project-bootstrap-guide.md) - How to start (Phase 0)
- [Development Sequence](../workflows/development-sequence.md) - Day-to-day workflow
- [Sprint Workflow](../workflows/sprint-workflow-v2.md) - How to execute sprints

---

## Pattern Reference

Detailed implementation guides in `patterns/`:

- **Foundation:** three-layer-database.md, graphql-schema.md, session-factory-testing.md
- **Integration:** provider-pattern.md, mcp-tool-registry.md
- **Advanced:** alert-engine.md, configuration-management.md

ADR references in vericorr: `vericorr/docs/architecture/decisions/`

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-02 | Initial version based on vericorr project analysis |
