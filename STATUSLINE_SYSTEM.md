# Claude Code Per-Terminal Status Line System

## Problem Solved
The original status line system showed the same ticket (ENGINE-103) across all terminals because it used shared global state. This caused confusion when running multiple agents or sessions simultaneously.

## Solution Overview
The new system implements **per-terminal/per-session ticket tracking** using Claude Code's unique session ID for each terminal instance.

## How It Works

### Status Line Script (`~/.claude/statusline-command.sh`)
- Extracts `session_id` from Claude Code's JSON input
- Maintains per-session ticket files in `~/.claude/session_tickets/`
- Falls back to git branch/commit analysis if no session-specific ticket exists
- **Removed** the hard-coded ENGINE-103 fallback

### Ticket Management Utility (`~/.claude/statusline-ticket`)
Command-line tool for managing tickets per session:

```bash
# Set ticket for current session
~/.claude/statusline-ticket set ENGINE-123

# Set ticket for specific session
~/.claude/statusline-ticket set ENGINE-456 session-abc123

# Get current session's ticket
~/.claude/statusline-ticket get

# List all active session tickets
~/.claude/statusline-ticket list

# Clear current session's ticket
~/.claude/statusline-ticket clear

# Cleanup old ticket files (7+ days)
~/.claude/statusline-ticket cleanup
```

## Per-Session Storage
- **Location**: `~/.claude/session_tickets/`
- **Format**: `{session_id}.ticket` files containing just the ticket number
- **Automatic cleanup**: Old files (7+ days) can be removed with `cleanup` command

## Fallback Behavior
If no session-specific ticket is set, the system falls back to:
1. Git branch name (if contains ENGINE-XXX pattern) - colored red
2. Recent git commit messages (last 5 commits) - colored cyan
3. No ticket displayed (instead of hard-coded ENGINE-103)

## Benefits
- ✅ **True per-terminal isolation** - each Claude Code session shows its own ticket
- ✅ **No cross-terminal interference** - multiple agents can work on different tickets
- ✅ **Persistent sessions** - tickets persist across terminal reopens
- ✅ **Easy management** - simple CLI for setting/getting/clearing tickets
- ✅ **Automatic fallbacks** - still works with git branch/commit patterns
- ✅ **Cleanup mechanism** - prevents accumulation of old session files

## Usage for Multi-Agent Workflows
1. Start Agent A: `statusline-ticket set ENGINE-123`
2. Start Agent B: `statusline-ticket set ENGINE-456`  
3. Each terminal now shows its respective ticket
4. No interference between agents

## Migration from Old System
- Old behavior: All terminals showed ENGINE-103 by default
- New behavior: Terminals show no ticket until explicitly set or detected from git
- Users can set specific tickets per terminal using the utility
- Git branch/commit detection still works as backup