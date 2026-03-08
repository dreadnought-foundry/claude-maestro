# Recipe: GraphQL Schema Design with Strawberry

**Category**: pattern
**Version**: 1.1
**Last Updated**: 2025-12-15
**Sprints**: Sprint 94 (dashboard queries), Sprint 102 (type aliasing), Sprint 133 (session factory), Multiple (foundation)
**ADRs**: [ADR-002](../../architecture/decisions/ADR-002-graphql-api.md), [ADR-038](../../architecture/decisions/ADR-038-graphql-api-architecture.md), [ADR-050](../../architecture/decisions/ADR-050-graphql-session-factory-pattern.md)

## Context

**When to use this recipe:**
- Building APIs for React/web frontends with complex data requirements
- Supporting both mobile (PWA) and desktop dashboards
- Preventing N+1 query problems with nested data
- Implementing real-time updates via subscriptions
- Enabling type-safe client code generation
- Optimizing for mobile networks (minimize payload size)

**When NOT to use this recipe:**
- Simple CRUD APIs with no nested relationships
- Backend-to-backend microservice communication (use gRPC)
- File upload/download heavy workloads (use REST)
- When team has no GraphQL experience and timeline is tight

## Ingredients

Before starting, ensure you have:

- [ ] Strawberry GraphQL installed (`strawberry-graphql[fastapi]`)
- [ ] FastAPI as the ASGI framework
- [ ] SQLAlchemy 2.0 models defined
- [ ] Understanding of DataLoader pattern
- [ ] Async database session management
- [ ] Frontend code generator setup (GraphQL Code Generator)
- [ ] Redis for subscription pub/sub (optional, for real-time)

## Overview

Strawberry GraphQL provides type-safe schema definition using Python type hints:

```
┌─────────────────────────────────────────────────────────────────┐
│                       Frontend Clients                           │
│  (React PWA, Ops Dashboard, Executive Portal)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                       GraphQL Queries
                    (POST /graphql)
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    Strawberry GraphQL                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Query, Mutation, Subscription Types                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  DataLoaders (N+1 Prevention)                              │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                   SQLAlchemy ORM                                 │
│              (PostgreSQL + TimescaleDB + PostGIS)                │
└─────────────────────────────────────────────────────────────────┘
```

## Steps

### Step 1: Define Core Domain Types

Create Strawberry types that mirror your domain (not database tables):

```python
# src/corrdata/api/graphql/types/asset.py
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID
import strawberry
from strawberry import Private

if TYPE_CHECKING:
    from corrdata.api.graphql.types.measurement import Measurement
    from corrdata.api.graphql.types.event import Event

@strawberry.enum
class AssetType(str, Enum):
    SEGMENT = "segment"
    TEST_STATION = "test_station"
    RECTIFIER = "rectifier"
    BOND = "bond"
    ANODE_BED = "anode_bed"

@strawberry.enum
class AssetStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RETIRED = "retired"
    PLANNED = "planned"

@strawberry.type
class Asset:
    """
    Represents a pipeline asset (segment, test station, rectifier, etc.)
    """
    id: UUID
    name: str
    type: AssetType
    status: AssetStatus
    description: Optional[str] = None

    # Geometry as GeoJSON string (Strawberry doesn't support native geometry)
    geometry: Optional[str] = None

    # Temporal validity
    valid_from: datetime
    valid_to: Optional[datetime] = None

    # Audit fields
    created_at: datetime
    updated_at: datetime

    # Private fields (not exposed in schema, used for DataLoader)
    tenant_id: Private[UUID]
    parent_id: Private[Optional[UUID]]

    @strawberry.field
    async def parent(self, info: strawberry.Info) -> Optional["Asset"]:
        """Parent asset (if this is a child asset)."""
        if not self.parent_id:
            return None
        loader = info.context.loaders.asset
        return await loader.load(self.parent_id)

    @strawberry.field
    async def children(
        self,
        info: strawberry.Info,
        first: int = 100
    ) -> list["Asset"]:
        """Child assets."""
        loader = info.context.loaders.asset_children
        return await loader.load((self.id, first))

    @strawberry.field
    async def measurements(
        self,
        info: strawberry.Info,
        type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        first: int = 100
    ) -> list["Measurement"]:
        """Measurements for this asset."""
        loader = info.context.loaders.measurements
        params = (self.id, type, start_time, end_time, first)
        return await loader.load(params)

    @strawberry.field
    async def events(
        self,
        info: strawberry.Info,
        first: int = 50
    ) -> list["Event"]:
        """Recent events for this asset."""
        loader = info.context.loaders.events
        return await loader.load((self.id, first))

    @strawberry.field
    def risk_score(self) -> Optional[float]:
        """
        Computed risk score (0-100).
        This would call risk scoring service.
        """
        # Placeholder - implement based on your risk model
        return None

    @strawberry.field
    def compliance_status(self) -> str:
        """Compliance status based on recent measurements."""
        # Placeholder - implement compliance logic
        return "compliant"

    @classmethod
    def from_orm(cls, model: "AssetModel") -> "Asset":
        """Convert SQLAlchemy model to Strawberry type."""
        return cls(
            id=model.uuid,
            name=model.name,
            type=AssetType(model.asset_type),
            status=AssetStatus(model.status),
            description=model.description,
            geometry=model.geometry.desc if model.geometry else None,
            valid_from=model.valid_from,
            valid_to=model.valid_to,
            created_at=model.created_at,
            updated_at=model.updated_at,
            tenant_id=model.tenant_id,
            parent_id=model.parent_uuid,
        )
```

**Expected outcome**: Type-safe GraphQL type with computed fields and relationships.

### Step 2: Implement DataLoaders for N+1 Prevention

Create batched loaders to prevent N+1 queries:

```python
# src/corrdata/api/graphql/dataloaders.py
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from strawberry.dataloader import DataLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from corrdata.db.models import Asset as AssetModel, Measurement as MeasurementModel

@dataclass
class DataLoaders:
    """Container for all DataLoaders (attached to request context)."""
    session: AsyncSession

    def __post_init__(self):
        self.asset = DataLoader(load_fn=self._load_assets)
        self.asset_children = DataLoader(load_fn=self._load_asset_children)
        self.measurements = DataLoader(load_fn=self._load_measurements)

    async def _load_assets(self, ids: list[UUID]) -> list[Optional[AssetModel]]:
        """
        Batch load assets by ID.
        Called automatically by DataLoader when multiple assets requested.
        """
        stmt = select(AssetModel).where(AssetModel.uuid.in_(ids))
        result = await self.session.execute(stmt)
        assets_by_id = {a.uuid: a for a in result.scalars()}

        # Return in same order as requested (important!)
        return [assets_by_id.get(id) for id in ids]

    async def _load_asset_children(
        self,
        params: list[tuple[UUID, int]]
    ) -> list[list[AssetModel]]:
        """
        Batch load children for multiple parent assets.
        Each param is (parent_id, limit).
        """
        # Group by parent_id
        parent_ids = [p[0] for p in params]

        stmt = (
            select(AssetModel)
            .where(AssetModel.parent_uuid.in_(parent_ids))
            .order_by(AssetModel.name)
        )
        result = await self.session.execute(stmt)
        all_children = result.scalars().all()

        # Group children by parent
        children_by_parent = {}
        for child in all_children:
            if child.parent_uuid not in children_by_parent:
                children_by_parent[child.parent_uuid] = []
            children_by_parent[child.parent_uuid].append(child)

        # Return in request order, applying limit
        return [
            children_by_parent.get(parent_id, [])[:limit]
            for parent_id, limit in params
        ]

    async def _load_measurements(
        self,
        params: list[tuple[UUID, Optional[str], Optional[datetime], Optional[datetime], int]]
    ) -> list[list[MeasurementModel]]:
        """
        Batch load measurements for multiple assets.
        Each param is (asset_id, type, start_time, end_time, limit).
        """
        asset_ids = [p[0] for p in params]

        # Build base query
        stmt = (
            select(MeasurementModel)
            .where(MeasurementModel.asset_uuid.in_(asset_ids))
            .order_by(MeasurementModel.recorded_at.desc())
        )

        result = await self.session.execute(stmt)
        all_measurements = result.scalars().all()

        # Filter and group by parameters
        results = []
        for asset_id, mtype, start, end, limit in params:
            filtered = [
                m for m in all_measurements
                if m.asset_uuid == asset_id
                and (mtype is None or m.measurement_type == mtype)
                and (start is None or m.recorded_at >= start)
                and (end is None or m.recorded_at <= end)
            ]
            results.append(filtered[:limit])

        return results
```

**Expected outcome**: DataLoaders that batch database queries to prevent N+1 problems.

### Step 3: Define Query Type

Create root Query type with resolvers:

```python
# src/corrdata/api/graphql/schema/query.py
from typing import Optional
from uuid import UUID
import strawberry
from corrdata.api.graphql.types.asset import Asset, AssetType, AssetStatus
from corrdata.api.graphql.types.dashboard import DashboardSummary
from corrdata.db.models import Asset as AssetModel
from sqlalchemy import select

@strawberry.type
class Query:
    """Root Query type - all GraphQL queries start here."""

    @strawberry.field
    async def asset(self, info: strawberry.Info, id: UUID) -> Optional[Asset]:
        """Get a single asset by ID."""
        session = info.context.session

        stmt = select(AssetModel).where(AssetModel.uuid == id)
        result = await session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return Asset.from_orm(model)

    @strawberry.field
    async def assets(
        self,
        info: strawberry.Info,
        type: Optional[AssetType] = None,
        status: Optional[AssetStatus] = None,
        search: Optional[str] = None,
        first: int = 100,
        offset: int = 0
    ) -> list[Asset]:
        """
        Query assets with filters.
        Supports pagination via first/offset.
        """
        session = info.context.session

        stmt = select(AssetModel).order_by(AssetModel.name)

        # Apply filters
        if type:
            stmt = stmt.where(AssetModel.asset_type == type.value)
        if status:
            stmt = stmt.where(AssetModel.status == status.value)
        if search:
            stmt = stmt.where(AssetModel.name.ilike(f"%{search}%"))

        # Pagination
        stmt = stmt.limit(first).offset(offset)

        result = await session.execute(stmt)
        models = result.scalars().all()

        return [Asset.from_orm(m) for m in models]

    @strawberry.field
    async def dashboard_summary(
        self,
        info: strawberry.Info,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> DashboardSummary:
        """
        Combined dashboard query (Sprint 94 pattern).
        Returns all dashboard data in one query.
        """
        session = info.context.session

        # This would aggregate multiple queries
        # See Sprint 94 for full implementation
        return DashboardSummary(
            total_assets=0,
            active_alerts=0,
            compliance_percentage=95.0,
            recent_measurements=[],
        )
```

**Expected outcome**: Query type that frontend can call to fetch data.

### Step 4: Define Mutation Type

Create mutations for data modification:

```python
# src/corrdata/api/graphql/schema/mutation.py
from typing import Optional
from uuid import UUID
import strawberry
from corrdata.api.graphql.types.measurement import Measurement
from corrdata.api.graphql.types.errors import UserError, ErrorCode
from corrdata.db.models import Measurement as MeasurementModel

@strawberry.input
class CreateFieldReadingInput:
    """Input for creating a field reading."""
    asset_id: UUID
    type: str
    value: float
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@strawberry.type
class CreateFieldReadingPayload:
    """Payload returned from createFieldReading mutation."""
    reading: Optional[Measurement] = None
    errors: list[UserError] = strawberry.field(default_factory=list)

    @property
    def success(self) -> bool:
        """True if mutation succeeded."""
        return self.reading is not None and len(self.errors) == 0

@strawberry.type
class Mutation:
    """Root Mutation type - all GraphQL mutations start here."""

    @strawberry.mutation
    async def create_field_reading(
        self,
        info: strawberry.Info,
        input: CreateFieldReadingInput
    ) -> CreateFieldReadingPayload:
        """
        Create a new field reading (mobile app pattern).
        Returns payload with either reading or errors.
        """
        session = info.context.session
        user = info.context.user

        # Validate input
        errors = []

        if input.value < -10000 or input.value > 10000:
            errors.append(UserError(
                field="value",
                message="Value out of acceptable range",
                code=ErrorCode.VALIDATION_ERROR
            ))

        if input.latitude is not None:
            if not (-90 <= input.latitude <= 90):
                errors.append(UserError(
                    field="latitude",
                    message="Latitude must be between -90 and 90",
                    code=ErrorCode.VALIDATION_ERROR
                ))

        if errors:
            return CreateFieldReadingPayload(errors=errors)

        # Create measurement
        measurement = MeasurementModel(
            asset_uuid=input.asset_id,
            measurement_type=input.type,
            value=input.value,
            recorded_at=input.timestamp or datetime.utcnow(),
            metadata={
                "notes": input.notes,
                "location": {
                    "latitude": input.latitude,
                    "longitude": input.longitude
                } if input.latitude else None,
                "technician_id": str(user.id),
            }
        )

        session.add(measurement)
        await session.commit()
        await session.refresh(measurement)

        return CreateFieldReadingPayload(
            reading=Measurement.from_orm(measurement)
        )
```

**Expected outcome**: Mutation that validates input and returns typed payload.

### Step 5: Set Up GraphQL Context

Create context with session and loaders:

```python
# src/corrdata/api/graphql/context.py
from dataclasses import dataclass
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from corrdata.api.graphql.dataloaders import DataLoaders
from corrdata.db.session import get_session
from corrdata.api.auth import get_current_user, User

@dataclass
class GraphQLContext:
    """Context passed to all GraphQL resolvers."""
    request: Request
    session: AsyncSession
    user: User
    loaders: DataLoaders

async def get_graphql_context(
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> GraphQLContext:
    """
    Create GraphQL context for each request.
    DataLoaders are recreated per request (important for caching).
    """
    return GraphQLContext(
        request=request,
        session=session,
        user=user,
        loaders=DataLoaders(session=session),
    )
```

**Expected outcome**: Context object available to all resolvers via `info.context`.

### Step 6: Create GraphQL Router

Mount GraphQL schema in FastAPI:

```python
# src/corrdata/api/app.py
from fastapi import FastAPI
import strawberry
from strawberry.fastapi import GraphQLRouter
from corrdata.api.graphql.schema.query import Query
from corrdata.api.graphql.schema.mutation import Mutation
from corrdata.api.graphql.context import get_graphql_context

# Create Strawberry schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)

# Create GraphQL router
graphql_router = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    graphiql=True,  # Enable GraphiQL UI in dev
)

# Create FastAPI app
app = FastAPI(title="CorrData API")

# Mount GraphQL
app.include_router(graphql_router, prefix="/graphql")

# Health check endpoint (REST)
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

**Expected outcome**: GraphQL endpoint available at `/graphql`, GraphiQL UI at `/graphql`.

## Code Examples

### Frontend Query (TypeScript)

```typescript
// packages/web-app/src/graphql/queries/asset.ts
import { gql } from '@apollo/client';

export const GET_ASSET = gql`
  query GetAsset($id: UUID!) {
    asset(id: $id) {
      id
      name
      type
      status
      riskScore
      parent {
        id
        name
      }
      measurements(first: 10, type: "pipe_to_soil_potential") {
        id
        value
        unit
        timestamp
      }
    }
  }
`;

// Usage in React component
import { useQuery } from '@apollo/client';
import { GET_ASSET } from './graphql/queries/asset';

function AssetDetail({ assetId }) {
  const { data, loading, error } = useQuery(GET_ASSET, {
    variables: { id: assetId }
  });

  if (loading) return <Spinner />;
  if (error) return <Error message={error.message} />;

  return <AssetCard asset={data.asset} />;
}
```

### Combined Dashboard Query (Sprint 94 Pattern)

```python
# src/corrdata/api/graphql/types/dashboard.py
import strawberry
from datetime import datetime
from typing import Optional

@strawberry.type
class DashboardSummary:
    """Combined dashboard data - fetched in single query."""
    total_assets: int
    active_alerts: int
    compliance_percentage: float
    avg_risk_score: Optional[float]

    # Nested data
    recent_measurements: list["Measurement"]
    high_risk_assets: list["Asset"]
    upcoming_compliance_deadlines: list["ComplianceDeadline"]

    @strawberry.field
    def status_breakdown(self) -> dict[str, int]:
        """Asset status counts."""
        # Would query database
        return {
            "active": 150,
            "inactive": 20,
            "planned": 5
        }

# In Query type
@strawberry.field
async def dashboard_summary(
    self,
    info: strawberry.Info,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> DashboardSummary:
    """
    Single query that returns all dashboard data.
    Prevents multiple round-trips for dashboard load.
    """
    session = info.context.session

    # Run queries in parallel
    total_assets, active_alerts, measurements = await asyncio.gather(
        get_total_assets(session),
        get_active_alerts(session),
        get_recent_measurements(session, start_date, end_date)
    )

    return DashboardSummary(
        total_assets=total_assets,
        active_alerts=active_alerts,
        recent_measurements=measurements,
        # ... other fields
    )
```

### Type Aliasing Pattern (Sprint 102)

```python
# When Strawberry type name differs from Python class name
from typing import Annotated
import strawberry

# Define alias for GraphQL schema
AssetGQL = Annotated[Asset, strawberry.type(name="Asset")]

# Use in resolver
@strawberry.field
async def assets(self) -> list[AssetGQL]:
    """Returns list of Asset type in schema."""
    return [Asset.from_orm(m) for m in models]
```

## Learnings

### From Sprint 94 (Dashboard Queries)

- **Combined queries reduce latency**: Single `dashboardSummary` query is 5x faster than 5 separate queries
- **Mobile optimization critical**: Minimize number of round-trips for cellular networks
- **Parallel resolution**: Use `asyncio.gather()` to run independent queries in parallel

### From Sprint 102 (Type Aliasing)

- **Strawberry type names can differ**: Use `Annotated` to alias types when Python name differs from GraphQL name
- **Avoid naming conflicts**: Prefix internal types with `GQL` or `Type` to avoid conflicts

### From Multiple Sprints

- **DataLoaders are per-request**: Never reuse DataLoaders across requests (caching would leak data)
- **Private fields useful**: Use `strawberry.Private[]` for fields needed for resolution but not exposed in schema
- **Error handling patterns**: Return union types or payload objects with errors field
- **N+1 testing critical**: Always test queries with `EXPLAIN ANALYZE` to catch N+1 problems

## Anti-Patterns

### Don't: Query Database Directly in Field Resolver

**What it looks like**:
```python
@strawberry.field
async def parent(self, info: strawberry.Info) -> Optional[Asset]:
    # Bad - direct query in resolver causes N+1
    stmt = select(AssetModel).where(AssetModel.uuid == self.parent_id)
    result = await info.context.session.execute(stmt)
    return Asset.from_orm(result.scalar_one())
```

**Why it's bad**: If querying 100 assets, this runs 100 additional queries (N+1 problem).

**Instead**: Use DataLoader to batch queries.

### Don't: Return SQLAlchemy Models Directly

**What it looks like**:
```python
@strawberry.field
async def asset(self, id: UUID) -> AssetModel:  # Bad - returns ORM model
    return session.get(AssetModel, id)
```

**Why it's bad**: Exposes internal database structure, breaks abstraction, can't add computed fields.

**Instead**: Convert to Strawberry types using `.from_orm()`.

### Don't: Ignore Query Complexity

**What it looks like**:
```graphql
# Bad - deeply nested query can DOS the server
query {
  assets {
    children {
      children {
        children {
          measurements(first: 1000) { ... }
        }
      }
    }
  }
}
```

**Why it's bad**: Exponential query explosion can crash server.

**Instead**: Implement query depth/complexity limits using Strawberry extensions.

### Don't: Use Sync Functions in Async Context

**What it looks like**:
```python
@strawberry.field
def measurements(self) -> list[Measurement]:  # Bad - sync function
    # Blocks event loop
    return session.execute(stmt).scalars().all()
```

**Why it's bad**: Blocks async event loop, kills performance.

**Instead**: Always use `async def` for resolvers that do I/O.

## Variations

### For Relay-Style Pagination

```python
@strawberry.type
class AssetEdge:
    node: Asset
    cursor: str

@strawberry.type
class AssetConnection:
    edges: list[AssetEdge]
    page_info: PageInfo
    total_count: int

@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str]
    end_cursor: Optional[str]
```

### For Subscriptions (Real-Time)

```python
import strawberry
from typing import AsyncGenerator

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def measurement_created(
        self,
        asset_id: UUID
    ) -> AsyncGenerator[Measurement, None]:
        """Stream measurements as they're created."""
        # Subscribe to Redis pub/sub or similar
        async for message in pubsub.listen(f"measurements:{asset_id}"):
            yield Measurement.from_dict(message)
```

### For File Uploads

```python
from strawberry.file_uploads import Upload

@strawberry.mutation
async def upload_document(
    self,
    info: strawberry.Info,
    file: Upload,
    asset_id: UUID
) -> Document:
    """Upload document attached to asset."""
    contents = await file.read()
    # Process file...
    return Document(...)
```

## Related Recipes

- [Three-Layer Database](./three-layer-database.md) - Database layer GraphQL queries
- [Provider Pattern](./provider-pattern.md) - External data in GraphQL
- [Domain Model Layering](./domain-model-layering.md) - Converting ORM to GraphQL types

## Verification

### Test DataLoader Batching

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_dataloader_batches_queries(graphql_client):
    # Execute query that fetches 10 assets with their parents
    query = """
        query {
            assets(first: 10) {
                id
                name
                parent {
                    id
                    name
                }
            }
        }
    """

    with patch('corrdata.api.graphql.dataloaders.select') as mock_select:
        result = await graphql_client.execute(query)

        # DataLoader should batch into single query, not 10 queries
        assert mock_select.call_count == 1  # Not 10!
```

### Test Schema Generation

```bash
# Generate schema.graphql file
strawberry export-schema corrdata.api.graphql.schema:schema > schema.graphql

# Verify it contains expected types
grep "type Asset" schema.graphql
grep "type Query" schema.graphql
```

### Test Frontend Code Generation

```bash
# Generate TypeScript types
npm run codegen

# Verify generated types
cat packages/web-app/src/generated/graphql.ts | grep "GetAssetQuery"
```

## Session Factory Pattern (Sprint 133)

### The Problem

SQLAlchemy's `AsyncSession` is **NOT safe for concurrent coroutine access**. When Strawberry resolves multiple root-level query fields in parallel (e.g., `riskAnalysis` and `trends`), they share the same session and cause:

```
This session is provisioning a new connection; concurrent operations are not permitted
```

### The Solution

Use a **session factory** instead of a pre-created session in the GraphQL context:

```python
# src/corrdata/graphql/context.py
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, Callable, AsyncContextManager

@dataclass
class GraphQLContext:
    """GraphQL context with session factory for parallel-safe resolution."""

    # Session factory - creates new session on demand
    get_session: Callable[[], AsyncContextManager[AsyncSession]]

    # Auth context (unchanged)
    user_uuid: UUID | None
    tenant_id: UUID | None
    is_authenticated: bool
    # ...


def create_session_factory(tenant_id: UUID | None, user_uuid: UUID | None):
    """Create a session factory that sets tenant context."""

    @asynccontextmanager
    async def session_factory() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            # Set PostgreSQL session variables for RLS
            if tenant_id:
                await session.execute(
                    text("SET LOCAL app.current_tenant_id = :tid"),
                    {"tid": str(tenant_id)}
                )
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    return session_factory
```

### Resolver Usage

```python
@strawberry.field
async def risk_analysis(self, info: Info[GraphQLContext, None], top_n: int = 10) -> RiskAnalysis:
    """Each resolver gets its own session."""
    ctx = info.context

    async with ctx.get_session() as db:
        loader = AnalyticsLoader(db)
        risk_points, total = await loader.calculate_risk_for_assets(limit=1000)
        # ... resolver logic
```

### Why This Works

```
BEFORE (single session - broken):
┌─────────────┐     ┌─────────────┐
│ riskAnalysis│     │   trends    │   Both use same session
└──────┬──────┘     └──────┬──────┘   concurrently = ERROR
       └───────┬───────────┘
               ▼
        ❌ Session Error

AFTER (session factory - safe):
┌─────────────┐     ┌─────────────┐
│ riskAnalysis│     │   trends    │   Each creates own session
└──────┬──────┘     └──────┬──────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│  Session A  │     │  Session B  │   Isolated = SAFE
└─────────────┘     └─────────────┘
```

### Connection Pool Considerations

With session factory, a query with N parallel resolvers may use N connections:

```python
# Recommended pool configuration for parallel resolvers
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Increase from default 5
    max_overflow=10,     # Allow burst to 30 total
    pool_pre_ping=True,
)
```

### References

- [ADR-050: GraphQL Session Factory Pattern](../../architecture/decisions/ADR-050-graphql-session-factory-pattern.md)
- [Sprint 133: Implementation](../../sprints/1-todo/sprint-133_graphql-session-factory.md)
- [SQLAlchemy AsyncSession Concurrent Tasks](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncsession-with-concurrent-tasks)

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2025-12-15 | Added Session Factory Pattern (Sprint 133, ADR-050) |
| 1.0 | 2025-12-14 | Initial version based on ADR-002, ADR-038, Sprint 94, Sprint 102 |
