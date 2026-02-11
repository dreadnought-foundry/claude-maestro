#!/bin/bash
# Mac Disk Cleanup Script - Interactive, show-first approach
# Scans for space hogs, shows sizes, asks before deleting anything.
# Usage: bash ~/.claude/scripts/disk_cleanup.sh

# Don't use set -e — we want to continue past permission errors
set -uo pipefail

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
CYAN=$'\033[0;36m'
BOLD=$'\033[1m'
DIM=$'\033[2m'
NC=$'\033[0m'

freed_total=0

header() {
    printf "\n"
    printf "%s\n" "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    printf "%s\n" "${BOLD}${CYAN}  $1${NC}"
    printf "%s\n" "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
}

section() {
    printf "\n"
    printf "%s\n" "${BOLD}${YELLOW}── $1 ──${NC}"
}

info() {
    printf "  %s\n" "$1"
}

get_size() {
    local path="$1"
    if [ -e "$path" ]; then
        du -sh "$path" 2>/dev/null | awk '{print $1}'
    else
        printf "0B"
    fi
}

get_size_bytes() {
    local path="$1"
    if [ -e "$path" ]; then
        du -sk "$path" 2>/dev/null | awk '{print $1}'
    else
        printf "0"
    fi
}

confirm() {
    local msg="$1"
    printf "\n"
    printf "  %s %s %s " "${BOLD}${GREEN}Clean this up?${NC}" "$msg" "${BOLD}[y/N]:${NC}"
    read -r answer
    [[ "$answer" =~ ^[Yy]$ ]]
}

track_freed() {
    local before=$1
    local path="$2"
    local after
    if [ -e "$path" ]; then
        after=$(get_size_bytes "$path")
    else
        after=0
    fi
    local diff=$(( before - after ))
    if [ $diff -gt 0 ]; then
        freed_total=$(( freed_total + diff ))
        local mb=$(( diff / 1024 ))
        printf "  %s\n" "${GREEN}Freed ~${mb}MB${NC}"
    fi
}

safe_clear_cache() {
    local name="$1"
    local path="$2"
    if [ -d "$path" ] && [ "$(ls -A "$path" 2>/dev/null)" ]; then
        local size
        size=$(get_size "$path")
        printf "  %-45s %s\n" "${name}" "${BOLD}${size}${NC}"
        return 0
    fi
    return 1
}

# ============================================================
header "Mac Disk Cleanup"
# ============================================================

printf "\n"
printf "  Current disk usage:\n"
df -h / | tail -1 | awk '{printf "  Total: %s  |  Used: %s  |  Free: %s  |  Capacity: %s\n", $2, $3, $4, $5}'
printf "\n"

# ============================================================
header "Phase 1: Docker"
# ============================================================

section "Docker Desktop disk image"
DOCKER_DATA="$HOME/Library/Containers/com.docker.docker/Data"
if [ -d "$DOCKER_DATA" ]; then
    printf "  Docker data:  %s\n" "$(get_size "$DOCKER_DATA")"
else
    info "Docker Desktop data directory not found"
fi

section "Docker images, containers, volumes, build cache"
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    printf "  %s\n" "${BOLD}Images:${NC}"
    docker images --format "    {{.Repository}}:{{.Tag}}\t{{.Size}}\t(created {{.CreatedSince}})" 2>/dev/null | head -20
    printf "\n"

    DANGLING=$(docker images -f "dangling=true" -q 2>/dev/null | wc -l | tr -d ' ')
    printf "  Dangling images: %s\n" "${BOLD}$DANGLING${NC}"

    STOPPED=$(docker ps -a --filter "status=exited" -q 2>/dev/null | wc -l | tr -d ' ')
    printf "  Stopped containers: %s\n" "${BOLD}$STOPPED${NC}"

    printf "\n"
    printf "  %s\n" "${BOLD}Docker disk usage summary:${NC}"
    docker system df 2>/dev/null | while IFS= read -r line; do printf "    %s\n" "$line"; done

    if confirm "Run 'docker system prune -a --volumes' (removes ALL unused images, containers, volumes, build cache)"; then
        printf "  Pruning Docker...\n"
        docker system prune -a --volumes -f 2>/dev/null
        printf "  %s\n" "${GREEN}Docker pruned.${NC}"
    fi
else
    info "Docker not running or not installed — skipping"
fi

# ============================================================
header "Phase 2: Xcode & Developer Tools"
# ============================================================

section "Xcode Derived Data"
XCODE_DD="$HOME/Library/Developer/Xcode/DerivedData"
if [ -d "$XCODE_DD" ]; then
    SIZE=$(get_size "$XCODE_DD")
    info "Size: ${BOLD}$SIZE${NC}"
    ls -1 "$XCODE_DD" 2>/dev/null | head -10 | while read -r d; do
        if [ -d "$XCODE_DD/$d" ]; then
            printf "    %s  %s\n" "$(du -sh "$XCODE_DD/$d" 2>/dev/null | awk '{print $1}')" "$d"
        fi
    done
    if confirm "Delete all Xcode derived data ($SIZE)"; then
        BEFORE=$(get_size_bytes "$XCODE_DD")
        rm -rf "${XCODE_DD:?}"/*
        track_freed "$BEFORE" "$XCODE_DD"
    fi
else
    info "Not found — skipping"
fi

section "Xcode Archives"
XCODE_ARCHIVES="$HOME/Library/Developer/Xcode/Archives"
if [ -d "$XCODE_ARCHIVES" ] && [ "$(ls -A "$XCODE_ARCHIVES" 2>/dev/null)" ]; then
    SIZE=$(get_size "$XCODE_ARCHIVES")
    info "Size: ${BOLD}$SIZE${NC}"
    if confirm "Delete Xcode archives ($SIZE)"; then
        BEFORE=$(get_size_bytes "$XCODE_ARCHIVES")
        rm -rf "${XCODE_ARCHIVES:?}"/*
        track_freed "$BEFORE" "$XCODE_ARCHIVES"
    fi
else
    info "Empty or not found — skipping"
fi

section "iOS Device Support"
IOS_SUPPORT="$HOME/Library/Developer/Xcode/iOS DeviceSupport"
if [ -d "$IOS_SUPPORT" ]; then
    SIZE=$(get_size "$IOS_SUPPORT")
    info "Size: ${BOLD}$SIZE${NC}"
    ls -1 "$IOS_SUPPORT" 2>/dev/null | while read -r d; do
        printf "    %s  %s\n" "$(du -sh "$IOS_SUPPORT/$d" 2>/dev/null | awk '{print $1}')" "$d"
    done
    if confirm "Delete iOS device support files ($SIZE)"; then
        BEFORE=$(get_size_bytes "$IOS_SUPPORT")
        rm -rf "${IOS_SUPPORT:?}"/*
        track_freed "$BEFORE" "$IOS_SUPPORT"
    fi
else
    info "Not found — skipping"
fi

section "CoreSimulator"
CORE_SIM="$HOME/Library/Developer/CoreSimulator"
if [ -d "$CORE_SIM" ]; then
    SIZE=$(get_size "$CORE_SIM")
    info "Size: ${BOLD}$SIZE${NC}"
    if confirm "Delete unavailable simulators + caches ($SIZE)"; then
        BEFORE=$(get_size_bytes "$CORE_SIM")
        xcrun simctl delete unavailable 2>/dev/null || true
        rm -rf "$CORE_SIM/Caches"/* 2>/dev/null || true
        track_freed "$BEFORE" "$CORE_SIM"
    fi
else
    info "Not found — skipping"
fi

# ============================================================
header "Phase 3: Package Manager Caches"
# ============================================================

section "Homebrew"
BREW_CACHE=$(brew --cache 2>/dev/null || echo "$HOME/Library/Caches/Homebrew")
if [ -d "$BREW_CACHE" ]; then
    SIZE=$(get_size "$BREW_CACHE")
    info "Size: ${BOLD}$SIZE${NC}"
    if confirm "Run 'brew cleanup -s' ($SIZE)"; then
        BEFORE=$(get_size_bytes "$BREW_CACHE")
        brew cleanup -s 2>/dev/null || true
        track_freed "$BEFORE" "$BREW_CACHE"
    fi
else
    info "Not found — skipping"
fi

section "npm cache"
NPM_CACHE="$HOME/.npm"
if [ -d "$NPM_CACHE" ]; then
    SIZE=$(get_size "$NPM_CACHE")
    info "Size: ${BOLD}$SIZE${NC}"
    if confirm "Run 'npm cache clean --force' ($SIZE)"; then
        BEFORE=$(get_size_bytes "$NPM_CACHE")
        npm cache clean --force 2>/dev/null || true
        track_freed "$BEFORE" "$NPM_CACHE"
    fi
else
    info "Not found — skipping"
fi

section "pnpm store"
PNPM_STORE="$HOME/Library/pnpm/store"
if [ -d "$PNPM_STORE" ]; then
    SIZE=$(get_size "$PNPM_STORE")
    info "Size: ${BOLD}$SIZE${NC}"
    if confirm "Run 'pnpm store prune' ($SIZE)"; then
        BEFORE=$(get_size_bytes "$PNPM_STORE")
        pnpm store prune 2>/dev/null || true
        track_freed "$BEFORE" "$PNPM_STORE"
    fi
else
    info "Not found — skipping"
fi

section "pip cache"
PIP_CACHE="$HOME/Library/Caches/pip"
if [ -d "$PIP_CACHE" ]; then
    SIZE=$(get_size "$PIP_CACHE")
    info "Size: ${BOLD}$SIZE${NC}"
    if confirm "Run 'pip cache purge' ($SIZE)"; then
        BEFORE=$(get_size_bytes "$PIP_CACHE")
        pip cache purge 2>/dev/null || true
        track_freed "$BEFORE" "$PIP_CACHE"
    fi
else
    info "Not found — skipping"
fi

section "CocoaPods cache"
PODS_CACHE="$HOME/Library/Caches/CocoaPods"
if [ -d "$PODS_CACHE" ]; then
    SIZE=$(get_size "$PODS_CACHE")
    info "Size: ${BOLD}$SIZE${NC}"
    if confirm "Clear CocoaPods cache ($SIZE)"; then
        BEFORE=$(get_size_bytes "$PODS_CACHE")
        pod cache clean --all 2>/dev/null || rm -rf "${PODS_CACHE:?}"/* 2>/dev/null || true
        track_freed "$BEFORE" "$PODS_CACHE"
    fi
else
    info "Not found — skipping"
fi

section "Poetry cache"
POETRY_CACHE="$HOME/Library/Caches/pypoetry"
if [ -d "$POETRY_CACHE" ]; then
    SIZE=$(get_size "$POETRY_CACHE")
    info "Size: ${BOLD}$SIZE${NC}"
    if confirm "Clear Poetry cache ($SIZE)"; then
        BEFORE=$(get_size_bytes "$POETRY_CACHE")
        rm -rf "${POETRY_CACHE:?}"/* 2>/dev/null || true
        track_freed "$BEFORE" "$POETRY_CACHE"
    fi
else
    info "Not found — skipping"
fi

# ============================================================
header "Phase 4: App Caches (safe to clear)"
# ============================================================

info "${DIM}These are app caches that rebuild automatically.${NC}"
printf "\n"

# Build list of clearable caches
CACHE_TARGETS=(
    "Google (Chrome)|Google"
    "Docker|com.docker.docker"
    "Spotify|com.spotify.client"
    "ChatGPT Desktop|com.openai.atlas"
    "ChatGPT Web|com.openai.chat"
    "VS Code Updater|com.microsoft.VSCode.ShipIt"
    "Claude Desktop Updater|com.anthropic.claudefordesktop.ShipIt"
    "Cypress|Cypress"
    "Raspberry Pi Imager|Raspberry Pi"
    "Go build|go-build"
    "node-gyp|node-gyp"
    "Apple Python|com.apple.python"
    "SiriTTS|SiriTTS"
)

CACHE_BASE="$HOME/Library/Caches"
has_caches=false
for entry in "${CACHE_TARGETS[@]}"; do
    IFS='|' read -r label dirname <<< "$entry"
    if [ -d "$CACHE_BASE/$dirname" ] && [ "$(ls -A "$CACHE_BASE/$dirname" 2>/dev/null)" ]; then
        safe_clear_cache "$label" "$CACHE_BASE/$dirname" && has_caches=true
    fi
done

if $has_caches; then
    if confirm "Clear ALL listed app caches above"; then
        for entry in "${CACHE_TARGETS[@]}"; do
            IFS='|' read -r label dirname <<< "$entry"
            if [ -d "$CACHE_BASE/$dirname" ] && [ "$(ls -A "$CACHE_BASE/$dirname" 2>/dev/null)" ]; then
                BEFORE=$(get_size_bytes "$CACHE_BASE/$dirname")
                rm -rf "${CACHE_BASE:?}/${dirname:?}"/* 2>/dev/null || true
                track_freed "$BEFORE" "$CACHE_BASE/$dirname"
            fi
        done
    fi
else
    info "No significant app caches found"
fi

# ============================================================
header "Phase 5: Large Application Support Directories"
# ============================================================

info "${DIM}These contain app data — review before clearing.${NC}"
printf "\n"

APP_SUPPORT="$HOME/Library/Application Support"
find "$APP_SUPPORT" -maxdepth 1 -type d -exec du -sk {} \; 2>/dev/null | \
    sort -rn | head -12 | while IFS=$'\t' read -r size path; do
    if [ "$path" != "$APP_SUPPORT" ]; then
        human_size=$(du -sh "$path" 2>/dev/null | awk '{print $1}')
        name=$(basename "$path")
        printf "  %-45s %s\n" "$name" "${BOLD}${human_size}${NC}"
    fi
done

printf "\n"
info "${DIM}To clear a specific item: rm -rf \"~/Library/Application Support/<name>\"${NC}"

# ============================================================
header "Phase 6: System Logs"
# ============================================================

SYS_LOGS="$HOME/Library/Logs"
if [ -d "$SYS_LOGS" ]; then
    SIZE=$(get_size "$SYS_LOGS")
    info "Size: ${BOLD}$SIZE${NC}"
    if confirm "Clear log files older than 7 days ($SIZE total, only old files removed)"; then
        BEFORE=$(get_size_bytes "$SYS_LOGS")
        find "$SYS_LOGS" -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true
        find "$SYS_LOGS" -type f -name "*.gz" -delete 2>/dev/null || true
        track_freed "$BEFORE" "$SYS_LOGS"
    fi
else
    info "Not found — skipping"
fi

# ============================================================
header "Phase 7: node_modules"
# ============================================================

info "Scanning for node_modules..."
printf "\n"

DEV_ROOT="/Volumes/Foundry/Development"
if [ -d "$DEV_ROOT" ]; then
    find "$DEV_ROOT" -name "node_modules" -type d -maxdepth 6 -prune 2>/dev/null | while read -r nm; do
        size=$(du -sh "$nm" 2>/dev/null | awk '{print $1}')
        printf "  %-8s %s\n" "$size" "$nm"
    done | sort -hr | head -15
else
    info "Development directory not found at $DEV_ROOT"
fi

printf "\n"
printf "  %s\n" "${DIM}To remove: rm -rf <path>  (restored with pnpm/npm install)${NC}"

# ============================================================
header "Phase 8: Trash"
# ============================================================

TRASH="$HOME/.Trash"
if [ -d "$TRASH" ] && [ "$(ls -A "$TRASH" 2>/dev/null)" ]; then
    SIZE=$(get_size "$TRASH")
    info "Trash size: ${BOLD}$SIZE${NC}"
    if confirm "Empty Trash ($SIZE)"; then
        BEFORE=$(get_size_bytes "$TRASH")
        rm -rf "${TRASH:?}"/* 2>/dev/null || true
        track_freed "$BEFORE" "$TRASH"
    fi
else
    info "Trash is empty"
fi

# ============================================================
header "Summary"
# ============================================================

printf "\n"
if [ $freed_total -gt 0 ]; then
    freed_mb=$(( freed_total / 1024 ))
    if [ $freed_mb -gt 1024 ]; then
        freed_gb=$(echo "scale=1; $freed_mb / 1024" | bc 2>/dev/null || echo "$((freed_mb / 1024))")
        printf "  %s\n" "${BOLD}${GREEN}Total freed: ~${freed_gb}GB${NC}"
    else
        printf "  %s\n" "${BOLD}${GREEN}Total freed: ~${freed_mb}MB${NC}"
    fi
else
    printf "  %s\n" "${YELLOW}No cleanup actions taken — scan only.${NC}"
fi
printf "\n"
printf "  Disk usage now:\n"
df -h / | tail -1 | awk '{printf "  Total: %s  |  Used: %s  |  Free: %s  |  Capacity: %s\n", $2, $3, $4, $5}'
printf "\n"
