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

### 0. Postmortem Section Exists (REQUIRED)

**This check MUST pass before any other checks.**

```bash
grep -q "## Postmortem" <sprint_file_path>
```

- [ ] Sprint file contains `## Postmortem` section
- [ ] Postmortem has "What Went Well" subsection
- [ ] Postmortem has "Action Items" subsection

**If postmortem is missing:**
```
BLOCKED: Sprint cannot be completed without a postmortem.

Run `/sprint-postmortem $ARGUMENTS` first, or manually add a ## Postmortem section.
```

Update: `pre_flight_checklist.postmortem_exists = true/false`

### 1. Tests Passing with 75% Coverage

```bash
source .venv/bin/activate && pytest tests/ -q --tb=no --cov=src/corrdata --cov-report=term --cov-fail-under=75
```

- [ ] Exit code is 0 (all tests pass)
- [ ] No failures in output
- [ ] Coverage is at least 75%

Update: `pre_flight_checklist.tests_passing = true/false`
Update: `pre_flight_checklist.coverage_percentage = <actual percentage>`

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

### 5. Sprint File Updated

Read the sprint file and verify:
- [ ] Status is "Complete" or ready to be set
- [ ] Completed date is set or ready to be set
- [ ] Implementation checklist items are checked off

Update: `pre_flight_checklist.sprint_file_updated = true/false`

### 6. Code Has Docstrings

Check new/modified Python files:
```bash
grep -L '"""' src/corrdata/**/*.py 2>/dev/null | head -5
```

- [ ] All new classes have docstrings
- [ ] All new public functions have docstrings

Update: `pre_flight_checklist.code_has_docstrings = true/false`

### 7. No Hardcoded Secrets

Search for potential secrets:
```bash
grep -rn -E "(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]" src/ --include="*.py" | grep -v "test" | grep -v "#"
```

- [ ] No hardcoded passwords
- [ ] No hardcoded API keys
- [ ] No hardcoded tokens

Update: `pre_flight_checklist.no_hardcoded_secrets = true/false`

### 8. Git Status Clean

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

2. **Generate Postmortem** (add to sprint file before completion):

   Read the state file and gather:
   - Duration: completed_at - started_at
   - Tests written: count from test_results in state or test files
   - Files created/modified: from completed_steps output

   Add a `## Postmortem` section to the sprint file with:

   ```markdown
   ## Postmortem

   ### Summary
   <One sentence describing what the sprint accomplished>

   ### Duration & Metrics
   - **Duration**: <hours> hours
   - **Tests Written**: <count> (backend: X, frontend: Y)
   - **Files Created**: <count>
   - **Files Modified**: <count>

   ### What Went Well
   - <Positive outcomes, patterns reused, early discoveries>

   ### What Could Improve
   - <Issues encountered, things discovered late, gaps>

   ### Patterns Discovered
   - <Reusable patterns or components created>
   - <Approaches that worked well>

   ### Action Items
   - [x] `[done]` <Completed items with link to resolution>
   - [ ] `[sprint]` <Items that need dedicated sprint> → Sprint NNN
   - [ ] `[backlog]` <Future work, not urgent>
   - [ ] `[pattern]` <Process/code patterns to document>
   ```

   **Action Item Tags**:
   | Tag | Meaning | Action |
   |-----|---------|--------|
   | `[done]` | Already resolved | Mark with link to resolution |
   | `[sprint]` | Needs dedicated sprint | Create todo sprint, add to backlog |
   | `[backlog]` | Future work | Add to `docs/sprints/backlog.md` |
   | `[pattern]` | Reusable pattern | Add to cookbook |

   **Guidelines for postmortem content**:
   - Be specific about what went well (e.g., "Pattern reuse from Sprint X saved time")
   - Be honest about what could improve (e.g., "Missing hook wasn't in initial plan")
   - Note any follow-up sprints created
   - Reference specific file names and component names
   - **Tag every action item** with one of the above tags

2b. **Process Action Items**:

   After writing the postmortem, process each action item:

   **For `[sprint]` items**:
   - Create a new sprint file in `docs/sprints/1-todo/`
   - Use `/sprint-new` format or create manually
   - Add reference to backlog.md with link to new sprint

   **For `[backlog]` items**:
   - Add to `docs/sprints/backlog.md` under "Active Backlog"
   - Include source sprint reference

   **For `[pattern]` items**:
   - Add to appropriate cookbook file in `docs/cookbook/`
   - Or create new pattern file if significant

   **For `[done]` items**:
   - Ensure link to resolution is included
   - Add to backlog.md "Resolved Items" table

3. **Update YAML frontmatter** in sprint file:
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

4. **Update the sprint file's markdown table** (if present):
   - Set `| **Status** |` to `Complete`
   - Set `| **Completed** |` to current date/time
   - Check off all checklist items

5. **Move or rename sprint file based on epic membership**:

   First, detect if sprint is part of an epic:
   ```bash
   # Find the current sprint file
   SPRINT_FILE=$(find docs/sprints -name "sprint-$ARGUMENTS_*.md" -o -name "sprint-$ARGUMENTS*.md" | grep -v "\-\-" | head -1)

   # Check if it's in an epic folder
   if echo "$SPRINT_FILE" | grep -q "/epic-"; then
     IS_IN_EPIC=true
   else
     IS_IN_EPIC=false
   fi
   ```

   **If in an epic** (IS_IN_EPIC=true):
   - Rename with `--done` suffix, keep in epic folder
   ```bash
   mv "$SPRINT_FILE" "${SPRINT_FILE%.md}--done.md"
   ```
   - **Note**: The epic folder stays in `2-in-progress/` until ALL sprints are complete.
   - Use `/epic-complete <N>` when all sprints in the epic are done.

   **If standalone** (IS_IN_EPIC=false):
   - Rename with `--done` suffix and move to `docs/sprints/3-done/_standalone/`
   ```bash
   mkdir -p docs/sprints/3-done/_standalone
   BASENAME=$(basename "$SPRINT_FILE" .md)
   mv "$SPRINT_FILE" "docs/sprints/3-done/_standalone/${BASENAME}--done.md"
   ```

6. **Update `docs/sprints/README.md`**:
   - Add sprint to completed list with hours tracked
   - Update statistics if present

7. **Update state file** `.claude/sprint-$ARGUMENTS-state.json`:
   - `status` = "complete"
   - `completed_at` = current ISO timestamp

8. **Report success**:

   **For epic sprints**:
   ```
   Sprint $ARGUMENTS: <title> - COMPLETE ✓

   Pre-Flight Checklist: 8/8 passed

   Summary:
   - Started: <timestamp>
   - Completed: <timestamp>
   - Hours: <calculated hours>
   - Steps completed: <count>

   Sprint file renamed to: <filename>--done.md
   State file preserved at .claude/sprint-$ARGUMENTS-state.json

   Epic status: <X of Y sprints complete>
   When all sprints done: /epic-complete <epic-number>
   ```

   **For standalone sprints**:
   ```
   Sprint $ARGUMENTS: <title> - COMPLETE ✓

   Pre-Flight Checklist: 8/8 passed

   Summary:
   - Started: <timestamp>
   - Completed: <timestamp>
   - Hours: <calculated hours>
   - Steps completed: <count>

   Sprint file moved to: docs/sprints/3-done/_standalone/<filename>--done.md
   State file preserved at .claude/sprint-$ARGUMENTS-state.json
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
