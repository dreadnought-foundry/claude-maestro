# Recipe: Session Factory Testing Pattern

**Category**: pattern
**Version**: 1.0
**Last Updated**: 2025-12-15
**Sprints**: Sprint 133 (GraphQL Session Factory), Sprint 139 (Test Fixtures)

## Context

**When to use this recipe:**
- Writing integration tests that need GraphQL context
- Testing mutations or queries that use `async with ctx.get_session() as db`
- Creating mock contexts for unit tests of GraphQL resolvers
- Testing code that was written after Sprint 133

**When NOT to use this recipe:**
- Unit tests that don't need database access
- Tests for non-GraphQL code (use `async_db_session` fixture directly)
- Code written before Sprint 133 that uses `ctx.db` directly (needs migration)

## Ingredients

Before starting, ensure you have:

- [ ] PostgreSQL test database running (`docker-compose up -d`)
- [ ] pytest-asyncio installed
- [ ] Access to `tests/integration/conftest.py`

## Background

Sprint 133 changed `GraphQLContext` from accepting a database session directly (`db=session`) to requiring a session factory (`get_session=factory`). This enables parallel-safe GraphQL execution but requires test fixtures to provide a factory instead of a raw session.

The `get_session` parameter expects:
- A callable (function) that returns an async context manager
- The context manager yields an `AsyncSession`

## Steps

### Step 1: Use the `get_session_factory` Fixture

In your test file, use the `get_session_factory` fixture from conftest:

```python
@pytest.fixture
async def graphql_context(get_session_factory, test_user, test_tenant):
    """Create GraphQL context for tests."""
    from corrdata.graphql.context import GraphQLContext

    return GraphQLContext(
        get_session=get_session_factory,  # Factory, not raw session
        user=test_user,
        user_uuid=test_user.uuid,
        tenant_id=test_tenant.uuid,
        is_authenticated=True,
    )
```

**Expected outcome**: A `GraphQLContext` that can be used in tests without `TypeError`

### Step 2: Use Session in Tests

When testing code that uses the session factory pattern:

```python
@pytest.mark.asyncio
async def test_query_with_session(graphql_context):
    """Test a query that uses get_session()."""
    from corrdata.graphql.loaders import DataLoaders

    # Inside test, use the same pattern as production code
    async with graphql_context.get_session() as db:
        loaders = DataLoaders.create(db, tenant_id=graphql_context.tenant_id)
        result = await loaders.asset.load(some_uuid)
        assert result is not None
```

**Expected outcome**: Session is available and transaction rolls back after test

### Step 3: Creating Mock Contexts for Unit Tests

For unit tests that don't need the full fixture chain:

```python
from contextlib import asynccontextmanager
from dataclasses import dataclass
from uuid import UUID

@dataclass
class MockContext:
    """Mock context for testing GraphQL mutations."""
    _db: AsyncSession
    user_uuid: UUID | None = None
    tenant_id: UUID | None = None
    is_authenticated: bool = False

    def get_session(self):
        """Return async context manager yielding the test session."""
        db = self._db

        @asynccontextmanager
        async def session_factory():
            yield db

        return session_factory()

    @property
    def db(self):
        """Backwards compatibility for code using ctx.db."""
        return self._db
```

**Expected outcome**: MockContext works with both old (`ctx.db`) and new (`ctx.get_session()`) patterns

## Verification

Run integration tests to verify the pattern works:

```bash
pytest tests/integration/test_sprint98_account_graphql.py -v --run-integration
```

Expected output:
```
tests/integration/test_sprint98_account_graphql.py::TestAccountSettingsQuery::test_account_settings_query_success PASSED
tests/integration/test_sprint98_account_graphql.py::TestAPIKeysQuery::test_api_keys_query_success PASSED
...
```

No `TypeError: GraphQLContext.__init__() got an unexpected keyword argument 'db'` errors.

## Learnings

### From Sprint 133
- Changed GraphQL to use session factories for parallel resolver execution
- `ctx.db` and `ctx.loaders` properties now raise `AttributeError`
- All resolvers must use `async with ctx.get_session() as db` pattern

### From Sprint 139
- Test fixtures must provide factories, not raw sessions
- MockContext needs both `get_session()` method AND `db` property for gradual migration
- Existing `async_db_session` fixture works well as the underlying session

## Anti-Patterns

### Don't: Pass Raw Sessions to GraphQLContext

**What it looks like**:
```python
# BROKEN - will raise TypeError
context = GraphQLContext(db=async_db_session)
```

**Why it's bad**: `GraphQLContext` no longer accepts `db` parameter since Sprint 133

**Instead**:
```python
# CORRECT - use session factory
context = GraphQLContext(get_session=get_session_factory)
```

### Don't: Create New Engines Per Test (Unless Necessary)

**What it looks like**:
```python
@pytest.fixture
async def my_session():
    engine = create_async_engine(URL)  # Creates new engine every test
    # ...
```

**Why it's bad**: Creates connection pool overhead, slower tests

**Instead**: Use the shared `async_db_session` fixture which reuses the engine but provides transaction isolation

## Variations

### For Tests That Need Direct Session Access

Some tests need to verify database state directly. Use both fixtures:

```python
@pytest.mark.asyncio
async def test_mutation_persists(graphql_context, async_db_session):
    """Test that mutation correctly persists to database."""
    # Run mutation through GraphQL context
    await some_mutation(info)

    # Verify directly in database
    result = await async_db_session.execute(
        select(SomeModel).where(SomeModel.id == expected_id)
    )
    assert result.scalar_one_or_none() is not None
```

### For Tests With Custom Tenant Context

```python
@pytest.fixture
async def tenant_graphql_context(get_session_factory, async_sample_tenant, async_sample_user):
    """Context with specific tenant for isolation tests."""
    return GraphQLContext(
        get_session=get_session_factory,
        user=async_sample_user,
        user_uuid=async_sample_user["uuid"],
        tenant_id=async_sample_tenant["uuid"],
        is_authenticated=True,
    )
```

## Related Recipes

- [GraphQL Schema Pattern](./graphql-schema.md)
- [Three-Layer Database Pattern](./three-layer-database.md)

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-15 | Initial version from Sprint 139 |
