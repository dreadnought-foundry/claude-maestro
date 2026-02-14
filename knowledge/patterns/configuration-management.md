# Recipe: Configuration Management

**Category**: pattern
**Version**: 1.0
**Last Updated**: 2025-12-14
**Sprints**: Sprint 68 (AWS Secrets Manager integration)
**ADRs**: [ADR-016: Environment-Based Configuration](../../architecture/decisions/ADR-016-environment-based-configuration.md), [ADR-042: AWS Infrastructure Configuration](../../architecture/decisions/ADR-042-aws-infrastructure-configuration.md)

## Context

**When to use this recipe:**
- You need to configure environment-specific settings (dev, staging, production)
- You want to switch between synthetic and real data providers
- You need to manage secrets securely (database credentials, API keys)
- You're deploying to AWS and need to integrate with Secrets Manager
- You need per-source data mode overrides for gradual migration

**When NOT to use this recipe:**
- For application constants that never change (use Python constants)
- For runtime user preferences (use database storage)
- For feature flags that change frequently (use feature flag service)
- For distributed configuration across microservices (use config server like Consul)

## Ingredients

Before starting, ensure you have:

- [ ] Environment variables or `.env` file for local development
- [ ] AWS Secrets Manager access (for production deployments)
- [ ] Understanding of the 12-factor app configuration principles
- [ ] List of configuration values your application needs
- [ ] Appropriate IAM permissions for Secrets Manager (if using AWS)

## Steps

### Step 1: Define Configuration Schema

Create a clear separation between legacy environment variables and AWS Secrets Manager configuration.

**CorrData uses a two-layer approach:**
1. **Legacy config** (`config_legacy.py`) - Simple environment variables for development
2. **Secrets Manager** (`config/secrets.py`) - Production secrets from AWS

```python
# src/corrdata/config/__init__.py
"""
Configuration module with AWS Secrets Manager integration.

Provides:
- get_secret() - Fetch from AWS Secrets Manager (production)
- get_database_url() - Database URL with fallback to environment
- Legacy environment variables - DataMode, corridors, etc.
"""

from corrdata.config.secrets import (
    get_secret,
    get_database_url,
    get_database_config,
    clear_secrets_cache,
)

from corrdata.config_legacy import (
    DataMode,
    DATA_MODE,
    ELEVATION_MODE,
    SOIL_MODE,
    # ... other legacy config items
)
```

**Expected outcome**: Clear separation between development (env vars) and production (AWS Secrets Manager) configuration.

### Step 2: Implement Data Mode Switching

Set up environment-based data mode configuration with per-source overrides.

```python
# src/corrdata/config_legacy.py
from enum import Enum
import os

class DataMode(str, Enum):
    """Data source mode."""
    SYNTHETIC = "synthetic"  # Generated data for demos/testing
    REAL = "real"            # Real external data for production

# Global data mode - default to synthetic for development
DATA_MODE = DataMode(os.getenv("DATA_MODE", "synthetic"))

# Per-source overrides (optional, for gradual migration)
ELEVATION_MODE = DataMode(os.getenv("ELEVATION_MODE", DATA_MODE.value))
SOIL_MODE = DataMode(os.getenv("SOIL_MODE", DATA_MODE.value))
CLIMATE_MODE = DataMode(os.getenv("CLIMATE_MODE", DATA_MODE.value))
FLOOD_ZONE_MODE = DataMode(os.getenv("FLOOD_ZONE_MODE", DATA_MODE.value))
WATER_QUALITY_MODE = DataMode(os.getenv("WATER_QUALITY_MODE", DATA_MODE.value))
SEISMIC_MODE = DataMode(os.getenv("SEISMIC_MODE", DATA_MODE.value))
SUBSIDENCE_MODE = DataMode(os.getenv("SUBSIDENCE_MODE", DATA_MODE.value))
NLCD_MODE = DataMode(os.getenv("NLCD_MODE", DATA_MODE.value))

# API Keys (only needed for DATA_MODE=real)
NOAA_CDO_API_TOKEN = os.getenv("NOAA_CDO_API_TOKEN", "")

# Cache settings
DATA_CACHE_DIR = os.getenv("DATA_CACHE_DIR", "data/external/cache")
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
```

**Expected outcome**: Application can switch between synthetic and real data via environment variables.

### Step 3: Create Environment Templates

Provide `.env.example` template for developers with all configuration options documented.

```bash
# .env.example

# =============================================================================
# DATA MODE CONFIGURATION
# =============================================================================
# Global data mode: synthetic (default) or real
DATA_MODE=synthetic

# Per-source overrides (uncomment to override global setting)
# ELEVATION_MODE=real
# SOIL_MODE=real
# CLIMATE_MODE=real
# FLOOD_ZONE_MODE=real
# WATER_QUALITY_MODE=real
# NLCD_MODE=real
# SEISMIC_MODE=real
# SUBSIDENCE_MODE=real

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
# Local development (asyncpg for async operations)
DATABASE_URL=postgresql+asyncpg://corrdata:corrdata@localhost:5432/corrdata
DATABASE_ECHO=false

# =============================================================================
# NEO4J CONFIGURATION
# =============================================================================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# =============================================================================
# CACHING CONFIGURATION
# =============================================================================
DATA_CACHE_DIR=data/cache
CACHE_TTL_HOURS=24

# =============================================================================
# EXTERNAL API KEYS (required for real mode)
# =============================================================================
# NOAA Climate Data Online API
# Get your key at: https://www.ncdc.noaa.gov/cdo-web/token
# NOAA_CDO_API_TOKEN=your-api-key-here

# =============================================================================
# AWS CONFIGURATION (production only)
# =============================================================================
# AWS_REGION=us-east-1
# AWS_SECRET_NAME=corrdata/production/database
# AWS_PROFILE=corrdata-production  # For local AWS CLI testing
```

**Expected outcome**: Developers can copy `.env.example` to `.env` and have working local configuration.

### Step 4: Implement AWS Secrets Manager Integration

For production deployments, integrate with AWS Secrets Manager for secure secret storage.

```python
# src/corrdata/config/secrets.py
"""
AWS Secrets Manager integration for production configuration.

Provides secure secret retrieval with local environment fallback.
"""

import os
import json
import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

def get_secret(secret_name: str, region: str | None = None) -> dict[str, Any]:
    """
    Retrieve secret from AWS Secrets Manager.

    Falls back to environment variables in development.

    Args:
        secret_name: Name of the secret (e.g., 'corrdata/production/database')
        region: AWS region (defaults to AWS_REGION env var or 'us-east-1')

    Returns:
        Dictionary containing secret values

    Raises:
        ValueError: If secret not found and no fallback available
    """
    # Check if running in AWS (has IAM role)
    if os.getenv("AWS_EXECUTION_ENV") or os.getenv("AWS_REGION"):
        return _get_secret_from_aws(secret_name, region)
    else:
        logger.info(f"Not in AWS environment, using local config for {secret_name}")
        return _get_secret_from_env(secret_name)

def _get_secret_from_aws(secret_name: str, region: str | None = None) -> dict[str, Any]:
    """Fetch secret from AWS Secrets Manager."""
    import boto3
    from botocore.exceptions import ClientError

    region = region or os.getenv("AWS_REGION", "us-east-1")

    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])
    except ClientError as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        raise ValueError(f"Secret {secret_name} not found in AWS Secrets Manager")

def _get_secret_from_env(secret_name: str) -> dict[str, Any]:
    """Fallback to environment variables for local development."""
    # Map secret names to environment variable patterns
    if "database" in secret_name.lower():
        return {
            "username": os.getenv("DATABASE_USER", "corrdata"),
            "password": os.getenv("DATABASE_PASSWORD", "corrdata"),
            "host": os.getenv("DATABASE_HOST", "localhost"),
            "port": int(os.getenv("DATABASE_PORT", "5432")),
            "database": os.getenv("DATABASE_NAME", "corrdata"),
        }
    else:
        raise ValueError(f"No local fallback defined for secret: {secret_name}")

@lru_cache(maxsize=10)
def get_database_config() -> dict[str, Any]:
    """
    Get database configuration from Secrets Manager or environment.

    Cached to avoid repeated AWS API calls.
    """
    secret_name = os.getenv("DATABASE_SECRET_NAME", "corrdata/production/database")
    return get_secret(secret_name)

def get_database_url() -> str:
    """
    Get database URL, preferring DATABASE_URL env var.

    Falls back to constructing from Secrets Manager config.
    """
    # Check for explicit DATABASE_URL first (easier for local dev)
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    # Construct from Secrets Manager config
    config = get_database_config()
    return (
        f"postgresql+asyncpg://{config['username']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['database']}"
    )

def clear_secrets_cache():
    """Clear the secrets cache (useful for testing)."""
    get_database_config.cache_clear()
```

**Expected outcome**: Application can fetch secrets from AWS Secrets Manager in production, with local environment variable fallback.

### Step 5: Integrate with Provider Factory

Use data mode configuration to select appropriate data providers.

```python
# src/corrdata/providers/factory.py
from corrdata.config import (
    DATA_MODE,
    ELEVATION_MODE,
    SOIL_MODE,
    CLIMATE_MODE,
    # ... other mode imports
    DataMode,
)

class DataProviderFactory:
    """Factory for creating data providers based on configuration."""

    # Mode overrides per source
    _mode_overrides: dict[str, DataMode] = {
        "elevation": ELEVATION_MODE,
        "soil": SOIL_MODE,
        "climate": CLIMATE_MODE,
        "flood_zone": FLOOD_ZONE_MODE,
        "water_quality": WATER_QUALITY_MODE,
        "seismic": SEISMIC_MODE,
        "subsidence": SUBSIDENCE_MODE,
        "land_cover": NLCD_MODE,
    }

    @classmethod
    def get_provider(
        cls,
        name: str,
        mode: DataMode | None = None,
    ) -> DataProvider:
        """
        Get provider instance based on configuration.

        Args:
            name: Provider name (e.g., 'elevation')
            mode: Override mode (uses per-source or global config if None)

        Returns:
            DataProvider instance (synthetic or real based on config)
        """
        # Determine effective mode
        if mode is None:
            mode = cls._mode_overrides.get(name, DATA_MODE)

        # Get and instantiate provider class
        provider_class = cls._providers[name][mode]
        return provider_class()

# Usage in MCP tools or API endpoints
provider = DataProviderFactory.get_provider("soil")  # Uses SOIL_MODE config
data = await provider.get_data(segment_uuid)
```

**Expected outcome**: Providers automatically switch based on configuration without code changes.

## Code Examples

### Gradual Migration from Synthetic to Real Data

Start with all synthetic data, then enable real data one source at a time:

```bash
# Week 1: All synthetic (default)
DATA_MODE=synthetic

# Week 2: Enable real elevation data (validated and working well)
DATA_MODE=synthetic
ELEVATION_MODE=real

# Week 3: Add soil data
DATA_MODE=synthetic
ELEVATION_MODE=real
SOIL_MODE=real

# Week 4: Add climate data
DATA_MODE=synthetic
ELEVATION_MODE=real
SOIL_MODE=real
CLIMATE_MODE=real

# Production: All real data
DATA_MODE=real
```

### Testing with Forced Modes

Override configuration in tests to ensure synthetic data:

```python
# tests/conftest.py
import pytest

@pytest.fixture(autouse=True)
def use_synthetic_data(monkeypatch):
    """Force synthetic mode for all tests."""
    monkeypatch.setenv("DATA_MODE", "synthetic")
    # Also override any per-source modes
    monkeypatch.setenv("ELEVATION_MODE", "synthetic")
    monkeypatch.setenv("SOIL_MODE", "synthetic")
    # ... etc

@pytest.fixture
def use_real_elevation(monkeypatch):
    """Test real elevation provider integration."""
    monkeypatch.setenv("ELEVATION_MODE", "real")
    monkeypatch.setenv("ELEVATION_API_KEY", "test-key")
```

### AWS Secrets Manager Secret Structure

Create secrets in AWS Secrets Manager with this structure:

```json
{
  "username": "corrdata_prod",
  "password": "secure-random-password-here",
  "host": "corrdata-prod.cluster-xxxxx.us-east-1.rds.amazonaws.com",
  "port": 5432,
  "database": "corrdata",
  "engine": "postgres"
}
```

Create via AWS CLI:

```bash
aws secretsmanager create-secret \
  --name corrdata/production/database \
  --description "CorrData production database credentials" \
  --secret-string file://database-secret.json \
  --region us-east-1

# Verify
aws secretsmanager get-secret-value \
  --secret-id corrdata/production/database \
  --region us-east-1
```

### Environment-Specific Configuration Files

Use different `.env` files for different environments:

```bash
# .env.development
DATA_MODE=synthetic
DATABASE_URL=postgresql+asyncpg://corrdata:corrdata@localhost:5432/corrdata

# .env.staging
DATA_MODE=real
DATABASE_SECRET_NAME=corrdata/staging/database
AWS_REGION=us-east-1

# .env.production
DATA_MODE=real
DATABASE_SECRET_NAME=corrdata/production/database
AWS_REGION=us-east-1
```

Load appropriate file based on environment:

```python
import os
from dotenv import load_dotenv

# Load environment-specific .env file
env = os.getenv("ENV", "development")
dotenv_path = f".env.{env}"

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()  # Fall back to .env
```

## Verification

Verify configuration is loaded correctly:

```python
# Test configuration loading
from corrdata.config import DATA_MODE, get_database_url

print(f"Data mode: {DATA_MODE}")
print(f"Database URL: {get_database_url()}")

# Test provider selection
from corrdata.providers.factory import DataProviderFactory

provider = DataProviderFactory.get_provider("elevation")
print(f"Elevation provider: {type(provider).__name__}")
```

Expected output (development):
```
Data mode: DataMode.SYNTHETIC
Database URL: postgresql+asyncpg://corrdata:corrdata@localhost:5432/corrdata
Elevation provider: SyntheticElevationProvider
```

Expected output (production with ELEVATION_MODE=real):
```
Data mode: DataMode.REAL
Database URL: postgresql+asyncpg://corrdata_prod:***@corrdata-prod.cluster-xxxxx.us-east-1.rds.amazonaws.com:5432/corrdata
Elevation provider: RealElevationProvider
```

## Learnings

### From Sprint 68 (AWS Secrets Manager Integration)
- Always provide environment variable fallback for local development
- Cache secrets to avoid repeated AWS API calls (use `@lru_cache`)
- Test both AWS and local paths in CI/CD
- Document all configuration options in `.env.example`
- Use IAM roles in production, not access keys
- Rotate secrets regularly and test rotation process

### From Real Data Migration
- Start with per-source overrides, don't switch everything at once
- Validate each data source thoroughly before enabling in production
- Monitor data quality after switching to real providers
- Keep synthetic mode available for demos and testing
- Document which data sources are validated for production use

### Configuration Best Practices
- Never commit `.env` files with real secrets to git
- Use different secret names for staging vs production
- Log which mode/provider is active at startup (but not the values!)
- Provide clear error messages when required config is missing
- Make development "just work" without configuration (sensible defaults)

## Anti-Patterns

### Don't: Hardcode Environment-Specific Values

**What it looks like**:
```python
if environment == "production":
    db_host = "prod.rds.amazonaws.com"
else:
    db_host = "localhost"
```

**Why it's bad**: Doesn't scale to multiple environments (staging, DR, etc.), requires code changes for new environments.

**Instead**: Use environment variables or Secrets Manager for all environment-specific values.

### Don't: Mix Secrets and Non-Secrets in Same Store

**What it looks like**: Storing `DATA_MODE=synthetic` in AWS Secrets Manager alongside database passwords.

**Why it's bad**: Secrets Manager is for secrets only (charged per secret, audited, rotated). Non-sensitive config should use environment variables or SSM Parameter Store.

**Instead**:
- Secrets Manager: Database passwords, API keys, private keys
- Environment variables: Data modes, cache settings, non-sensitive config
- SSM Parameter Store: Shared configuration values, feature flags

### Don't: Use Different Configuration Patterns Across Modules

**What it looks like**: Some modules use environment variables directly, others use a Settings class, others use config files.

**Why it's bad**: Inconsistent, hard to understand, difficult to override in tests.

**Instead**: Centralize configuration in one module (`corrdata.config`) and import from there. Provide single source of truth.

### Don't: Fail Silently on Missing Configuration

**What it looks like**:
```python
api_key = os.getenv("API_KEY", "")  # Empty string if missing
# Later: API call fails with cryptic error
```

**Why it's bad**: Errors happen far from the source, hard to debug.

**Instead**: Fail fast with clear error messages:
```python
def get_required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

api_key = get_required_env("API_KEY")
```

### Don't: Put Secrets in Environment Variables in Production

**What it looks like**: Setting database password via `DATABASE_PASSWORD=secret123` in container environment.

**Why it's bad**: Environment variables are visible in process listings, container metadata, logs. Not audited or rotated.

**Instead**: Use AWS Secrets Manager or equivalent secret store in production. Environment variables are fine for development.

## Variations

### For Multi-Region Deployments

If deploying to multiple AWS regions:

```python
def get_database_url(region: str | None = None) -> str:
    """Get database URL for specific region."""
    region = region or os.getenv("AWS_REGION", "us-east-1")
    secret_name = f"corrdata/{region}/database"
    config = get_secret(secret_name, region)
    # Construct URL...
```

### For Multi-Tenant SaaS

If you need per-tenant configuration:

```python
def get_tenant_config(tenant_id: str) -> dict:
    """Get tenant-specific configuration."""
    secret_name = f"corrdata/tenants/{tenant_id}/config"
    return get_secret(secret_name)

# Example: Tenant-specific API keys
def get_provider(source: str, tenant_id: str):
    config = get_tenant_config(tenant_id)
    api_key = config.get(f"{source}_api_key")
    return RealProvider(api_key=api_key)
```

### For Kubernetes Deployments

If using Kubernetes instead of AWS ECS:

```python
# Use Kubernetes secrets mounted as volumes
def get_secret_from_file(secret_path: str) -> dict:
    """Read secret from Kubernetes mounted volume."""
    with open(f"/var/secrets/{secret_path}") as f:
        return json.load(f)

DATABASE_CONFIG = get_secret_from_file("database.json")
```

## Related Recipes

- [Alert Engine Configuration](./alert-engine.md) - Uses configuration for notification channels
- [Database Migrations](../workflows/database-migrations.md) - Uses database URL from configuration

## Backlog Items

From Sprint 97 (Team Integration):

- [ ] **Tenant-Scoped Role Management Pattern**: Document pattern for managing user roles and permissions per tenant, including:
  - Role assignment with tenant context
  - Permission checking with tenant isolation
  - Role hierarchy and inheritance
  - Audit logging of permission changes

## References

- **Source Code**: `/Volumes/Foundry/Development/CorrData/POC/src/corrdata/config/`
  - `__init__.py` - Main config module (exports legacy + secrets)
  - `secrets.py` - AWS Secrets Manager integration
  - `config_legacy.py` - Legacy environment variable config
- **ADRs**:
  - [ADR-016: Environment-Based Configuration](../../architecture/decisions/ADR-016-environment-based-configuration.md)
  - [ADR-042: AWS Infrastructure Configuration](../../architecture/decisions/ADR-042-aws-infrastructure-configuration.md)

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-14 | Initial version based on Sprint 68 and ADR-016 |
