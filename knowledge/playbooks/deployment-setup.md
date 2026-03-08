# Recipe: Deployment Setup

**Category**: playbook
**Version**: 1.0
**Last Updated**: 2025-12-13
**Sprints**: Sprint 115 (planned)

## Context

**When to use this recipe:**
- Setting up staging/production environments for a new project
- Adding CI/CD pipelines to existing projects
- Migrating from local development to cloud deployment

**When NOT to use this recipe:**
- Local development setup (see development-infrastructure.md)
- Database-only changes (use run-migrations skill)

## Ingredients

Before starting, ensure you have:

- [ ] Working local development environment
- [ ] All tests passing locally
- [ ] GitHub repository with main branch
- [ ] Account on hosting platform (Railway, Render, Fly.io, etc.)
- [ ] List of required environment variables

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Deployment Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LOCAL DEV                                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Docker Compose: PostgreSQL, Neo4j, Backend, Frontend   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                    git push to main                              │
│                            ▼                                     │
│  GITHUB ACTIONS                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  1. Run tests                                            │    │
│  │  2. Build containers                                     │    │
│  │  3. Deploy to staging                                    │    │
│  │  4. Run smoke tests                                      │    │
│  │  5. (Manual) Deploy to production                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│              ┌─────────────┴─────────────┐                      │
│              ▼                           ▼                       │
│  STAGING                      PRODUCTION                         │
│  ┌───────────────────┐       ┌───────────────────┐              │
│  │  staging.app.com  │       │  app.com          │              │
│  │  - Test data      │       │  - Live data      │              │
│  │  - Auto-deploy    │       │  - Manual deploy  │              │
│  └───────────────────┘       └───────────────────┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Steps

### Step 1: Choose Hosting Platform

| Platform | Best For | Pros | Cons |
|----------|----------|------|------|
| **Railway** | Quick setup | Simple, good DX, managed DBs | Can get expensive at scale |
| **Render** | Static + API | Free tier, easy deploys | Cold starts on free tier |
| **Fly.io** | Global edge | Fast, great CLI | More complex setup |
| **AWS** | Enterprise | Full control, scalable | Complex, requires expertise |
| **Vercel** | Next.js frontend | Best Next.js support | Backend needs separate host |

**Recommendation for CorrData**: Railway for simplicity, or Fly.io for performance.

### Step 2: Set Up Staging Environment

```bash
# Example: Railway CLI
railway login
railway init
railway add --database postgresql
railway add --database redis  # if needed

# Link to project
railway link

# Set environment variables
railway variables set DATABASE_URL="..."
railway variables set NEO4J_URI="..."
```

**Expected outcome**: Staging environment provisioned with databases

### Step 3: Configure CI/CD

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest tests/

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        run: |
          # Platform-specific deploy command
          railway up --environment staging

  deploy-production:
    needs: test
    if: github.event.inputs.environment == 'production'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          railway up --environment production
```

**Expected outcome**: Automated deployments on push to main

### Step 4: Database Migration Strategy

```bash
# Run migrations on deploy
alembic upgrade head

# Verify migration status
alembic current
alembic history
```

Add to deployment script:
```yaml
- name: Run migrations
  run: |
    alembic upgrade head
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### Step 5: Set Up Monitoring

**Logging**:
```python
# In your FastAPI app
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**Error Tracking** (Sentry):
```python
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

**Health Check Endpoint**:
```python
@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.0.0"}
```

## Verification

How to confirm the deployment worked:

```bash
# Check staging health
curl https://staging.yourapp.com/health

# Expected output
{"status": "healthy", "version": "1.0.0"}

# Check GraphQL
curl -X POST https://staging.yourapp.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'
```

## Learnings

### From Previous Deployments
- Always test migrations on staging before production
- Keep staging and production configs as similar as possible
- Use environment-specific secrets, never commit them
- Set up monitoring BEFORE you need it

### Common Pitfalls
- Forgetting to set all environment variables
- Database connection string format differences
- CORS issues between frontend and backend
- SSL certificate provisioning delays

## Anti-Patterns

### Don't: Deploy Directly to Production

**What it looks like**: Pushing to main deploys straight to production

**Why it's bad**: No testing buffer, risky releases

**Instead**: Always deploy to staging first, verify, then promote to production

---

### Don't: Share Secrets Between Environments

**What it looks like**: Using same API keys for staging and production

**Why it's bad**: Staging bugs can affect production data/services

**Instead**: Use separate credentials for each environment

---

### Don't: Skip Health Checks

**What it looks like**: Deploying without verification endpoints

**Why it's bad**: No way to know if deploy succeeded

**Instead**: Always have `/health` endpoint, check it in CI/CD

## Variations

### For Monorepo (Backend + Frontend)

Deploy separately:
```yaml
jobs:
  deploy-backend:
    # Deploy FastAPI to Railway/Fly.io
  deploy-frontend:
    # Deploy Next.js to Vercel
```

### For Database-Heavy Apps

Add migration check step:
```yaml
- name: Check migration status
  run: alembic check
- name: Run migrations
  run: alembic upgrade head
- name: Verify schema
  run: pytest tests/test_models.py
```

## Environment Variables Checklist

```bash
# Required for CorrData
DATABASE_URL=postgresql://user:pass@host:5432/db
NEO4J_URI=bolt://host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

# Optional
MAPBOX_TOKEN=pk.xxx
SENTRY_DSN=https://xxx@sentry.io/xxx
LOG_LEVEL=INFO

# Frontend (Next.js)
NEXT_PUBLIC_API_URL=https://api.yourapp.com
NEXT_PUBLIC_GRAPHQL_URL=https://api.yourapp.com/graphql
```

## Related Recipes

- [Development Infrastructure](../workflows/development-infrastructure.md) - Local setup
- [Sprint Workflow v2.0](../workflows/sprint-workflow-v2.md) - Development process

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-13 | Initial deployment playbook |
