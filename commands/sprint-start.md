---
description: "Start a sprint - move to in-progress, create state file"
allowed-tools: [Bash]
---

# Start Sprint

Run the start-sprint automation command:

```bash
python3 scripts/sprint_lifecycle.py start-sprint $ARGUMENTS
```

This command handles all startup steps:
- Finds sprint file in backlog/todo
- Validates sprint is not in unstarted epic (blocks if needed)
- Moves file to 2-in-progress/ (preserving epic structure if applicable)
- Updates YAML frontmatter (status, started timestamp)
- Creates sprint state file with workflow version 3.0
- Updates registry

**Prerequisites:**
- Sprint must be in 0-backlog/ or 1-todo/
- If sprint is in an epic, the epic must already be started (in 2-in-progress/)

**After starting:**
- Use `/sprint-status` to check current progress
- Use `/sprint-next` to advance through workflow steps
