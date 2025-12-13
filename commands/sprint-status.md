---
description: "Show current sprint progress and next action"
allowed-tools: [Read, Glob, AgentOutputTool]
---

# Sprint Status

Check sprint progress including parallel agent status.

## BACKWARD COMPATIBILITY

**Check `workflow_version` in state file:**
- If missing or "1.0": Show legacy 6-phase status (no parallel agents section)
- If "2.0" or "2.1": Show full v2.x status with parallel agents

Existing sprints continue with their original workflow.

---

**Workflow Version**: 2.1

## Instructions

### 1. Determine Which Sprint

If `$ARGUMENTS` is provided:
- Read `.claude/sprint-$ARGUMENTS-state.json`

If `$ARGUMENTS` is empty:
- Use Glob to find all sprint state files: `.claude/sprint-*-state.json`
- If multiple found, list summary and ask which one
- If only one found, use that one
- If none found, report "No active sprint. Use /sprint-start <N> to begin."

### 2. Read State and Sprint File

1. Read state file for:
   - `current_phase`, `current_step`
   - `workflow_version`
   - `team_strategy`
   - `parallel_agents` (if Phase 2)
   - `completed_steps`
   - `pre_flight_checklist`

2. Read sprint file YAML frontmatter for:
   - `status`, `started`, `completed`

### 3. Check Parallel Agent Status (Phase 2 Only)

If `current_phase == 2` and `parallel_agents` exists:

For each agent in `parallel_agents`:
```
result = AgentOutputTool(agent_id=agent.agent_id, block=false)
agent.status = result.status  # running, complete, error
agent.last_output = last_lines(result.output, 5)
```

Parse agent output for STATUS/ISSUES markers.

### 4. Display Status

---

## Sprint $sprint_number: $sprint_title

**Status:** $status | **Workflow:** v$workflow_version
**Started:** $started_at
**Sprint File:** $sprint_file

---

### Phase Progress

```
Phase 1: Planning      [####----] Step 1.$step
Phase 2: Implementation [--------]
Phase 3: Validation     [--------]
Phase 4: Complete       [--------]
```

**Current:** Phase $current_phase - Step $current_step: $step_name

---

### Team Strategy

**Type:** $sprint_type
**Parallelism:** $parallel_enabled
**TDD Approach:** $tdd_approach

| Role | Agent | Files Owned | Skills |
|------|-------|-------------|--------|
$for_each_team_member

---

### Parallel Agents (Phase 2)

*Only shown during Phase 2 implementation*

| ID | Role | Status | Progress | Last Update |
|----|------|--------|----------|-------------|
| $agent_id | $role | $status | $progress_summary | $last_update |

**Issues Reported:**
- $agent_id: $issue (or "None")

**Recent Activity:**
```
$last_5_lines_from_each_agent
```

---

### Completed Steps

| Step | Name | Completed | Agent |
|------|------|-----------|-------|
$for_each_completed_step

---

### Next Action

**Step $next_step:** $next_description

$if_parallel: "Parallel agents running. Use `/sprint-status $N` to refresh."
$if_gate: "Waiting for user approval."
$if_normal: "Use `/sprint-next $N` to advance."

---

### Pre-Flight Checklist

| Item | Status |
|------|--------|
| Tests passing | $icon |
| Coverage >= 75% | $icon |
| Migrations verified | $icon |
| Lint clean | $icon |
| User approved | $icon |

---

### Test Results (if available)

- Passed: $passed
- Failed: $failed
- Coverage: $coverage%
- Last run: $timestamp

---

## Showing All Active Sprints

If `/sprint-status all`:

| Sprint | Title | Phase | Step | Agents | Status |
|--------|-------|-------|------|--------|--------|
| N | Title | 2/4 | 2.1 | 3 running | in_progress |
| M | Title | 1/4 | 1.3 | - | planning |

---

## Quick Actions

- `/sprint-next $N` - Advance to next step
- `/sprint-status $N` - Refresh status (check agent progress)
- `/sprint-postmortem $N` - Generate postmortem (after completion)
- `/sprint-abort $N` - Abort sprint
- `/sprint-blocked $N` - Mark as blocked
