---
name: "smoke-tests"
description: "Run quick smoke tests to verify API and core functionality"
---

# Skill: Smoke Tests

Quick sanity checks to verify the system is working.

## When to Use

- After deployment
- Before running full test suite
- After major changes
- As part of CI/CD pipeline

## Steps

1. **Check API Health**
   ```bash
   curl -s http://localhost:8000/health | python -c "
   import json, sys
   data = json.load(sys.stdin)
   print(f'API Status: {data.get(\"status\", \"unknown\")}')
   print(f'Database: {data.get(\"database\", \"unknown\")}')
   "
   ```

2. **Test GraphQL Endpoint**
   ```bash
   curl -s http://localhost:8000/graphql \
     -H "Content-Type: application/json" \
     -d '{"query": "{ __typename }"}' | python -c "
   import json, sys
   data = json.load(sys.stdin)
   if 'data' in data:
       print('GraphQL: OK')
   else:
       print('GraphQL: FAILED')
       sys.exit(1)
   "
   ```

3. **Test Core Query**
   ```bash
   curl -s http://localhost:8000/graphql \
     -H "Content-Type: application/json" \
     -d '{"query": "{ assets(limit: 1) { uuid name } }"}' | python -c "
   import json, sys
   data = json.load(sys.stdin)
   if 'data' in data and 'assets' in data['data']:
       print(f'Assets Query: OK ({len(data[\"data\"][\"assets\"])} returned)')
   else:
       print('Assets Query: FAILED')
       sys.exit(1)
   "
   ```

4. **Test MCP Server Import**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   python -c "
   from corrdata.mcp.server_v2 import mcp
   tools = mcp.list_tools()
   print(f'MCP Tools: {len(tools)} registered')
   " 2>&1 || echo "MCP Import: FAILED"
   ```

5. **Run Pytest Smoke Marker**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   pytest tests/test_smoke.py -v --tb=short 2>&1 | tail -20
   ```

## Success Criteria

- API health returns "healthy"
- GraphQL endpoint responds
- At least one asset query succeeds
- MCP server imports without error
- Smoke tests pass

## Output Format

```json
{
  "skill": "smoke-tests",
  "status": "pass|fail",
  "checks": {
    "api_health": true|false,
    "graphql": true|false,
    "assets_query": true|false,
    "mcp_import": true|false,
    "smoke_tests": true|false
  },
  "errors": []
}
```
