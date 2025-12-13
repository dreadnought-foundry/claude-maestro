#!/bin/bash

# Read JSON input from stdin
input=$(cat)

# Extract information from JSON
model_name=$(echo "$input" | jq -r '.model.display_name')
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')
output_style=$(echo "$input" | jq -r '.output_style.name')

# Use full directory path
dir_name="$current_dir"

# Check if we're in a git repository and get branch info
if git -C "$current_dir" rev-parse --git-dir >/dev/null 2>&1; then
    git_branch=$(git -C "$current_dir" branch --show-current 2>/dev/null || echo "detached")
    git_info=" [git:$git_branch]"
else
    git_info=""
fi

# Check for sprint state
sprint_state_file="$current_dir/.claude/sprint-state.json"
if [[ -f "$sprint_state_file" ]]; then
    sprint_num=$(jq -r '.sprint_number // empty' "$sprint_state_file" 2>/dev/null)
    sprint_step=$(jq -r '.current_step // empty' "$sprint_state_file" 2>/dev/null)
    sprint_status=$(jq -r '.status // empty' "$sprint_state_file" 2>/dev/null)

    if [[ -n "$sprint_num" ]]; then
        # Create compact sprint info
        if [[ -n "$sprint_step" ]]; then
            sprint_info=" [Sprint $sprint_num:$sprint_step]"
        else
            sprint_info=" [Sprint $sprint_num]"
        fi
    else
        sprint_info=""
    fi
else
    sprint_info=""
fi

# Check bypass permission status from settings.local.json
settings_file="$HOME/.claude/settings.local.json"
if [[ -f "$settings_file" ]]; then
    bypass_status=$(jq -r '.permissions.defaultMode // "standard"' "$settings_file" 2>/dev/null)
    if [[ "$bypass_status" == "bypassPermissions" ]]; then
        bypass_info=" [bypass:ON]"
    else
        bypass_info=" [bypass:OFF]"
    fi
else
    bypass_info=" [bypass:unknown]"
fi

# Check MCP configuration status
# First check project-level .mcp.json (Claude Code)
project_mcp_config="$current_dir/.mcp.json"
desktop_mcp_config="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

if [[ -f "$project_mcp_config" ]]; then
    # Using Claude Code with project config
    if grep -q '"mcpServers": {}' "$project_mcp_config" 2>/dev/null; then
        mcp_info=" [mcp:OFF]"
    elif grep -q "CORRDATA_MCP_MODULES" "$project_mcp_config" 2>/dev/null; then
        # Extract modules list
        modules=$(grep -o '"CORRDATA_MCP_MODULES": *"[^"]*"' "$project_mcp_config" 2>/dev/null | sed 's/.*: *"//' | sed 's/"//')
        if [[ -n "$modules" ]]; then
            mcp_info=" [mcp:$modules]"
        else
            mcp_info=" [mcp:core]"
        fi
    elif grep -q '"corrdata"' "$project_mcp_config" 2>/dev/null; then
        # No CORRDATA_MCP_MODULES means default (now core)
        mcp_info=" [mcp:core]"
    else
        mcp_info=" [mcp:none]"
    fi
elif [[ -f "$desktop_mcp_config" ]]; then
    # Fallback to Claude Desktop config
    if grep -q '"mcpServers": {}' "$desktop_mcp_config" 2>/dev/null; then
        mcp_info=" [mcp:OFF]"
    elif grep -q "CORRDATA_MCP_MODULES" "$desktop_mcp_config" 2>/dev/null; then
        modules=$(grep -o '"CORRDATA_MCP_MODULES": *"[^"]*"' "$desktop_mcp_config" 2>/dev/null | sed 's/.*: *"//' | sed 's/"//')
        if [[ -n "$modules" ]]; then
            mcp_info=" [mcp:$modules]"
        else
            mcp_info=" [mcp:core]"
        fi
    elif grep -q '"corrdata"' "$desktop_mcp_config" 2>/dev/null; then
        mcp_info=" [mcp:FULL]"
    else
        mcp_info=" [mcp:none]"
    fi
else
    mcp_info=" [mcp:none]"
fi

# Output the status line with colors
# Cyan for model, Yellow for dir, default for git, Blue for sprint, Green for bypass, Magenta for MCP
printf "\033[36m%s\033[0m in \033[33m%s\033[0m%s\033[34m%s\033[0m\033[32m%s\033[0m\033[35m%s\033[0m" \
    "$model_name" \
    "$dir_name" \
    "$git_info" \
    "$sprint_info" \
    "$bypass_info" \
    "$mcp_info"
