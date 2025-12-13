# Skill: Deploy to Staging

## Purpose
Deploy the application to the staging environment for testing.

## When to Use
- After completing a sprint with code changes
- When testing deployment before production
- After infrastructure changes

## Steps

1. **Verify tests pass locally**
```bash
pytest tests/ -v
```

2. **Check for uncommitted changes**
```bash
git status
```

3. **Push to main branch**
```bash
git push origin main
```

4. **Trigger staging deploy** (if not auto-triggered)
```bash
# Railway
railway up --environment staging

# Or via GitHub Actions
gh workflow run deploy.yml -f environment=staging
```

5. **Verify deployment**
```bash
curl https://staging.corrdata.com/health
```

## Success Criteria
- [ ] All tests pass locally
- [ ] Changes pushed to main
- [ ] Staging deployment completes
- [ ] Health check returns 200
- [ ] GraphQL endpoint responds

## Failure Handling
- If deploy fails: Check logs with `railway logs` or GitHub Actions
- If health check fails: Check application logs, verify env vars
- If rollback needed: `railway rollback` or redeploy previous commit
