# Recipe: Provider Pattern for External Data

**Category**: pattern
**Version**: 1.0
**Last Updated**: 2025-12-14
**Sprints**: Multiple (foundation pattern), Sprint 110 (hazard levels)
**ADRs**: [ADR-012](../../architecture/decisions/ADR-012-external-data-integration-pattern.md), [ADR-016](../../architecture/decisions/ADR-016-environment-based-configuration.md), [ADR-017](../../architecture/decisions/ADR-017-file-based-caching.md), [ADR-032](../../architecture/decisions/ADR-032-data-provider-factory.md)

## Context

**When to use this recipe:**
- Integrating data from external APIs (USGS, NOAA, USDA, vendor systems)
- Supporting both real and synthetic data sources for development/testing
- Building systems that work offline during development
- Creating consistent interfaces across diverse data sources
- Implementing caching and fallback strategies

**When NOT to use this recipe:**
- Simple one-off API calls
- Internal microservice communication
- Data sources with identical interfaces
- When external API is the only source (no synthetic needed)

## Ingredients

Before starting, ensure you have:

- [ ] List of external data sources and their characteristics
- [ ] API documentation for real sources
- [ ] Understanding of data schemas (soil, weather, incidents, etc.)
- [ ] Caching strategy (Redis, file-based, or in-memory)
- [ ] Environment configuration system (`.env` files)
- [ ] Async HTTP library (`aiohttp` or `httpx`)
- [ ] Pandas/GeoPandas for data manipulation

## Overview

The Provider Pattern creates a unified interface for diverse external data sources:

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION CODE                              │
│  (Calls providers via common interface)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    PROVIDER INTERFACE                            │
│  - get_data(location, time_range) → DataFrame                   │
│  - get_corridor_data(geometry) → GeoDataFrame                   │
│  - health_check() → bool                                         │
└──────────┬─────────────────┬────────────────┬───────────────────┘
           │                 │                │
┌──────────┴────┐  ┌─────────┴──────┐  ┌──────┴────────────┐
│  Synthetic    │  │  Real API      │  │  Cached           │
│  Provider     │  │  Provider      │  │  Provider         │
│  (Dev/Test)   │  │  (Production)  │  │  (Wrapper)        │
└───────────────┘  └────────────────┘  └───────────────────┘
```

## Steps

### Step 1: Define the Provider Interface

Create abstract base class with common methods:

```python
# src/corrdata/providers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon

@dataclass
class DataRequest:
    """Request for point-based data."""
    latitude: float
    longitude: float
    radius_km: float = 50.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_metadata: bool = True

@dataclass
class CorridorRequest:
    """Request for corridor-based data (pipeline route)."""
    geometry: LineString | Polygon
    buffer_meters: float = 100.0
    include_metadata: bool = True

class DataProvider(ABC):
    """Abstract base class for all external data providers."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this data source (e.g., 'usda_ssurgo')."""
        pass

    @property
    @abstractmethod
    def data_type(self) -> str:
        """Type of data provided (e.g., 'soil', 'weather', 'incidents')."""
        pass

    @abstractmethod
    async def get_data(self, request: DataRequest) -> pd.DataFrame:
        """
        Get data for a point location.

        Returns DataFrame with columns specific to data_type.
        Always includes: latitude, longitude, source, sample_date
        """
        pass

    @abstractmethod
    async def get_corridor_data(self, request: CorridorRequest) -> gpd.GeoDataFrame:
        """
        Get data along a corridor (pipeline route with buffer).

        Returns GeoDataFrame with geometry column and attributes.
        """
        pass

    @abstractmethod
    def get_schema(self) -> dict:
        """
        Return schema definition for this data source.

        Example:
        {
            "columns": {
                "resistivity_ohm_cm": {"type": "float", "unit": "ohm-cm"},
                "ph": {"type": "float", "range": [0, 14]},
            }
        }
        """
        pass

    async def health_check(self) -> bool:
        """Check if the data source is available and responding."""
        return True
```

**Expected outcome**: Abstract interface that all providers must implement.

### Step 2: Implement Synthetic Provider for Development

Create realistic data generator for testing without external dependencies:

```python
# src/corrdata/providers/synthetic/soil.py
import random
from datetime import datetime
import pandas as pd
import geopandas as gpd
from corrdata.providers.base import DataProvider, DataRequest, CorridorRequest

class SyntheticSoilProvider(DataProvider):
    """
    Generate realistic soil data based on location.
    Uses regional profiles for consistency.
    """

    source_name = "synthetic_soil"
    data_type = "soil"

    # Regional profiles (from Sprint 110)
    REGIONAL_PROFILES = {
        "gulf_coast": {
            "base_resistivity": 1500,
            "ph_range": (6.0, 7.5),
            "chlorides_ppm": (200, 500),
            "sulfates_ppm": (150, 400),
        },
        "midwest": {
            "base_resistivity": 3000,
            "ph_range": (6.5, 7.8),
            "chlorides_ppm": (20, 100),
            "sulfates_ppm": (50, 200),
        },
        "arid_west": {
            "base_resistivity": 8000,
            "ph_range": (7.5, 8.5),
            "chlorides_ppm": (10, 50),
            "sulfates_ppm": (100, 300),
        },
    }

    def _determine_region(self, latitude: float, longitude: float) -> str:
        """Determine region based on coordinates."""
        if latitude < 32 and longitude > -100:
            return "gulf_coast"
        elif latitude > 40 and -100 < longitude < -80:
            return "midwest"
        else:
            return "arid_west"

    def _classify_corrosivity(self, resistivity: float) -> str:
        """
        Classify soil corrosivity based on resistivity.
        Based on ASTM G187 and industry standards.
        """
        if resistivity < 1000:
            return "severely_corrosive"
        elif resistivity < 2000:
            return "corrosive"
        elif resistivity < 5000:
            return "moderately_corrosive"
        elif resistivity < 10000:
            return "mildly_corrosive"
        else:
            return "non_corrosive"

    async def get_data(self, request: DataRequest) -> pd.DataFrame:
        """Generate realistic soil properties based on location."""
        region = self._determine_region(request.latitude, request.longitude)
        profile = self.REGIONAL_PROFILES[region]

        # Generate values with realistic variation
        resistivity = profile["base_resistivity"] * random.gauss(1.0, 0.3)
        resistivity = max(100, resistivity)  # Floor at 100

        ph = random.uniform(*profile["ph_range"])
        chlorides = random.uniform(*profile["chlorides_ppm"])
        sulfates = random.uniform(*profile["sulfates_ppm"])

        data = {
            "latitude": request.latitude,
            "longitude": request.longitude,
            "resistivity_ohm_cm": round(resistivity, 1),
            "ph": round(ph, 2),
            "chlorides_ppm": round(chlorides, 1),
            "sulfates_ppm": round(sulfates, 1),
            "moisture_percent": round(random.uniform(10, 30), 1),
            "corrosivity_class": self._classify_corrosivity(resistivity),
            "region": region,
            "source": self.source_name,
            "sample_date": datetime.utcnow(),
            "confidence": 0.7,  # Synthetic data has lower confidence
        }

        if request.include_metadata:
            data["metadata"] = {
                "synthetic": True,
                "regional_profile": region,
                "notes": "Generated from regional statistical model"
            }

        return pd.DataFrame([data])

    async def get_corridor_data(self, request: CorridorRequest) -> gpd.GeoDataFrame:
        """Generate soil data along a corridor."""
        # Sample points every 100 meters along corridor
        line = request.geometry
        length = line.length
        num_samples = int(length / 0.001) + 1  # ~100m in degrees

        samples = []
        for i in range(num_samples):
            fraction = i / max(1, num_samples - 1)
            point = line.interpolate(fraction, normalized=True)

            point_request = DataRequest(
                latitude=point.y,
                longitude=point.x,
                include_metadata=request.include_metadata
            )
            sample_df = await self.get_data(point_request)
            sample_df["geometry"] = point
            samples.append(sample_df)

        if not samples:
            return gpd.GeoDataFrame()

        gdf = gpd.GeoDataFrame(pd.concat(samples, ignore_index=True))
        gdf.set_crs(epsg=4326, inplace=True)
        return gdf

    def get_schema(self) -> dict:
        """Return schema for soil data."""
        return {
            "columns": {
                "resistivity_ohm_cm": {
                    "type": "float",
                    "unit": "ohm-cm",
                    "description": "Soil electrical resistivity"
                },
                "ph": {
                    "type": "float",
                    "range": [0, 14],
                    "description": "Soil pH"
                },
                "chlorides_ppm": {
                    "type": "float",
                    "unit": "ppm",
                    "description": "Chloride concentration"
                },
                "sulfates_ppm": {
                    "type": "float",
                    "unit": "ppm",
                    "description": "Sulfate concentration"
                },
                "corrosivity_class": {
                    "type": "string",
                    "enum": [
                        "non_corrosive",
                        "mildly_corrosive",
                        "moderately_corrosive",
                        "corrosive",
                        "severely_corrosive"
                    ]
                }
            }
        }
```

**Expected outcome**: Synthetic provider that generates realistic data for development/testing.

### Step 3: Implement Real API Provider

Create provider that calls actual external API:

```python
# src/corrdata/providers/real/ssurgo.py
import aiohttp
from typing import Optional
import pandas as pd
import geopandas as gpd
from corrdata.providers.base import DataProvider, DataRequest, CorridorRequest

class SSURGOProvider(DataProvider):
    """
    USDA SSURGO (Soil Survey Geographic Database) provider.
    Official source for soil properties in the United States.
    """

    source_name = "usda_ssurgo"
    data_type = "soil"

    def __init__(
        self,
        base_url: str = "https://sdmdataaccess.sc.usda.gov",
        timeout: int = 30
    ):
        self.base_url = base_url
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Lazy session creation."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    def _build_spatial_query(
        self,
        latitude: float,
        longitude: float,
        radius_km: float
    ) -> str:
        """
        Build SSURGO SQL query for spatial lookup.
        SSURGO uses SQL Server spatial syntax.
        """
        radius_m = radius_km * 1000
        return f"""
        SELECT
            m.mukey,
            m.muname,
            c.cokey,
            c.compname,
            c.comppct_r,
            -- Soil properties from component table
            ch.hzdept_r AS depth_cm,
            ch.ksat_r AS ksat,
            ch.ph1to1h2o_r AS ph,
            ch.ec_r AS ec,
            ch.cec7_r AS cec,
            -- Additional properties from chorizon table
            ch.sandtotal_r AS sand_pct,
            ch.silttotal_r AS silt_pct,
            ch.claytotal_r AS clay_pct
        FROM
            mapunit m
            INNER JOIN component c ON m.mukey = c.mukey
            INNER JOIN chorizon ch ON c.cokey = ch.cokey
        WHERE
            m.mukey IN (
                SELECT DISTINCT mukey
                FROM mupolygon
                WHERE mupolygon.mukey IN (
                    SELECT mukey
                    FROM SDA_Get_Mukey_from_intersection_with_WktWgs84(
                        'POINT({longitude} {latitude})'
                    )
                )
            )
            AND ch.hzdept_r = 0  -- Surface layer only
        ORDER BY c.comppct_r DESC
        """

    async def get_data(self, request: DataRequest) -> pd.DataFrame:
        """Query SSURGO API for soil data."""
        session = await self._get_session()

        query = self._build_spatial_query(
            request.latitude,
            request.longitude,
            request.radius_km
        )

        try:
            async with session.post(
                f"{self.base_url}/Tabular/post.rest",
                data={
                    "query": query,
                    "format": "JSON+COLUMNNAME"
                }
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if not data.get("Table"):
                    # No data for this location
                    return pd.DataFrame()

                df = pd.DataFrame(data["Table"])

                # Transform to common schema
                return self._transform_to_common_schema(df, request)

        except aiohttp.ClientError as e:
            raise RuntimeError(f"SSURGO API error: {e}")

    def _transform_to_common_schema(
        self,
        df: pd.DataFrame,
        request: DataRequest
    ) -> pd.DataFrame:
        """Transform SSURGO data to common provider schema."""
        if df.empty:
            return df

        # Take highest percentage component
        row = df.iloc[0]

        # Convert SSURGO properties to common schema
        # EC (electrical conductivity) → resistivity
        ec_ds_m = row.get("ec", 2.0)  # Default if missing
        resistivity = 10000 / max(ec_ds_m, 0.1)  # Convert EC to resistivity

        result = {
            "latitude": request.latitude,
            "longitude": request.longitude,
            "resistivity_ohm_cm": round(resistivity, 1),
            "ph": row.get("ph", None),
            "texture": f"{row.get('sand_pct', 0):.0f}% sand, "
                      f"{row.get('silt_pct', 0):.0f}% silt, "
                      f"{row.get('clay_pct', 0):.0f}% clay",
            "source": self.source_name,
            "sample_date": datetime.utcnow(),
            "confidence": 1.0,  # Real data has high confidence
        }

        if request.include_metadata:
            result["metadata"] = {
                "mukey": row.get("mukey"),
                "map_unit_name": row.get("muname"),
                "component": row.get("compname"),
                "component_pct": row.get("comppct_r"),
            }

        return pd.DataFrame([result])

    async def get_corridor_data(self, request: CorridorRequest) -> gpd.GeoDataFrame:
        """Get soil data along corridor."""
        # Implementation similar to synthetic version
        # but calls real API for each sample point
        pass

    def get_schema(self) -> dict:
        """Return schema."""
        return {
            "columns": {
                "resistivity_ohm_cm": {"type": "float", "unit": "ohm-cm"},
                "ph": {"type": "float", "range": [0, 14]},
                "texture": {"type": "string"},
            }
        }

    async def health_check(self) -> bool:
        """Check if SSURGO API is responding."""
        session = await self._get_session()
        try:
            async with session.get(f"{self.base_url}/Tabular/version") as response:
                return response.status == 200
        except:
            return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session and not self._session.closed:
            await self._session.close()
```

**Expected outcome**: Provider that calls real SSURGO API and transforms data to common schema.

### Step 4: Create Provider Factory

Implement factory pattern for selecting providers based on environment:

```python
# src/corrdata/providers/factory.py
import os
from typing import Optional
from corrdata.providers.base import DataProvider
from corrdata.providers.synthetic.soil import SyntheticSoilProvider
from corrdata.providers.real.ssurgo import SSURGOProvider

class ProviderFactory:
    """
    Factory for creating data providers based on environment.
    Singleton pattern ensures providers are reused.
    """

    _providers: dict[str, type[DataProvider]] = {}
    _instances: dict[str, DataProvider] = {}

    @classmethod
    def register(cls, key: str, provider_class: type[DataProvider]):
        """Register a provider class."""
        cls._providers[key] = provider_class

    @classmethod
    def get_provider(
        cls,
        data_type: str,
        use_synthetic: Optional[bool] = None
    ) -> DataProvider:
        """
        Get provider for a data type.

        Args:
            data_type: Type of data ('soil', 'weather', 'incidents')
            use_synthetic: Override env variable (True=synthetic, False=real, None=auto)

        Returns:
            Provider instance (reused across calls)
        """
        # Determine which implementation to use
        if use_synthetic is None:
            use_synthetic = os.getenv("USE_SYNTHETIC_DATA", "false").lower() == "true"

        key = f"{'synthetic' if use_synthetic else 'real'}_{data_type}"

        # Return existing instance if available
        if key in cls._instances:
            return cls._instances[key]

        # Create new instance
        provider_class = cls._providers.get(key)
        if not provider_class:
            raise ValueError(
                f"No provider registered for {key}. "
                f"Available: {list(cls._providers.keys())}"
            )

        instance = provider_class()
        cls._instances[key] = instance
        return instance

    @classmethod
    def clear_instances(cls):
        """Clear provider instances (useful for testing)."""
        cls._instances.clear()


# Register providers
ProviderFactory.register("synthetic_soil", SyntheticSoilProvider)
ProviderFactory.register("real_soil", SSURGOProvider)
```

**Expected outcome**: Factory that returns appropriate provider based on environment.

### Step 5: Add Caching Wrapper

Create decorator/wrapper for caching provider responses:

```python
# src/corrdata/providers/cached.py
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import geopandas as gpd
from corrdata.providers.base import DataProvider, DataRequest, CorridorRequest

class CachedProvider(DataProvider):
    """
    Wrapper that adds caching to any provider.
    Uses file-based cache for persistence across restarts.
    """

    def __init__(
        self,
        inner: DataProvider,
        cache_dir: str = "./cache/providers",
        ttl_hours: int = 24
    ):
        self.inner = inner
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)

        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

    @property
    def source_name(self) -> str:
        return f"cached_{self.inner.source_name}"

    @property
    def data_type(self) -> str:
        return self.inner.data_type

    def _make_cache_key(self, request: DataRequest | CorridorRequest) -> str:
        """Generate cache key from request parameters."""
        # Create deterministic hash of request parameters
        params = {
            "source": self.inner.source_name,
            "latitude": getattr(request, "latitude", None),
            "longitude": getattr(request, "longitude", None),
            "radius_km": getattr(request, "radius_km", None),
            "geometry_wkt": getattr(request.geometry, "wkt", None) if hasattr(request, "geometry") else None,
        }
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> str:
        """Get file path for cache key."""
        return os.path.join(self.cache_dir, f"{cache_key}.parquet")

    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cached file exists and is not expired."""
        if not os.path.exists(cache_path):
            return False

        mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        age = datetime.utcnow() - mtime
        return age < self.ttl

    async def get_data(self, request: DataRequest) -> pd.DataFrame:
        """Get data with caching."""
        cache_key = self._make_cache_key(request)
        cache_path = self._get_cache_path(cache_key)

        # Try cache first
        if self._is_cache_valid(cache_path):
            return pd.read_parquet(cache_path)

        # Fetch from real source
        data = await self.inner.get_data(request)

        # Cache result
        if not data.empty:
            data.to_parquet(cache_path)

        return data

    async def get_corridor_data(self, request: CorridorRequest) -> gpd.GeoDataFrame:
        """Get corridor data with caching."""
        # Similar to get_data but for GeoDataFrame
        cache_key = self._make_cache_key(request)
        cache_path = self._get_cache_path(cache_key)

        if self._is_cache_valid(cache_path):
            return gpd.read_parquet(cache_path)

        data = await self.inner.get_corridor_data(request)

        if not data.empty:
            data.to_parquet(cache_path)

        return data

    def get_schema(self) -> dict:
        """Return inner provider's schema."""
        return self.inner.get_schema()

    async def health_check(self) -> bool:
        """Check inner provider's health."""
        return await self.inner.health_check()
```

**Expected outcome**: Wrapper that caches provider responses to disk.

## Code Examples

### Basic Usage

```python
from corrdata.providers.factory import ProviderFactory
from corrdata.providers.base import DataRequest

# Get provider (automatically selects synthetic vs real based on env)
soil_provider = ProviderFactory.get_provider("soil")

# Make request
request = DataRequest(
    latitude=29.7604,
    longitude=-95.3698,
    radius_km=10.0
)

# Fetch data
soil_data = await soil_provider.get_data(request)

print(soil_data)
# Output:
#    latitude  longitude  resistivity_ohm_cm   ph  corrosivity_class
# 0   29.7604   -95.3698              1450.2  6.8          corrosive
```

### With Caching

```python
from corrdata.providers.cached import CachedProvider

# Wrap provider with caching
soil_provider = ProviderFactory.get_provider("soil", use_synthetic=False)
cached_provider = CachedProvider(soil_provider, ttl_hours=24)

# First call hits API
data1 = await cached_provider.get_data(request)  # API call

# Second call uses cache
data2 = await cached_provider.get_data(request)  # From cache (fast)
```

### Corridor Analysis

```python
from shapely.geometry import LineString

# Define pipeline route
pipeline_route = LineString([
    (-95.5, 29.7),
    (-95.4, 29.8),
    (-95.3, 29.9)
])

# Get soil data along corridor
corridor_request = CorridorRequest(
    geometry=pipeline_route,
    buffer_meters=100
)

soil_gdf = await soil_provider.get_corridor_data(corridor_request)

# Analyze corrosivity along route
high_risk_sections = soil_gdf[
    soil_gdf["corrosivity_class"].isin(["corrosive", "severely_corrosive"])
]

print(f"High risk sections: {len(high_risk_sections)} / {len(soil_gdf)}")
```

## Learnings

### From Sprint 110 (Hazard Levels)

- **Regional profiles improve realism**: Synthetic providers should use statistical models based on geography
- **Hazard classification matters**: Standardize classification schemes (ASTM G187 for soil corrosivity)
- **Confidence scoring**: Real data gets confidence=1.0, synthetic gets confidence=0.7
- **Metadata is valuable**: Include source provenance even for synthetic data

### From Multiple Sprints

- **File-based caching works**: Parquet format is fast and compact for DataFrames
- **TTL tuning**: 24 hours works well for soil data (rarely changes), shorter for weather
- **Session reuse critical**: aiohttp sessions must be reused for performance
- **Schema documentation**: Always return schema from `get_schema()` for API documentation
- **Async everywhere**: All providers must be async for parallel fetching

## Anti-Patterns

### Don't: Create Provider Instance Every Call

**What it looks like**:
```python
# Bad - creates new instance every time
def get_soil_data(lat, lon):
    provider = SSURGOProvider()  # New session every call
    return await provider.get_data(request)
```

**Why it's bad**: Creates new HTTP session every call, wastes resources.

**Instead**: Use factory pattern to reuse provider instances.

### Don't: Mix Synthetic and Real Data

**What it looks like**:
```python
# Bad - unpredictable behavior
if random.random() > 0.5:
    provider = SyntheticSoilProvider()
else:
    provider = SSURGOProvider()
```

**Why it's bad**: Inconsistent results, hard to debug, violates reproducibility.

**Instead**: Use environment variable to control which provider is used globally.

### Don't: Ignore Health Checks

**What it looks like**:
```python
# Bad - no fallback when API is down
data = await real_provider.get_data(request)  # Fails if API down
```

**Why it's bad**: Application breaks when external API has outage.

**Instead**: Implement health checks and fallback to cached/synthetic data.

### Don't: Return Inconsistent Schemas

**What it looks like**:
```python
# Bad - different column names per provider
# SyntheticSoilProvider returns "resistivity"
# SSURGOProvider returns "soil_resistivity"
```

**Why it's bad**: Breaks code that expects consistent schema.

**Instead**: Transform all providers to common schema in base class contract.

## Variations

### For High-Frequency Updates (Weather)

```python
class WeatherProvider(DataProvider):
    def __init__(self, cache_ttl_minutes: int = 15):
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)  # Shorter TTL
```

### For Batch Processing

```python
async def get_data_batch(
    self,
    requests: list[DataRequest]
) -> pd.DataFrame:
    """Fetch multiple locations in parallel."""
    results = await asyncio.gather(*[
        self.get_data(req) for req in requests
    ])
    return pd.concat(results, ignore_index=True)
```

### For Fallback Strategy

```python
class ResilientProvider(DataProvider):
    def __init__(
        self,
        primary: DataProvider,
        fallback: DataProvider,
        max_retries: int = 3
    ):
        self.primary = primary
        self.fallback = fallback
        self.max_retries = max_retries

    async def get_data(self, request: DataRequest) -> pd.DataFrame:
        for attempt in range(self.max_retries):
            try:
                return await self.primary.get_data(request)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # Fall back to synthetic/cached
                    return await self.fallback.get_data(request)
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Related Recipes

- [Three-Layer Database](./three-layer-database.md) - Storing provider data
- [GraphQL Schema Design](./graphql-schema.md) - Exposing provider data via API
- [MCP Tool Registry](./mcp-tool-registry.md) - Exposing providers as LLM tools

## Verification

### Test Provider Registration

```python
from corrdata.providers.factory import ProviderFactory

# List all registered providers
print(ProviderFactory._providers.keys())

# Expected: dict_keys(['synthetic_soil', 'real_soil', ...])
```

### Test Health Check

```python
provider = ProviderFactory.get_provider("soil", use_synthetic=False)
is_healthy = await provider.health_check()
print(f"Provider healthy: {is_healthy}")
```

### Test Schema Consistency

```python
synthetic = ProviderFactory.get_provider("soil", use_synthetic=True)
real = ProviderFactory.get_provider("soil", use_synthetic=False)

synthetic_schema = synthetic.get_schema()
real_schema = real.get_schema()

# Should have same column names
assert set(synthetic_schema["columns"].keys()) == set(real_schema["columns"].keys())
```

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-14 | Initial version based on ADR-012, ADR-032, Sprint 110 patterns |
