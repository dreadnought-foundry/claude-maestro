# Skill: Setup CI/CD Pipeline

## Purpose
Configure GitHub Actions workflow for automated testing and deployment.

## When to Use
- Initial project setup
- Adding new deployment environments
- Modifying deployment process

## Steps

### 1. Create Workflow Directory

```bash
mkdir -p .github/workflows
```

### 2. Create Main Deploy Workflow

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

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: timescale/timescaledb-ha:pg15-latest
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: corrdata_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests
        run: pytest tests/ -v --cov=src/corrdata
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/corrdata_test

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Railway (staging)
        run: |
          npm install -g @railway/cli
          railway up --environment staging
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

      - name: Health check
        run: |
          sleep 30
          curl -f https://staging.corrdata.com/health

  deploy-production:
    needs: test
    if: github.event.inputs.environment == 'production'
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Railway (production)
        run: |
          npm install -g @railway/cli
          railway up --environment production
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

      - name: Health check
        run: |
          sleep 30
          curl -f https://corrdata.com/health
```

### 3. Configure GitHub Secrets

Go to GitHub repo → Settings → Secrets → Actions:

```
RAILWAY_TOKEN=xxx          # From Railway dashboard
DATABASE_URL=xxx           # For test database (optional)
```

### 4. Configure Environments

Go to GitHub repo → Settings → Environments:

1. Create "staging" environment
   - No required reviewers
   - Auto-deploy enabled

2. Create "production" environment
   - Required reviewers: 1+
   - Wait timer: optional

### 5. Test the Pipeline

```bash
# Trigger manually
gh workflow run deploy.yml -f environment=staging

# Or push to main
git push origin main
```

## Success Criteria
- [ ] Workflow file created and valid
- [ ] GitHub secrets configured
- [ ] Environments configured
- [ ] Test job passes
- [ ] Deploy job completes
- [ ] Health check succeeds

## Troubleshooting

**Tests fail in CI but pass locally:**
- Check environment variables
- Verify database service is running
- Check for timing issues

**Deploy fails:**
- Verify RAILWAY_TOKEN is set
- Check Railway project is linked
- Review Railway logs
