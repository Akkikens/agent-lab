#!/bin/bash
# Safety hook: blocks dangerous operations in the agent-lab project
# Install: add to .claude/settings.json under hooks.PreToolUse
#
# This hook demonstrates the PreToolUse lifecycle event.
# It receives the tool call details via stdin as JSON.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check Bash tool calls
if [ -z "$COMMAND" ]; then
  exit 0
fi

# Block force pushes
if echo "$COMMAND" | grep -qE "git\s+push.*--force|git\s+push.*-f\b"; then
  echo "BLOCKED: Force push not allowed. Use --force-with-lease if needed." >&2
  exit 2
fi

# Block destructive git operations
if echo "$COMMAND" | grep -qE "git\s+reset\s+--hard"; then
  echo "BLOCKED: git reset --hard can lose work. Use git stash instead." >&2
  exit 2
fi

# Block rm -rf on source directories
if echo "$COMMAND" | grep -qE "rm\s+-rf\s+(/|~|src|lib|app|agents|skills)/"; then
  echo "BLOCKED: Cannot recursively delete critical directories." >&2
  exit 2
fi

# Block writing to .env files (secrets protection)
if echo "$COMMAND" | grep -qE ">\s*\.env|tee.*\.env"; then
  echo "BLOCKED: Cannot write to .env files via shell. Edit manually." >&2
  exit 2
fi

exit 0
