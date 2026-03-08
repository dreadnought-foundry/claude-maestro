# Foundation Patterns

This directory contains battle-tested design patterns extracted from CorrData development. Each pattern recipe provides:

- **Context**: When to use (and when NOT to use)
- **Step-by-step instructions**: Concrete implementation steps
- **Real code examples**: Extracted from actual CorrData source files
- **Learnings**: Insights from sprints where pattern was refined
- **Anti-patterns**: Common mistakes and how to avoid them
- **Variations**: Adaptations for different scenarios

## Pattern Categories

### Database & Persistence
- [Three-Layer Database Architecture](./three-layer-database.md) - PostgreSQL + PostGIS + TimescaleDB + Neo4j
- [Domain Model Layering](./domain-model-layering.md) - SQLAlchemy → Dataclass → Pydantic → Strawberry

### External Integration
- [Provider Pattern](./provider-pattern.md) - Unified interface for external data sources (synthetic + real)

### API & Communication
- [GraphQL Schema Design](./graphql-schema.md) - Strawberry types, DataLoaders, N+1 prevention
- [MCP Tool Registry](./mcp-tool-registry.md) - LLM tool definitions with JSON Schema generation

### Infrastructure
- [Configuration Management](./configuration-management.md) - Environment-based configuration
- [Alert Engine](./alert-engine.md) - Real-time alerting system

## Pattern Selection Guide

| If you need to... | Use this pattern |
|-------------------|------------------|
| Store time-series measurements with spatial queries | [Three-Layer Database](./three-layer-database.md) |
| Integrate external APIs (USGS, NOAA, etc.) | [Provider Pattern](./provider-pattern.md) |
| Build GraphQL API for React frontend | [GraphQL Schema](./graphql-schema.md) |
| Expose tools to LLMs via MCP | [MCP Tool Registry](./mcp-tool-registry.md) |
| Convert between database, domain, and API models | [Domain Model Layering](./domain-model-layering.md) |

## Quality Standards

All pattern recipes in this directory:
- ✅ Include real code examples from CorrData codebase
- ✅ Reference source ADRs for architectural context
- ✅ List sprints where pattern was used/refined
- ✅ Provide verification steps to confirm implementation
- ✅ Document learnings and anti-patterns
- ✅ Maintain changelog for version tracking

## Related Documentation

- **ADRs**: `docs/architecture/decisions/` - Architecture decision records (source material)
- **Workflows**: `docs/playbook/workflows/` - Development process recipes
- **Playbooks**: `docs/playbook/playbooks/` - Operational runbooks
- **Integrations**: `docs/playbook/integrations/` - External system integration guides

## Contributing

When adding new patterns:

1. Use the template at `docs/playbook/_TEMPLATE.md`
2. Extract real code from `src/` directory (no made-up examples)
3. Reference relevant ADRs in metadata
4. Include verification steps
5. Document both success patterns and anti-patterns
6. Update this README with the new pattern

## Version History

| Date | Change |
|------|--------|
| 2025-12-14 | Created 5 foundation pattern recipes |
| (Earlier) | Added alert-engine and configuration-management patterns |
