# Recipe: Development Sequence for Maximum Synergy

**Category**: workflow
**Version**: 1.0
**Last Updated**: 2025-12-14
**Sprints**: Synthesis of 119+ sprints
**ADRs**: ADR-014 (TDD), ADR-015 (Sprint-Based Development)

## Context

**When to use this recipe:**
- Starting a new feature or subsystem from scratch
- Onboarding to understand how components fit together
- Planning multi-sprint initiatives (epics)
- Deciding which part of a feature to build first
- Maximizing reuse and minimizing rework

**When NOT to use this recipe:**
- Bug fixes (just fix the bug)
- Minor enhancements to existing features
- Urgent production issues (follow incident response)

## Overview

Building software in the right order creates compounding returns. Each layer you build provides foundations for the next, reduces rework, and enables parallel work streams.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OPTIMAL DEVELOPMENT SEQUENCE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: DATA FOUNDATION                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  1. Database Schema + Migrations                                        ││
│  │  2. SQLAlchemy Models with relationships                                ││
│  │  3. Synthetic data generators                                           ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              ↓                                               │
│  Phase 2: API LAYER                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  4. GraphQL types + resolvers                                           ││
│  │  5. DataLoaders for N+1 prevention                                      ││
│  │  6. MCP tools for LLM access                                            ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              ↓                                               │
│  Phase 3: BUSINESS LOGIC                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  7. Domain services and calculations                                    ││
│  │  8. Alert rules and notifications                                       ││
│  │  9. Background tasks                                                    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              ↓                                               │
│  Phase 4: FRONTEND                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  10. GraphQL queries/mutations                                          ││
│  │  11. Page components                                                    ││
│  │  12. Interactive features                                               ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              ↓                                               │
│  Phase 5: INTEGRATION & POLISH                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  13. End-to-end testing                                                 ││
│  │  14. Performance optimization                                           ││
│  │  15. Documentation                                                      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## The Principle: Build Bottom-Up, Test Top-Down

**Bottom-up building** means starting with foundational layers:
- Data models before APIs
- APIs before frontends
- Core logic before edge cases

**Top-down testing** means verifying from user perspective:
- E2E tests validate user flows
- Integration tests validate API contracts
- Unit tests validate individual functions

This combination ensures each layer works before building on top of it, while tests catch integration issues early.

## Phase 1: Data Foundation

**Goal**: Create stable data structures that won't change mid-feature.

### Step 1.1: Design Schema First

Before writing any code, design your data model:

```python
# Ask these questions:
# 1. What entities are involved?
# 2. What are the relationships (1:1, 1:N, N:M)?
# 3. What fields need to be indexed?
# 4. Is there time-series data (→ hypertable)?
# 5. Is there spatial data (→ PostGIS)?
```

**Why first?** Schema changes after data exists are painful. Migrations are easier on empty tables.

### Step 1.2: Create SQLAlchemy Models

```python
# src/corrdata/db/models.py
class MyNewEntity(Base):
    __tablename__ = "my_new_entities"

    uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Define relationships explicitly
    parent_uuid: Mapped[UUID] = mapped_column(ForeignKey("parents.uuid"))
    parent: Mapped["Parent"] = relationship(back_populates="children")
```

**Why second?** SQLAlchemy models are the source of truth. They generate migrations and define relationships.

### Step 1.3: Create Alembic Migration

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "add_my_new_entity"

# Review the generated migration!
# Then apply
alembic upgrade head
```

**Why third?** Migrations lock in your schema. Run them before writing business logic.

### Step 1.4: Create Synthetic Data Generator

```python
# scripts/seed_my_new_entities.py
def generate_synthetic_entities(count: int = 100):
    """Generate realistic test data."""
    for i in range(count):
        yield MyNewEntity(
            name=f"Entity {i}",
            # Realistic variation in test data
        )
```

**Why fourth?** You need data to test. Synthetic generators let you test at scale without waiting for real data.

### Synergy Effect

After Phase 1, you have:
- ✅ Stable schema that won't change
- ✅ Models that APIs can query
- ✅ Test data for development
- ✅ Foundation for parallel API + frontend work

## Phase 2: API Layer

**Goal**: Expose data through type-safe APIs.

### Step 2.1: Create GraphQL Types

```python
# src/corrdata/api/graphql/types/my_entity.py
import strawberry

@strawberry.type
class MyEntityType:
    uuid: strawberry.ID
    name: str

    @strawberry.field
    async def parent(self, info) -> "ParentType":
        # Use DataLoader for N+1 prevention
        return await info.context.loaders.parent.load(self.parent_uuid)
```

**Why first in Phase 2?** Types define the API contract. Frontend and backend can now work in parallel against this contract.

### Step 2.2: Create Resolvers

```python
# src/corrdata/api/graphql/resolvers/my_entity.py
@strawberry.type
class Query:
    @strawberry.field
    async def my_entities(
        self,
        info,
        limit: int = 50,
        offset: int = 0
    ) -> list[MyEntityType]:
        session = info.context.session
        result = await session.execute(
            select(MyNewEntity).limit(limit).offset(offset)
        )
        return [MyEntityType.from_orm(e) for e in result.scalars()]
```

**Why second?** Resolvers implement the contract. Tests can now verify the API works.

### Step 2.3: Create DataLoaders

```python
# src/corrdata/api/graphql/loaders.py
async def load_parents(keys: list[UUID]) -> list[Parent]:
    """Batch load parents for N+1 prevention."""
    async with get_session() as session:
        result = await session.execute(
            select(Parent).where(Parent.uuid.in_(keys))
        )
        parent_map = {p.uuid: p for p in result.scalars()}
        return [parent_map.get(key) for key in keys]
```

**Why third?** DataLoaders prevent N+1 queries. Add them before frontend queries reveal performance issues.

### Step 2.4: Create MCP Tools (if LLM access needed)

```python
# src/corrdata/mcp/tools/my_entity.py
TOOL_DEFINITION = ToolDefinition(
    name="get_my_entities",
    description="Retrieve my entities with optional filtering",
    parameters=[
        ParamDefinition("limit", "int", "Maximum results", required=False),
    ]
)

async def handle_get_my_entities(params: dict) -> dict:
    """Handler for MCP tool."""
    # Implementation
```

**Why fourth?** MCP tools enable LLM interaction. Build after core API so tools can reuse resolver logic.

### Synergy Effect

After Phase 2, you have:
- ✅ Type-safe API contract
- ✅ Frontend can start building against GraphQL schema
- ✅ LLM can query via MCP tools
- ✅ Performance optimizations (DataLoaders) in place

## Phase 3: Business Logic

**Goal**: Implement domain-specific rules and calculations.

### Step 3.1: Domain Services

```python
# src/corrdata/services/my_entity_service.py
class MyEntityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate_risk_score(self, entity_uuid: UUID) -> float:
        """Calculate risk based on entity attributes."""
        entity = await self.get_entity(entity_uuid)
        # Domain logic here
        return score
```

**Why first in Phase 3?** Services encapsulate business logic. Resolvers and tasks call services, not the other way around.

### Step 3.2: Alert Rules

```python
# If your feature needs alerts
rule = AlertRule(
    name="My Entity High Risk",
    trigger_type=TriggerType.THRESHOLD,
    condition={"field": "risk_score", "operator": ">", "value": 0.8},
    # ...
)
```

**Why second?** Alert rules depend on services that calculate the values being monitored.

### Step 3.3: Background Tasks

```python
# src/corrdata/tasks/my_entity_tasks.py
@celery_app.task
def process_entity_batch(entity_uuids: list[str]):
    """Process entities in background."""
    # Long-running work here
```

**Why third?** Background tasks often aggregate service calls. Build services first.

### Synergy Effect

After Phase 3, you have:
- ✅ Business logic testable in isolation
- ✅ Alerts can trigger on domain events
- ✅ Heavy processing runs in background
- ✅ Frontend can show calculated values

## Phase 4: Frontend

**Goal**: Build user interface on top of stable APIs.

> **Tip**: Use v0.dev for rapid UI generation. See [v0 UI Generation Playbook](../playbooks/v0-ui-generation.md) for the complete workflow. Generate components from specs, export as ZIP, and integrate with Claude Code.

### Step 4.1: GraphQL Queries/Mutations

```typescript
// packages/web-app/src/graphql/queries/myEntities.ts
export const GET_MY_ENTITIES = gql`
  query GetMyEntities($limit: Int, $offset: Int) {
    myEntities(limit: $limit, offset: $offset) {
      uuid
      name
      parent {
        uuid
        name
      }
    }
  }
`;
```

**Why first in Phase 4?** Queries define what data the UI needs. Build queries before components.

### Step 4.2: Page Components

```tsx
// packages/web-app/src/app/my-entities/page.tsx
export default function MyEntitiesPage() {
  const { data, loading } = useQuery(GET_MY_ENTITIES);

  if (loading) return <Skeleton />;

  return (
    <DataTable
      columns={columns}
      data={data.myEntities}
    />
  );
}
```

**Why second?** Pages compose components around data. Data access pattern determined by queries.

### Step 4.3: Interactive Features

```tsx
// Add after basic page works
function MyEntityDetail({ uuid }: { uuid: string }) {
  const { data } = useQuery(GET_MY_ENTITY_DETAIL, { variables: { uuid } });

  return (
    <Sheet>
      <SheetContent>
        {/* Detail view */}
      </SheetContent>
    </Sheet>
  );
}
```

**Why third?** Interactive features build on working pages. Get basic display working first.

### Synergy Effect

After Phase 4, you have:
- ✅ Full user interface
- ✅ Type-safe queries (generated types)
- ✅ Consistent UI patterns (shadcn/ui)
- ✅ Ready for user testing

## Phase 5: Integration & Polish

**Goal**: Ensure everything works together, optimize, document.

### Step 5.1: End-to-End Tests

```typescript
// packages/web-app/tests/e2e/my-entities.spec.ts
test('user can view my entities list', async ({ page }) => {
  await page.goto('/my-entities');
  await expect(page.getByRole('table')).toBeVisible();
  await expect(page.getByText('Entity 1')).toBeVisible();
});
```

**Why first in Phase 5?** E2E tests verify the full stack works. Catch integration bugs early.

### Step 5.2: Performance Optimization

```python
# Profile slow queries
EXPLAIN ANALYZE SELECT ...;

# Add indexes where needed
CREATE INDEX idx_my_entities_parent ON my_entities(parent_uuid);
```

**Why second?** Optimize only after measuring. Premature optimization wastes time.

### Step 5.3: Documentation

```markdown
# Add to playbook if pattern is reusable
# Update API docs if new endpoints
# Add examples to dialog examples
```

**Why third?** Document after implementation stabilizes. Don't document features that might change.

### Synergy Effect

After Phase 5, you have:
- ✅ Confidence from E2E tests
- ✅ Performance meets requirements
- ✅ Documentation for maintenance

## Parallel Work Opportunities

Once Phase 1 (Data Foundation) is complete, these can run in parallel:

```
                    ┌── Phase 2A: GraphQL Types ─── Phase 4A: Queries
Phase 1: Data ──────┼── Phase 2B: MCP Tools
                    └── Phase 3: Business Logic ─── Phase 4B: UI Components
```

**Key insight**: Data models are the bottleneck. Get them right, then parallelize.

## Anti-Patterns

### Don't: Start with Frontend

**What it looks like**: Building React components before data models exist.

**Why it's bad**:
- Frontend makes assumptions about data shape
- API changes break frontend repeatedly
- Lots of rework when models change

**Instead**: Build data foundation first. Frontend is the last thing to build.

### Don't: Skip Synthetic Data

**What it looks like**: Waiting for "real data" to test.

**Why it's bad**:
- Development blocked waiting for data
- Can't test edge cases
- Can't test at scale

**Instead**: Generate synthetic data immediately. Validate against real data later.

### Don't: Optimize Before Measuring

**What it looks like**: Adding caching, indexes, eager loading "just in case."

**Why it's bad**:
- Adds complexity without proven benefit
- May optimize the wrong thing
- Harder to debug

**Instead**: Build simple version first. Profile. Optimize hot paths.

### Don't: Build Features in Isolation

**What it looks like**: Building complete vertical slice without integration testing.

**Why it's bad**:
- Integration issues discovered late
- Components may not compose well
- Duplicate effort across features

**Instead**: Build layers horizontally. Integrate often. Share components.

## Real Example: Adding External Data Source

Here's how the sequence applies to adding a new external data source:

```
Sprint N: Data Foundation
├── Design schema for external data (soil, flood, etc.)
├── Create SQLAlchemy models
├── Create migration
└── Create synthetic provider

Sprint N+1: API Layer
├── GraphQL types for external data
├── Resolvers with DataLoaders
└── MCP tools for LLM queries

Sprint N+2: Business Logic
├── Risk scoring integration
├── Alert rules for thresholds
└── Background refresh tasks

Sprint N+3: Frontend
├── GraphQL queries
├── Dashboard components
├── Map layer visualization

Sprint N+4: Polish
├── E2E tests
├── Performance tuning (caching)
└── Documentation
```

**Total**: 4-5 sprints for complete feature
**Parallelization**: Sprints N+1 and N+2 can partially overlap
**Dependencies**: Each sprint depends on previous completing

## Learnings

### From 119+ Sprints

- **Schema stability is critical**: We've never regretted spending extra time on schema design
- **Synthetic data is non-negotiable**: Features blocked on real data missed deadlines
- **API-first enables parallelism**: Frontend and backend teams work independently
- **E2E tests catch integration bugs**: Unit tests alone miss integration issues

### Key Metrics

| Phase | Typical Duration | Rework Risk if Skipped |
|-------|------------------|------------------------|
| Data Foundation | 1-2 sprints | High (50%+ rework) |
| API Layer | 1 sprint | Medium (20-30% rework) |
| Business Logic | 1 sprint | Low (10% rework) |
| Frontend | 1-2 sprints | Low (5% rework) |
| Polish | 1 sprint | N/A |

## Related Recipes

- [Tech Stack Reference](../patterns/tech-stack-reference.md) - Technology choices
- [Three-Layer Database](../patterns/three-layer-database.md) - Database architecture
- [Sprint Workflow v2.2](./sprint-workflow-v2.md) - Sprint execution process
- [v0 UI Generation](../playbooks/v0-ui-generation.md) - AI-powered UI component generation
- [Adding External Data Source](../playbooks/adding-external-data-source.md) - Specific example

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-14 | Initial version synthesizing 119+ sprints of learnings |
