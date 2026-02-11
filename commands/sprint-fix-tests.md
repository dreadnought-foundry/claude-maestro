---
description: "Run full test suite, categorize failures, and fix text matcher issues"
allowed-tools: [Bash, Read, Glob, Grep, Edit, Write, Task]
---

# Fix Tests

Run the full test suite, analyze failures, and fix text matcher issues that result
from copy/UI changes.

## Instructions

### 1. Run Full Test Suite

Run both frontend and backend test suites:

```bash
cd frontend && npx jest --no-coverage 2>&1
```

```bash
cd backend && pytest 2>&1
```

If all tests pass, report success and exit.

### 2. Categorize Failures

For each failing test, determine the category:

**Category A: Text Matcher Failures (auto-fixable)**
- `Unable to find an accessible element with the role "heading" and name /old text/`
- `Unable to find an element with the text: old text`
- `Found multiple elements with the text: duplicate text`
- `expect(received).toBe(expected)` where expected is a count (e.g., h3 count changed)

**Category B: Real Bugs (require investigation)**
- TypeError, ReferenceError, import errors
- Logic failures (wrong values, missing props)
- Timeout errors, async failures

### 3. Fix Category A Failures

For each text matcher failure:
1. Read the source component to find the NEW text
2. Read the test file to find the OLD matcher
3. Update the test matcher to use the new text
4. For "multiple elements found" errors: use `getAllByText` instead of `getByText`,
   or scope the query to a parent container (e.g., `main.querySelectorAll`)

### 4. Re-run and Report

After fixing, re-run the full suite to verify:

```bash
cd frontend && npx jest --no-coverage 2>&1
```

Report results:
```
============================================================
Test Fix Results
============================================================
Category A (auto-fixed): N failures in M files
Category B (needs investigation): N failures in M files
Final: X suites passed, Y suites failed, Z total
============================================================
```

If Category B failures remain, list them with file paths and error summaries.
