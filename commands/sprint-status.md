---
description: "Show current sprint progress and next action"
allowed-tools: [Read, Glob]
---

# Sprint Status

Check sprint progress by reading the state file and YAML frontmatter.

**NOTE**: This workflow supports multiple concurrent sprints. Each sprint has its own state file: `.claude/sprint-{N}-state.json`

## Instructions

### 1. Determine Which Sprint

If `$ARGUMENTS` is provided:
- Read `.claude/sprint-$ARGUMENTS-state.json`

If `$ARGUMENTS` is empty:
- Use Glob to find all sprint state files: `.claude/sprint-*-state.json`
- If multiple found, list them and ask user which one to show status for
- If only one found, use that one
- If none found, report "No active sprint. Use /sprint-start <N> to begin."

### 2. Read Sprint File and Frontmatter

Read the sprint file from the path in state file and extract YAML frontmatter:
- `sprint`: Sprint number
- `title`: Sprint title
- `status`: Current status (in-progress, done, blocked, aborted)
- `started`: ISO timestamp when started
- `completed`: ISO timestamp when completed (if done)
- `hours`: Calculated hours worked
- `blocked_at` / `aborted_at`: Timestamps if applicable
- `blocker` / `abort_reason`: Reasons if applicable

### 3. Read Sprint Steps

Read `~/.claude/sprint-steps.json` to get step names

### 4. Display Status

Display status in this format:

---

## Sprint $sprint_number: $sprint_title

**Status:** $status
**Started:** $started_at
**Sprint File:** $sprint_file
**State File:** .claude/sprint-$sprint_number-state.json

### Progress

**Current Phase:** $current_phase of 6 - $phase_name
**Current Step:** $current_step - $step_name

### Completed Steps

| Step | Name | Completed | Agent |
|------|------|-----------|-------|
$for_each_completed_step

### Next Action

**Step $next_action.step:** $next_action.description

$if_required_agent: Required Agent: `$next_action.required_agent`

### Pre-Flight Checklist

| Item | Status |
|------|--------|
| Tests passing | $checklist_icon |
| Migrations verified | $checklist_icon |
| Sample data generated | $checklist_icon |
| MCP tools tested | $checklist_icon |
| Dialog example created | $checklist_icon |
| Sprint file updated | $checklist_icon |
| Code has docstrings | $checklist_icon |
| No hardcoded secrets | $checklist_icon |
| Git status clean | $checklist_icon |

$if_blockers:
### Blockers
$for_each_blocker

$if_test_results:
### Latest Test Results
- Passed: $test_results.passed
- Failed: $test_results.failed
- Skipped: $test_results.skipped
- Last run: $test_results.last_run

---

**Tip:** Use `/sprint-next $sprint_number` to advance after completing the current step.

---

## Showing All Active Sprints

If user runs `/sprint-status all` or if multiple sprints are found:

List all active sprints in summary format:

| Sprint | Title | Phase | Step | Status |
|--------|-------|-------|------|--------|
| N | Title | X/6 | Y.Z | in_progress |
| M | Title | X/6 | Y.Z | in_progress |

Then prompt: "Use `/sprint-status <N>` for details on a specific sprint."
