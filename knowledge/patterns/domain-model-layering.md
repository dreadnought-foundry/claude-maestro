# Recipe: Domain Model Layering

**Category**: pattern
**Version**: 1.0
**Last Updated**: 2025-12-14
**Sprints**: Sprint 102 (Strawberry aliasing), Multiple (foundation)
**ADRs**: [ADR-022](../../architecture/decisions/ADR-022-dataclass-domain-models.md), [ADR-011](../../architecture/decisions/ADR-011-sqlalchemy-2-orm.md)

## Context

**When to use this recipe:**
- Building systems with multiple data representation layers (DB, API, domain logic, ML)
- Converting between SQLAlchemy ORM, Pydantic, Strawberry, and dataclass models
- Maintaining clean separation between database structure and business logic
- Supporting different serialization formats (JSON, protobuf, etc.)
- Keeping API responses independent of database schema changes

**When NOT to use this recipe:**
- Simple CRUD apps where database schema = API schema
- Prototypes where schema stability isn't important
- Systems with a single data representation layer
- When direct ORM exposure is acceptable

## Ingredients

Before starting, ensure you have:

- [ ] SQLAlchemy 2.0 models defined (`Mapped[]` types)
- [ ] Understanding of Python type hints
- [ ] Knowledge of dataclasses, Pydantic, and Strawberry (if using GraphQL)
- [ ] Clear separation of concerns in your architecture
- [ ] Conversion function patterns established

## Overview

CorrData uses four primary data structure patterns, each with a specific purpose:

```
┌─────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYERS                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  LAYER 1: SQLAlchemy ORM Models                            │ │
│  │  Purpose: Database persistence                             │ │
│  │  Example: Asset, Measurement, Event                        │ │
│  │  Location: src/corrdata/db/models.py                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓ from_orm()                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  LAYER 2: Domain Dataclasses                               │ │
│  │  Purpose: Business logic, ML inputs, internal APIs         │ │
│  │  Example: RiskScore, SoilCorrosivityInput                  │ │
│  │  Location: src/corrdata/domain/, src/corrdata/twin/        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                      ↙ to_response()  ↘ to_graphql()            │
│  ┌─────────────────────────┐  ┌──────────────────────────────┐ │
│  │  LAYER 3A: Pydantic     │  │  LAYER 3B: Strawberry        │ │
│  │  Purpose: REST API      │  │  Purpose: GraphQL API        │ │
│  │  Example: AssetResponse │  │  Example: Asset (GraphQL)    │ │
│  │  Location: api/types.py │  │  Location: api/graphql/      │ │
│  └─────────────────────────┘  └──────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Steps

### Step 1: Define SQLAlchemy ORM Model

Start with the database layer using SQLAlchemy 2.0:

```python
# src/corrdata/db/models.py
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Numeric, TIMESTAMP, ForeignKey, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass

class Asset(Base):
    """
    ORM model for pipeline assets.
    Maps directly to 'assets' table in PostgreSQL.
    """
    __tablename__ = "assets"

    # Primary key
    uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Core attributes (match database columns)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Geometry (PostGIS)
    geometry = mapped_column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True)

    # Foreign keys
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.uuid"), nullable=False)
    parent_uuid: Mapped[Optional[UUID]] = mapped_column(ForeignKey("assets.uuid"), nullable=True)

    # Temporal validity
    valid_from: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    valid_to: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Metadata (flexible JSON)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    measurements: Mapped[list["Measurement"]] = relationship(back_populates="asset")
    parent: Mapped[Optional["Asset"]] = relationship(remote_side=[uuid], back_populates="children")
    children: Mapped[list["Asset"]] = relationship(back_populates="parent")

    def __repr__(self) -> str:
        return f"<Asset(uuid={self.uuid}, name={self.name}, type={self.asset_type})>"
```

**Expected outcome**: ORM model with full type hints, relationships, and database mappings.

### Step 2: Create Domain Dataclass

Define business logic layer using dataclasses:

```python
# src/corrdata/domain/asset.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

class AssetType(Enum):
    """Asset type enumeration (domain model)."""
    SEGMENT = "segment"
    TEST_STATION = "test_station"
    RECTIFIER = "rectifier"
    BOND = "bond"
    ANODE_BED = "anode_bed"

class AssetStatus(Enum):
    """Asset status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    RETIRED = "retired"
    PLANNED = "planned"

@dataclass
class AssetDomain:
    """
    Domain model for pipeline assets.
    Used for business logic, not directly tied to database schema.
    """
    uuid: UUID
    name: str
    type: AssetType
    status: AssetStatus
    description: Optional[str] = None
    tenant_id: UUID = field(repr=False)  # Present but not shown in repr
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Computed properties
    risk_score: Optional[float] = None
    compliance_status: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """Check if asset is currently active."""
        return self.status == AssetStatus.ACTIVE

    @property
    def is_critical_infrastructure(self) -> bool:
        """Check if asset is critical infrastructure (segment or rectifier)."""
        return self.type in [AssetType.SEGMENT, AssetType.RECTIFIER]

    def calculate_age_years(self) -> float:
        """Calculate asset age in years."""
        age = datetime.utcnow() - self.created_at
        return age.days / 365.25

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "uuid": str(self.uuid),
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "description": self.description,
            "risk_score": self.risk_score,
            "compliance_status": self.compliance_status,
            "age_years": self.calculate_age_years(),
        }
```

**Expected outcome**: Domain model with business logic methods, independent of database structure.

### Step 3: Create Conversion Functions

Build converters between layers:

```python
# src/corrdata/domain/converters.py
from typing import Optional
from corrdata.db.models import Asset as AssetORM
from corrdata.domain.asset import AssetDomain, AssetType, AssetStatus

def orm_to_domain(orm_model: AssetORM) -> AssetDomain:
    """
    Convert SQLAlchemy ORM model to domain model.

    Args:
        orm_model: SQLAlchemy Asset model

    Returns:
        Domain AssetDomain object
    """
    return AssetDomain(
        uuid=orm_model.uuid,
        name=orm_model.name,
        type=AssetType(orm_model.asset_type),
        status=AssetStatus(orm_model.status),
        description=orm_model.description,
        tenant_id=orm_model.tenant_id,
        created_at=orm_model.created_at,
        # Computed fields would be populated separately
        risk_score=None,
        compliance_status=None,
    )

def domain_to_orm(domain_model: AssetDomain) -> AssetORM:
    """
    Convert domain model to SQLAlchemy ORM model.
    Use when creating new database records from domain objects.

    Args:
        domain_model: Domain AssetDomain object

    Returns:
        SQLAlchemy Asset model
    """
    return AssetORM(
        uuid=domain_model.uuid,
        name=domain_model.name,
        asset_type=domain_model.type.value,
        status=domain_model.status.value,
        description=domain_model.description,
        tenant_id=domain_model.tenant_id,
        created_at=domain_model.created_at,
    )

def orm_list_to_domain_list(orm_models: list[AssetORM]) -> list[AssetDomain]:
    """Batch convert ORM models to domain models."""
    return [orm_to_domain(m) for m in orm_models]
```

**Expected outcome**: Type-safe conversion functions between ORM and domain layers.

### Step 4: Define Pydantic Model for REST API

Create Pydantic model for REST request/response validation:

```python
# src/corrdata/api/schemas/asset.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class AssetResponse(BaseModel):
    """
    REST API response model for assets.
    Used for JSON serialization in REST endpoints.
    """
    model_config = ConfigDict(
        from_attributes=True,  # Enable from_orm() conversion
        json_schema_extra={
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Segment A-1",
                "type": "segment",
                "status": "active",
                "risk_score": 45.2,
            }
        }
    )

    uuid: UUID
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., description="Asset type")
    status: str = Field(..., description="Current status")
    description: Optional[str] = None
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    compliance_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Computed fields
    age_years: Optional[float] = None

class AssetCreateRequest(BaseModel):
    """Request model for creating new assets."""
    model_config = ConfigDict(strict=True)

    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern="^(segment|test_station|rectifier|bond|anode_bed)$")
    description: Optional[str] = Field(None, max_length=1000)
    parent_uuid: Optional[UUID] = None

    # Pydantic validators
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()

def domain_to_response(domain: AssetDomain) -> AssetResponse:
    """Convert domain model to REST API response."""
    return AssetResponse(
        uuid=domain.uuid,
        name=domain.name,
        type=domain.type.value,
        status=domain.status.value,
        description=domain.description,
        risk_score=domain.risk_score,
        compliance_status=domain.compliance_status,
        created_at=domain.created_at,
        updated_at=domain.created_at,  # Would come from ORM
        age_years=domain.calculate_age_years(),
    )
```

**Expected outcome**: Pydantic models with validation for REST API.

### Step 5: Define Strawberry Type for GraphQL

Create GraphQL type using Strawberry:

```python
# src/corrdata/api/graphql/types/asset.py
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID
import strawberry
from strawberry import Private

if TYPE_CHECKING:
    from corrdata.api.graphql.types.measurement import Measurement

@strawberry.enum
class AssetTypeGQL(str, Enum):
    """GraphQL enum for asset types."""
    SEGMENT = "segment"
    TEST_STATION = "test_station"
    RECTIFIER = "rectifier"
    BOND = "bond"
    ANODE_BED = "anode_bed"

@strawberry.enum
class AssetStatusGQL(str, Enum):
    """GraphQL enum for asset status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    RETIRED = "retired"
    PLANNED = "planned"

@strawberry.type
class Asset:
    """
    GraphQL type for pipeline assets.
    Exposed via GraphQL API, supports nested queries.
    """
    id: UUID = strawberry.field(description="Unique identifier")
    name: str = strawberry.field(description="Asset name")
    type: AssetTypeGQL = strawberry.field(description="Asset type")
    status: AssetStatusGQL = strawberry.field(description="Current status")
    description: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    # Private fields (not exposed in schema)
    tenant_id: Private[UUID]
    parent_id: Private[Optional[UUID]]

    @strawberry.field
    def risk_score(self) -> Optional[float]:
        """Computed risk score (0-100)."""
        # Would call risk scoring service
        return None

    @strawberry.field
    def age_years(self) -> float:
        """Age of asset in years."""
        age = datetime.utcnow() - self.created_at
        return age.days / 365.25

    @strawberry.field
    async def measurements(
        self,
        info: strawberry.Info,
        first: int = 10
    ) -> list["Measurement"]:
        """Recent measurements for this asset (uses DataLoader)."""
        loader = info.context.loaders.measurements
        return await loader.load((self.id, first))

    @classmethod
    def from_orm(cls, orm_model: "AssetORM") -> "Asset":
        """Convert SQLAlchemy model to GraphQL type."""
        from corrdata.domain.asset import AssetType, AssetStatus

        return cls(
            id=orm_model.uuid,
            name=orm_model.name,
            type=AssetTypeGQL(orm_model.asset_type),
            status=AssetStatusGQL(orm_model.status),
            description=orm_model.description,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
            tenant_id=orm_model.tenant_id,
            parent_id=orm_model.parent_uuid,
        )

    @classmethod
    def from_domain(cls, domain: AssetDomain) -> "Asset":
        """Convert domain model to GraphQL type."""
        return cls(
            id=domain.uuid,
            name=domain.name,
            type=AssetTypeGQL(domain.type.value),
            status=AssetStatusGQL(domain.status.value),
            description=domain.description,
            created_at=domain.created_at,
            updated_at=domain.created_at,
            tenant_id=domain.tenant_id,
            parent_id=None,  # Would need to be passed separately
        )
```

**Expected outcome**: Strawberry type with nested resolvers and computed fields.

### Step 6: Implement ML Input Dataclass

Create specialized dataclass for ML/analytics:

```python
# src/corrdata/twin/risk_scoring.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SoilCorrosivityInput:
    """
    Input for soil corrosivity assessment.
    Pure data container for ML model.
    """
    resistivity_ohm_cm: float
    ph: Optional[float] = None
    chlorides_ppm: Optional[float] = None
    sulfates_ppm: Optional[float] = None
    moisture_percent: Optional[float] = None

    def get_corrosivity_class(self) -> str:
        """
        Classify soil corrosivity based on resistivity.
        Business logic in domain dataclass.
        """
        if self.resistivity_ohm_cm < 1000:
            return "severely_corrosive"
        elif self.resistivity_ohm_cm < 2000:
            return "corrosive"
        elif self.resistivity_ohm_cm < 5000:
            return "moderately_corrosive"
        elif self.resistivity_ohm_cm < 10000:
            return "mildly_corrosive"
        else:
            return "non_corrosive"

    def is_high_risk(self) -> bool:
        """Check if soil conditions indicate high corrosion risk."""
        if self.resistivity_ohm_cm < 2000:
            return True
        if self.ph and self.ph < 5.5:
            return True
        if self.chlorides_ppm and self.chlorides_ppm > 500:
            return True
        return False

@dataclass
class RiskScoringInput:
    """
    Combined input for risk scoring model.
    Aggregates data from multiple sources.
    """
    asset_uuid: UUID
    soil_corrosivity: SoilCorrosivityInput
    cp_effectiveness: Optional[float] = None  # -850 mV criterion
    coating_condition: Optional[float] = None  # 0-1 scale
    pipe_age_years: Optional[float] = None
    ili_anomaly_count: int = 0
    environmental_factors: Optional[dict] = None

    def to_feature_vector(self) -> dict[str, float]:
        """Convert to flat feature vector for ML model."""
        return {
            "resistivity": self.soil_corrosivity.resistivity_ohm_cm,
            "ph": self.soil_corrosivity.ph or 7.0,
            "chlorides": self.soil_corrosivity.chlorides_ppm or 0.0,
            "cp_effectiveness": self.cp_effectiveness or 0.0,
            "coating_condition": self.coating_condition or 0.5,
            "age_years": self.pipe_age_years or 0.0,
            "anomaly_count": float(self.ili_anomaly_count),
        }
```

**Expected outcome**: Specialized dataclasses for ML inputs with feature extraction methods.

## Code Examples

### Complete Conversion Flow

```python
# Example: Database → Domain → API Response
from corrdata.db.models import Asset as AssetORM
from corrdata.domain.converters import orm_to_domain
from corrdata.api.schemas.asset import domain_to_response

async def get_asset_for_api(session, asset_uuid: UUID) -> AssetResponse:
    """Fetch asset from DB and convert to API response."""

    # Layer 1: Fetch from database (ORM)
    stmt = select(AssetORM).where(AssetORM.uuid == asset_uuid)
    result = await session.execute(stmt)
    orm_model = result.scalar_one()

    # Layer 2: Convert to domain model
    domain_model = orm_to_domain(orm_model)

    # Calculate risk score (domain logic)
    domain_model.risk_score = calculate_risk_score(domain_model)

    # Layer 3: Convert to API response
    response = domain_to_response(domain_model)

    return response
```

### Batch Conversion with Enrichment

```python
async def get_assets_with_risk_scores(
    session,
    asset_type: str,
    limit: int = 100
) -> list[AssetResponse]:
    """Fetch assets and enrich with computed data."""

    # Fetch from database
    stmt = (
        select(AssetORM)
        .where(AssetORM.asset_type == asset_type)
        .limit(limit)
    )
    result = await session.execute(stmt)
    orm_models = result.scalars().all()

    # Convert to domain models
    domain_models = [orm_to_domain(m) for m in orm_models]

    # Enrich with risk scores (parallel computation)
    risk_scores = await asyncio.gather(*[
        calculate_risk_score_async(d) for d in domain_models
    ])

    for domain_model, risk_score in zip(domain_models, risk_scores):
        domain_model.risk_score = risk_score

    # Convert to API responses
    return [domain_to_response(d) for d in domain_models]
```

### Type Aliasing Pattern (Sprint 102)

```python
# When Strawberry type name should differ from Python class
from typing import Annotated
import strawberry

# Define alias
AssetGQL = Annotated[Asset, strawberry.type(name="Asset")]

# Use in schema
@strawberry.type
class Query:
    @strawberry.field
    async def assets(self) -> list[AssetGQL]:
        """Returns Asset type in GraphQL schema."""
        return [Asset.from_orm(m) for m in models]
```

## Learnings

### From Sprint 102 (Strawberry Type Aliasing)

- **Name conflicts resolved**: Use `Annotated` to alias GraphQL types when names conflict
- **Separate namespaces**: Domain classes can have same name as GraphQL types
- **IDE support maintained**: Type hints still work with aliasing

### From Multiple Sprints

- **Dataclasses for domain logic**: Best for internal business logic and ML inputs
- **Pydantic for validation**: Essential for REST API request/response validation
- **Strawberry for GraphQL**: Provides resolvers and nested query support
- **ORM for persistence**: SQLAlchemy models stay close to database schema
- **Conversion overhead**: Small (<1ms) for typical models, batch when possible

## Anti-Patterns

### Don't: Expose ORM Models Directly in API

**What it looks like**:
```python
# Bad - returns SQLAlchemy model directly
@app.get("/assets/{uuid}")
async def get_asset(uuid: UUID) -> Asset:  # ORM model
    return session.get(Asset, uuid)
```

**Why it's bad**:
- Exposes internal database structure
- No control over serialization
- Breaks when schema changes
- Can leak sensitive data (passwords, internal IDs)

**Instead**: Convert to Pydantic response model.

### Don't: Duplicate Business Logic Across Layers

**What it looks like**:
```python
# Bad - age calculation in multiple places
# In ORM model
class Asset(Base):
    def age_years(self):
        return (datetime.now() - self.created_at).days / 365

# In Pydantic model
class AssetResponse(BaseModel):
    def age_years(self):
        return (datetime.now() - self.created_at).days / 365  # Duplicate!
```

**Why it's bad**: Logic drift, harder to maintain, inconsistent results.

**Instead**: Centralize business logic in domain dataclass.

### Don't: Mix Validation with ORM Models

**What it looks like**:
```python
# Bad - validation in ORM model
class Asset(Base):
    @validates('name')
    def validate_name(self, key, value):
        if len(value) < 3:
            raise ValueError("Name too short")
        return value
```

**Why it's bad**: Database layer shouldn't know about business rules, makes testing harder.

**Instead**: Use Pydantic for request validation, domain dataclass for business rules.

### Don't: Create Circular Conversion Dependencies

**What it looks like**:
```python
# Bad - circular conversion
def orm_to_domain(orm):
    domain = AssetDomain(...)
    domain.risk = domain_to_risk_score(domain)  # Calls back to domain
    return domain
```

**Why it's bad**: Creates circular dependencies, hard to test.

**Instead**: Convert first, then enrich with computed fields.

## Variations

### For Read-Only DTOs

```python
from dataclasses import dataclass

@dataclass(frozen=True)  # Immutable
class AssetDTO:
    """Read-only data transfer object."""
    uuid: UUID
    name: str
    type: str

    # No methods that modify state
```

### For Complex Nested Conversions

```python
def orm_to_domain_with_relations(orm_model: AssetORM) -> AssetDomain:
    """Convert ORM with eager-loaded relationships."""
    domain = orm_to_domain(orm_model)

    # Convert relationships
    if orm_model.parent:
        domain.parent = orm_to_domain(orm_model.parent)

    domain.children = [
        orm_to_domain(child) for child in orm_model.children
    ]

    return domain
```

### For Partial Updates

```python
from pydantic import BaseModel

class AssetUpdateRequest(BaseModel):
    """Partial update request (all fields optional)."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

    def apply_to_orm(self, orm_model: AssetORM) -> AssetORM:
        """Apply partial update to ORM model."""
        if self.name is not None:
            orm_model.name = self.name
        if self.description is not None:
            orm_model.description = self.description
        if self.status is not None:
            orm_model.status = self.status
        return orm_model
```

## Related Recipes

- [Three-Layer Database](./three-layer-database.md) - ORM models for database layer
- [GraphQL Schema Design](./graphql-schema.md) - Strawberry types and conversions
- [Provider Pattern](./provider-pattern.md) - External data to domain models

## Verification

### Test Conversion Functions

```python
import pytest
from corrdata.db.models import Asset as AssetORM
from corrdata.domain.converters import orm_to_domain, domain_to_orm

def test_orm_to_domain_conversion():
    """Test ORM → Domain conversion."""
    orm = AssetORM(
        uuid=uuid4(),
        name="Test Asset",
        asset_type="segment",
        status="active",
        tenant_id=uuid4(),
    )

    domain = orm_to_domain(orm)

    assert domain.uuid == orm.uuid
    assert domain.name == orm.name
    assert domain.type.value == orm.asset_type

def test_roundtrip_conversion():
    """Test ORM → Domain → ORM preserves data."""
    original_orm = AssetORM(
        uuid=uuid4(),
        name="Test",
        asset_type="segment",
        status="active",
        tenant_id=uuid4(),
    )

    domain = orm_to_domain(original_orm)
    converted_orm = domain_to_orm(domain)

    assert converted_orm.uuid == original_orm.uuid
    assert converted_orm.name == original_orm.name
    assert converted_orm.asset_type == original_orm.asset_type
```

### Verify Schema Consistency

```python
def test_pydantic_strawberry_schema_consistency():
    """Ensure Pydantic and Strawberry types have same fields."""
    from corrdata.api.schemas.asset import AssetResponse
    from corrdata.api.graphql.types.asset import Asset

    pydantic_fields = set(AssetResponse.model_fields.keys())
    strawberry_fields = {
        f.name for f in Asset.__strawberry_definition__.fields
        if not f.name.startswith("_")
    }

    # Core fields should match
    common_fields = {"uuid", "name", "type", "status"}
    assert common_fields.issubset(pydantic_fields)
    assert common_fields.issubset(strawberry_fields)
```

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-14 | Initial version based on ADR-022, ADR-011, Sprint 102 |
