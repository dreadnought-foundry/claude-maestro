---
description: "Initialize a new project with the sprint workflow system"
allowed-tools: [Read, Write, Bash, Glob]
---

# Create Project Workflow

Initialize a new project with the complete sprint workflow system from the master template.

## What Gets Copied

| Component | Source | Destination |
|-----------|--------|-------------|
| Commands | `~/Development/Dreadnought/claude-maestro/commands/` | `./commands/` |
| Scripts | `~/Development/Dreadnought/claude-maestro/scripts/` | `./scripts/` |
| Global Agents | `~/.claude/agents/` | `.claude/agents/` |
| Project Agents | `~/.claude/templates/project/.claude/agents/` | `.claude/agents/` |
| Global Hooks | `~/.claude/hooks/` | `.claude/hooks/` |
| Project Hooks | `~/.claude/templates/project/.claude/hooks/` | `.claude/hooks/` |
| Workflow Config | `~/.claude/templates/project/.claude/` | `.claude/` |
| CLAUDE.md | `~/.claude/templates/project/CLAUDE.md` | `./CLAUDE.md` |
| Sprint Dirs | `~/.claude/templates/project/docs/sprints/` | `./docs/sprints/` |

**Note:** Commands and scripts are copied from the master project (claude-maestro).

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
mkdir -p "$TARGET_PATH/commands"
mkdir -p "$TARGET_PATH/scripts"
mkdir -p "$TARGET_PATH/docs/sprints/0-backlog"
mkdir -p "$TARGET_PATH/docs/sprints/1-todo"
mkdir -p "$TARGET_PATH/docs/sprints/2-in-progress"
mkdir -p "$TARGET_PATH/docs/sprints/3-done"
mkdir -p "$TARGET_PATH/docs/sprints/4-blocked"
mkdir -p "$TARGET_PATH/docs/sprints/5-aborted"
mkdir -p "$TARGET_PATH/docs/sprints/6-archived"
```

### 4. Copy Commands and Scripts

```bash
# Define master project path
MASTER_PROJECT="$HOME/Development/Dreadnought/claude-maestro"

# Copy commands
if [ -d "$MASTER_PROJECT/commands" ]; then
  cp -r "$MASTER_PROJECT/commands"/*.md "$TARGET_PATH/commands/" 2>/dev/null || true
  echo "Copied $(ls -1 "$TARGET_PATH/commands"/*.md 2>/dev/null | wc -l) command files"
else
  echo "WARNING: Master project not found at $MASTER_PROJECT"
fi

# Copy scripts
if [ -d "$MASTER_PROJECT/scripts" ]; then
  cp -r "$MASTER_PROJECT/scripts"/* "$TARGET_PATH/scripts/" 2>/dev/null || true
  echo "Copied automation scripts"
  chmod +x "$TARGET_PATH/scripts"/*.py 2>/dev/null || true
else
  echo "WARNING: Master project scripts not found"
fi
```

### 5. Copy Agents

```bash
# Copy global agents
cp ~/.claude/agents/*.md "$TARGET_PATH/.claude/agents/" 2>/dev/null || true

# Copy project agents from template
cp ~/.claude/templates/project/.claude/agents/*.md "$TARGET_PATH/.claude/agents/" 2>/dev/null || true

echo "Copied agents:"
ls "$TARGET_PATH/.claude/agents/"
```

### 6. Copy Hooks

```bash
# Copy global hooks
cp ~/.claude/hooks/*.py "$TARGET_PATH/.claude/hooks/" 2>/dev/null || true

# Copy project hooks from template
cp ~/.claude/templates/project/.claude/hooks/*.py "$TARGET_PATH/.claude/hooks/" 2>/dev/null || true

echo "Copied hooks:"
ls "$TARGET_PATH/.claude/hooks/"
```

### 7. Copy Configuration

```bash
# Copy sprint-steps.json
cp ~/.claude/templates/project/.claude/sprint-steps.json "$TARGET_PATH/.claude/"

# Copy settings.json
cp ~/.claude/templates/project/.claude/settings.json "$TARGET_PATH/.claude/"

# Copy workflow version
cp ~/.claude/WORKFLOW_VERSION "$TARGET_PATH/.claude/" 2>/dev/null || true
```

### 8. Copy CLAUDE.md

```bash
# Copy CLAUDE.md template (don't overwrite if exists)
if [ ! -f "$TARGET_PATH/CLAUDE.md" ]; then
  cp ~/.claude/templates/project/CLAUDE.md "$TARGET_PATH/CLAUDE.md"
  echo "Created CLAUDE.md"
else
  echo "CLAUDE.md already exists, skipping"
fi
```

### 9. Create Sprint Registry

```bash
# Create registry file
cat > "$TARGET_PATH/docs/sprints/registry.json" << 'REGISTRY'
{
  "counters": {
    "next_sprint": 1,
    "next_epic": 1
  },
  "sprints": {},
  "epics": {}
}
REGISTRY
echo "Created sprint registry"
```

### 10. Update .gitignore

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

### 11. Report Success

```
✅ Project workflow initialized at: $TARGET_PATH

Created structure:
├── commands/             (X command files)
├── scripts/              (automation)
├── .claude/
│   ├── agents/           (X agents)
│   ├── hooks/            (X hooks)
│   ├── settings.json
│   ├── sprint-steps.json
│   └── WORKFLOW_VERSION
├── docs/sprints/
│   ├── 0-backlog/
│   ├── 1-todo/
│   ├── 2-in-progress/
│   ├── 3-done/
│   ├── 4-blocked/
│   ├── 5-aborted/
│   ├── 6-archived/
│   └── registry.json
└── CLAUDE.md

Next steps:
1. Review and customize CLAUDE.md for your project
2. Create your first sprint: /sprint-new "Initial Setup"
3. Start working: /sprint-start 1

To sync future updates: /project-update
Workflow version: $(cat ~/.claude/WORKFLOW_VERSION 2>/dev/null || echo "unknown")
```
