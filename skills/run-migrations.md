---
name: "run-migrations"
description: "Apply and verify Alembic database migrations"
---

# Skill: Run Migrations

Apply Alembic migrations and verify database state.

## Steps

1. **Check Migration Status**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   alembic current
   ```

2. **Check for Pending Migrations**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   alembic heads
   ```

3. **Check for Multiple Heads**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   alembic heads | wc -l
   ```
   If more than 1 head, merge is needed:
   ```bash
   alembic merge heads -m "merge_heads"
   ```

4. **Apply Migrations**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   alembic upgrade head
   ```

5. **Verify Migration Applied**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   alembic current
   ```

## Success Criteria

- No multiple heads (or merged)
- Migration applies without errors
- Current revision matches head
- Database tables created correctly

## Output Format

```json
{
  "skill": "run-migrations",
  "status": "pass|fail",
  "current_revision": "",
  "head_revision": "",
  "migrations_applied": 0,
  "errors": []
}
```
