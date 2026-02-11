---
description: "Scan Mac for disk space hogs and interactively clean up caches, Docker, Xcode, and more"
allowed-tools: [Bash, Read, Glob]
---

# Disk Cleanup $ARGUMENTS

Scan the Mac for disk space hogs and help the user reclaim space. Shows everything first, asks before deleting.

## Instructions

### Quick Mode (default)

If no arguments or `$ARGUMENTS` is empty, run the interactive cleanup script:

```bash
bash ~/.claude/scripts/disk_cleanup.sh
```

This walks through 8 phases interactively:
1. Docker (images, containers, volumes, build cache)
2. Xcode (DerivedData, archives, iOS device support, simulators)
3. Package managers (Homebrew, npm, pnpm, pip, CocoaPods, Poetry)
4. App caches (Chrome, Spotify, ChatGPT, VS Code, Claude, etc.)
5. Application Support (shows large items for review)
6. System logs (clears old logs >7 days)
7. node_modules (lists large ones)
8. Trash

### Scan Mode

If `$ARGUMENTS` contains "scan" or "report", do a read-only scan without prompts:

1. Show current disk usage with `df -h /`
2. List the top space consumers:

```bash
# Top 15 ~/Library/Caches items
du -sh ~/Library/Caches/* 2>/dev/null | sort -hr | head -15

# Top 10 ~/Library/Application Support items
find ~/Library/Application\ Support -maxdepth 1 -type d -exec du -sh {} \; 2>/dev/null | sort -hr | head -12

# Top 10 ~/Library/Developer items
du -sh ~/Library/Developer/* 2>/dev/null | sort -hr | head -10

# Docker disk usage
docker system df 2>/dev/null

# node_modules
find /Volumes/Foundry/Development -name node_modules -type d -maxdepth 6 -prune -exec du -sh {} \; 2>/dev/null | sort -hr | head -10

# Trash
du -sh ~/.Trash 2>/dev/null
```

3. Present a summary table with recommendations (safe to clear vs review first)

### Targeted Mode

If `$ARGUMENTS` contains a specific target, only clean that:

| Argument | Action |
|----------|--------|
| `docker` | Docker system prune |
| `xcode` | DerivedData + archives + device support |
| `brew` | Homebrew cleanup |
| `npm` | npm + pnpm cache clean |
| `pip` | pip + poetry cache purge |
| `caches` | All ~/Library/Caches app caches |
| `trash` | Empty trash |
| `node_modules` | List and optionally remove node_modules |

For targeted mode, show the current size, confirm with user, then clean.

### Safety Rules

- **Always show sizes before deleting**
- **Always confirm before destructive actions**
- **Never delete Application Support items without explicit user approval** — these contain app data, not just caches
- **Never delete ~/Library/Caches/com.apple.*` items** — macOS system caches
- **Use `rm -rf "${path:?}"/*` pattern** — the `:?` prevents accidental deletion if variable is empty
