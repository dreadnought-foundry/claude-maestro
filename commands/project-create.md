---
description: "Initialize a new project with the sprint workflow system"
allowed-tools: [Bash]
---

# Create Project Workflow

Run the create-project automation command:

```bash
python3 scripts/sprint_lifecycle.py create-project $ARGUMENTS
```

This command handles:
- Creating complete directory structure
- Copying commands/ and scripts/ from master project
- Copying agents (global + template)
- Copying hooks (global + template)
- Copying configuration files
- Creating sprint registry
- Updating .gitignore

**Usage:**
```
/project-create [target-path]
```

**Examples:**
```
/project-create                    # Initialize current directory
/project-create /path/to/project   # Initialize specific directory
/project-create --dry-run          # Preview changes
```

**What Gets Copied:**

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
| Sprint Dirs | Created automatically | `./docs/sprints/` |

**Prerequisites:**
- Master project must exist at `~/Development/Dreadnought/claude-maestro`
- Template files must exist at `~/.claude/templates/project/`
- Target directory must exist

**Next Steps After Creation:**
1. Review and customize CLAUDE.md for your project
2. Create your first sprint: `/sprint-new "Initial Setup"`
3. Start working: `/sprint-start 1`
