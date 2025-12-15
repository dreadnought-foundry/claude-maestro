---
description: "Initialize a new project with the sprint workflow system"
allowed-tools: [Read, Write, Bash, Glob]
---

# Create Project Workflow

Initialize a new project with the complete sprint workflow system from the master template.

## What Gets Copied

| Component | Source | Destination |
|-----------|--------|-------------|
| Slash Commands | `~/.claude/commands/` | (uses global) |
| Global Agents | `~/.claude/agents/` | `.claude/agents/` |
| Project Agents | `~/.claude/templates/project/.claude/agents/` | `.claude/agents/` |
| Global Hooks | `~/.claude/hooks/` | `.claude/hooks/` |
| Project Hooks | `~/.claude/templates/project/.claude/hooks/` | `.claude/hooks/` |
| Workflow Config | `~/.claude/templates/project/.claude/` | `.claude/` |
| CLAUDE.md | `~/.claude/templates/project/CLAUDE.md` | `./CLAUDE.md` |
| Sprint Dirs | `~/.claude/templates/project/docs/sprints/` | `./docs/sprints/` |

## Instructions

### 1. Determine Target Project

Parse $ARGUMENTS:
- If empty, use current working directory
- If a path is provided, use that path

```bash
TARGET_PATH="${ARGUMENTS:-$(pwd)}"
echo "Target: $TARGET_PATH"
```

### 2. Validate Target

```bash
# Check path exists
if [ ! -d "$TARGET_PATH" ]; then
  echo "ERROR: Directory not found: $TARGET_PATH"
  exit 1
fi

# Check if already initialized
if [ -d "$TARGET_PATH/.claude/sprint-steps.json" ]; then
  echo "WARNING: Project already initialized. Use /project-update to sync changes."
  exit 1
fi
```

### 3. Create Directory Structure

```bash
mkdir -p "$TARGET_PATH/.claude/agents"
mkdir -p "$TARGET_PATH/.claude/hooks"
mkdir -p "$TARGET_PATH/docs/sprints/1-todo"
mkdir -p "$TARGET_PATH/docs/sprints/2-in-progress"
mkdir -p "$TARGET_PATH/docs/sprints/3-done/_standalone"
mkdir -p "$TARGET_PATH/docs/sprints/5-aborted"
```

### 4. Copy Agents

```bash
# Copy global agents
cp ~/.claude/agents/*.md "$TARGET_PATH/.claude/agents/" 2>/dev/null || true

# Copy project agents from template
cp ~/.claude/templates/project/.claude/agents/*.md "$TARGET_PATH/.claude/agents/" 2>/dev/null || true

echo "Copied agents:"
ls "$TARGET_PATH/.claude/agents/"
```

### 5. Copy Hooks

```bash
# Copy global hooks
cp ~/.claude/hooks/*.py "$TARGET_PATH/.claude/hooks/" 2>/dev/null || true

# Copy project hooks from template
cp ~/.claude/templates/project/.claude/hooks/*.py "$TARGET_PATH/.claude/hooks/" 2>/dev/null || true

echo "Copied hooks:"
ls "$TARGET_PATH/.claude/hooks/"
```

### 6. Copy Configuration

```bash
# Copy sprint-steps.json
cp ~/.claude/templates/project/.claude/sprint-steps.json "$TARGET_PATH/.claude/"

# Copy settings.json
cp ~/.claude/templates/project/.claude/settings.json "$TARGET_PATH/.claude/"

# Copy workflow version
cp ~/.claude/WORKFLOW_VERSION "$TARGET_PATH/.claude/" 2>/dev/null || true
```

### 7. Copy CLAUDE.md

```bash
# Copy CLAUDE.md template (don't overwrite if exists)
if [ ! -f "$TARGET_PATH/CLAUDE.md" ]; then
  cp ~/.claude/templates/project/CLAUDE.md "$TARGET_PATH/CLAUDE.md"
  echo "Created CLAUDE.md"
else
  echo "CLAUDE.md already exists, skipping"
fi
```

### 8. Initialize Sprint Counter

```bash
# Create sprint counter if it doesn't exist
if [ ! -f "$TARGET_PATH/docs/sprints/next-sprint.txt" ]; then
  echo "1" > "$TARGET_PATH/docs/sprints/next-sprint.txt"
  echo "Created sprint counter (starting at 1)"
fi
```

### 9. Update .gitignore

```bash
# Add workflow state files to .gitignore
if [ -f "$TARGET_PATH/.gitignore" ]; then
  if ! grep -q "sprint-.*-state.json" "$TARGET_PATH/.gitignore"; then
    echo "" >> "$TARGET_PATH/.gitignore"
    echo "# Sprint workflow state files" >> "$TARGET_PATH/.gitignore"
    echo ".claude/sprint-*-state.json" >> "$TARGET_PATH/.gitignore"
    echo ".claude/product-state.json" >> "$TARGET_PATH/.gitignore"
  fi
else
  cat > "$TARGET_PATH/.gitignore" << 'GITIGNORE'
# Sprint workflow state files
.claude/sprint-*-state.json
.claude/product-state.json
GITIGNORE
fi
```

### 10. Report Success

```
✅ Project workflow initialized at: $TARGET_PATH

Created structure:
├── .claude/
│   ├── agents/           (X agents)
│   ├── hooks/            (X hooks)
│   ├── settings.json
│   ├── sprint-steps.json
│   └── WORKFLOW_VERSION
├── docs/sprints/
│   ├── 1-todo/
│   ├── 2-in-progress/
│   ├── 3-done/_standalone/
│   ├── 5-aborted/
│   └── next-sprint.txt   (counter: 1)
└── CLAUDE.md

Next steps:
1. Review and customize CLAUDE.md for your project
2. Create your first sprint: /sprint-new "Initial Setup"
3. Start working: /sprint-start 1

To sync future updates: /project-update
Workflow version: $(cat ~/.claude/WORKFLOW_VERSION 2>/dev/null || echo "unknown")
```
