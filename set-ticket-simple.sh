#!/bin/bash
# Simple ticket setter that works with Claude Code's session system

TICKET="$1"
if [[ -z "$TICKET" ]]; then
    echo "Usage: set-ticket-simple.sh CLAUD-56"
    exit 1
fi

# Set as default ticket (always works)
echo "$TICKET" > /Users/fsconklin/.claude/session_tickets/default.ticket
echo "✅ Set default ticket to: $TICKET"

# Also set in multiple locations for robustness
echo "$TICKET" > /Users/fsconklin/.claude/session_tickets/current.ticket
echo "✅ Set current ticket to: $TICKET"

echo "Status line should now show: [$TICKET]"