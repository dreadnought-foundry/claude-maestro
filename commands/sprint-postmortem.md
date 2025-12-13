---
description: "Run postmortem analysis after sprint completion"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Sprint Postmortem for Sprint $ARGUMENTS

You are running a postmortem for Sprint **$ARGUMENTS**. This captures learnings and improvements.

## Step 1: Locate Sprint File

Find the sprint file (should be in 4-done/ after completion):
```
docs/sprints/4-done/**/sprint-$ARGUMENTS*.md
```

If not in 4-done/, check 2-in-progress/ and warn user sprint may not be complete.

## Step 2: Gather Metrics

1. **Read the sprint state file** (if exists):
   ```
   .claude/sprint-$ARGUMENTS-state.json
   ```

2. **Calculate metrics**:
   - Duration: completed_at - started_at
   - Files changed: `git diff --stat <commit_before>..<commit_after>`
   - Tests added: count test functions in tests/test_sprint{N}_*.py

3. **Get coverage delta** (if available):
   - Compare coverage before/after sprint

## Step 3: Summarize Agent Work

Review the state file's `completed_steps` to summarize:
- What each agent accomplished
- Files each agent created/modified
- Any blockers encountered

## Step 4: Identify Learnings

Ask these questions:

### What Went Well?
- Did the team strategy work effectively?
- Were file ownership boundaries respected?
- Did skills run correctly?

### What Could Improve?
- Were there integration conflicts?
- Did any agent get blocked waiting for another?
- Were there unexpected dependencies?

### Patterns Discovered
- Any reusable code patterns that emerged?
- Common error handling approaches?
- Useful test fixtures created?

### Technical Insights
- Performance considerations learned?
- API design patterns that worked well?
- Database schema decisions that helped/hurt?

## Step 5: Update Sprint File

Add/update the Postmortem section in the sprint file with:

```markdown
## Postmortem

### Summary

| Metric | Value |
|--------|-------|
| Started | {from state file} |
| Completed | {from state file} |
| Duration | {calculated} |
| Tests Added | {count} |
| Coverage Delta | {if available} |
| Files Changed | {from git} |

### Agent Work Summary

{Table of agent contributions}

### What Went Well

- {List positives}

### What Could Improve

- {List improvements}

### Patterns Discovered

{Code patterns worth reusing}

### Learnings for Future Sprints

1. **Technical**: {insight}
2. **Process**: {improvement}
3. **Integration**: {lesson}

### Action Items

- [ ] {Follow-up tasks}
```

## Step 6: Update Epic (if applicable)

If the sprint is part of an epic, update the epic's `_epic.md` with:
- Sprint completion summary (one line)
- Key learnings that apply to other sprints in the epic

## Step 7: Extract Patterns

If any significant patterns were discovered:
1. Create a pattern file in `docs/patterns/{pattern-name}.md`
2. Document the pattern with examples
3. Reference it from the sprint postmortem

## Step 8: Report

Output to user:
1. Summary of metrics
2. Key learnings
3. Action items identified
4. Recommendations for next sprint

---

**Note**: Postmortem is part of continuous improvement. Be honest about what didn't work - that's how we get better.
