# Skill: Health Check

## Purpose
Verify application health across all environments and services.

## When to Use
- After any deployment
- When troubleshooting issues
- As part of monitoring routine

## Steps

### 1. Check API Health

```bash
# Local
curl http://localhost:8000/health

# Staging
curl https://staging.corrdata.com/health

# Production
curl https://corrdata.com/health
```

**Expected response:**
```json
{"status": "healthy", "version": "1.0.0"}
```

### 2. Check GraphQL Endpoint

```bash
curl -X POST https://staging.corrdata.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```

**Expected response:**
```json
{"data": {"__typename": "Query"}}
```

### 3. Check Database Connectivity

```bash
# Via API endpoint (if available)
curl https://staging.corrdata.com/health/db

# Or run a simple query
curl -X POST https://staging.corrdata.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ assets(limit: 1) { uuid } }"}'
```

### 4. Check Neo4j Connectivity

```bash
curl https://staging.corrdata.com/health/neo4j
```

### 5. Check MCP Server (if applicable)

```bash
# List available tools
curl https://staging.corrdata.com/mcp/tools
```

## Quick Health Summary Script

```bash
#!/bin/bash
ENV=${1:-staging}
BASE_URL="https://${ENV}.corrdata.com"

echo "Checking $ENV environment..."
echo "API Health: $(curl -s $BASE_URL/health | jq -r '.status')"
echo "GraphQL: $(curl -s -X POST $BASE_URL/graphql -H 'Content-Type: application/json' -d '{"query":"{ __typename }"}' | jq -r '.data.__typename')"
echo "Version: $(curl -s $BASE_URL/health | jq -r '.version')"
```

## Success Criteria
- [ ] API returns 200 with "healthy" status
- [ ] GraphQL responds to introspection
- [ ] Database queries succeed
- [ ] Response time < 500ms

## Failure Response
- If API unhealthy: Check application logs
- If DB unavailable: Check database status, connection string
- If slow response: Check resource usage, scaling
