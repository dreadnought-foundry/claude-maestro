# Coding Standards

This document defines the coding standards for the CorrData project. All contributors must follow these standards to ensure consistency and prevent bugs.

## Python Standards

### General

- **Python Version**: 3.11+
- **Linting/Formatting**: Ruff (configured in `pyproject.toml`)
- **Type Hints**: Required for all function signatures
- **Docstrings**: Required for public functions and classes

### SQLAlchemy

- Use SQLAlchemy 2.0 style with `mapped_column` and `Mapped` types
- Always use async sessions (`AsyncSession`)
- Use the session factory pattern for database access

```python
# CORRECT - SQLAlchemy 2.0 style
class Asset(Base):
    __tablename__ = "assets"

    uuid: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)

# WRONG - SQLAlchemy 1.x style
class Asset(Base):
    __tablename__ = "assets"

    uuid = Column(UUID, primary_key=True)
    name = Column(String(255), nullable=False)
```

### Type Field Comparisons (Sprint 133)

**CRITICAL**: Database stores type fields in UPPERCASE (e.g., `PIPELINE`, `SEGMENT`, `TEST_STATION`). Frontend may send lowercase.

Always use case-insensitive comparison for type fields:

```python
from sqlalchemy import func

# CORRECT - handles any case from frontend
if asset_type:
    stmt = stmt.where(func.upper(AssetModel.type) == asset_type.upper())

# ALSO CORRECT - for in-memory filtering
if asset_type:
    assets = [a for a in assets if a.type.upper() == asset_type.upper()]

# WRONG - case-sensitive, will fail if frontend sends lowercase
if asset_type:
    stmt = stmt.where(AssetModel.type == asset_type)
```

**Affected fields**:
- `asset_type` / `AssetModel.type`
- `event_type` / `EventModel.event_type`
- `measurement_type` / `MeasurementModel.measurement_type`
- `reading_type` / `FieldReadingModel.reading_type`
- `work_type` / `WorkOrderModel.work_type`

### Multi-Tenancy (Sprint 133)

All tenant-scoped models must inherit from `TenantMixin`:

```python
from corrdata.db.mixins import TenantMixin

class WorkOrder(Base, TenantMixin):
    """Work orders are scoped to a tenant."""
    __tablename__ = "work_orders"
    # ... fields
```

All queries on tenant-scoped tables must filter by `tenant_uuid`:

```python
# CORRECT - filtered by tenant
if self.tenant_id:
    stmt = stmt.where(AssetModel.tenant_uuid == self.tenant_id)

# WRONG - returns data from all tenants
stmt = select(AssetModel)  # Missing tenant filter!
```

### Async Patterns

Use `async`/`await` consistently:

```python
# CORRECT
async def get_asset(self, id: UUID) -> Asset | None:
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()

# WRONG - blocking call in async context
def get_asset(self, id: UUID) -> Asset | None:
    result = self.session.execute(stmt)  # Blocking!
    return result.scalar_one_or_none()
```

---

## Frontend Standards (TypeScript/React)

### General

- **TypeScript**: Strict mode enabled
- **React**: Functional components with hooks
- **State Management**: React Context + Apollo Client cache
- **Styling**: Tailwind CSS

### GraphQL Queries

Always specify `fetchPolicy` for queries that need fresh data:

```typescript
// CORRECT - for data that should always be fresh
const { data, loading } = useQuery(ASSETS_QUERY, {
  fetchPolicy: "network-only",
})

// CORRECT - for data that can be cached but should refresh on navigation
const { data, loading } = useQuery(ASSETS_QUERY, {
  fetchPolicy: "cache-and-network",
})
```

### Tenant Header

The Apollo client automatically sends `X-Tenant-ID` header from localStorage:

```typescript
// Set by tenant selection
localStorage.setItem('selectedTenantId', tenantId)

// Read by Apollo client in authLink
const tenantId = localStorage.getItem('selectedTenantId')
headers['X-Tenant-ID'] = tenantId
```

After changing tenant, reload the page to clear Apollo cache:

```typescript
localStorage.setItem('selectedTenantId', newTenantId)
window.location.reload()  // Required to clear cached data
```

---

## Database Standards

### Migrations

- Use Alembic for all schema changes
- Never modify production data in migrations (use separate scripts)
- Always include `down_revision` to maintain migration chain

```python
# In alembic/versions/xxx_migration_name.py
revision = "abc123"
down_revision = "xyz789"  # Previous migration

def upgrade():
    op.add_column("assets", sa.Column("new_field", sa.String(100)))

def downgrade():
    op.drop_column("assets", "new_field")
```

### Naming Conventions

| Entity | Convention | Example |
|--------|------------|---------|
| Tables | snake_case, plural | `work_orders`, `field_readings` |
| Columns | snake_case | `tenant_uuid`, `created_at` |
| Indexes | `ix_{table}_{column}` | `ix_assets_tenant_uuid` |
| Foreign Keys | `fk_{table}_{column}` | `fk_work_orders_asset_uuid` |

### UUID Primary Keys

All tables use UUID primary keys:

```python
uuid: Mapped[UUID] = mapped_column(
    PG_UUID(as_uuid=True),
    primary_key=True,
    default=uuid4
)
```

---

## Testing Standards

### Coverage

- Minimum 75% coverage threshold
- All new features must include tests
- Sprint-specific tests in `tests/test_sprint{N}_*.py`

### Test Structure

```python
import pytest
from corrdata.db.session import async_session_factory

class TestAssetLoader:
    """Tests for the AssetLoader."""

    @pytest.fixture
    async def db(self):
        """Create database session for tests."""
        async with async_session_factory() as session:
            yield session

    @pytest.mark.asyncio
    async def test_load_asset_by_id(self, db):
        """Test loading a single asset by UUID."""
        # Arrange
        loader = AssetLoader(db, tenant_id=SEED_TENANT_UUID)

        # Act
        asset = await loader.load(known_asset_id)

        # Assert
        assert asset is not None
        assert asset.name == "Expected Name"
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/corrdata --cov-report=term-missing

# Run specific sprint tests
pytest tests/test_sprint133_*.py -v

# Skip integration tests
pytest tests/ --ignore=tests/integration
```

---

## Git Standards

### Commit Messages

Use conventional commit format:

```
feat: Add tenant selection for SuperAdmins
fix: Case-insensitive asset type comparison
docs: Update coding standards
refactor: Extract session factory pattern
test: Add tenant isolation tests
```

### Branch Naming

```
feature/sprint-133-tenant-isolation
bugfix/case-sensitive-asset-type
docs/coding-standards
```

### Pre-Commit Checks

Run before pushing:

```bash
# Quick validation
pytest tests/test_smoke_imports.py -v --no-cov

# Full test suite
./scripts/run-parallel-tests.sh
```

---

## Security Standards

### Never Commit Secrets

- Use environment variables for secrets
- Never commit `.env` files
- Check for secrets before committing

### SQL Injection Prevention

Always use parameterized queries:

```python
# CORRECT - parameterized
stmt = text("SELECT * FROM assets WHERE tenant_uuid = :tenant_uuid")
result = await db.execute(stmt, {"tenant_uuid": tenant_id})

# WRONG - string interpolation (SQL injection risk!)
stmt = text(f"SELECT * FROM assets WHERE tenant_uuid = '{tenant_id}'")
```

### Tenant Isolation

All data access must respect tenant boundaries. Never allow cross-tenant data access except for SuperAdmins with explicit tenant selection.
