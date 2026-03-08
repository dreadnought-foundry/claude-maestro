# Playbook: Adding a New External Data Source

**Category**: playbook
**Version**: 1.0
**Last Updated**: 2025-12-14
**Estimated Time**: 2-3 hours
**Prerequisites**:
- Python 3.11+
- Understanding of the Provider Pattern (see patterns/provider-pattern.md)
- API access credentials for external data source (if applicable)
- Knowledge of the data structure and API endpoints

**Related Patterns**:
- [Provider Pattern](../patterns/provider-pattern.md)
- [Data Provider Factory (ADR-032)](../../architecture/decisions/ADR-032-data-provider-factory.md)
- [External Data Integration (ADR-012)](../../architecture/decisions/ADR-012-external-data-integration-pattern.md)
- [Environment-Based Configuration (ADR-016)](../../architecture/decisions/ADR-016-environment-based-configuration.md)
- [File-Based Caching (ADR-017)](../../architecture/decisions/ADR-017-file-based-caching.md)

## Overview

This playbook guides you through adding a new external data source to CorrData using the Provider Pattern. The Provider Pattern enables seamless switching between synthetic (mock) and real data sources through environment configuration, allowing development and testing without API dependencies.

External data sources might include:
- Geospatial APIs (USGS, NOAA, FEMA)
- Weather and climate services
- Soil and environmental databases
- Regulatory compliance databases
- Third-party corrosion or material databases

## When to Use This Playbook

- You need to integrate a new external API or data service
- You want to add support for a new geospatial data layer
- You need environmental or regulatory data for risk calculations
- You're replacing synthetic data with a real API connection
- You want to provide both mock and production data sources

## Checklist

- [ ] Step 1: Define data requirements and API interface
- [ ] Step 2: Create synthetic provider implementation
- [ ] Step 3: Create real provider implementation
- [ ] Step 4: Register providers with factory
- [ ] Step 5: Add environment configuration
- [ ] Step 6: Create tests for both providers
- [ ] Step 7: Update documentation

## Step 1: Define Data Requirements

### What You'll Do
Analyze the external data source, understand its API structure, define what data you need, and document the interface that both providers will implement.

### Instructions

1. Research the external API documentation
2. Identify required data fields
3. Determine query parameters and response format
4. Document data structure and constraints
5. Define error handling requirements

### Example: Adding a Vegetation Cover Data Source

Let's say we want to add vegetation cover data from a hypothetical "VegCover API" that provides information about plant coverage, which affects corrosion risk due to moisture retention.

**API Research:**
- Endpoint: `https://api.vegcover.example.com/v1/coverage`
- Authentication: API key in header
- Parameters: latitude, longitude, radius
- Response: JSON with coverage type, density, moisture index

**Data Requirements Document:**
```python
# Vegetation Cover Data Requirements
#
# Purpose: Determine vegetation type and density around pipeline assets
# to assess moisture retention risk.
#
# Required Fields:
# - coverage_type: string (grass, shrubs, trees, bare, agricultural)
# - coverage_density: float (0.0-1.0, where 1.0 is 100% coverage)
# - moisture_retention_index: float (0.0-1.0, higher = more moisture)
# - dominant_species: list[str]
# - source: string (data source identifier)
#
# API Details:
# - Base URL: https://api.vegcover.example.com/v1
# - Auth: Bearer token in Authorization header
# - Rate Limit: 100 requests/minute
# - Coverage: North America only
```

### Verification
- Data requirements documented
- API endpoints identified
- Authentication method understood
- Response structure mapped

## Step 2: Create Synthetic Provider Implementation

### What You'll Do
Create a synthetic (mock) provider that generates realistic test data without requiring API credentials. This enables development and testing without external dependencies.

### Files to Create/Modify
- `src/corrdata/providers/synthetic.py` (append new provider class)

### Code

```python
# Add to src/corrdata/providers/synthetic.py

import random
from typing import Any

from corrdata.config import DataMode
from corrdata.providers.base import DataProvider


class SyntheticVegCoverProvider(DataProvider):
    """Synthetic vegetation cover provider for testing and development.

    Generates realistic vegetation data based on latitude/longitude patterns.
    Northern latitudes tend toward forest, southern toward grassland/shrubs.
    """

    @property
    def name(self) -> str:
        return "veg_cover"

    @property
    def mode(self) -> DataMode:
        return DataMode.SYNTHETIC

    def get_data(
        self,
        lat: float,
        lon: float,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate synthetic vegetation cover data.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            **kwargs: Additional parameters (radius, season)

        Returns:
            Dictionary with vegetation cover data
        """
        # Use lat/lon to seed random for consistent results
        random.seed(int((lat + lon) * 10000))

        # Northern latitudes (>45°) tend toward forest
        # Mid latitudes (30-45°) tend toward grass/agricultural
        # Southern latitudes (<30°) tend toward shrubs/bare
        if lat > 45:
            coverage_types = ["trees", "trees", "grass", "shrubs"]
            base_density = 0.7
            base_moisture = 0.6
        elif lat > 30:
            coverage_types = ["grass", "agricultural", "grass", "shrubs"]
            base_density = 0.5
            base_moisture = 0.4
        else:
            coverage_types = ["shrubs", "bare", "grass", "agricultural"]
            base_density = 0.3
            base_moisture = 0.2

        coverage_type = random.choice(coverage_types)

        # Add some randomness to density and moisture
        density = min(1.0, max(0.0, base_density + random.uniform(-0.2, 0.2)))
        moisture = min(1.0, max(0.0, base_moisture + random.uniform(-0.15, 0.15)))

        # Generate species list based on coverage type
        species_map = {
            "trees": ["Oak", "Pine", "Maple", "Birch"],
            "grass": ["Bluegrass", "Fescue", "Ryegrass"],
            "shrubs": ["Sagebrush", "Juniper", "Mesquite"],
            "agricultural": ["Corn", "Soybeans", "Wheat"],
            "bare": [],
        }

        species = species_map.get(coverage_type, [])
        dominant = random.sample(species, min(2, len(species))) if species else []

        return {
            "coverage_type": coverage_type,
            "coverage_density": round(density, 2),
            "moisture_retention_index": round(moisture, 2),
            "dominant_species": dominant,
            "source": "synthetic",
            "location": {
                "latitude": lat,
                "longitude": lon,
            },
        }

    def is_available(self, lat: float, lon: float) -> bool:
        """Synthetic data is always available."""
        return True
```

### Verification
```bash
# Test the synthetic provider in Python REPL
python3 -c "
from corrdata.providers.synthetic import SyntheticVegCoverProvider

provider = SyntheticVegCoverProvider()
data = provider.get_data(lat=40.7128, lon=-74.0060)  # New York
print(data)
"
```

Expected output should show realistic vegetation data for NYC area.

## Step 3: Create Real Provider Implementation

### What You'll Do
Create the real provider that connects to the actual external API. Include proper error handling, rate limiting, and caching.

### Files to Create/Modify
- `src/corrdata/providers/real.py` (append new provider class)

### Code

```python
# Add to src/corrdata/providers/real.py

import os
from typing import Any

import httpx

from corrdata.config import DataMode
from corrdata.providers.base import DataProvider


class RealVegCoverProvider(DataProvider):
    """Real vegetation cover provider using VegCover API.

    Requires VEGCOVER_API_KEY environment variable.
    Data available for North America only.
    """

    def __init__(self):
        """Initialize with API credentials."""
        self.api_key = os.getenv("VEGCOVER_API_KEY")
        if not self.api_key:
            raise ValueError("VEGCOVER_API_KEY environment variable required")

        self.base_url = os.getenv(
            "VEGCOVER_API_URL",
            "https://api.vegcover.example.com/v1"
        )
        self.timeout = float(os.getenv("VEGCOVER_TIMEOUT", "30.0"))

    @property
    def name(self) -> str:
        return "veg_cover"

    @property
    def mode(self) -> DataMode:
        return DataMode.REAL

    def get_data(
        self,
        lat: float,
        lon: float,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Fetch vegetation cover data from VegCover API.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            **kwargs: Additional parameters:
                - radius: Query radius in meters (default: 100)
                - season: Season for temporal analysis (spring/summer/fall/winter)

        Returns:
            Dictionary with vegetation cover data

        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If location is outside coverage area
        """
        radius = kwargs.get("radius", 100)
        season = kwargs.get("season")

        # Build request parameters
        params = {
            "lat": lat,
            "lon": lon,
            "radius": radius,
        }
        if season:
            params["season"] = season

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        # Make API request
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/coverage",
                params=params,
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()

        # Transform API response to standard format
        return {
            "coverage_type": data.get("type", "unknown"),
            "coverage_density": data.get("density", 0.0),
            "moisture_retention_index": data.get("moisture_index", 0.0),
            "dominant_species": data.get("species", []),
            "source": "vegcover_api",
            "location": {
                "latitude": lat,
                "longitude": lon,
            },
            "metadata": {
                "query_radius_m": radius,
                "season": season,
                "query_timestamp": data.get("timestamp"),
            },
        }

    def is_available(self, lat: float, lon: float) -> bool:
        """Check if data is available for location.

        VegCover API covers North America only (lat 15-70, lon -170 to -50).
        """
        return (15 <= lat <= 70) and (-170 <= lon <= -50)
```

### Verification
```bash
# Set test API key
export VEGCOVER_API_KEY="test-key-here"

# Test the real provider (will fail if API not accessible)
python3 -c "
from corrdata.providers.real import RealVegCoverProvider

provider = RealVegCoverProvider()
print(f'Provider initialized: {provider.name}')
print(f'Available for NYC: {provider.is_available(40.7128, -74.0060)}')
print(f'Available for Tokyo: {provider.is_available(35.6762, 139.6503)}')
"
```

## Step 4: Register Providers with Factory

### What You'll Do
Register both synthetic and real providers with the DataProviderFactory so they can be accessed through the factory pattern.

### Files to Modify
- `src/corrdata/providers/factory.py`
- `src/corrdata/config.py`

### Code

**1. Add configuration in `src/corrdata/config.py`:**

```python
# Add to src/corrdata/config.py after other mode definitions

# Vegetation cover data mode
VEGCOVER_MODE = DataMode(os.getenv("VEGCOVER_MODE", DATA_MODE.value))
```

**2. Update factory registration in `src/corrdata/providers/factory.py`:**

```python
# In DataProviderFactory class, update _mode_overrides dict
_mode_overrides: dict[str, DataMode] = {
    "elevation": ELEVATION_MODE,
    "land_cover": NLCD_MODE,
    "flood_zone": FLOOD_ZONE_MODE,
    "soil": SOIL_MODE,
    "climate": CLIMATE_MODE,
    "water_quality": WATER_QUALITY_MODE,
    "seismic": SEISMIC_MODE,
    "subsidence": SUBSIDENCE_MODE,
    "veg_cover": VEGCOVER_MODE,  # ADD THIS LINE
}
```

**3. Update `_register_default_providers()` function:**

```python
def _register_default_providers() -> None:
    """Register default synthetic and real providers."""
    from corrdata.providers.real import (
        RealClimateProvider,
        RealElevationProvider,
        RealFloodZoneProvider,
        RealLandCoverProvider,
        RealSeismicProvider,
        RealSoilProvider,
        RealSubsidenceProvider,
        RealWaterQualityProvider,
        RealVegCoverProvider,  # ADD THIS
    )
    from corrdata.providers.synthetic import (
        SyntheticClimateProvider,
        SyntheticElevationProvider,
        SyntheticFloodZoneProvider,
        SyntheticLandCoverProvider,
        SyntheticSeismicProvider,
        SyntheticSoilProvider,
        SyntheticSubsidenceProvider,
        SyntheticWaterQualityProvider,
        SyntheticVegCoverProvider,  # ADD THIS
    )

    # ... existing registrations ...

    # ADD THESE TWO LINES:
    DataProviderFactory.register("veg_cover", DataMode.SYNTHETIC, SyntheticVegCoverProvider)
    DataProviderFactory.register("veg_cover", DataMode.REAL, RealVegCoverProvider)
```

### Verification
```python
# Test factory registration
python3 -c "
from corrdata.providers.factory import DataProviderFactory
from corrdata.config import DataMode

# List all registered providers
print('Registered providers:', DataProviderFactory.list_providers())

# Get synthetic provider
synth_provider = DataProviderFactory.get_provider('veg_cover', DataMode.SYNTHETIC)
print(f'Synthetic provider: {synth_provider}')

# Get real provider (requires API key)
# real_provider = DataProviderFactory.get_provider('veg_cover', DataMode.REAL)
# print(f'Real provider: {real_provider}')
"
```

## Step 5: Add Environment Configuration

### What You'll Do
Document environment variables and create example configuration for both development and production environments.

### Files to Create/Modify
- `.env.example` (update)
- `README.md` or relevant documentation

### Code

**Update `.env.example`:**

```bash
# Add to .env.example

# ============================================================================
# Vegetation Cover Provider Configuration
# ============================================================================

# Mode: 'synthetic' (default) or 'real'
VEGCOVER_MODE=synthetic

# Real provider configuration (only needed if VEGCOVER_MODE=real)
VEGCOVER_API_KEY=your-api-key-here
VEGCOVER_API_URL=https://api.vegcover.example.com/v1
VEGCOVER_TIMEOUT=30.0
```

**Create documentation snippet:**

```markdown
## Vegetation Cover Data Configuration

### Development (Default)
Uses synthetic data - no configuration needed:
```bash
export VEGCOVER_MODE=synthetic
```

### Production
Requires API credentials:
```bash
export VEGCOVER_MODE=real
export VEGCOVER_API_KEY="your-production-api-key"
```

### Per-Location Fallback
Use real data where available, synthetic elsewhere:
```python
from corrdata.providers.factory import DataProviderFactory

# Automatically selects best provider for location
provider = DataProviderFactory.get_provider_for_location(
    name="veg_cover",
    latitude=40.7128,
    longitude=-74.0060
)
```
```

### Verification
```bash
# Test different modes
export VEGCOVER_MODE=synthetic
python3 -c "from corrdata.providers.factory import DataProviderFactory; p = DataProviderFactory.get_provider('veg_cover'); print(p.mode)"

export VEGCOVER_MODE=real
export VEGCOVER_API_KEY=test
python3 -c "from corrdata.providers.factory import DataProviderFactory; p = DataProviderFactory.get_provider('veg_cover'); print(p.mode)"
```

## Step 6: Create Tests for Both Providers

### What You'll Do
Write comprehensive tests for both synthetic and real providers, including unit tests, integration tests, and error cases.

### Files to Create
- `tests/test_veg_cover_providers.py`

### Code

```python
# tests/test_veg_cover_providers.py

import os
from unittest.mock import Mock, patch

import httpx
import pytest

from corrdata.config import DataMode
from corrdata.providers.factory import DataProviderFactory
from corrdata.providers.real import RealVegCoverProvider
from corrdata.providers.synthetic import SyntheticVegCoverProvider


class TestSyntheticVegCoverProvider:
    """Test suite for synthetic vegetation cover provider."""

    def test_provider_properties(self):
        """Test provider name and mode."""
        provider = SyntheticVegCoverProvider()
        assert provider.name == "veg_cover"
        assert provider.mode == DataMode.SYNTHETIC

    def test_get_data_basic(self):
        """Test basic data retrieval."""
        provider = SyntheticVegCoverProvider()
        data = provider.get_data(lat=40.7128, lon=-74.0060)

        # Verify required fields
        assert "coverage_type" in data
        assert "coverage_density" in data
        assert "moisture_retention_index" in data
        assert "dominant_species" in data
        assert "source" in data

        # Verify data types and ranges
        assert isinstance(data["coverage_type"], str)
        assert 0.0 <= data["coverage_density"] <= 1.0
        assert 0.0 <= data["moisture_retention_index"] <= 1.0
        assert isinstance(data["dominant_species"], list)
        assert data["source"] == "synthetic"

    def test_get_data_consistency(self):
        """Test that same coordinates return consistent data."""
        provider = SyntheticVegCoverProvider()

        data1 = provider.get_data(lat=40.7128, lon=-74.0060)
        data2 = provider.get_data(lat=40.7128, lon=-74.0060)

        assert data1["coverage_type"] == data2["coverage_type"]
        assert data1["coverage_density"] == data2["coverage_density"]

    def test_get_data_latitude_patterns(self):
        """Test that northern latitudes tend toward forest."""
        provider = SyntheticVegCoverProvider()

        # Test northern latitude (should favor trees)
        northern_data = provider.get_data(lat=55.0, lon=-100.0)
        assert northern_data["coverage_density"] > 0.5

        # Test southern latitude (should favor shrubs/bare)
        southern_data = provider.get_data(lat=25.0, lon=-100.0)
        # Just verify it returns valid data
        assert 0.0 <= southern_data["coverage_density"] <= 1.0

    def test_is_available(self):
        """Test that synthetic data is always available."""
        provider = SyntheticVegCoverProvider()
        assert provider.is_available(40.7128, -74.0060)
        assert provider.is_available(0.0, 0.0)
        assert provider.is_available(90.0, 180.0)

    def test_get_corridor_data(self):
        """Test corridor data retrieval."""
        provider = SyntheticVegCoverProvider()

        corridor_data = provider.get_corridor_data(
            start=(-74.0060, 40.7128),  # NYC
            end=(-118.2437, 34.0522),   # LA
            sample_count=5
        )

        assert len(corridor_data) == 5
        assert all("coverage_type" in d for d in corridor_data)
        assert all("location" in d for d in corridor_data)


class TestRealVegCoverProvider:
    """Test suite for real vegetation cover provider."""

    def test_provider_properties(self):
        """Test provider name and mode."""
        with patch.dict(os.environ, {"VEGCOVER_API_KEY": "test-key"}):
            provider = RealVegCoverProvider()
            assert provider.name == "veg_cover"
            assert provider.mode == DataMode.REAL

    def test_initialization_requires_api_key(self):
        """Test that initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="VEGCOVER_API_KEY"):
                RealVegCoverProvider()

    def test_is_available_north_america(self):
        """Test coverage check for North America."""
        with patch.dict(os.environ, {"VEGCOVER_API_KEY": "test-key"}):
            provider = RealVegCoverProvider()

            # Within coverage
            assert provider.is_available(40.7128, -74.0060)  # NYC
            assert provider.is_available(34.0522, -118.2437)  # LA

            # Outside coverage
            assert not provider.is_available(35.6762, 139.6503)  # Tokyo
            assert not provider.is_available(-33.8688, 151.2093)  # Sydney

    @patch("httpx.Client")
    def test_get_data_success(self, mock_client_class):
        """Test successful API data retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "type": "grass",
            "density": 0.75,
            "moisture_index": 0.45,
            "species": ["Bluegrass", "Fescue"],
            "timestamp": "2025-12-14T10:00:00Z",
        }
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client

        with patch.dict(os.environ, {"VEGCOVER_API_KEY": "test-key"}):
            provider = RealVegCoverProvider()
            data = provider.get_data(lat=40.7128, lon=-74.0060)

        # Verify API call
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "/coverage" in call_args[0][0]
        assert call_args[1]["params"]["lat"] == 40.7128
        assert call_args[1]["params"]["lon"] == -74.0060
        assert "Bearer test-key" in call_args[1]["headers"]["Authorization"]

        # Verify transformed data
        assert data["coverage_type"] == "grass"
        assert data["coverage_density"] == 0.75
        assert data["moisture_retention_index"] == 0.45
        assert data["dominant_species"] == ["Bluegrass", "Fescue"]
        assert data["source"] == "vegcover_api"

    @patch("httpx.Client")
    def test_get_data_with_optional_params(self, mock_client_class):
        """Test API call with optional parameters."""
        mock_response = Mock()
        mock_response.json.return_value = {"type": "grass", "density": 0.5, "moisture_index": 0.3}
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client

        with patch.dict(os.environ, {"VEGCOVER_API_KEY": "test-key"}):
            provider = RealVegCoverProvider()
            provider.get_data(lat=40.7128, lon=-74.0060, radius=200, season="summer")

        # Verify optional params passed
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["radius"] == 200
        assert call_args[1]["params"]["season"] == "summer"

    @patch("httpx.Client")
    def test_get_data_api_error(self, mock_client_class):
        """Test API error handling."""
        mock_client = Mock()
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=Mock(),
            response=Mock(status_code=404),
        )
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client

        with patch.dict(os.environ, {"VEGCOVER_API_KEY": "test-key"}):
            provider = RealVegCoverProvider()

            with pytest.raises(httpx.HTTPStatusError):
                provider.get_data(lat=40.7128, lon=-74.0060)


class TestVegCoverProviderFactory:
    """Test factory integration."""

    def test_factory_registration(self):
        """Test that providers are registered with factory."""
        providers = DataProviderFactory.list_providers()
        assert "veg_cover" in providers
        assert "synthetic" in providers["veg_cover"]
        assert "real" in providers["veg_cover"]

    def test_get_synthetic_provider(self):
        """Test getting synthetic provider from factory."""
        provider = DataProviderFactory.get_provider("veg_cover", DataMode.SYNTHETIC)
        assert isinstance(provider, SyntheticVegCoverProvider)
        assert provider.mode == DataMode.SYNTHETIC

    def test_get_real_provider(self):
        """Test getting real provider from factory."""
        with patch.dict(os.environ, {"VEGCOVER_API_KEY": "test-key"}):
            provider = DataProviderFactory.get_provider("veg_cover", DataMode.REAL)
            assert isinstance(provider, RealVegCoverProvider)
            assert provider.mode == DataMode.REAL

    @patch.dict(os.environ, {"VEGCOVER_MODE": "synthetic"})
    def test_get_provider_respects_mode(self):
        """Test that factory respects VEGCOVER_MODE environment variable."""
        from importlib import reload
        from corrdata import config
        reload(config)  # Reload to pick up env var

        provider = DataProviderFactory.get_provider("veg_cover")
        assert provider.mode == DataMode.SYNTHETIC
```

### Verification
```bash
# Run tests
pytest tests/test_veg_cover_providers.py -v

# Run with coverage
pytest tests/test_veg_cover_providers.py --cov=corrdata.providers --cov-report=term-missing
```

Expected: All tests pass with >90% coverage.

## Step 7: Update Documentation

### What You'll Do
Document the new provider in the playbook, update relevant ADRs, and create usage examples.

### Files to Create/Modify
- `docs/playbook/patterns/provider-pattern.md` (update)
- `docs/examples/using-veg-cover-data.md` (create)

### Code

**Create usage example:**

```markdown
# Example: Using Vegetation Cover Data

## Basic Usage

```python
from corrdata.providers.factory import DataProviderFactory

# Get provider (uses environment config)
provider = DataProviderFactory.get_provider("veg_cover")

# Get data for a location
data = provider.get_data(lat=40.7128, lon=-74.0060)

print(f"Coverage: {data['coverage_type']}")
print(f"Density: {data['coverage_density']}")
print(f"Moisture: {data['moisture_retention_index']}")
```

## Integration with Risk Scoring

```python
from corrdata.analytics.risk_scoring import calculate_vegetation_risk

# Get vegetation data
veg_data = provider.get_data(lat=segment.latitude, lon=segment.longitude)

# Calculate risk contribution
risk_score = calculate_vegetation_risk(
    coverage_type=veg_data['coverage_type'],
    moisture_index=veg_data['moisture_retention_index'],
    coating_condition=segment.coating_condition
)
```

## Corridor Analysis

```python
# Analyze vegetation along pipeline corridor
corridor_data = provider.get_corridor_data(
    start=(-74.0060, 40.7128),
    end=(-118.2437, 34.0522),
    sample_count=20
)

# Identify high-risk areas
high_risk_areas = [
    d for d in corridor_data
    if d['moisture_retention_index'] > 0.7
]
```
```

### Verification
- Documentation is clear and complete
- Examples work as written
- Related patterns are cross-referenced

## Troubleshooting

### Common Issue 1: API Authentication Fails
**Symptom**: `ValueError: VEGCOVER_API_KEY environment variable required`

**Solution**:
```bash
export VEGCOVER_API_KEY="your-api-key-here"
# Verify it's set
echo $VEGCOVER_API_KEY
```

### Common Issue 2: Import Errors After Registration
**Symptom**: `ImportError: cannot import name 'RealVegCoverProvider'`

**Solution**: Ensure provider classes are added to the correct files:
- Synthetic provider in `src/corrdata/providers/synthetic.py`
- Real provider in `src/corrdata/providers/real.py`
- Both imported in `src/corrdata/providers/factory.py`

### Common Issue 3: Factory Returns Wrong Provider
**Symptom**: Getting synthetic provider when expecting real

**Solution**: Check environment variable precedence:
1. Specific override: `VEGCOVER_MODE=real`
2. Global mode: `DATA_MODE=real`
3. Default: synthetic

```bash
# Force real mode for this provider only
export VEGCOVER_MODE=real
export VEGCOVER_API_KEY=your-key
```

### Common Issue 4: API Rate Limiting
**Symptom**: `httpx.HTTPStatusError: 429 Too Many Requests`

**Solution**: Implement caching wrapper (see ADR-017):
```python
from corrdata.providers.cache import CachedProvider

provider = DataProviderFactory.get_provider("veg_cover")
cached_provider = CachedProvider(provider, ttl=3600)  # 1 hour cache
```

## Learnings

### From Sprint 12 (External Data Integration)
- Always provide synthetic provider first for development
- Document data coverage limitations clearly
- Include comprehensive error handling for API failures
- Test both providers with same test cases for consistency

### From Sprint 16 (Environment Configuration)
- Use environment-specific configuration for API credentials
- Provide sensible defaults (synthetic mode)
- Document all environment variables in `.env.example`

### From Sprint 17 (File-Based Caching)
- Cache expensive API calls to avoid rate limits
- Use TTL appropriate to data freshness requirements
- Monitor cache hit rates in production

## Related

- [Pattern: Provider Pattern](../patterns/provider-pattern.md)
- [Playbook: Creating REST Endpoint](./creating-rest-endpoint.md)
- [ADR-012: External Data Integration Pattern](../../architecture/decisions/ADR-012-external-data-integration-pattern.md)
- [ADR-032: Data Provider Factory](../../architecture/decisions/ADR-032-data-provider-factory.md)

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-14 | Initial version - comprehensive external data source integration guide |
