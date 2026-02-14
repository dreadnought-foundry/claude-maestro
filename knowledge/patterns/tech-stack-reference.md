# Recipe: CorrData Tech Stack Reference

**Category**: pattern
**Version**: 1.0
**Last Updated**: 2025-12-14
**Sprints**: Foundation (all sprints)
**ADRs**: ADR-001 through ADR-049

## Context

**When to use this recipe:**
- Onboarding new team members to understand our technology choices
- Making decisions about adding new dependencies
- Understanding why specific libraries were chosen over alternatives
- Troubleshooting compatibility issues between components
- Planning infrastructure upgrades or migrations

**When NOT to use this recipe:**
- For implementation details (see individual pattern recipes)
- For operational runbooks (see playbooks/)
- For external system integration specifics (see integrations/)

## Overview

CorrData uses a modern, Python-first stack with React frontends. Every technology choice was made for specific reasons documented here.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CorrData Architecture                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                           FRONTEND LAYER                                ││
│  │  React 18 + Next.js 14 (App Router) + TypeScript 5.3                   ││
│  │  TailwindCSS + Radix UI + shadcn/ui components                          ││
│  │  Mapbox GL JS for geospatial visualization                              ││
│  │  Apollo Client for GraphQL, Vitest for testing                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│                          GraphQL + REST (FastAPI)                            │
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                            API LAYER                                     ││
│  │  FastAPI 0.100+ with async/await throughout                             ││
│  │  Strawberry GraphQL for type-safe schema                                ││
│  │  MCP Server for LLM integration                                         ││
│  │  Pydantic 2.0 for validation                                            ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│                              SQLAlchemy 2.0                                  │
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         DATA LAYER (3-Layer)                             ││
│  │                                                                          ││
│  │  Layer 1: FACT STORE                                                    ││
│  │    PostgreSQL 15 + TimescaleDB + PostGIS                                ││
│  │                                                                          ││
│  │  Layer 2: RELATIONSHIP GRAPH                                            ││
│  │    Neo4j 5.x for temporal knowledge graphs                              ││
│  │                                                                          ││
│  │  Layer 3: DIGITAL TWIN / ML                                             ││
│  │    PyTorch + SHAP for explainable predictions                           ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## The Stack

### Python Backend

| Component | Version | Why We Chose It |
|-----------|---------|-----------------|
| **Python** | 3.11+ | Best balance of performance, typing support, and library ecosystem. 3.11's performance improvements (10-60% faster) and improved error messages made it the minimum version. |
| **FastAPI** | 0.100+ | Automatic OpenAPI docs, native async support, Pydantic integration. Faster development than Flask/Django with automatic validation. |
| **Pydantic** | 2.0+ | Type coercion, validation, serialization in one. v2 rewrote core in Rust for 5-50x performance improvement. |
| **Strawberry GraphQL** | 0.200+ | Python-native GraphQL with dataclass-style type definitions. Better typing than Graphene, integrates cleanly with FastAPI and Pydantic. |
| **SQLAlchemy** | 2.0+ | Industry standard ORM with excellent PostgreSQL support. 2.0 brought type hints, better async, and improved performance. |
| **Alembic** | 1.12+ | SQLAlchemy's migration tool. Autogeneration works well, integrates with our models. |

**Why Not Django?**
- FastAPI is more explicit (no magic)
- Better async support out of the box
- GraphQL integrations are cleaner with Strawberry
- We don't need Django's admin/auth/forms

**Why Not Flask?**
- No native async (requires extensions)
- Manual validation (Pydantic integration not native)
- No automatic API documentation

### Database Layer

| Component | Version | Purpose | Why We Chose It |
|-----------|---------|---------|-----------------|
| **PostgreSQL** | 15+ | Relational data, JSONB, base | Most feature-complete open-source RDBMS. Handles relational queries, JSONB for flexibility, and hosts extensions. |
| **TimescaleDB** | 2.x | Time-series data | Only production-ready time-series extension for PostgreSQL. Hypertables provide automatic partitioning, continuous aggregates, and compression. |
| **PostGIS** | 3.x | Spatial data | Industry standard for geospatial. Supports all OGC types, spatial indexes (GiST), and complex spatial queries. |
| **Neo4j** | 5.x | Relationship graphs | Best-in-class graph database. Cypher query language is intuitive, native graph storage gives performance on multi-hop queries. |

**Why Not MongoDB?**
- Schema flexibility isn't worth losing JOIN capabilities
- PostgreSQL's JSONB gives us document-style when needed
- PostGIS spatial is far superior to MongoDB's geo support

**Why Not InfluxDB/TimescaleDB standalone?**
- TimescaleDB as PostgreSQL extension means one database technology
- Can JOIN time-series with relational data seamlessly
- Standard SQL tooling and ORMs work

**Why Neo4j over PostgreSQL recursive CTEs?**
- Multi-hop relationship queries are 10-100x faster
- Cypher is more readable for graph patterns
- Native graph storage vs. emulated graph on tables

### Frontend Stack

| Component | Version | Purpose | Why We Chose It |
|-----------|---------|---------|-----------------|
| **React** | 18.2+ | UI framework | Industry standard, huge ecosystem, easy hiring. React 18's concurrent features improve responsiveness. |
| **Next.js** | 14.x | React framework | App Router, server components, API routes. Handles SSR, routing, bundling—we just write components. |
| **TypeScript** | 5.3+ | Type safety | Catches errors at compile time, enables IDE autocomplete, self-documenting code. |
| **TailwindCSS** | 3.3+ | Styling | Utility-first CSS eliminates naming debates. Purges unused styles for small bundles. |
| **Radix UI** | 1.x | Accessible primitives | Unstyled, accessible components. We add our styles on top. |
| **shadcn/ui** | - | Component library | Copy-paste components built on Radix + Tailwind. Full control, no npm dependency. |
| **Apollo Client** | 3.8+ | GraphQL client | Normalized caching, automatic query deduplication, excellent DevTools. |
| **Mapbox GL JS** | 3.x | Mapping | Best-in-class vector maps. Smooth performance, extensive styling, good React bindings. |
| **Recharts** | 3.5+ | Charts | Declarative React charts. Simple API, good defaults, handles most visualization needs. |

**Why Not Vue/Svelte/Angular?**
- React has the largest ecosystem and talent pool
- Next.js provides the best full-stack React experience
- shadcn/ui and Radix UI are React-first

**Why Not Material UI?**
- Too opinionated on design
- Harder to customize to match our design system
- shadcn/ui gives us components we fully own

### Infrastructure & DevOps

| Component | Version | Purpose | Why We Chose It |
|-----------|---------|---------|-----------------|
| **Docker** | - | Containerization | Standard for reproducible deployments. Same container runs locally, staging, and production. |
| **AWS ECS Fargate** | - | Container orchestration | Serverless containers without managing EC2 instances. Right-sizes based on demand. |
| **AWS Cognito** | - | Authentication | Managed auth with MFA, social login, RBAC. Don't have to build/maintain auth ourselves. |
| **AWS CloudWatch** | - | Monitoring/Logs | Native AWS integration. Centralized logs, metrics, alarms. |
| **Sentry** | 8.0+ | Error tracking | Best-in-class error aggregation with source maps. Catches frontend and backend errors. |
| **Redis** | 5.0+ | Caching/Queues | In-memory data store for sessions, caching, Celery broker. Fast and battle-tested. |
| **Celery** | 5.3+ | Task queue | Async task processing for reports, emails, long-running jobs. Redis as broker. |

### LLM Integration

| Component | Version | Purpose | Why We Chose It |
|-----------|---------|---------|-----------------|
| **MCP** | 1.0+ | LLM tool protocol | Anthropic's Model Context Protocol standardizes LLM-tool communication. Works with Claude Desktop, Cline, etc. |

**Why MCP over OpenAI Function Calling?**
- Standard protocol supported by multiple clients
- Better context management
- Native Anthropic integration

### Data Processing & Analysis

| Component | Version | Purpose | Why We Chose It |
|-----------|---------|---------|-----------------|
| **Pandas** | 2.0+ | Data manipulation | Industry standard for tabular data. Excellent integration with SQLAlchemy, GeoPandas. |
| **GeoPandas** | 0.14+ | Geospatial data | Pandas + Shapely. Spatial operations on DataFrames. |
| **Polars** | 0.20+ | Fast data processing | 10-100x faster than Pandas for large datasets. Lazy evaluation, multi-threaded. |
| **Shapely** | 2.0+ | Geometry operations | Python bindings for GEOS. Create, manipulate, analyze geometries. |
| **Rasterio** | 1.3+ | Raster data | Read COG tiles from cloud storage. Used for NLCD land cover, 3DEP elevation. |

**Why Both Pandas and Polars?**
- Pandas for small-medium data, GeoPandas integration
- Polars for large datasets where performance matters
- Different tools for different jobs

### ML & Prediction

| Component | Version | Purpose | Why We Chose It |
|-----------|---------|---------|-----------------|
| **PyTorch** | 2.0+ | Deep learning | Most flexible DL framework. Dynamic graphs, excellent debugging. |
| **SHAP** | 0.43+ | Explainability | Industry standard for model explanations. Visual feature importance. |
| **MLflow** | 2.0+ | Experiment tracking | Model versioning, experiment comparison, deployment. |
| **scikit-learn** | 1.3+ | Traditional ML | Classic algorithms, preprocessing, model selection. |

**Why PyTorch over TensorFlow?**
- More Pythonic API
- Better debugging (eager execution)
- Dominant in research, catches new techniques faster

### Testing

| Component | Version | Purpose | Why We Chose It |
|-----------|---------|---------|-----------------|
| **pytest** | 7.4+ | Python testing | Most popular Python test framework. Fixtures, markers, plugins. |
| **pytest-asyncio** | 0.21+ | Async tests | Native async test support for our async codebase. |
| **pytest-cov** | 4.1+ | Coverage | Track test coverage with fail threshold (75% minimum). |
| **Vitest** | 1.1+ | Frontend testing | Fast, Vite-native test runner. Compatible with Jest. |
| **Playwright** | 1.40+ | E2E testing | Cross-browser automation. More reliable than Selenium. |
| **MSW** | 2.0+ | API mocking | Mock GraphQL/REST at network level for frontend tests. |

### Code Quality

| Component | Version | Purpose | Why We Chose It |
|-----------|---------|---------|-----------------|
| **Ruff** | 0.1+ | Linting/formatting | 10-100x faster than flake8/black. Replaces multiple tools. |
| **mypy** | 1.7+ | Type checking | Static type analysis for Python. Catches type errors early. |
| **ESLint** | 8.55+ | JS/TS linting | Catches code quality issues in frontend. |
| **TypeScript** | 5.3+ | JS type checking | Compile-time type errors in frontend. |

**Why Ruff over Black + isort + flake8?**
- Single tool replaces all three
- 10-100x faster (written in Rust)
- Compatible rules with existing configs

## Configuration Files

### Backend Configuration

```python
# pyproject.toml - Central Python project config
[project]
name = "corrdata"
requires-python = ">=3.11"
dependencies = [
    # Core dependencies listed with version constraints
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "-v --cov=corrdata --cov-report=term-missing"

[tool.coverage.report]
fail_under = 75.0  # Minimum coverage threshold
```

### Frontend Configuration

```json
// packages/web-app/package.json
{
  "name": "@corrdata/web-app",
  "dependencies": {
    "next": "14.0.4",
    "react": "^18.2.0",
    "@apollo/client": "^3.8.8",
    // ... other dependencies
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "vitest": "^1.1.0",
    "@playwright/test": "^1.40.0"
  }
}
```

## Version Compatibility Matrix

| Python | SQLAlchemy | Strawberry | FastAPI | Pydantic |
|--------|------------|------------|---------|----------|
| 3.11   | 2.0+       | 0.200+     | 0.100+  | 2.0+     |
| 3.12   | 2.0+       | 0.200+     | 0.100+  | 2.0+     |

| Next.js | React | TypeScript | Node |
|---------|-------|------------|------|
| 14.x    | 18.2+ | 5.3+       | 18+  |

## Adding New Dependencies

Before adding a new dependency:

1. **Check if existing tools cover the use case** - We may already have something that works
2. **Evaluate alternatives** - Document why this library over others
3. **Check maintenance status** - Look at GitHub activity, release cadence
4. **Consider bundle size impact** (frontend) - Use bundlephobia.com
5. **Version pin appropriately** - Use `>=` for libraries, `~=` for frameworks
6. **Update this document** - Add to the stack reference with rationale

## Learnings

### From 119+ Sprints

- **Type hints everywhere**: TypeScript frontend + typed Python backend catches bugs early
- **Async by default**: FastAPI async handlers, SQLAlchemy async sessions—consistency matters
- **One database technology**: TimescaleDB + PostGIS on PostgreSQL beats multiple databases
- **Component ownership**: shadcn/ui pattern (own your components) beats npm dependency hell
- **Test infrastructure early**: CI validation (Sprint 117) prevents broken main branch

### Technology Decisions We Revisited

| Original Choice | Replaced With | Why |
|-----------------|---------------|-----|
| Black + isort | Ruff | Faster, single tool |
| Jest | Vitest | Faster, native Vite support |
| SQLAlchemy 1.4 | SQLAlchemy 2.0 | Better typing, async |
| Pydantic 1.x | Pydantic 2.0 | Performance, cleaner API |

## Anti-Patterns

### Don't: Add Dependencies for One-Off Tasks

**What it looks like**: Installing a library for a single function.

**Why it's bad**: Dependency bloat, security surface, maintenance burden.

**Instead**: Write the code yourself if it's simple, or use an existing library differently.

### Don't: Pin Exact Versions for Everything

**What it looks like**: `numpy==1.24.3` instead of `numpy>=1.24.0`

**Why it's bad**: Prevents security patches, creates dependency conflicts.

**Instead**: Use `>=` for libraries (security patches), `~=` or `^` for frameworks (minor version flexibility).

### Don't: Use Different Languages/Frameworks Without Strong Reason

**What it looks like**: Adding a Go microservice for "performance" without benchmarks.

**Why it's bad**: Splits team expertise, complicates deployment, increases cognitive load.

**Instead**: Optimize Python first. It's fast enough for 99% of use cases. Profile before rewriting.

## Related Recipes

- [Three-Layer Database](./three-layer-database.md) - Database architecture details
- [GraphQL Schema Design](./graphql-schema.md) - API layer implementation
- [Provider Pattern](./provider-pattern.md) - External data integration
- [Development Infrastructure](../workflows/development-infrastructure.md) - CI/CD and tooling

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-14 | Initial version documenting complete tech stack |
