---
description: "Advance to next sprint step after validating current step is complete"
allowed-tools: [Read, Write, Edit, Bash, Task, Glob, AskUserQuestion]
---

# Advance to Next Sprint Step

Validate the current step is complete, then advance to the next step.

**NOTE**: This workflow supports multiple concurrent sprints. You MUST specify the sprint number.

## Instructions

### 0. Determine Sprint Number

**REQUIRED**: `$ARGUMENTS` must contain the sprint number.

If `$ARGUMENTS` is empty:
- Use Glob to find all sprint state files: `.claude/sprint-*-state.json`
- If multiple found, ask user which sprint to advance
- If only one found, use that sprint number
- If none found, report "No active sprint. Use /sprint-start <N> to begin."

State file path: `.claude/sprint-$ARGUMENTS-state.json`

### 1. Read Current State

Read `.claude/sprint-$ARGUMENTS-state.json` to get:
- `current_step`
- `completed_steps`
- `plan_output`
- `test_results`
- `refactoring_complete`
- `pre_flight_checklist`

### 2. Validate Current Step

Based on `current_step`, verify the deliverable exists:

#### Step 1.1: Read Sprint File
- Check: `sprint_file` field is populated in state

#### Step 1.2: Spawn Plan Agent
- Check: `plan_output` field exists with `files_to_create`

#### Step 1.3: Clarify Requirements
- Check: `clarifications` field exists in state (can be empty array if no questions)
- Check: User has confirmed requirements are clear

#### Step 1.4: Mark Start
- Check: Sprint file has "Status: In Progress"
- Read the sprint file and verify

#### Step 2.1: Write Tests First
- Check: Test file exists at `tests/test_sprint{N}_*.py`
- Use Glob to verify

#### Step 2.2: Implement Feature
- Check: Files from `plan_output.files_to_create` exist
- Use Glob/Read to verify key files

#### Step 2.3: Run Tests
- Check: `test_results` field exists in state
- Verify tests were actually run

#### Step 2.4: Fix Failures
- Check: `test_results.failed == 0`
- If tests pass, this step can be skipped

#### Step 3.1: Verify Migration
- Check: Migration file exists in `alembic/versions/`
- Or: No migration needed (skippable)
- Update `pre_flight_checklist.migrations_verified`

#### Step 3.2: Quality Review
- Check: Quality engineer reviewed code
- Update `pre_flight_checklist.code_has_docstrings`

#### Step 3.3: Refactoring
- Check: `refactoring_complete == true` in state
- Or: No refactoring needed per quality review (skippable)
- Refactoring should address:
  - Code duplication (DRY violations)
  - Overly complex logic
  - Inconsistent naming or patterns
  - Missing abstractions

#### Step 3.4: Re-run Tests After Refactoring
- Check: `test_results.failed == 0` after refactoring
- Skippable if step 3.3 was skipped

#### Step 4.1: Generate Documentation
- Check: Dialog example created OR not applicable
- Update `pre_flight_checklist.dialog_example_created`

#### Step 5.1: Git Commit
- Check: `git status` shows clean working directory
- Run: `git status --porcelain`
- Update `pre_flight_checklist.git_status_clean`

#### Step 6.1: Update Sprint File
- Check: Sprint file has "Status: Complete" and "Completed: <date>"

#### Step 6.2: Handle Incomplete Items
- Check: All items complete OR user approved deferrals

#### Step 6.3: Pre-Flight Checklist
- Check: All `pre_flight_checklist` items are `true`

#### Step 6.4: Update Sprint README
- Check: `docs/sprints/README.md` lists sprint as complete

### 3. If Validation Fails

Report what's missing:
```
Cannot advance Sprint $ARGUMENTS from step X.Y

Missing deliverable: <what's missing>

To complete this step:
1. <action needed>
2. <action needed>

Then run /sprint-next $ARGUMENTS again.
```

### 4. If Validation Passes

1. Add current step to `completed_steps`:
   ```json
   {
     "step": "X.Y",
     "completed_at": "<ISO timestamp>",
     "output": "<summary of what was done>",
     "agent_used": "<agent if applicable>"
   }
   ```

2. Determine next step from `~/.claude/sprint-steps.json`:
   - Get `step_order` array
   - Find current step index
   - Next step is index + 1

3. Update state file `.claude/sprint-$ARGUMENTS-state.json`:
   - `current_step` = next step
   - `current_phase` = phase of next step
   - `next_action` = details of next step

4. Report advancement:
   ```
   Sprint $ARGUMENTS - Step X.Y complete: <summary>

   Advanced to Step X.Y: <step name>

   Next action: <description>
   Required agent: <agent or "none">
   ```

### 5. If Sprint Complete

If current step was 6.4 and it passes:

1. Update state:
   - `status` = "complete"
   - `completed_at` = current timestamp

2. Report:
   ```
   Sprint $ARGUMENTS complete!

   Summary:
   - Steps completed: X
   - Time elapsed: <duration>
   - Files created: <count>

   State file preserved at .claude/sprint-$ARGUMENTS-state.json for reference.
   Ready to start next sprint? Use /sprint-start <N+1>
   ```
