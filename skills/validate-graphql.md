---
name: "validate-graphql"
description: "Validate GraphQL schema, resolvers, and run GraphQL-specific tests"
---

# Skill: Validate GraphQL

Run comprehensive GraphQL validation for the current sprint.

## Steps

1. **Schema Validation**
   ```bash
   # Check schema files exist and are valid
   ls src/corrdata/api/graphql/schema/*.py
   ```

2. **Import Check**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   python -c "from corrdata.api.graphql.schema import schema; print('Schema imports OK')"
   ```

3. **Run GraphQL Tests**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   pytest tests/ -k "graphql" -v --tb=short
   ```

4. **Introspection Test**
   ```bash
   # If server is running, test introspection
   curl -s http://localhost:8000/graphql -H "Content-Type: application/json" \
     -d '{"query": "{ __schema { types { name } } }"}' | head -100
   ```

## Success Criteria

- All schema files import without errors
- GraphQL tests pass
- No type errors in resolvers
- Introspection returns valid schema

## Output Format

```json
{
  "skill": "validate-graphql",
  "status": "pass|fail",
  "schema_valid": true|false,
  "tests_passed": 0,
  "tests_failed": 0,
  "errors": []
}
```
