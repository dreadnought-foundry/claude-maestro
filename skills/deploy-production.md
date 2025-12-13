# Skill: Deploy to Production

## Purpose
Deploy the application to production environment with safety checks.

## When to Use
- After successful staging verification
- For planned production releases
- NEVER for untested changes

## Pre-Flight Checklist

**REQUIRED before production deploy:**
- [ ] Changes tested on staging for at least 1 hour
- [ ] All smoke tests passing on staging
- [ ] No critical errors in staging logs
- [ ] Database migrations verified on staging
- [ ] User has approved production deploy

## Steps

1. **Verify staging health**
```bash
curl https://staging.corrdata.com/health
```

2. **Run smoke tests on staging**
```bash
pytest tests/test_smoke.py --base-url=https://staging.corrdata.com
```

3. **Check staging logs for errors**
```bash
railway logs --environment staging | grep -i error
```

4. **Deploy to production** (requires manual trigger)
```bash
# Via GitHub Actions (recommended)
gh workflow run deploy.yml -f environment=production

# Or Railway
railway up --environment production
```

5. **Verify production deployment**
```bash
curl https://corrdata.com/health
```

6. **Monitor for 15 minutes**
- Check error rates
- Monitor response times
- Watch for user reports

## Success Criteria
- [ ] Health check returns 200
- [ ] GraphQL endpoint responds
- [ ] No spike in error rates
- [ ] Response times within normal range

## Rollback Procedure
If issues detected:
```bash
# Railway
railway rollback --environment production

# Or redeploy previous commit
git checkout HEAD~1
railway up --environment production
```

## WARNINGS
- NEVER deploy to production without staging verification
- NEVER skip the pre-flight checklist
- ALWAYS have rollback plan ready
- ALWAYS monitor after deploy
