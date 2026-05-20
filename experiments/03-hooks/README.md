# Experiment 03: Hooks — Agent Lifecycle Events

## What This Teaches

- How hooks provide safety guardrails at runtime
- The event model (when hooks fire)
- How to implement validation without blocking flow
- Why hooks > in-prompt rules for enforcement

## What Are Hooks?

Hooks are shell commands that Claude Code executes in response to lifecycle events.
They run OUTSIDE the LLM — they're deterministic code, not probabilistic prompts.

```
User says "delete all test files"
    │
    ▼
Claude generates: rm -rf tests/
    │
    ▼
[PRE-TOOL HOOK fires] ← shell script checks the command
    │
    ├─ Hook returns exit 0 → command proceeds
    └─ Hook returns exit 2 → command BLOCKED, error shown to Claude
```

## Why Hooks > Prompt Rules

| Approach | Reliability | Bypass Risk |
|----------|-------------|-------------|
| "Never delete test files" in CLAUDE.md | ~95% | Jailbreak/context loss |
| Pre-tool hook that blocks `rm` on test dirs | 100% | Cannot be bypassed |

Hooks are DETERMINISTIC. They don't depend on the LLM "remembering" a rule.
They execute as real code outside the model's control.

## Hook Events Available

| Event | When It Fires | Use Case |
|-------|---------------|----------|
| PreToolUse | Before any tool execution | Block dangerous commands, validate args |
| PostToolUse | After tool returns | Log, audit, modify output |
| Notification | When Claude sends a notification | Custom alerting |
| Stop | When Claude finishes a turn | Post-processing, cleanup |

## Configuration (settings.json)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/hook-script.sh"
          }
        ]
      }
    ]
  }
}
```

## Hook Script Interface

Hooks receive context via environment variables:
- `CLAUDE_TOOL_NAME` — which tool is being called
- `CLAUDE_TOOL_INPUT` — JSON of the tool's parameters

And via stdin:
- Full JSON payload with tool details

Hook exit codes:
- `0` — allow (proceed normally)
- `2` — block (stop the tool call, show error to Claude)
- Other — error (treated as allow with warning)

## Example: Safety Hook

```bash
#!/bin/bash
# hooks/safety-check.sh
# Blocks dangerous bash commands

INPUT=$(cat)  # Read stdin JSON
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Block force pushes
if echo "$COMMAND" | grep -q "push.*--force\|push.*-f"; then
  echo "BLOCKED: Force push requires manual confirmation" >&2
  exit 2
fi

# Block rm -rf on important dirs
if echo "$COMMAND" | grep -qE "rm\s+-rf\s+(src|lib|app|tests)/"; then
  echo "BLOCKED: Cannot recursively delete source directories" >&2
  exit 2
fi

exit 0
```

## Example: File Write Audit Hook

```bash
#!/bin/bash
# hooks/write-audit.sh
# Logs all file writes for audit trail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')

if [ "$TOOL" = "Write" ] || [ "$TOOL" = "Edit" ]; then
  echo "$(date -Iseconds) WRITE $FILE_PATH" >> /tmp/claude-audit.log
fi

exit 0  # Always allow (just logging)
```

## Token/Context Implications

Hooks have ZERO context cost. They run outside the LLM entirely.
This makes them the most efficient safety mechanism available:
- No tokens spent on safety rules in CLAUDE.md
- No context window pollution
- Deterministic behavior regardless of conversation state

The only cost: if a hook blocks, the error message enters the context (~50 tokens).

## Design Principles

1. **Hooks for enforcement** — things that MUST be true regardless of prompt
2. **CLAUDE.md for guidance** — things that should be true but can flex
3. **Hooks are invisible** — they don't consume context until they trigger
4. **Keep hooks fast** — they block execution while running
5. **Hooks can't modify** — they allow or block, never change tool inputs
