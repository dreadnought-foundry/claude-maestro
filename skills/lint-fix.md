---
name: "lint-fix"
description: "Run linting and auto-fix code formatting issues"
---

# Skill: Lint Fix

Run code linting and auto-fix formatting issues.

## Steps

1. **Run Ruff Linter with Auto-Fix**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   ruff check src/ tests/ --fix
   ```

2. **Run Ruff Formatter**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   ruff format src/ tests/
   ```

3. **Check for Remaining Issues**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   ruff check src/ tests/
   ```

4. **Type Check (Optional)**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   mypy src/corrdata --ignore-missing-imports || true
   ```

## Success Criteria

- Ruff check passes with no errors
- Code is formatted consistently
- No unfixable lint errors remain

## Output Format

```json
{
  "skill": "lint-fix",
  "status": "pass|fail",
  "errors_fixed": 0,
  "errors_remaining": 0,
  "files_formatted": 0
}
```
