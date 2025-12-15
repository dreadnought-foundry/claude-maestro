---
description: "Initialize a new project with the sprint workflow system"
allowed-tools: [Read, Write, Bash, Glob]
---

# Create Project Workflow

Initialize a new project with the sprint workflow system from the master environment.

## Instructions

### 1. Determine Target Project

Parse $ARGUMENTS:
- If empty, use current working directory
- If a path is provided, use that path
- Validate the path exists and is a directory

```bash
# Check if path exists
ls -la "$TARGET_PATH" 2>/dev/null || echo "Directory not found"
```

### 2. Check for Existing Setup

```bash
# Check if .claude directory already exists
ls -la "$TARGET_PATH/.claude" 2>/dev/null
```

If `.claude/` already exists:
```
WARNING: Project already has a .claude directory.
Use /project-update to sync changes from master, or remove .claude/ first.
```

### 3. Create Project Structure

Create the `.claude/` directory structure:

```bash
mkdir -p "$TARGET_PATH/.claude/commands"
mkdir -p "$TARGET_PATH/.claude/hooks"
mkdir -p "$TARGET_PATH/.claude/agents"
```

### 4. Copy Master Files

Copy files from master environment (`~/.claude/`) to project:

#### Commands (from ~/.claude/commands/)
All sprint, epic, and product commands:
- sprint-*.md
- epic-*.md
- product-*.md

```bash
# Copy all workflow commands
cp ~/.claude/commands/sprint-*.md "$TARGET_PATH/.claude/commands/"
cp ~/.claude/commands/epic-*.md "$TARGET_PATH/.claude/commands/"
cp ~/.claude/commands/product-*.md "$TARGET_PATH/.claude/commands/"
```

#### Hooks (from ~/.claude/hooks/)
Copy enforcement hooks:
- pre_tool_use.py
- session_start.py

```bash
cp ~/.claude/hooks/*.py "$TARGET_PATH/.claude/hooks/"
```

#### Configuration Files
Copy workflow configuration:

```bash
# Copy sprint steps definition if it exists in master
cp ~/.claude/sprint-steps.json "$TARGET_PATH/.claude/" 2>/dev/null || true

# Copy sprint state schema
cp ~/.claude/sprint-state.schema.json "$TARGET_PATH/.claude/" 2>/dev/null || true
```

### 5. Create Project-Specific Files

Create default project configuration:

#### settings.json
```json
{
  "workflow_version": "2.0",
  "sprint_counter_file": "docs/sprints/next-sprint.txt",
  "sprint_directories": {
    "todo": "docs/sprints/1-todo",
    "in_progress": "docs/sprints/2-in-progress",
    "done": "docs/sprints/3-done",
    "aborted": "docs/sprints/5-aborted"
  }
}
```

#### Create sprint directories
```bash
mkdir -p "$TARGET_PATH/docs/sprints/1-todo"
mkdir -p "$TARGET_PATH/docs/sprints/2-in-progress"
mkdir -p "$TARGET_PATH/docs/sprints/3-done/_standalone"
mkdir -p "$TARGET_PATH/docs/sprints/5-aborted"
```

#### Create sprint counter
```bash
echo "1" > "$TARGET_PATH/docs/sprints/next-sprint.txt"
```

### 6. Create CLAUDE.md Template

Create a project CLAUDE.md with workflow instructions:

```markdown
# Project Instructions

## Workflow System

This project uses the **AI-assisted sprint workflow** system.

### Quick Start

```bash
/sprint-new "Feature Name"    # Create a new sprint
/sprint-start <N>             # Start working on sprint N
/sprint-status                # Check current progress
/sprint-next                  # Advance to next step
/sprint-complete              # Finish sprint (runs checklist)
```

### Sprint Directories

- `docs/sprints/1-todo/` - Planned sprints
- `docs/sprints/2-in-progress/` - Active sprints
- `docs/sprints/3-done/` - Completed sprints
- `docs/sprints/5-aborted/` - Cancelled sprints

### Workflow Enforcement

The sprint workflow is enforced via hooks. Key rules:
- Cannot skip steps - must complete current before advancing
- Cannot commit without completing sprint
- All sprints require postmortem before completion

## Project-Specific Instructions

Add your project-specific instructions below...
```

### 7. Add to .gitignore

Ensure state files are ignored:

```bash
# Add to .gitignore if not already present
grep -q ".claude/sprint-.*-state.json" "$TARGET_PATH/.gitignore" 2>/dev/null || \
  echo -e "\n# Sprint workflow state files\n.claude/sprint-*-state.json\n.claude/product-state.json" >> "$TARGET_PATH/.gitignore"
```

### 8. Report Success

```
Project workflow initialized at: $TARGET_PATH

Created:
├── .claude/
│   ├── commands/          (XX workflow commands)
│   ├── hooks/             (enforcement hooks)
│   ├── settings.json      (workflow configuration)
│   └── sprint-steps.json  (workflow definition)
├── docs/sprints/
│   ├── 1-todo/
│   ├── 2-in-progress/
│   ├── 3-done/_standalone/
│   └── 5-aborted/
├── CLAUDE.md              (project instructions)
└── next-sprint.txt        (sprint counter: 1)

Next steps:
1. Review and customize CLAUDE.md
2. Create your first sprint: /sprint-new "Initial Setup"
3. Start working: /sprint-start 1

To sync updates from master later: /project-update
```
