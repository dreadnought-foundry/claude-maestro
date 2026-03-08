# Recipe: VS Code Setup for AI-Assisted Development

**Category**: workflow
**Version**: 1.0
**Last Updated**: 2025-12-18
**Purpose**: Configure VS Code for parallel Claude Code sessions

## Overview

This recipe documents how to set up VS Code with multiple dedicated terminal sessions for AI-assisted development. The approach enables parallel Claude Code agents working on different aspects of a project simultaneously.

## Why Multiple Terminals?

### The Problem

When working on complex features, you often need:
- Multiple Claude agents working in parallel (backend, frontend, tests)
- A dedicated CI/CD terminal for running builds
- A testing terminal for validation
- A general-purpose shell for quick commands

Running everything in one terminal creates bottlenecks and context-switching overhead.

### The Solution

Configure VS Code to automatically spawn named, dedicated terminals on project open:

```
┌─────────────────────────────────────────────────────────────┐
│  VS Code Terminal Panel                                      │
├─────────────────────────────────────────────────────────────┤
│  📁 Dev 1      - Primary Claude agent (feature work)        │
│  📁 Dev 2      - Secondary Claude agent (parallel task)     │
│  📁 Dev 3      - Tertiary Claude agent (exploration)        │
│  📁 CI/CD      - Build, deploy, CI commands                 │
│  📁 Tester     - Claude agent focused on testing            │
│  📁 Assistant  - Claude agent for questions/research        │
│  📁 Front-end  - Frontend-specific work (web-app)           │
│  📁 Back-end   - Backend-specific work                      │
│  📁 zsh        - General purpose shell                      │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Prerequisites

- [ ] VS Code installed
- [ ] Claude Code CLI installed (`claude` command available)
- [ ] Project has `.vscode` directory

### Step 1: Enable Automatic Tasks

Add to `.vscode/settings.json`:

```json
{
    "task.allowAutomaticTasks": "on"
}
```

This allows tasks to run automatically when the folder opens.

### Step 2: Create Tasks Configuration

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Dev 1",
      "type": "shell",
      "command": "claude --dangerously-skip-permissions",
      "isBackground": true,
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      },
      "runOptions": { "runOn": "folderOpen" }
    },
    {
      "label": "Dev 2",
      "type": "shell",
      "command": "claude --dangerously-skip-permissions",
      "isBackground": true,
      "presentation": {
        "panel": "dedicated"
      },
      "runOptions": { "runOn": "folderOpen" }
    },
    {
      "label": "Dev 3",
      "type": "shell",
      "command": "claude --dangerously-skip-permissions",
      "isBackground": true,
      "presentation": {
        "panel": "dedicated"
      },
      "runOptions": { "runOn": "folderOpen" }
    },
    {
      "label": "CI/CD",
      "type": "shell",
      "command": "echo 'CI/CD terminal ready'",
      "isBackground": true,
      "presentation": {
        "panel": "dedicated"
      },
      "runOptions": { "runOn": "folderOpen" }
    },
    {
      "label": "Tester",
      "type": "shell",
      "command": "claude --dangerously-skip-permissions",
      "isBackground": true,
      "presentation": {
        "panel": "dedicated"
      },
      "runOptions": { "runOn": "folderOpen" }
    },
    {
      "label": "Assistant",
      "type": "shell",
      "command": "claude --dangerously-skip-permissions",
      "isBackground": true,
      "presentation": {
        "panel": "dedicated"
      },
      "runOptions": { "runOn": "folderOpen" }
    },
    {
      "label": "Front-end",
      "detail": "web-app",
      "type": "shell",
      "command": "echo 'Front-end ready'",
      "isBackground": true,
      "presentation": {
        "panel": "dedicated"
      },
      "runOptions": { "runOn": "folderOpen" }
    },
    {
      "label": "Back-end",
      "type": "shell",
      "command": "echo 'Back-end ready'",
      "isBackground": true,
      "presentation": {
        "panel": "dedicated"
      },
      "runOptions": { "runOn": "folderOpen" }
    },
    {
      "label": "zsh",
      "type": "shell",
      "command": "zsh",
      "isBackground": true,
      "presentation": {
        "panel": "dedicated"
      },
      "runOptions": { "runOn": "folderOpen" }
    }
  ]
}
```

### Step 3: Reload VS Code

Press `Cmd+Shift+P` > "Developer: Reload Window" to apply changes.

## Key Configuration Options

### Task Properties

| Property | Purpose | Example |
|----------|---------|---------|
| `label` | Terminal name in sidebar | `"Dev 1"` |
| `detail` | Subtitle shown under label | `"web-app"` |
| `command` | What runs in the terminal | `"claude --dangerously-skip-permissions"` |
| `isBackground` | Keep terminal alive | `true` |
| `runOptions.runOn` | Auto-start trigger | `"folderOpen"` |

### Presentation Options

| Property | Purpose | Value |
|----------|---------|-------|
| `panel` | Terminal isolation | `"dedicated"` (separate) or `"shared"` |
| `reveal` | Show on start | `"always"`, `"silent"`, `"never"` |
| `group` | Group terminals together | **AVOID** - causes linking |

### Anti-Pattern: Grouped Terminals

**Don't do this:**

```json
{
  "presentation": {
    "panel": "dedicated",
    "group": "claude"  // ❌ Links terminals together
  }
}
```

The `group` property causes terminals to be linked in the sidebar, making them harder to manage individually. Always omit `group` for independent terminals.

## Usage Patterns

### Parallel Sprint Work

```
Dev 1:  /sprint-start 172    → Planning phase
Dev 2:  (waiting)
Dev 3:  (waiting)

[After planning]

Dev 1:  Backend implementation
Dev 2:  Frontend implementation
Dev 3:  Test writing
Tester: Continuous test runs
```

### Feature + Bug Fix

```
Dev 1:  Working on Sprint 172 (new feature)
Dev 2:  Hot fix for production bug
Dev 3:  Code review assistance
```

### Research + Implementation

```
Dev 1:      Implementation work
Assistant:  "How does the auth flow work?"
Tester:     Running test suite
```

## Customization

### Minimal Setup (3 terminals)

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Claude",
      "type": "shell",
      "command": "claude --dangerously-skip-permissions",
      "isBackground": true,
      "presentation": { "reveal": "always", "panel": "dedicated" },
      "runOptions": { "runOn": "folderOpen" }
    },
    {
      "label": "Tests",
      "type": "shell",
      "command": "echo 'Test terminal ready'",
      "isBackground": true,
      "presentation": { "panel": "dedicated" },
      "runOptions": { "runOn": "folderOpen" }
    },
    {
      "label": "Shell",
      "type": "shell",
      "command": "zsh",
      "isBackground": true,
      "presentation": { "panel": "dedicated" },
      "runOptions": { "runOn": "folderOpen" }
    }
  ]
}
```

### With Auto-Start Commands

```json
{
  "label": "API Server",
  "type": "shell",
  "command": "PYTHONPATH=src uvicorn corrdata.api.app:app --reload",
  "isBackground": true,
  "presentation": { "panel": "dedicated" },
  "runOptions": { "runOn": "folderOpen" }
}
```

### With Working Directory

```json
{
  "label": "Front-end",
  "type": "shell",
  "command": "pnpm dev",
  "options": {
    "cwd": "${workspaceFolder}/packages/web-app"
  },
  "isBackground": true,
  "presentation": { "panel": "dedicated" },
  "runOptions": { "runOn": "folderOpen" }
}
```

## Troubleshooting

### Terminals Not Starting

1. Check `task.allowAutomaticTasks` is `"on"` in settings
2. Reload VS Code window
3. Verify tasks.json syntax is valid JSON

### Terminals Grouped Together

Remove any `"group"` properties from presentation settings.

### Wrong Shell

Specify shell explicitly:

```json
{
  "command": "/bin/zsh -l -c 'claude --dangerously-skip-permissions'"
}
```

### Permission Issues

If Claude needs permissions, either:
1. Use `--dangerously-skip-permissions` (development only)
2. Pre-configure permissions in `~/.claude/settings.json`

## Security Considerations

The `--dangerously-skip-permissions` flag should only be used in development environments where you trust the codebase. For shared or production environments, configure explicit permissions instead.

## Related Recipes

- [Development Infrastructure](./development-infrastructure.md) - Overall AI development setup
- [Sprint Workflow v2.0](./sprint-workflow-v2.md) - How to use multiple agents in sprints

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-18 | Initial version with 9-terminal setup |
