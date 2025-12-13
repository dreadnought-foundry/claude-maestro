---
description: "Initialize a sprint - creates state file, spawns Plan agent"
allowed-tools: [Read, Write, Edit, Bash, Glob, Task, TodoWrite, AskUserQuestion]
---

# Start Sprint $ARGUMENTS

You are initializing Sprint **$ARGUMENTS** using the optimized v2.1 workflow.

## Workflow Overview (v2.1)

```
Phase 1: Planning (sequential)
  1.1 Read Sprint → 1.2 Plan & Team Design → 1.3 Clarify → 1.4 Document Strategy

Phase 2: Implementation (parallel)
  2.1 Backend ──┐
  2.2 Frontend ─┼─→ Parent integrates
  2.3 Tests ────┘

Phase 3: Integration & Validation (sequential)
  3.1 Integrate → 3.2 Run Tests → 3.3 Quality Review → 3.4 User Approval

Phase 4: Commit & Complete (sequential)
  4.1 Commit → 4.2 Update Sprint → 4.3 Postmortem → 4.4 Final Commit
```

---

## Step 1.1: Find and Read Sprint File

1. Use Glob to find the sprint file:
   ```
   docs/sprints/**/sprint-$ARGUMENTS*.md
   ```

2. Read the sprint planning file completely

3. Extract:
   - Sprint title
   - Sprint type (backend-only, frontend-only, fullstack, integration, data-layer)
   - Epic number (if part of epic)
   - Tasks and acceptance criteria
   - Any open questions

## Step 1.1a: Move Sprint File to In-Progress

**Use Bash to move the file:**
```bash
mv docs/sprints/1-todo/<epic-folder>/sprint-$ARGUMENTS*.md docs/sprints/2-in-progress/<epic-folder>/
```

Validate move succeeded with Glob.

Update YAML frontmatter:
```yaml
---
sprint: $ARGUMENTS
title: <title>
status: in-progress
workflow_version: "2.1"
epic: <epic number or null>
created: <original created date>
started: <ISO timestamp>
completed: null
hours: null
---
```

## Step 1.1b: Check Backlog for Related Items

Read `docs/sprints/backlog.md` and identify any action items that may be relevant to this sprint:

1. **Search for related items**:
   - Items mentioning similar files/components
   - Items from the same epic
   - Items tagged `[backlog]` that could be addressed in this sprint

2. **If relevant items found**, display to user:
   ```
   Backlog items related to Sprint $ARGUMENTS:

   - [ ] [backlog] <item description> (from Sprint NN)
   - [ ] [backlog] <item description> (from Sprint MM)

   Consider addressing these during this sprint if scope allows.
   ```

3. **If no relevant items**, continue silently.

This ensures learnings from previous sprints are surfaced at the right time.

## Step 1.2: Create State File

Create `.claude/sprint-$ARGUMENTS-state.json`:

```json
{
  "sprint_number": $ARGUMENTS,
  "sprint_file": "<path>",
  "sprint_title": "<title>",
  "sprint_type": "<type>",
  "status": "in_progress",
  "current_phase": 1,
  "current_step": "1.2",
  "started_at": "<timestamp>",
  "workflow_version": "2.1",
  "team_strategy": null,
  "parallel_agents": [],
  "completed_steps": [
    {"step": "1.1", "completed_at": "<timestamp>", "output": "Sprint file read"}
  ],
  "clarifications": [],
  "plan_output": null,
  "test_results": null,
  "coverage_percentage": null,
  "pre_flight_checklist": {
    "tests_passing": null,
    "coverage_met": null,
    "migrations_verified": null,
    "lint_clean": null,
    "user_approved": null
  }
}
```

## Step 1.3: Spawn Plan Agent

Use Task tool with Plan agent:

```
Task(subagent_type="Plan", prompt="""
Review sprint {N} at {sprint_file_path}

Design implementation with TEAM STRATEGY:

1. **Determine Sprint Type**
   - backend-only: Models, migrations, API only
   - frontend-only: UI components, pages only
   - fullstack: Both backend and frontend
   - integration: Wiring existing components
   - data-layer: Database and data processing

2. **Design Team Composition**
   For each work stream, specify:
   - Agent type (product-engineer, quality-engineer)
   - Files owned (exclusive ownership)
   - Skills to invoke (validate-graphql, validate-mcp, etc.)

3. **Plan Parallel Execution**
   - Which streams can run in parallel?
   - What are the integration points?
   - What order should integration happen?

4. **TDD Approach**
   Recommend TDD level:
   - Strict: Complex business logic, risk scoring
   - Flexible: Standard features (DEFAULT)
   - Coverage-based: Simple CRUD, UI-only

5. **Identify Risks & Questions**
   - Ambiguous requirements
   - Design decisions needing user input
   - Potential conflicts between parallel agents

Return structured output:
- sprint_type: string
- team_composition: [{agent, role, files, skills}]
- parallel_streams: [stream_names]
- integration_order: [stream_names]
- tdd_approach: strict|flexible|coverage
- file_ownership: {file: agent}
- risks: [strings]
- questions: [strings]
""")
```

## Step 1.4: Clarify Requirements

Present user with:
1. Questions from Plan agent
2. Confirm team strategy makes sense
3. Confirm TDD approach

Use AskUserQuestion tool. If no questions:
"Requirements are clear. Ready to proceed with team strategy: {summary}"

## Step 1.5: Document Team Strategy

Update the sprint file with Team Strategy section:

```markdown
## Team Strategy

### Sprint Type
- **Type**: {sprint_type}
- **Parallelism**: {yes if multiple streams}

### Agent Assignments

| Agent | Role | Files Owned | Skills |
|-------|------|-------------|--------|
{from plan_output}

### File Ownership

{from plan_output.file_ownership}

### Integration Strategy

{from plan_output.integration_order}

### TDD Approach

{from plan_output.tdd_approach with justification}
```

## Step 1.6: Update State and Report

Update state file:
- `team_strategy`: from plan output
- `current_step`: "2.1"
- Add completed steps

Report to user:
1. Sprint {N}: {title}
2. Type: {sprint_type}
3. Team composition summary
4. Parallel streams: {list}
5. Skills to be invoked: {list}
6. TDD approach: {approach}

## Step 1.7: AUTO-CONTINUE TO PHASE 2

**IMPORTANT**: v2.1 workflow has only ONE user gate (step 3.4 before commit).
After planning is complete, AUTOMATICALLY proceed to implementation.

Immediately invoke the sprint-next command behavior:
- Spawn parallel agents based on team_strategy
- Do NOT wait for user confirmation
- Continue working until Phase 3.4 (user approval before commit)

---

## Notes

- v2.1 = Single gate workflow (only pause at step 3.4 before commit)
- Phase 2 spawns parallel agents based on team_strategy
- Each agent only modifies files in their ownership
- Parent agent handles integration in Phase 3
- User sees progress but doesn't need to approve until commit
