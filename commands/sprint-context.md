---
description: "Generate a context brief for an upcoming sprint"
allowed-tools: [Bash, Read]
---

# Generate Sprint Context Brief

Generates a structured context document that summarizes prior sprint work, project state, and key decisions. The brief is designed to be fed into a sprint prompt so Claude has full project awareness before starting implementation.

## Instructions

### 1. Generate the Context Brief

Run the context builder:

```bash
python3 ~/.claude/scripts/sprint_lifecycle.py build-context $ARGUMENTS
```

If the legacy script doesn't support `build-context`, use the modular package:

```bash
cd <project_root> && python3 -m sprint_automation build-context $ARGUMENTS
```

### 2. Read and Present the Brief

After generation, read the output file:

```bash
# Default output location
cat .claude/sprint-<N>-context.md
```

Present a summary to the user:
- How many sprints were included at each tier
- Approximate token count
- Any sprints that couldn't be read (missing files)

### 3. Optional: Inject into Sprint Start

The generated brief can be automatically prepended to sprint prompts by reading it at the start of `/sprint-start`. This is opt-in — the brief exists as a standalone file that can also be used manually.

## Arguments

- `<sprint_num>` — The sprint number to generate context for (required)
- `--token-budget <N>` — Max approximate tokens (default: 8000)
- `--output <path>` — Custom output path

## Examples

```bash
# Generate context for Sprint 21
/sprint-context 21

# With custom token budget
/sprint-context 21 --token-budget 12000

# Custom output location
/sprint-context 21 --output ./context-brief.md
```

## Compression Tiers

The brief uses tiered compression to fit within the token budget:

| Tier | Criteria | Detail Level |
|------|----------|-------------|
| 1 (Full) | Same epic or most recent sprint | Goal, requirements, full postmortem |
| 2 (Summary) | Recent sprints (within last 5) | Goal and key metrics only |
| 3 (One-liner) | Old or unrelated sprints | Sprint title and status |

Sprints are automatically demoted to lower tiers if the token budget is exceeded.
