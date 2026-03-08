# Seed Data Service Pattern

**Pattern Type:** Service Layer
**Sprint:** 144 - Consolidate Seed Data Service
**Related ADR:** ADR-055 - Consolidated Seed Data Service

## Overview

The Seed Data Service provides a **single source of truth** for generating realistic demo data in the seed tenant. It consolidates previously scattered data generation logic into a comprehensive, configurable service.

## When to Use

Use the Seed Data Service when you need to:

- Generate seed data for local development
- Reset demo environment via GraphQL admin panel
- Create consistent test fixtures
- Populate a fresh database with realistic data
- Test with varied risk profile distributions

## Key Concepts

### Single Responsibility

The service owns ALL seed data generation:
- Assets (pipelines, segments, test stations, rectifiers, etc.)
- Measurements (CP readings, rectifier data)
- Events (anomalies, maintenance)
- Users, roles, and technicians
- Compliance data (regulations, audits, documents)
- Work orders and alerts
- Risk profile assignment

### Configuration-Driven

Use `SeedDataConfig` to customize generation:

```python
from corrdata.services.seed_data_service import SeedDataConfig

config = SeedDataConfig(
    num_segments=12,              # Pipeline segments to create
    num_test_stations=24,         # Test stations
    num_rectifiers=12,            # Rectifiers
    num_anode_beds=12,            # Anode beds
    num_facilities=5,             # Facilities
    num_equipment=15,             # Equipment items
    create_users=True,            # Generate users and technicians
    create_compliance=True,       # Generate compliance data
    create_work_orders=True,      # Generate work orders
    create_alerts=True,           # Generate alerts
    random_seed=42                # For reproducibility
)
```

### Structured Results

The service returns `SeedDataResult` with detailed counts:

```python
result = await service.generate_all()

if result.success:
    print(f"Created {result.segments} segments")
    print(f"Created {result.measurements} measurements")
    print(f"Risk distribution: {result.profile_distribution}")
else:
    print(f"Error: {result.message}")
```

## Usage Examples

### Example 1: CLI Script (Default Configuration)

```python
#!/usr/bin/env python3
"""Generate seed data from CLI."""

import asyncio
from corrdata.db.session import async_session_factory, init_db
from corrdata.services.seed_data_service import generate_seed_data

async def main():
    await init_db()

    async with async_session_factory() as session:
        # Use defaults (12 segments, all features enabled)
        result = await generate_seed_data(session)

        if result.success:
            print(f"Success: {result.message}")
        else:
            print(f"Error: {result.message}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: GraphQL Mutation (Custom Configuration)

```python
from corrdata.services.seed_data_service import SeedDataConfig, SeedDataService

async def generate_seed_data_mutation(session, num_segments: int = 12):
    """GraphQL mutation using the service."""

    # Configure based on user input
    config = SeedDataConfig(
        num_segments=num_segments,
        num_test_stations=min(num_segments * 2, 24),
        num_rectifiers=max(6, num_segments),
        create_users=True,
        create_compliance=True,
    )

    # Generate
    service = SeedDataService(session, config)
    result = await service.generate_all()

    # Format for GraphQL response
    if result.success:
        summary = f"Generated {result.segments} segments, {result.measurements} measurements"
        return {"success": True, "message": summary}
    else:
        return {"success": False, "message": result.message}
```

### Example 3: Custom Scenario (Minimal Data for Fast Tests)

```python
from corrdata.services.seed_data_service import SeedDataConfig, generate_seed_data

async def generate_minimal_seed_data(session):
    """Generate minimal seed data for fast tests."""

    config = SeedDataConfig(
        num_segments=3,              # Just 3 segments
        num_test_stations=6,         # 6 test stations
        num_rectifiers=3,            # 3 rectifiers
        num_anode_beds=0,            # Skip anode beds
        num_facilities=0,            # Skip facilities
        num_equipment=0,             # Skip equipment
        create_users=False,          # Skip user creation
        create_compliance=False,     # Skip compliance
        create_work_orders=False,    # Skip work orders
        create_alerts=False,         # Skip alerts
    )

    return await generate_seed_data(session, config)
```

### Example 4: Large Scenario (Comprehensive Demo)

```python
async def generate_large_demo(session):
    """Generate large comprehensive demo dataset."""

    config = SeedDataConfig(
        num_segments=50,             # 50 segments for full distribution
        num_test_stations=100,       # More test stations
        num_rectifiers=25,           # More rectifiers
        num_anode_beds=25,
        num_facilities=10,
        num_equipment=50,
        create_users=True,
        create_compliance=True,
        create_work_orders=True,
        create_alerts=True,
    )

    service = SeedDataService(session, config)
    result = await service.generate_all()

    # Log detailed statistics
    print(f"Created {result.segments} segments:")
    for profile, count in result.profile_distribution.items():
        percentage = (count / result.segments) * 100
        print(f"  - {profile.capitalize()}: {count} ({percentage:.1f}%)")

    return result
```

### Example 5: Testing Fixture (Reproducible Data)

```python
import pytest
from corrdata.services.seed_data_service import SeedDataConfig, SeedDataService

@pytest.fixture
async def seed_data(db_session):
    """Pytest fixture for consistent seed data."""

    config = SeedDataConfig(
        num_segments=12,
        random_seed=42,  # Same seed = same data every time
        create_users=True,
        create_compliance=False,
    )

    service = SeedDataService(db_session, config)
    result = await service.generate_all()

    assert result.success, f"Seed data generation failed: {result.message}"

    return result
```

## Risk Profile System

The service uses a realistic risk distribution based on industry standards:

### Distribution (Default for 12 Segments)

| Profile  | Percentage | Count | Description                    |
|----------|------------|-------|--------------------------------|
| Critical | 6%         | 2     | Major failures, immediate action |
| High     | 12%        | 3     | Significant issues, investigate |
| Medium   | 30%        | 5     | Moderate concerns, monitor     |
| Low      | 32%        | 4     | Minor issues, routine checks   |
| Minimal  | 20%        | 3     | Well-protected, standard       |

### Profile Characteristics

Each profile has distinct characteristics:

**Critical (Risk 80-100):**
- Coating: Degraded
- Install Year: 1970-1985 (40-55 years old)
- Soil Resistivity: 500-1500 Ω-cm (very corrosive)
- Soil pH: 5.0 (acidic)
- CP Readings: -650mV (inadequate protection)
- Anomaly Count: 8-15

**High (Risk 60-79):**
- Coating: Poor
- Install Year: 1985-1995 (30-40 years old)
- Soil Resistivity: 1000-3000 Ω-cm (corrosive)
- Soil pH: 5.5
- CP Readings: -750mV (below threshold)
- Anomaly Count: 4-8

**Medium (Risk 40-59):**
- Coating: Fair
- Install Year: 1995-2005 (20-30 years old)
- Soil Resistivity: 2000-5000 Ω-cm (moderate)
- Soil pH: 6.5
- CP Readings: -850mV (at threshold)
- Anomaly Count: 2-4

**Low (Risk 20-39):**
- Coating: Good
- Install Year: 2005-2015 (10-20 years old)
- Soil Resistivity: 4000-8000 Ω-cm (low corrosivity)
- Soil pH: 7.0
- CP Readings: -950mV (adequate)
- Anomaly Count: 0-2

**Minimal (Risk 0-19):**
- Coating: Excellent
- Install Year: 2015-2023 (0-10 years old)
- Soil Resistivity: 8000-20000 Ω-cm (very low)
- Soil pH: 7.2
- CP Readings: -1100mV (excellent)
- Anomaly Count: 0

### Asset Naming Convention

Assets are prefixed by risk level for easy identification:

- **A-prefix**: Critical risk (A-1, A-2, etc.)
- **B-prefix**: High risk (B-1, B-2, etc.)
- **C-prefix**: Medium risk (C-1, C-2, etc.)
- **D-prefix**: Low risk (D-1, D-2, etc.)
- **E-prefix**: Minimal risk (E-1, E-2, etc.)

Example: `Segment A-3` = Critical risk segment, `Test Station TS-B-005` = High risk test station

## Data Generation Details

### Measurements

**Segment CP Readings:**
- Frequency: Monthly for last 12 months
- Values: Risk-appropriate based on profile
- Seasonal variation: ±50mV sine wave
- Trend: Degrading/stable/improving based on profile
- Quality flags: "alarm" if > -700mV, "suspect" if > -850mV

**Rectifier Readings:**
- Frequency: Daily for last 30 days
- Current: Target × profile ratio (30%-100%)
- Voltage: Current × 1.5 ± 2V
- Source: "scada" or "manual"

### Events

**Anomaly Events:**
- Critical assets: 80% probability, 1-5 events
- High assets: 50% probability, 1-2 events
- Medium assets: 30% probability, 1-2 events
- Low assets: 10% probability, 1 event
- Minimal assets: 5% probability, 1 event

**Maintenance Events:**
- Inverse relationship to anomalies
- Minimal assets: 80% probability (well-maintained)
- Critical assets: 20% probability (neglected)

### Users and Technicians

**Users (16 total):**
- 2 Operations Managers
- 2 Integrity Engineers
- 2 Compliance Officers
- 8 Field Technicians (4 North, 4 South)
- 2 Analysts

**Technicians (8 total):**
- Certifications: CP Tester Level 1-3, NACE CP2, NACE CIP
- Linked to user accounts
- Regional assignment

### Compliance

**Regulations:**
- 49 CFR 192 (Gas Pipeline Safety)
- 49 CFR 195 (Hazardous Liquids)

**Audits:**
- 1 audit per regulation
- Status: "completed" or "in_progress"
- Random findings count: 0-5

**Documents:**
- Folder: "Compliance Documents"
- Types: CP Survey Report, Compliance Audit, ILI Report

## Common Patterns

### Pattern 1: Clear Before Generate

```python
async def reset_and_generate(session):
    """Clear existing seed data and generate fresh."""

    service = SeedDataService(session)

    # Clear existing data
    tables_cleared = await service.clear_seed_data()
    print(f"Cleared {len(tables_cleared)} tables")

    # Generate fresh data
    result = await service.generate_all()
    return result
```

### Pattern 2: Partial Clear and Generate

```python
async def regenerate_measurements_only(session):
    """Clear and regenerate just measurements."""

    # Clear measurements manually
    await session.execute(text("DELETE FROM measurements WHERE tenant_uuid = :tenant"),
                          {"tenant": str(SEED_TENANT_UUID)})

    # Get existing segments
    segments_result = await session.execute(
        text("SELECT uuid FROM assets WHERE type = 'SEGMENT' AND tenant_uuid = :tenant"),
        {"tenant": str(SEED_TENANT_UUID)}
    )
    # ... recreate measurements
```

### Pattern 3: Extend with Custom Data

```python
async def generate_with_custom_additions(session):
    """Generate standard seed data then add custom assets."""

    # Generate standard seed data
    result = await generate_seed_data(session)

    # Add custom pipeline
    custom_pipeline = Asset(
        uuid=uuid4(),
        tenant_uuid=SEED_TENANT_UUID,
        name="Custom Test Pipeline",
        type="PIPELINE",
        # ... custom attributes
    )
    session.add(custom_pipeline)
    await session.commit()

    return result
```

## Best Practices

### DO

1. **Use config objects** for customization instead of hardcoding
2. **Check result.success** before assuming data was created
3. **Use random_seed** for reproducible test data
4. **Clear existing data** before regenerating to avoid duplicates
5. **Commit after generation** if using manual session management

### DON'T

1. **Don't mix manual and service data generation** - use one or the other
2. **Don't modify service internals** - use configuration instead
3. **Don't rely on specific UUIDs** - they're randomly generated
4. **Don't skip error checking** - always check result.success
5. **Don't generate in production** - seed data is for dev/demo only

## Performance Considerations

### Generation Time

Typical generation times (12 segments):
- Assets: ~50ms
- Users/Compliance: ~100ms
- Measurements (12 months): ~500ms
- Events: ~200ms
- **Total: ~1 second**

### Scaling

For large datasets (50+ segments):
- Consider batch inserts for measurements
- Use `create_users=False` if not needed
- Disable compliance data for faster generation
- Adjust measurement timeframe (reduce from 12 months)

### Memory Usage

Memory usage scales with:
- Number of segments × measurements per segment (12 months = 12 measurements)
- Number of rectifiers × daily readings (30 days = 60 measurements)
- Keep asset counts reasonable (<100 segments) for CLI usage

## Troubleshooting

### Issue: Duplicate Key Errors

**Symptom:** `IntegrityError: duplicate key value violates unique constraint`

**Cause:** Trying to generate when seed data already exists

**Solution:**
```python
# Clear before generating
service = SeedDataService(session)
await service.clear_seed_data()
result = await service.generate_all()
```

### Issue: Missing Foreign Key

**Symptom:** `IntegrityError: violates foreign key constraint`

**Cause:** Tenant doesn't exist

**Solution:**
```python
# Ensure tenant exists first
service = SeedDataService(session)
await service.ensure_tenant_exists()
result = await service.generate_all()
```

### Issue: No Data Created

**Symptom:** `result.success=True` but counts are all 0

**Cause:** Configuration disabled all features

**Solution:**
```python
# Check config - ensure at least basic features enabled
config = SeedDataConfig(
    num_segments=12,  # Must be > 0
    # Ensure some features enabled
)
```

### Issue: Inconsistent Risk Distribution

**Symptom:** Not getting expected 6/12/30/32/20 distribution

**Cause:** Too few segments for proper distribution

**Solution:**
```python
# Use at least 12 segments for realistic distribution
# For 50 segments, you get closer to exact percentages
config = SeedDataConfig(num_segments=50)
```

## Related Documentation

- **ADR-055**: Consolidated Seed Data Service architecture decision
- **Sprint 144**: Implementation sprint documentation
- **Service Source**: `src/corrdata/services/seed_data_service.py`
- **GraphQL Wrapper**: `src/corrdata/graphql/mutations/seed_data.py`
- **CLI Wrapper**: `scripts/generate_sample_data.py`

## Migration from Old Patterns

### If You Were Using GraphQL Inline Generation

**Before (2,859 lines in GraphQL mutation):**
```python
# Inline data generation in mutation
async def generate_seed_data(self, info):
    # 2,800+ lines of inline logic
    ...
```

**After (279 lines, uses service):**
```python
from corrdata.services.seed_data_service import SeedDataService

async def generate_seed_data(self, info):
    async with ctx.get_session() as db:
        service = SeedDataService(db)
        result = await service.generate_all()
        return format_result(result)
```

### If You Were Using CLI Script

**Before (1,081 lines in CLI script):**
```python
# Duplicate implementation
async def main():
    # 1,000+ lines of data generation
    ...
```

**After (93 lines, uses service):**
```python
from corrdata.services.seed_data_service import generate_seed_data

async def main():
    async with async_session_factory() as session:
        result = await generate_seed_data(session)
        print_summary(result)
```

### If You Were Using Basic Service

**Before (599 lines, incomplete):**
```python
# Only basic assets, no users/compliance
service = SeedDataService(session)
result = await service.generate_all()
# Missing: users, compliance, work orders, alerts
```

**After (1,525 lines, complete):**
```python
# Full feature set
service = SeedDataService(session, config)
result = await service.generate_all()
# Includes: everything
```

## Summary

The Seed Data Service provides a **battle-tested, comprehensive solution** for generating realistic demo data. By consolidating three separate implementations into one authoritative service, we've:

- Reduced code by 58% (2,642 lines eliminated)
- Eliminated code drift and maintenance burden
- Provided flexible configuration via dataclasses
- Maintained backward compatibility with existing APIs
- Improved testability and reliability

Use it for local development, testing, and demo environments with confidence that you're using the single source of truth.
