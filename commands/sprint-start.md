---
description: "Initialize a sprint - creates state file, spawns Plan agent"
allowed-tools: [Read, Write, Edit, Bash, Glob, Task, TodoWrite, AskUserQuestion]
---

# Start Sprint $ARGUMENTS

You are initializing Sprint **$ARGUMENTS**. Follow these steps exactly in order.

**NOTE**: This workflow supports multiple concurrent sprints. Each sprint has its own state file: `.claude/sprint-{N}-state.json`

## Step 1.1: Find and Read Sprint File

1. Use Glob to find the sprint file in any folder:
   ```
   docs/sprints/**/sprint-$ARGUMENTS*.md
   ```

2. Read the sprint planning file completely

3. Extract from the file:
   - Sprint title (from the header or YAML frontmatter)
   - Description
   - Dependencies
   - Main tasks/goals
   - Any open questions or ambiguities

## Step 1.1a: Move Sprint File and Set Metadata

1. **Move the sprint file to `in-progress/` folder** (if not already there):
   ```bash
   mv docs/sprints/todo/sprint-$ARGUMENTS*.md docs/sprints/in-progress/
   ```

2. **Add or update YAML frontmatter** at the top of the sprint file with:
   ```yaml
   ---
   sprint: $ARGUMENTS
   title: <extracted title>
   status: in-progress
   started: <current ISO 8601 timestamp with time, e.g., 2025-12-03T14:30:00>
   completed: null
   hours: null
   ---
   ```

   If the file already has a markdown table with metadata (Status, Started, etc.), keep it but ensure the YAML frontmatter is added at the very top of the file.

3. **Update the sprint file's markdown table** (if present):
   - Set `| **Status** |` to `In Progress`
   - Set `| **Started** |` to current timestamp

## Step 1.2: Create State File

Create the file `.claude/sprint-$ARGUMENTS-state.json` with this structure:

```json
{
  "sprint_number": $ARGUMENTS,
  "sprint_file": "<path to sprint file>",
  "sprint_title": "<title from sprint file>",
  "status": "in_progress",
  "current_phase": 1,
  "current_step": "1.2",
  "started_at": "<current ISO timestamp>",
  "completed_at": null,
  "completed_steps": [
    {
      "step": "1.1",
      "completed_at": "<current ISO timestamp>",
      "output": "Sprint file read: <sprint_file>",
      "agent_used": null
    }
  ],
  "blockers": [],
  "clarifications": [],
  "next_action": {
    "step": "1.2",
    "description": "Spawn Plan agent to design implementation",
    "required_agent": "Plan"
  },
  "plan_output": null,
  "test_results": null,
  "refactoring_complete": null,
  "pre_flight_checklist": {
    "tests_passing": null,
    "migrations_verified": null,
    "sample_data_generated": null,
    "mcp_tools_tested": null,
    "dialog_example_created": null,
    "sprint_file_updated": null,
    "code_has_docstrings": null,
    "no_hardcoded_secrets": null,
    "git_status_clean": null
  }
}
```

## Step 1.3: Create TodoWrite List

Create a TodoWrite list with high-level tasks from the sprint file. Include at minimum:
- Phase 1: Planning tasks
- Phase 2: Implementation tasks
- Phase 3: Validation & Refactoring tasks
- Phase 5: Commit
- Phase 6: Completion

## Step 1.4: Spawn Plan Agent

Use the Task tool to spawn a Plan agent:

```
Task(subagent_type="Plan", prompt="""
Review sprint {N} planning file at {sprint_file_path}

Design the implementation approach with a focus on clean, DRY architecture:

1. **Analyze existing codebase patterns**
   - What similar functionality already exists?
   - What base classes, utilities, or patterns can be reused?
   - Are there any abstractions that should be extended vs created new?

2. **Design code structure BEFORE implementation**
   - Define classes, functions, and their responsibilities
   - Identify shared logic that should be extracted to utilities
   - Plan inheritance/composition relationships
   - Ensure no duplication with existing code

3. **Identify files to create/modify**
   - List all files with their purpose
   - For each new class/function, explain why it can't reuse existing code

4. **Determine implementation order**
   - Base/shared components first
   - Then dependent components

5. **Flag risks and questions**
   - Unclear requirements
   - Design decisions that need user input
   - Potential performance or maintainability concerns

Return a structured implementation plan with:
- **Code Architecture**: Classes, their responsibilities, and relationships
- **Shared Utilities**: Any new utility functions needed (or existing ones to reuse)
- **Files to create**: Full paths with purpose
- **Files to modify**: What changes and why
- **Implementation order**: Dependencies-first ordering
- **Patterns to follow**: Existing code patterns to maintain consistency
- **DRY Analysis**: How this design avoids duplication
- **Risks/Concerns**: Technical or requirement risks
- **Questions for user**: Ambiguities, edge cases, design preferences
""")
```

## Step 1.5: Update State with Plan Output

After the Plan agent returns, update `.claude/sprint-$ARGUMENTS-state.json`:
- Set `plan_output` with the agent's findings
- Set `current_step` to "1.3"
- Add step 1.2 to `completed_steps`
- Update `next_action` to step 1.3

## Step 1.6: Clarify Requirements (REQUIRED)

**Before any implementation begins, you MUST ask the user clarifying questions.**

Review the sprint file and Plan agent output for:
1. **Ambiguous requirements** - anything that could be interpreted multiple ways
2. **Edge cases** - how should the system handle unusual inputs or states?
3. **Design preferences** - are there multiple valid approaches? Let user choose
4. **Dependencies** - are there external dependencies or constraints?
5. **Acceptance criteria** - what does "done" look like for each feature?

Use the AskUserQuestion tool to present questions. Example:

```
Based on the sprint requirements and planning analysis, I have some questions before we start implementation:

1. [Specific question about requirement X]
2. [Question about edge case Y]
3. [Design choice between option A vs B]

Please clarify these so I can proceed with the correct approach.
```

**If there are no questions**, confirm with the user:
"I've reviewed the sprint requirements and don't have any clarifying questions. The requirements seem clear. Ready to proceed?"

## Step 1.7: Record Clarifications

After user responds, update `.claude/sprint-$ARGUMENTS-state.json`:
- Add user's answers to `clarifications` array
- Set `current_step` to "1.4"
- Add step 1.3 to `completed_steps`
- Update `next_action` to step 1.4

## Step 1.8: Report and Confirm

Output to user:
1. Sprint number and title
2. Summary of files to create/modify
3. Implementation order
4. Clarifications received
5. Ask: "Ready to proceed with implementation? Use `/sprint-next $ARGUMENTS` to begin Phase 2."

**IMPORTANT**: Do NOT proceed to implementation until user explicitly confirms.
