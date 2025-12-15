---
description: "Recover a sprint file that ended up in the wrong location"
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
---

# Recover Sprint File

Recover a sprint file that ended up in the wrong location during completion.

**NOTE**: This command fixes sprint files that:
- Were moved to wrong folders (e.g., `4-done/` instead of `3-done/`)
- Are missing the `--done` suffix
- Were not moved at all

## Determine Sprint Number

**REQUIRED**: `$ARGUMENTS` must contain the sprint number.

If `$ARGUMENTS` is empty:
- Ask user which sprint to recover
- Example: "Which sprint number needs recovery?"

---

## Step 1: Locate the Sprint File

Search for the sprint file in all possible locations:

```bash
# Find all files matching this sprint number
find docs/sprints -name "*sprint-$ARGUMENTS*" -o -name "*sprint-$ARGUMENTS_*" 2>/dev/null

# Also check for state file
cat .claude/sprint-$ARGUMENTS-state.json 2>/dev/null | grep sprint_file
```

Report what you find:
```
Sprint $ARGUMENTS File Search:

Found files:
- <path1>
- <path2>

State file says: <sprint_file value from state>
```

---

## Step 2: Determine Correct Location

Based on sprint type:

**Check if sprint is part of an epic**:
```bash
# Read state file for epic info
cat .claude/sprint-$ARGUMENTS-state.json | grep -E "(epic|sprint_file)"
```

**Correct locations**:

| Sprint Type | Correct Location |
|-------------|------------------|
| Standalone (not in epic) | `docs/sprints/3-done/_standalone/sprint-$ARGUMENTS_<title>--done.md` |
| In epic (incomplete epic) | `docs/sprints/2-in-progress/epic-N/sprint-$ARGUMENTS_<title>--done.md` |
| In epic (complete epic) | `docs/sprints/3-done/epic-N/sprint-$ARGUMENTS_<title>--done.md` |

---

## Step 3: Validate Current Location

Check if file is in correct location:

```bash
FOUND_FILE="<path from step 1>"

# Check 1: Is it in 3-done/_standalone for standalone sprints?
# Check 2: Does it have --done suffix?
# Check 3: Is it NOT in invalid folders (4-done, 5-done, etc.)?
```

**If file is in wrong location**, report:
```
PROBLEM DETECTED:

Current location: <current path>
Expected location: <correct path>

Issues:
- [ ] Wrong folder (found: X, expected: Y)
- [ ] Missing --done suffix
- [ ] Invalid folder created (e.g., 4-done)
```

---

## Step 4: Fix the Location

If recovery is needed:

### 4a. Create correct directory if needed

```bash
# For standalone sprints
mkdir -p docs/sprints/3-done/_standalone

# For epic sprints (if epic is complete)
mkdir -p docs/sprints/3-done/epic-N
```

### 4b. Move and rename file

```bash
# Get the base filename without path and existing --done
BASENAME=$(basename "$FOUND_FILE" .md | sed 's/--done$//' | sed 's/--block$//')

# Move to correct location with --done suffix
git mv "$FOUND_FILE" "docs/sprints/3-done/_standalone/${BASENAME}--done.md"
```

### 4c. Clean up invalid folders

```bash
# Remove any incorrectly created folders
rmdir docs/sprints/4-done 2>/dev/null
rmdir docs/sprints/5-done 2>/dev/null
# etc.
```

### 4d. Update state file

Update `.claude/sprint-$ARGUMENTS-state.json`:
- Set `sprint_file` to the new correct path
- Set `status` to `complete` if all checks pass

```json
{
  "sprint_file": "docs/sprints/3-done/_standalone/sprint-$ARGUMENTS_<title>--done.md",
  "status": "complete"
}
```

---

## Step 5: Commit the Fix

```bash
git add -A
git commit -m "fix: recover sprint $ARGUMENTS file to correct location

- Moved from: <old path>
- Moved to: <new path>
- Cleaned up invalid folders

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Step 6: Report Success

```
Sprint $ARGUMENTS: RECOVERED ✓

Fixed issues:
- [x] Moved to correct folder: docs/sprints/3-done/_standalone/
- [x] Added --done suffix
- [x] Removed invalid 4-done folder
- [x] Updated state file

New location: <new path>
Commit: <hash>

Sprint is now properly completed.
```

---

## Common Recovery Scenarios

### Scenario 1: File in wrong folder without suffix

```
Before: docs/sprints/4-done/sprint-124_fullcalendar-integration.md
After:  docs/sprints/3-done/_standalone/sprint-124_fullcalendar-integration--done.md
```

### Scenario 2: File has suffix but wrong folder

```
Before: docs/sprints/2-in-progress/sprint-100_something--done.md
After:  docs/sprints/3-done/_standalone/sprint-100_something--done.md
```

### Scenario 3: Epic sprint completed but epic incomplete

```
Before: docs/sprints/3-done/sprint-50_epic-task.md
After:  docs/sprints/2-in-progress/epic-5/sprint-50_epic-task--done.md
```

---

## Prevention Notes

This command exists because sprints can end up in wrong locations due to:

1. **Manual moves** bypassing the workflow
2. **State file manipulation** to bypass gates
3. **Interrupted sessions** leaving partial moves
4. **Typos** in folder names

To prevent future issues:
- Always use `/sprint-complete` to finish sprints
- Never manually edit state file `status` field
- The pre-tool hook now blocks moves to invalid folders
- The sprint-complete command validates file location before marking complete
