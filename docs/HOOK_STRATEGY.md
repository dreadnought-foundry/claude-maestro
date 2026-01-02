# Hook Strategy for Automated Lifecycle Management

## Overview

The workflow uses hooks to enforce proper sprint lifecycle operations while allowing authorized automation to bypass restrictions.

## Hook Architecture

```
┌─────────────────────────────────────────────────────┐
│ pre_tool_use.py Hook                                 │
│                                                      │
│  ┌─────────────────┐                                │
│  │ Check Tool Call │                                │
│  └────────┬────────┘                                │
│           │                                          │
│           ├─ Is Bash mv/git mv?                      │
│           │  └─ YES                                  │
│           │     ├─ Contains scripts/sprint_lifecycle │
│           │     │  └─ ALLOW ✅ (Authorized)          │
│           │     │                                    │
│           │     ├─ Moving sprint file?              │
│           │     │  └─ YES                            │
│           │     │     ├─ State file exists?         │
│           │     │     ├─ Checklist passed?          │
│           │     │     ├─ Valid destination?         │
│           │     │     └─ Has --done suffix?         │
│           │     │        ├─ YES → ALLOW ✅           │
│           │     │        └─ NO → BLOCK ❌            │
│           │     │                                    │
│           │     └─ Other operations → Continue      │
│           │                                          │
│           └─ Other tools → Continue                 │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Gate Rules

### 1. Sprint Completion Gate

**Purpose**: Prevent manual file operations that bypass workflow validation

**Blocks:**
- ❌ Manual `mv` of sprint files without completion checklist
- ❌ Moving to wrong folders (4-done, 5-done, etc.)
- ❌ Moving without `--done` suffix
- ❌ State file edits that bypass workflow

**Allows:**
- ✅ Operations from `scripts/sprint_lifecycle.py` (trusted automation)
- ✅ Moves when state file shows `status='complete'` and checklist passed
- ✅ Valid destinations: `3-done/_standalone/` or stay in epic folder
- ✅ Files with proper `--done` suffix

### 2. Whitelist Strategy

**Authorized Automation:**
```python
if 'scripts/sprint_lifecycle.py' in command:
    return {'continue': True}  # Bypass all gates
```

Commands containing `scripts/sprint_lifecycle.py` are **trusted** because:
- They implement proper validation internally
- They use atomic operations with rollback
- They update state files correctly
- They enforce workflow rules programmatically

**Manual Operations:**
Must go through `/sprint-complete` workflow which:
1. Runs pre-flight checklist (9 items)
2. Updates state file with completion status
3. Then calls `scripts/sprint_lifecycle.py` (which bypasses hook)

## Why This Works

### Three-Layer Protection

```
Layer 1: Hook Gates
├─ Block manual operations
└─ Allow automation

Layer 2: Automation Validation
├─ Check git status
├─ Validate file locations
├─ Atomic operations with rollback
└─ Update state files

Layer 3: Workflow Commands
├─ /sprint-complete runs checklist
├─ /sprint-new auto-assigns numbers
└─ /epic-start moves epic to in-progress
```

### Trust Model

```
User → /sprint-complete → Automation → File Operations
  ↑          ↑                ↑              ↑
  │          │                │              └─ Python shutil (bypasses hook)
  │          │                └─ scripts/sprint_lifecycle.py (whitelisted)
  │          └─ Validates checklist, updates state
  └─ Initiates workflow

User → mv sprint-file.md (direct) → BLOCKED by hook ❌
```

## Hook Bypass Methods

### Method 1: Use Automation (Recommended)
```bash
# This bypasses hook (trusted)
python3 scripts/sprint_lifecycle.py move-to-done 2
```

### Method 2: Complete Workflow First
```bash
# This updates state file, then automation bypasses hook
/sprint-complete 2
```

### Method 3: Python File Operations
```python
# Python operations (shutil, pathlib) don't trigger Bash hook
from pathlib import Path
sprint_file.rename(new_path)  # Not blocked
```

## Security Considerations

### Why Whitelist Automation?

**Without whitelist:**
- Automation would need to create state files first
- Circular dependency: automation needs to move files to update state
- Can't use automation for creation (no state file yet)

**With whitelist:**
- Automation is self-validating (checks git status, validates paths)
- Atomic operations prevent partial failures
- State files updated correctly by automation
- Manual operations still blocked

### Audit Trail

All operations tracked in:
1. **State files**: `.claude/sprint-N-state.json`
2. **Registry**: `docs/sprints/registry.json`
3. **Git commits**: Tags for each sprint completion
4. **Hook logs**: Denied operations logged to stderr

## Migration Notes

### Before Automation (Manual)
```
User manually:
1. Runs tests
2. Edits state file
3. Moves sprint file
4. Updates registry
5. Creates git tag

Hook: Validates each step
```

### After Automation (Scripted)
```
User runs: /sprint-complete 2

Workflow:
1. Runs pre-flight checklist
2. Calls automation script
3. Automation (whitelisted):
   - Moves files
   - Updates registry
   - Creates git tag
   - Updates state file

Hook: Trusts automation, blocks manual bypasses
```

## Testing

```bash
# Should BLOCK (manual operation)
mv docs/sprints/2-in-progress/sprint-02.md docs/sprints/3-done/

# Should ALLOW (automation)
python3 scripts/sprint_lifecycle.py move-to-done 2

# Should ALLOW (workflow command calls automation)
/sprint-complete 2
```

## Future Enhancements

1. **Environment Variables**: Add `SPRINT_LIFECYCLE_AUTHORIZED` env var
2. **Signature Verification**: Verify automation script hasn't been tampered with
3. **Rate Limiting**: Prevent automation abuse
4. **Audit Logging**: Log all automation operations to separate file

## Summary

**Hook Strategy = Prevent Manual Mistakes + Trust Automation**

- ✅ Blocks manual file operations (prevent mistakes)
- ✅ Allows automation scripts (trusted, validated)
- ✅ Maintains audit trail (state files, registry, git)
- ✅ Enforces workflow (must use commands/automation)
- ✅ Backwards compatible (existing workflows still work)
