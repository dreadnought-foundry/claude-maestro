---
name: "check-coverage"
description: "Run tests with coverage and report against threshold"
---

# Skill: Check Coverage

Run pytest with coverage and validate against the 75% threshold.

## Steps

1. **Run Coverage**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   source .venv/bin/activate
   pytest tests/ --cov=src/corrdata --cov-report=term-missing --cov-report=json -q
   ```

2. **Parse Coverage Report**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   cat coverage.json | python -c "
   import json, sys
   data = json.load(sys.stdin)
   total = data['totals']['percent_covered']
   print(f'Total Coverage: {total:.1f}%')
   print(f'Threshold: 75%')
   print(f'Status: {\"PASS\" if total >= 75 else \"FAIL\"}')"
   ```

3. **Identify Low Coverage Files**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC
   cat coverage.json | python -c "
   import json, sys
   data = json.load(sys.stdin)
   print('Files below 80% coverage:')
   for path, info in data['files'].items():
       pct = info['summary']['percent_covered']
       if pct < 80:
           print(f'  {path}: {pct:.1f}%')"
   ```

## Success Criteria

- Tests complete without errors
- Total coverage >= 75%
- No critical files below 50%

## Output Format

```json
{
  "skill": "check-coverage",
  "status": "pass|fail",
  "total_coverage": 0.0,
  "threshold": 75.0,
  "files_below_threshold": [],
  "tests_passed": 0,
  "tests_failed": 0
}
```
