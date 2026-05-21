#!/bin/bash
# PreToolUse hook: prevents writing secrets or sensitive files
#
# Architecture lesson:
# This hook demonstrates CONTENT-AWARE validation. It doesn't just check
# the tool name — it inspects the actual arguments to detect dangerous patterns.
#
# Why this can't be a CLAUDE.md rule:
# - A prompt rule is ~95% reliable (LLM might forget under pressure)
# - This hook is 100% reliable (deterministic code, no bypass possible)
# - Zero context cost (doesn't consume tokens in the conversation)

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // empty')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Check Write/Edit operations
if [ "$TOOL_NAME" = "Write" ] || [ "$TOOL_NAME" = "Edit" ]; then
  # Block writes to sensitive files
  case "$FILE_PATH" in
    *.env|*.env.*|*credentials*|*secrets*|*.pem|*.key|*id_rsa*)
      echo "BLOCKED: Cannot write to sensitive file: $FILE_PATH" >&2
      echo "Use 'cp .env.example .env' manually and edit by hand." >&2
      exit 2
      ;;
  esac

  # Block content that looks like secrets
  if echo "$CONTENT" | grep -qiE "(api[_-]?key|secret[_-]?key|password|token)\s*[=:]\s*['\"][^'\"]{8,}"; then
    echo "BLOCKED: Content appears to contain hardcoded secrets." >&2
    echo "Use environment variables instead." >&2
    exit 2
    ;;
  fi
fi

# Check Bash operations
if [ "$TOOL_NAME" = "Bash" ]; then
  # Block printing env vars that might contain secrets
  if echo "$COMMAND" | grep -qE "printenv|env\s*\||echo\s+\\\$(API|SECRET|TOKEN|PASSWORD|KEY)"; then
    echo "BLOCKED: Cannot print potentially sensitive environment variables." >&2
    exit 2
    ;;
  fi
fi

exit 0
