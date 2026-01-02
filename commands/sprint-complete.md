---
description: "Complete a sprint with full automation"
allowed-tools: [Bash]
---

# Complete Sprint

Run the complete-sprint automation command:

```bash
python3 scripts/sprint_lifecycle.py complete-sprint $ARGUMENTS
```

This command handles all completion steps:
- Verifies postmortem exists
- Calculates hours worked
- Updates YAML frontmatter
- Moves file with --done suffix
- Updates registry
- Commits changes
- Creates and pushes git tag
- Checks epic completion
- Updates state file

**Prerequisites:**
- Sprint must have a postmortem section (run `/sprint-postmortem $ARGUMENTS` first if missing)
- All work should be committed before completion
