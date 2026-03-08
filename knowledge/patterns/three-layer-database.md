# Recipe: Three-Layer Database Architecture

**Category**: pattern
**Version**: 1.0
**Last Updated**: 2025-12-14
**Sprints**: Multiple (foundation pattern)
**ADRs**: [ADR-001](../../architecture/decisions/ADR-001-three-layer-architecture.md), [ADR-007](../../architecture/decisions/ADR-007-timescaledb-time-series.md), [ADR-008](../../architecture/decisions/ADR-008-postgis-spatial-data.md), [ADR-011](../../architecture/decisions/ADR-011-sqlalchemy-2-orm.md)

## Context

**When to use this recipe:**
- Building a system with spatial, temporal, and relational query requirements
- Managing multi-decade time-series data (measurements, sensor readings)
- Answering "what affects what" questions across system relationships
- Combining location-based queries with time-series aggregations
- Creating a digital twin with predictive capabilities

**When NOT to use this recipe:**
- Simple CRUD applications with basic data models
- Pure document-oriented data with no relationships
- Systems without spatial or graph requirements
- Microservices that need only one database type

## Ingredients

Before starting, ensure you have:

- [ ] PostgreSQL 15+ installed with superuser access
- [ ] TimescaleDB extension available
- [ ] PostGIS extension available
- [ ] Neo4j 5.x for graph layer (if using Layer 2)
- [ ] SQLAlchemy 2.0+ and GeoAlchemy2 for Python ORM
- [ ] Understanding of coordinate reference systems (SRID)
- [ ] Database migration tool (Alembic)

## Overview

The three-layer architecture separates concerns by database capability:

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: FACT STORE (PostgreSQL + PostGIS + TimescaleDB)        │
│   • Authoritative source of truth                               │
│   • Measurements, events, assets                                │
│   • Spatial queries via PostGIS                                 │
│   • Time-series via TimescaleDB hypertables                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│ Layer 2: RELATIONSHIP GRAPH (Neo4j)                             │
│   • Temporal knowledge graph                                    │
│   • "What affects what" relationships                           │
│   • Multi-hop traversal                                         │
│   • Causal chain analysis                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│ Layer 3: DIGITAL TWIN / ML (PyTorch + Vector Store)             │
│   • Deep learning models                                        │
│   • Situation encoder embeddings                                │
│   • Corrosion prediction                                        │
│   • Similar situation search                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Steps

### Step 1: Set Up PostgreSQL Extensions

Enable TimescaleDB and PostGIS on your database:

```sql
-- Enable extensions (requires superuser)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- For gen_random_uuid()

-- Verify installation
SELECT extname, extversion FROM pg_extension
WHERE extname IN ('timescaledb', 'postgis');
```

**Expected outcome**: Both extensions show installed with version numbers.

### Step 2: Create Base Tables with Geometry Columns

Define tables using SQLAlchemy 2.0 with PostGIS support:

```python
# src/corrdata/db/models.py
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Text, Numeric, ForeignKey, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

class Base(DeclarativeBase):
    """Base class for all models."""
    pass

class Asset(Base):
    __tablename__ = "assets"

    # Primary key
    uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Core attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # PostGIS geometry column - SRID 4326 = WGS84 (GPS coordinates)
    geometry = mapped_column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True)

    # For linear assets (LINESTRING), store computed length
    length_miles: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)

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

    # Relationships
    measurements: Mapped[list["Measurement"]] = relationship(back_populates="asset", lazy="selectin")
```

**Expected outcome**: SQLAlchemy model with proper type hints and PostGIS geometry column.

### Step 3: Convert Time-Series Tables to Hypertables

Create measurement table and convert to TimescaleDB hypertable:

```python
# In models.py
class Measurement(Base):
    __tablename__ = "measurements"

    uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    asset_uuid: Mapped[UUID] = mapped_column(ForeignKey("assets.uuid"), nullable=False)
    sensor_uuid: Mapped[Optional[UUID]] = mapped_column(ForeignKey("sensors.uuid"), nullable=True)

    measurement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Numeric, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)

    # TIME DIMENSION - critical for TimescaleDB partitioning
    recorded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    # Metadata as JSONB for flexibility
    metadata: Mapped[Optional[dict]] = mapped_column(type_=JSONB, nullable=True)

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="measurements")
```

Create Alembic migration to convert to hypertable:

```python
# alembic/versions/xxxx_create_hypertable.py
def upgrade():
    # Create table normally first
    op.create_table(
        'measurements',
        # ... column definitions
    )

    # Convert to hypertable - CRITICAL STEP
    op.execute("""
        SELECT create_hypertable(
            'measurements',
            'recorded_at',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE
        );
    """)

    # Add indexes for common query patterns
    op.create_index(
        'idx_measurements_asset_time',
        'measurements',
        ['asset_uuid', 'recorded_at DESC']
    )

    op.create_index(
        'idx_measurements_type_time',
        'measurements',
        ['measurement_type', 'recorded_at DESC']
    )

def downgrade():
    # Note: Hypertables can't be easily downgraded
    # Typically requires recreating as regular table
    op.drop_table('measurements')
```

**Expected outcome**: `measurements` table is now a TimescaleDB hypertable with automatic monthly partitioning.

### Step 4: Add Spatial Indexes

Create GiST indexes for efficient spatial queries:

```python
# In Alembic migration
def upgrade():
    # GiST index for geometry queries
    op.execute("""
        CREATE INDEX idx_assets_geometry
        ON assets USING GIST (geometry);
    """)

    # Partial index for specific asset types
    op.execute("""
        CREATE INDEX idx_segments_geometry
        ON assets USING GIST (geometry)
        WHERE asset_type = 'segment';
    """)
```

**Expected outcome**: Spatial queries use index scans instead of sequential scans.

### Step 5: Configure Compression and Retention

Set up TimescaleDB compression and retention policies:

```sql
-- Enable compression on chunks older than 7 days
ALTER TABLE measurements SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'asset_uuid, measurement_type',
    timescaledb.compress_orderby = 'recorded_at DESC'
);

-- Add compression policy
SELECT add_compression_policy('measurements', INTERVAL '7 days');

-- Add retention policy - keep raw data for 2 years
SELECT add_retention_policy('measurements', INTERVAL '2 years');
```

**Expected outcome**: Older data is compressed (90%+ storage savings), data older than 2 years is automatically dropped.

### Step 6: Create Continuous Aggregates

Pre-compute rollups for dashboard queries:

```sql
-- Hourly aggregates
CREATE MATERIALIZED VIEW measurements_hourly
WITH (timescaledb.continuous) AS
SELECT
    asset_uuid,
    measurement_type,
    time_bucket('1 hour', recorded_at) AS bucket,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    STDDEV(value) AS stddev_value,
    COUNT(*) AS sample_count
FROM measurements
GROUP BY asset_uuid, measurement_type, time_bucket('1 hour', recorded_at);

-- Add refresh policy (update every hour)
SELECT add_continuous_aggregate_policy(
    'measurements_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

-- Daily aggregates for long-term trends
CREATE MATERIALIZED VIEW measurements_daily
WITH (timescaledb.continuous) AS
SELECT
    asset_uuid,
    measurement_type,
    time_bucket('1 day', recorded_at) AS bucket,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    COUNT(*) AS sample_count
FROM measurements
GROUP BY asset_uuid, measurement_type, time_bucket('1 day', recorded_at);
```

**Expected outcome**: Dashboard queries use pre-computed aggregates instead of scanning raw data.

## Code Examples

### Spatial Query: Find Assets Near a Point

```python
from sqlalchemy import select, func
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_SetSRID, ST_MakePoint

async def get_assets_near_point(
    session: AsyncSession,
    longitude: float,
    latitude: float,
    radius_meters: float = 500
) -> list[Asset]:
    """Find all assets within radius of a point."""

    # Create point geometry
    point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)

    # Query with distance calculation
    stmt = (
        select(
            Asset,
            func.ST_Distance(
                func.cast(Asset.geometry, Geography),
                func.cast(point, Geography)
            ).label("distance_m")
        )
        .where(
            func.ST_DWithin(
                func.cast(Asset.geometry, Geography),
                func.cast(point, Geography),
                radius_meters
            )
        )
        .order_by("distance_m")
    )

    result = await session.execute(stmt)
    return [row.Asset for row in result]
```

### Time-Series Query: Get Measurements with Aggregation

```python
async def get_measurement_trend(
    session: AsyncSession,
    asset_uuid: UUID,
    measurement_type: str,
    start_date: datetime,
    end_date: datetime,
    use_hourly_rollup: bool = True
) -> list[dict]:
    """Get measurement trend, optionally using pre-aggregated data."""

    if use_hourly_rollup:
        # Use continuous aggregate for faster queries
        stmt = text("""
            SELECT bucket, avg_value, min_value, max_value, sample_count
            FROM measurements_hourly
            WHERE asset_uuid = :asset_uuid
              AND measurement_type = :type
              AND bucket BETWEEN :start AND :end
            ORDER BY bucket
        """)
    else:
        # Query raw hypertable
        stmt = (
            select(Measurement)
            .where(Measurement.asset_uuid == asset_uuid)
            .where(Measurement.measurement_type == measurement_type)
            .where(Measurement.recorded_at.between(start_date, end_date))
            .order_by(Measurement.recorded_at)
        )

    result = await session.execute(stmt, {
        "asset_uuid": str(asset_uuid),
        "type": measurement_type,
        "start": start_date,
        "end": end_date
    })

    return [dict(row) for row in result]
```

### Combined Spatial + Temporal Query

```python
async def get_high_risk_segments_in_flood_zone(
    session: AsyncSession,
    flood_zone_geometry: str,  # WKT or GeoJSON
    days_back: int = 90
) -> list[dict]:
    """Find pipeline segments in flood zones with declining CP readings."""

    cutoff_date = datetime.utcnow() - timedelta(days=days_back)

    stmt = text("""
        WITH recent_readings AS (
            SELECT
                m.asset_uuid,
                AVG(m.value) as avg_potential,
                COUNT(*) as reading_count,
                (array_agg(m.value ORDER BY m.recorded_at DESC))[1] as latest_value,
                (array_agg(m.value ORDER BY m.recorded_at DESC))[2] as previous_value
            FROM measurements m
            WHERE m.measurement_type = 'pipe_to_soil_potential'
              AND m.recorded_at >= :cutoff_date
            GROUP BY m.asset_uuid
            HAVING COUNT(*) >= 2
        )
        SELECT
            a.uuid,
            a.name,
            r.avg_potential,
            r.latest_value,
            ST_Length(a.geometry::geography) as length_m,
            ST_AsGeoJSON(a.geometry) as geometry
        FROM assets a
        JOIN recent_readings r ON a.uuid = r.asset_uuid
        WHERE a.asset_type = 'segment'
          AND ST_Intersects(
              a.geometry,
              ST_GeomFromText(:flood_zone, 4326)
          )
          AND r.latest_value < -750  -- Getting less negative = worse protection
          AND r.latest_value > r.previous_value  -- Declining trend
        ORDER BY r.latest_value DESC
    """)

    result = await session.execute(stmt, {
        "cutoff_date": cutoff_date,
        "flood_zone": flood_zone_geometry
    })

    return [dict(row) for row in result]
```

### GeoJSON Export

```sql
-- Export assets as GeoJSON FeatureCollection
SELECT json_build_object(
    'type', 'FeatureCollection',
    'features', json_agg(
        json_build_object(
            'type', 'Feature',
            'id', uuid,
            'geometry', ST_AsGeoJSON(geometry)::json,
            'properties', json_build_object(
                'name', name,
                'type', asset_type,
                'length_miles', length_miles,
                'created_at', created_at
            )
        )
    )
) AS geojson
FROM assets
WHERE asset_type = 'segment';
```

## Learnings

### From Multiple Sprints

- **Chunk interval matters**: 1-month chunks work well for moderate-volume time-series (100-1000 readings/day). Higher volume may need 1-week chunks.
- **Compression timing**: Compress after 7 days balances query performance (recent data uncompressed) with storage savings.
- **SRID consistency**: Always store in SRID 4326 (WGS84), transform at query time if needed for accurate distance calculations (e.g., UTM zones).
- **Index selectivity**: Partial indexes on asset_type significantly improve query performance when filtering by type.
- **Continuous aggregates**: Refresh policies should have `start_offset > end_offset` to allow data to "settle" before aggregating.
- **Geography vs Geometry**: Cast to `Geography` type for accurate distance calculations on Earth's curved surface.

### Performance Insights

- TimescaleDB hypertables: 10-100x faster range queries vs non-partitioned tables at scale
- PostGIS GiST indexes: Enable sub-second spatial queries on millions of features
- Continuous aggregates: Dashboard queries run in milliseconds instead of seconds
- Compression: Achieves 90-95% storage reduction on older time-series data

## Anti-Patterns

### Don't: Use Geometry Type for Distance Calculations

**What it looks like**:
```sql
SELECT ST_Distance(geometry1, geometry2) AS distance
```

**Why it's bad**: Returns distance in degrees (lat/long), not meters. Meaningless for real-world distance.

**Instead**:
```sql
SELECT ST_Distance(geometry1::geography, geometry2::geography) AS distance_m
```

### Don't: Create Hypertables After Data is Loaded

**What it looks like**:
```sql
INSERT INTO measurements VALUES (...);  -- Load data first
SELECT create_hypertable('measurements', 'recorded_at');  -- Then convert
```

**Why it's bad**: TimescaleDB must repartition existing data, which is slow and error-prone.

**Instead**: Create hypertable immediately after creating empty table, before inserting data.

### Don't: Query Raw Hypertable for Dashboard Aggregations

**What it looks like**:
```sql
-- Runs every time dashboard loads
SELECT asset_uuid, AVG(value)
FROM measurements
WHERE recorded_at > NOW() - INTERVAL '30 days'
GROUP BY asset_uuid;
```

**Why it's bad**: Scans millions of rows every query. Slow and resource-intensive.

**Instead**: Use continuous aggregates that pre-compute these rollups.

### Don't: Mix Coordinate Reference Systems

**What it looks like**:
```python
# Some assets in SRID 4326, others in SRID 3857
asset1.geometry = mapped_column(Geometry(srid=4326))
asset2.geometry = mapped_column(Geometry(srid=3857))
```

**Why it's bad**: Spatial queries fail or return incorrect results when SRIDs don't match.

**Instead**: Store everything in SRID 4326, transform at query time if needed.

### Don't: Forget to Add Compression Policy

**What it looks like**: Create hypertable but never enable compression.

**Why it's bad**: Storage costs grow linearly, wasting disk space and reducing query performance.

**Instead**: Add compression policy during initial setup.

## Variations

### For Very High Volume Time-Series

If ingesting >10,000 measurements/second:

```sql
-- Use smaller chunk intervals
SELECT create_hypertable(
    'measurements',
    'recorded_at',
    chunk_time_interval => INTERVAL '1 week'  -- Instead of 1 month
);

-- Consider distributed hypertables (TimescaleDB multi-node)
SELECT create_distributed_hypertable(
    'measurements',
    'recorded_at',
    'asset_uuid'  -- Space partitioning key
);
```

### For Point-Only Geometries

If only storing points (no lines/polygons):

```python
# Use specific geometry type for better validation
geometry = mapped_column(Geometry(geometry_type="POINT", srid=4326))
```

### For Global Deployments

If assets span multiple UTM zones:

```python
# Store in WGS84, create helper function for distance in local zone
def calculate_distance_local(geom1, geom2):
    """Calculate distance using appropriate UTM zone."""
    # Determine UTM zone from longitude
    lon = get_longitude(geom1)
    utm_srid = calculate_utm_srid(lon)

    return func.ST_Distance(
        func.ST_Transform(geom1, utm_srid),
        func.ST_Transform(geom2, utm_srid)
    )
```

## Related Recipes

- [Provider Pattern](./provider-pattern.md) - External data integration
- [GraphQL Schema Design](./graphql-schema.md) - Querying this architecture via GraphQL
- [Domain Model Layering](./domain-model-layering.md) - Converting ORM models to domain objects

## Verification

### Confirm TimescaleDB Hypertable

```sql
SELECT hypertable_name, num_chunks
FROM timescaledb_information.hypertables;
```

Expected: `measurements` listed with chunk count.

### Confirm PostGIS Spatial Index

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'assets' AND indexdef LIKE '%GIST%';
```

Expected: `idx_assets_geometry` index shown.

### Test Spatial Query Performance

```sql
EXPLAIN ANALYZE
SELECT * FROM assets
WHERE ST_DWithin(
    geometry::geography,
    ST_SetSRID(ST_MakePoint(-95.5, 29.7), 4326)::geography,
    1000
);
```

Expected: Uses "Index Scan using idx_assets_geometry", not "Seq Scan".

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-14 | Initial version based on ADR-001, ADR-007, ADR-008, ADR-011 |
