---
description: "Run pre-flight checklist and mark sprint complete"
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
---

# Complete Sprint

Run the pre-flight checklist and mark the sprint as complete.

**NOTE**: This workflow supports multiple concurrent sprints. You MUST specify the sprint number.

## Determine Sprint Number

**REQUIRED**: `$ARGUMENTS` must contain the sprint number.

If `$ARGUMENTS` is empty:
- Use Glob to find all sprint state files: `.claude/sprint-*-state.json`
- If multiple found, ask user which sprint to complete
- If only one found, use that sprint number
- If none found, report "No active sprint. Use /sprint-start <N> to begin."

State file path: `.claude/sprint-$ARGUMENTS-state.json`

---

## Pre-Flight Checklist

Run each check and update the state file. ALL checks must pass.

### 1. Tests Passing

```bash
source .venv/bin/activate && pytest tests/ -q --tb=no
```

- [ ] Exit code is 0 (all tests pass)
- [ ] No failures in output

Update: `pre_flight_checklist.tests_passing = true/false`

### 2. Database Migrations Verified

Check if sprint created a migration:
```bash
ls -la alembic/versions/*sprint{N}* 2>/dev/null || echo "No migration"
```

If migration exists:
- [ ] Migration file exists
- [ ] Migration has upgrade() and downgrade() functions

Update: `pre_flight_checklist.migrations_verified = true/false/null` (null if no migration)

### 3. Sample Data Generated

Check if sprint requires sample data:
- [ ] Sample data script exists in `scripts/` OR
- [ ] Data generation is part of tests OR
- [ ] Not applicable for this sprint

Update: `pre_flight_checklist.sample_data_generated = true/false/null`

### 4. MCP Tools Tested

If sprint added MCP tools:
```bash
grep -l "def.*sprint{N}" src/corrdata/mcp/tools/*.py 2>/dev/null
```

- [ ] New tools are registered
- [ ] Tools have proper type hints and docstrings

Update: `pre_flight_checklist.mcp_tools_tested = true/false/null`

### 5. Dialog Example Created

Check for dialog example:
```bash
ls docs/examples/*sprint*{N}* 2>/dev/null || ls docs/examples/dialog_* 2>/dev/null | tail -1
```

- [ ] Dialog example exists for significant new capability OR
- [ ] Not applicable (bug fix, refactoring, infrastructure)

Update: `pre_flight_checklist.dialog_example_created = true/false/null`

### 6. Sprint File Updated

Read the sprint file and verify:
- [ ] Status is "Complete" or ready to be set
- [ ] Completed date is set or ready to be set
- [ ] Implementation checklist items are checked off

Update: `pre_flight_checklist.sprint_file_updated = true/false`

### 7. Code Has Docstrings

Check new/modified Python files:
```bash
grep -L '"""' src/corrdata/**/*.py 2>/dev/null | head -5
```

- [ ] All new classes have docstrings
- [ ] All new public functions have docstrings

Update: `pre_flight_checklist.code_has_docstrings = true/false`

### 8. No Hardcoded Secrets

Search for potential secrets:
```bash
grep -rn -E "(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]" src/ --include="*.py" | grep -v "test" | grep -v "#"
```

- [ ] No hardcoded passwords
- [ ] No hardcoded API keys
- [ ] No hardcoded tokens

Update: `pre_flight_checklist.no_hardcoded_secrets = true/false`

### 9. Git Status Clean

```bash
git status --porcelain
```

- [ ] Output is empty (all changes committed)
- [ ] No untracked files that should be committed

Update: `pre_flight_checklist.git_status_clean = true/false`

---

## If All Checks Pass

1. **Calculate hours worked**:
   - Read the `started` timestamp from YAML frontmatter
   - Current time minus started time = hours (decimal, e.g., 5.25)

2. **Update YAML frontmatter** in sprint file:
   ```yaml
   ---
   sprint: N
   title: <title>
   status: done
   started: <original timestamp>
   completed: <current ISO 8601 timestamp with time>
   hours: <calculated hours as decimal>
   ---
   ```

3. **Update the sprint file's markdown table** (if present):
   - Set `| **Status** |` to `Complete`
   - Set `| **Completed** |` to current date/time
   - Check off all checklist items

4. **Rename and move sprint file to `done/` folder**:
   - Add completion date suffix to filename
   - Format: `sprint-NN_title_done-YYYY-MM-DD.md`
   - Example: `sprint-18_mcp-modular-architecture_done-2025-12-02.md`
   ```bash
   mv docs/sprints/in-progress/sprint-$ARGUMENTS*.md docs/sprints/done/sprint-$ARGUMENTS_<slug>_done-<YYYY-MM-DD>.md
   ```

5. **Update `docs/sprints/README.md`**:
   - Add sprint to completed list with hours tracked
   - Update statistics if present

6. **Update state file** `.claude/sprint-$ARGUMENTS-state.json`:
   - `status` = "complete"
   - `completed_at` = current ISO timestamp

7. **Report success**:
   ```
   Sprint $ARGUMENTS: <title> - COMPLETE

   Pre-Flight Checklist: 9/9 passed

   Summary:
   - Started: <timestamp>
   - Completed: <timestamp>
   - Hours: <calculated hours>
   - Steps completed: <count>

   Sprint file moved to: docs/sprints/done/<new filename>
   State file preserved at .claude/sprint-$ARGUMENTS-state.json
   Ready for next sprint? Use /sprint-start <N+1>
   ```

---

## If Any Checks Fail

Report failures and DO NOT mark complete:

```
Sprint $ARGUMENTS: Pre-Flight Checklist FAILED

Failed checks:
- [ ] <check name>: <reason>
- [ ] <check name>: <reason>

To resolve:
1. <action for first failure>
2. <action for second failure>

After fixing, run /sprint-complete $ARGUMENTS again.
```

**IMPORTANT**: Never mark a sprint complete if any checklist item fails.
