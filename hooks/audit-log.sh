#!/bin/bash
# PostToolUse audit hook: logs all tool executions for analysis
# This runs AFTER every tool call completes — used for observability, not blocking.
#
# Architecture lesson:
# PostToolUse hooks see the RESULT of the tool call. They can't block (the action
# already happened), but they can log, alert, or trigger side effects.
#
# This creates an audit trail you can analyze later:
# - What files were modified in this session?
# - How many tool calls did this task take?
# - What was the pattern of tool usage?

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"')
TIMESTAMP=$(date -Iseconds)
LOG_DIR="/Users/akshay/Documents/GitHub/agent-lab/.claude/audit"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).jsonl"

# Extract relevant details based on tool type
case "$TOOL_NAME" in
  Write|Edit)
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // "unknown"')
    echo "{\"ts\":\"$TIMESTAMP\",\"tool\":\"$TOOL_NAME\",\"file\":\"$FILE_PATH\"}" >> "$LOG_FILE"
    ;;
  Bash)
    COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // "unknown"' | head -c 200)
    echo "{\"ts\":\"$TIMESTAMP\",\"tool\":\"$TOOL_NAME\",\"cmd\":\"$COMMAND\"}" >> "$LOG_FILE"
    ;;
  Agent)
    DESC=$(echo "$INPUT" | jq -r '.tool_input.description // "unknown"')
    echo "{\"ts\":\"$TIMESTAMP\",\"tool\":\"$TOOL_NAME\",\"desc\":\"$DESC\"}" >> "$LOG_FILE"
    ;;
  *)
    echo "{\"ts\":\"$TIMESTAMP\",\"tool\":\"$TOOL_NAME\"}" >> "$LOG_FILE"
    ;;
esac

exit 0
