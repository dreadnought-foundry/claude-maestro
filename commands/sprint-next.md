---
description: "Advance to next sprint step after validating current step is complete"
allowed-tools: [Read, Write, Edit, Bash, Task, Glob, AskUserQuestion, AgentOutputTool, TodoWrite]
---

# Advance to Next Sprint Step

Validate the current step is complete, then advance to the next step.

## BACKWARD COMPATIBILITY

**Check `workflow_version` in state file:**
- If `workflow_version` is missing or "1.0": Use **Legacy Flow** (below)
- If `workflow_version` is "2.0" or "2.1": Use **v2.x Flow** (this document)

Existing sprints without `workflow_version` field should continue with the original 6-phase, 22-step workflow. Only sprints started with v2.x `/sprint-start` will use the new parallel workflow.

---

**Workflow Version**: 2.1 (Staged Parallelism + Auto-Postmortems)

## Legacy Flow (v1.0)

For sprints without `workflow_version` field, use the original sequential flow:
1. Follow the original 6-phase workflow from sprint-steps.json v1.0
2. Do NOT spawn parallel agents
3. Steps proceed sequentially: 1.1 → 1.2 → ... → 6.6
4. All original validation rules apply

---

## v2.x Flow

## Instructions

### 0. Determine Sprint Number

**REQUIRED**: `$ARGUMENTS` must contain the sprint number.

If `$ARGUMENTS` is empty:
- Use Glob to find all sprint state files: `.claude/sprint-*-state.json`
- If multiple found, ask user which sprint to advance
- If only one found, use that sprint number
- If none found, report "No active sprint. Use /sprint-start <N> to begin."

### 1. Read Current State

Read `.claude/sprint-$ARGUMENTS-state.json` to get:
- `current_step`
- `workflow_version`
- `team_strategy`
- `parallel_agents` (for Phase 2)
- `completed_steps`

### 2. Handle Based on Current Phase

---

## Phase 1: Planning (Steps 1.1-1.4)

Sequential execution. Validate each step before advancing.

#### Step 1.1 → 1.2
- **Validate**: `sprint_file` and `sprint_type` in state
- **Next**: Spawn Plan agent for team strategy

#### Step 1.2 → 1.3
- **Validate**: `plan_output` exists with `team_composition`
- **Next**: Clarify requirements with user

#### Step 1.3 → 1.4
- **Validate**: `clarifications` array exists (can be empty)
- **Next**: Document team strategy in sprint file

#### Step 1.4 → 2.1 (Phase Transition)
- **Validate**: Sprint file has "Team Strategy" section
- **Next**: Begin Phase 2 parallel implementation

---

## Phase 2: Implementation (Steps 2.1-2.3) - PARALLEL

When entering Phase 2, spawn parallel agents based on `team_strategy`:

### Spawning Parallel Agents

```
# Read team_strategy from state
team = state.team_strategy.team_composition

# Spawn agents in parallel using Task tool with run_in_background=true
for agent_config in team:
    Task(
        subagent_type=agent_config.agent,
        prompt="Implement {role} for Sprint {N}...",
        run_in_background=true
    )

# Store agent IDs in state
state.parallel_agents = [
    {
        "agent_id": "<id>",
        "role": "backend",
        "status": "running",
        "started_at": "<timestamp>",
        "files_owned": [...],
        "progress": [],
        "issues": []
    },
    ...
]
```

### Agent Prompt Template

Each parallel agent receives:
```
You are implementing {role} for Sprint {N}.

## Your Assignment
- Files you own: {files_owned}
- Skills to invoke: {skills}

## Rules
1. ONLY modify files in your ownership list
2. Update progress by appending to your work log
3. Report issues immediately
4. Do NOT modify files owned by other agents

## Progress Reporting
After each significant action, output a status update:
```
STATUS: {step description}
FILES: {files created/modified}
ISSUES: {any blockers or concerns}
```

## Your Tasks
{tasks from sprint file relevant to this role}

## Completion
When done, output:
```
COMPLETE: {summary}
FILES_CREATED: [list]
FILES_MODIFIED: [list]
TESTS_ADDED: {count if applicable}
```
```

### Monitoring Parallel Agents

While Phase 2 is active, `/sprint-status` shows:

```
Sprint $ARGUMENTS - Phase 2: Implementation

| Agent | Role | Status | Progress | Issues |
|-------|------|--------|----------|--------|
| abc123 | Backend | running | 3/5 tasks | None |
| def456 | Frontend | running | 2/4 tasks | Waiting for API |
| ghi789 | Tests | running | 5 tests written | None |

Use /sprint-next $ARGUMENTS when all agents complete.
```

### Checking Agent Status

Use AgentOutputTool to check each parallel agent:

```
for agent in state.parallel_agents:
    result = AgentOutputTool(agent_id=agent.agent_id, block=false)
    # Update agent status in state
    agent.status = result.status
    agent.progress = parse_progress(result.output)
    agent.issues = parse_issues(result.output)
```

### Phase 2 Completion

All agents must complete before advancing:

```
if all(agent.status == "complete" for agent in state.parallel_agents):
    # Collect outputs
    for agent in state.parallel_agents:
        output = AgentOutputTool(agent_id=agent.agent_id)
        state.agent_outputs[agent.role] = output

    # Advance to Phase 3
    state.current_step = "3.1"
    state.current_phase = 3
else:
    # Report status and wait
    report_parallel_status()
```

---

## Phase 3: Integration & Validation (Steps 3.1-3.4)

Sequential execution with integration first.

#### Step 3.1: Integration
- **Action**: Parent agent integrates parallel agent outputs
- **Check**: No file conflicts, all pieces fit together
- **Resolve**: Any merge conflicts or integration issues
- **Update**: `integration_complete = true`

#### Step 3.2: Run All Tests
- **Action**: Execute full test suite
- **Invoke**: `skill:check-coverage`
- **Validate**: All tests pass, coverage >= 75%
- **Update**: `test_results`, `coverage_percentage`

#### Step 3.3: Quality Review
- **Action**: Spawn quality-engineer agent
- **Invoke**: `skill:lint-fix`
- **Check**: No lint errors, code quality acceptable
- **Update**: `quality_review_complete = true`

#### Step 3.4: User Approval Gate
- **Action**: Present summary to user
- **Show**:
  ```
  Sprint $ARGUMENTS ready for commit.

  ## Summary
  - Files created: {count}
  - Files modified: {count}
  - Tests: {passed}/{total}
  - Coverage: {percentage}%
  - Lint: Clean

  ## Changes by Agent
  {backend agent: files}
  {frontend agent: files}
  {test agent: files}

  Approve commit? [Yes/No]
  ```
- **Validate**: User approves
- **Update**: `pre_flight_checklist.user_approved = true`

---

## Phase 4: Commit & Complete (Steps 4.1-4.4)

#### Step 4.1: Git Commit
- **Action**: Stage and commit all changes
- **Message**: Conventional commit format
- **Update**: `commit_hash`

#### Step 4.2: Update Sprint File
- **Action**: Set status to done, move to 4-done/
- **Validate**: File in correct location

#### Step 4.3: Postmortem
- **Action**: Run `/sprint-postmortem $ARGUMENTS`
- **Generate**: Agent work summary, learnings, improvements
- **Update**: Sprint file with Postmortem section

#### Step 4.4: Final Commit
- **Action**: Commit sprint file updates
- **Complete**: Sprint finished

---

## Status Update Format

When reporting status, always show:

```
Sprint $ARGUMENTS - Step X.Y: {step_name}

Phase: {phase_number} - {phase_name}
Status: {in_progress|complete|blocked}

{Phase-specific details}

Next action: {what happens next}
```

---

## If Validation Fails

```
Cannot advance Sprint $ARGUMENTS from step X.Y

Missing: {what's missing}

To complete:
1. {action needed}
2. {action needed}

Then run /sprint-next $ARGUMENTS again.
```
