---
description: "Start a sprint in studly mode - auto-loads project context before executing"
allowed-tools: [Bash, Read, Glob, Grep, Task, Edit, Write, AskUserQuestion]
---

# Start Sprint — Studly Mode

`/sprint-start` but smarter. Automatically generates and loads a project context brief before executing the sprint workflow. Claude gets full awareness of prior sprints, project conventions, and key decisions without you lifting a finger.

Use this instead of `/sprint-start` when working on a project with multiple completed sprints.

## Instructions

### 0. Build and Read Project Context

Generate a context brief for the target sprint:

```bash
cd <project_root> && PYTHONPATH=~/.claude/scripts python3 -m sprint_automation build-context $ARGUMENTS
```

Then read the generated brief to load project awareness:

```bash
cat .claude/sprint-*-context.md
```

This gives you: prior sprint summaries, project tech stack, team structure, code standards, and key decisions. Use this context throughout the sprint — do NOT ask the user for information that's already in the brief.

If the context builder fails (missing module, no registry), skip this step and continue normally. It is not blocking.

### 1. Initialize Sprint

Run the start-sprint automation:

```bash
python3 ~/.claude/scripts/sprint_lifecycle.py start-sprint $ARGUMENTS
```

If sprint is already started, continue from current step.

### 2. Execute Phase 1: Planning (Steps 1.1-1.2)

**Step 1.1 - Read Sprint File:**
- Read the sprint file from the state
- Cross-reference with the context brief from step 0
- Understand requirements, scope, and technical approach
- Advance step: `python3 ~/.claude/scripts/sprint_lifecycle.py advance-step $ARGUMENTS`

**Step 1.2 - Spawn Plan Agent:**
- Use Task tool with subagent_type="Plan" to design implementation
- Include relevant context from the brief in the agent prompt (tech stack, prior work, conventions)
- Prompt should include sprint requirements and ask for:
  - Files to create/modify
  - Architecture decisions
  - Test strategy
- Advance step after plan is complete

### 3. PAUSE at Step 1.3: Clarify Requirements

**CRITICAL: Stop and ask user questions using AskUserQuestion tool.**

Based on the sprint requirements, plan, AND context brief, identify:
- Ambiguous requirements that need clarification
- Edge cases that need decisions
- Implementation preferences (e.g., library choices, patterns)
- Any open questions from the sprint file

Present 1-4 focused questions. Wait for user response before continuing.

After user responds, advance step.

### 4. Execute Steps 1.4 through 5.2 (Automated)

**Step 1.4 - Mark Start:** Update sprint file status (advance step)

**Phase 1.5 - Interface Contract (fullstack only):**
- 1.5.1: Define interface contract if fullstack sprint
- 1.5.2: Validate contract

**Phase 2 - Test-First Implementation:**
- 2.1: Write failing tests using product-engineer agent
- 2.2: Implement feature using product-engineer agent
- 2.3: Run tests using test-runner agent
- 2.4: Fix failures if any (skip if tests pass)

**Phase 3 - Validation & Refactoring:**
- 3.1: Verify migrations (skip if none)
- 3.2: Run ALL Tests (not just changed files):
  - Run the COMPLETE test suite: `npx jest --no-coverage` (frontend) and `pytest` (backend)
  - If tests fail in files NOT touched by this sprint, these are collateral failures
  - Collateral failures from text/copy changes MUST be fixed before advancing
  - Common pattern: test uses getByText/getByRole with old text that was changed
- 3.3: Refactoring based on review
- 3.4: Re-run tests after refactoring

**Phase 4 - Documentation:**
- 4.1: Generate documentation if significant new capability

**Phase 5 - Commit:**
- 5.1: Verify coverage gate meets sprint type threshold
- 5.2: Git commit all changes

### 5. Stop Before Phase 6

After completing step 5.2, report:

```
============================================================
Sprint $N: $TITLE - READY FOR COMPLETION
============================================================
All implementation steps complete.
Context: Project brief loaded (N prior sprints summarized)
Tests: PASSING
Coverage: XX%
Commit: <hash>

Run `/sprint-complete` to finalize the sprint.
============================================================
```

DO NOT execute Phase 6 steps. User controls completion.

## Execution Pattern

For each step:
1. Execute the step's work (agent, validation, etc.)
2. Run `python3 ~/.claude/scripts/sprint_lifecycle.py advance-step $ARGUMENTS`
3. Continue to next step (unless at 1.3 pause or 5.2 stop)

## Error Handling

If any step fails:
- Report the error clearly
- Do NOT advance to next step
- Suggest fix or ask user for guidance
- User can retry with `/sprint-studlymode $ARGUMENTS` to resume from current step
