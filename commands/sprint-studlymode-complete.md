---
description: "Complete a sprint in studly mode - auto-generates a real postmortem from git data"
allowed-tools: [Bash, Read, Glob, Grep, Edit, Write]
---

# Complete Sprint — Studly Mode

`/sprint-complete` but smarter. Instead of generating a postmortem full of TODOs, this command analyzes the actual sprint work (git diff, test results, acceptance criteria) and writes a real postmortem automatically. Then runs the normal completion flow.

## Instructions

### 1. Load Context

Generate and read the context brief to understand what was planned:

```bash
cd <project_root> && PYTHONPATH=~/.claude/scripts python3 -m sprint_automation build-context $ARGUMENTS
```

Read the generated brief:

```bash
cat .claude/sprint-*-context.md
```

### 2. Read the Sprint Spec

Find and read the sprint file to understand:
- What was the goal?
- What were the requirements?
- What were the acceptance criteria?
- What files were supposed to be modified?

### 3. Gather Actual Results

Run these commands to collect real data about what happened:

**Files changed:**
```bash
git diff --stat HEAD~1
```

If the sprint had multiple commits, use the sprint's start commit:
```bash
git log --oneline --since="<sprint_started_date>" | tail -1
```
Then diff from there:
```bash
git diff --stat <first_commit>..HEAD
```

**Test results:**
```bash
# For JavaScript/TypeScript projects
npx jest --no-coverage 2>&1 | tail -5

# For Python projects
pytest --tb=no -q 2>&1 | tail -5
```

**Test count:**
```bash
# Count test functions added in this sprint
git diff HEAD~1 --diff-filter=A -- "**/*.test.*" "**/*.spec.*" "**/test_*" | grep -c "^\+.*\(it\|test\|describe\|def test_\)"
```

### 4. Compare Plan vs Actual

For each acceptance criterion in the sprint spec:
- Check if it was implemented (search codebase for evidence)
- Mark as DONE or NOT DONE
- Note any deviations from the plan

### 5. Write the Real Postmortem

Find the postmortem file (or create it):
```bash
find docs/sprints -name "sprint-*$ARGUMENTS*postmortem*"
```

Write a REAL postmortem — not a template. Fill in every section with actual analysis:

**Metrics section** — use real numbers:
```markdown
## Metrics

| Metric | Value |
|--------|-------|
| Sprint Number | N |
| Started | <from state file> |
| Completed | <now> |
| Duration | X.X hours |
| Files Changed | <from git diff --stat> |
| Tests Added | <counted> |
| Tests Passing | <from test run> |
```

**What Went Well** — specific, not generic:
- Reference actual code decisions that worked
- Note patterns that were reused effectively
- Mention any particularly clean implementations

**What Could Improve** — honest and specific:
- Requirements that were ambiguous
- Approaches that needed rework
- Missing test coverage areas
- Any acceptance criteria not met and why

**Technical Insights** — things learned:
- New patterns discovered
- Gotchas encountered
- Performance or architecture observations

**Action Items** — concrete follow-ups:
- Bugs discovered but not fixed (out of scope)
- Technical debt introduced
- Documentation gaps

### 6. Write Postmortem into Sprint File

Also add/update the `## Postmortem` section directly in the sprint file with a summary (the detailed version goes in the separate postmortem file).

### 7. Run Normal Completion

After the postmortem is written with real content, run the standard completion:

```bash
python3 ~/.claude/scripts/sprint_lifecycle.py complete-sprint $ARGUMENTS
```

This handles file movement, registry updates, git tags, and epic checks.

## Key Difference from /sprint-complete

| Aspect | /sprint-complete | /sprint-studlymode-complete |
|--------|-----------------|---------------------------|
| Postmortem | Template with TODOs | Auto-filled with real git/test data |
| Acceptance criteria | Not checked | Compared plan vs actual |
| Metrics | Placeholders | Real numbers from git and tests |
| Context | None | Full project brief loaded |
| Completion flow | Same | Same (runs the automation script) |

## Error Handling

- If git diff fails, note it and continue with available data
- If tests can't run, note the reason in the postmortem
- If context builder fails, skip context and continue
- The postmortem should always reflect what actually happened, including failures
