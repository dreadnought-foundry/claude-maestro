#!/bin/bash

# Simple script to set the current ticket for Claude Code statusline
# Usage: ./set-current-ticket.sh CLAUD-56

TICKET="$1"
SESSION_TICKET_DIR="/Users/fsconklin/.claude/session_tickets"

if [[ -z "$TICKET" ]]; then
    echo "Usage: $0 TICKET-NUMBER"
    echo "Example: $0 CLAUD-56"
    exit 1
fi

# Validate ticket format
if [[ ! "$TICKET" =~ ^[A-Z]+-[0-9]+$ ]]; then
    echo "Error: Invalid ticket format. Expected format: PROJECT-123"
    exit 1
fi

# Create directory if it doesn't exist
mkdir -p "$SESSION_TICKET_DIR"

# Set as default ticket (fallback when no session ID)
echo "$TICKET" > "$SESSION_TICKET_DIR/default.ticket"
echo "Set $TICKET as default ticket"

# Also set for a few common session patterns just in case
echo "$TICKET" > "$SESSION_TICKET_DIR/current.ticket"
echo "Set $TICKET as current ticket"

# Clean up any old ENGINE-200 references
find "$SESSION_TICKET_DIR" -name "*.ticket" -exec grep -l "ENGINE-200" {} \; | while read -r file; do
    echo "$TICKET" > "$file"
    echo "Updated $(basename "$file") from ENGINE-200 to $TICKET"
done

echo "Ticket $TICKET is now set for statusline display"