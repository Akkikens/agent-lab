# Complete Hook Reference

## All Available Hook Events

From the settings schema, these are ALL lifecycle events you can hook into:

| Event | When It Fires | Can Block? | Use Cases |
|-------|---------------|-----------|-----------|
| **PreToolUse** | Before any tool executes | YES (exit 2) | Safety, validation, secrets detection |
| **PostToolUse** | After tool returns success | No | Audit logging, notifications |
| **PostToolUseFailure** | After tool returns error | No | Error tracking, alerting |
| **PostToolBatch** | After a batch of tools complete | No | Batch analysis |
| **Notification** | When Claude sends OS notification | No | Custom notification routing |
| **UserPromptSubmit** | When user submits a message | YES | Input validation, transformation |
| **UserPromptExpansion** | During prompt expansion | No | Dynamic context injection |
| **SessionStart** | When a new session begins | No | Setup, welcome messages |
| **SessionEnd** | When session ends | No | Cleanup, summaries |
| **Stop** | When Claude finishes a turn | No | Post-processing, alerts |
| **StopFailure** | When Claude's turn errors | No | Error recovery |
| **SubagentStart** | When a sub-agent spawns | No | Sub-agent monitoring |
| **SubagentStop** | When a sub-agent completes | No | Sub-agent result tracking |
| **PreCompact** | Before context compaction | No | State preservation |
| **PostCompact** | After context compaction | No | State restoration |
| **PermissionRequest** | When permission is needed | No | Custom approval flows |
| **PermissionDenied** | When permission is denied | No | Logging denied actions |
| **Setup** | During initial setup | No | Environment preparation |
| **TaskCreated** | When a task is created | No | Task tracking integration |
| **TaskCompleted** | When a task completes | No | Progress notifications |
| **Elicitation** | When Claude asks a question | No | Custom UI |
| **ElicitationResult** | When user answers | No | Answer logging |
| **ConfigChange** | When settings change | No | Config audit |
| **WorktreeCreate** | When a worktree is created | No | Worktree setup |
| **WorktreeRemove** | When a worktree is removed | No | Cleanup |
| **InstructionsLoaded** | When CLAUDE.md loads | No | Dynamic instructions |
| **CwdChanged** | When directory changes | No | Context switching |
| **FileChanged** | When a file is modified | No | File watching |
| **TeammateIdle** | When a teammate is idle | No | Team coordination |

## Hook Types

### 1. Command Hook (shell script)
```json
{
  "type": "command",
  "command": "cat | /path/to/script.sh",
  "timeout": 10,
  "statusMessage": "Running check...",
  "async": false,
  "once": false
}
```
- Runs a shell command
- Receives context via stdin (JSON)
- Exit 0 = allow, Exit 2 = block
- `async: true` = runs in background, doesn't block

### 2. Prompt Hook (LLM-evaluated)
```json
{
  "type": "prompt",
  "prompt": "Evaluate whether this tool call is safe: $ARGUMENTS",
  "model": "claude-haiku-4-5-20251001",
  "timeout": 15,
  "statusMessage": "AI reviewing..."
}
```
- Uses a SMALL model (Haiku) to evaluate
- The `$ARGUMENTS` placeholder gets the hook input JSON
- LLM returns ok:true/false
- Great for nuanced checks shell scripts can't handle
- Token cost: ~200-500 tokens per evaluation

### 3. Agent Hook (full agent evaluation)
```json
{
  "type": "agent",
  "prompt": "Verify that the tests pass after this change: $ARGUMENTS",
  "model": "claude-sonnet-4-6",
  "timeout": 60,
  "statusMessage": "Agent verifying..."
}
```
- Spawns a mini-agent with tool access
- Can read files, run commands to verify
- Most powerful but most expensive
- Use for complex validation (e.g., "do tests still pass?")

### 4. HTTP Hook (webhook)
```json
{
  "type": "http",
  "url": "https://hooks.example.com/audit",
  "headers": {"Authorization": "Bearer $HOOK_TOKEN"},
  "allowedEnvVars": ["HOOK_TOKEN"],
  "timeout": 5,
  "statusMessage": "Notifying..."
}
```
- POSTs hook context to a URL
- Good for external integrations (Slack, PagerDuty, custom dashboards)
- Headers can reference env vars for auth

### 5. MCP Tool Hook
```json
{
  "type": "mcp_tool",
  "server": "task-tracker",
  "tool": "add_task",
  "input": {"title": "Reviewed: ${tool_input.file_path}"},
  "timeout": 10
}
```
- Calls a tool on an already-configured MCP server
- Input supports `${path}` interpolation from hook context
- Great for using your MCP servers as side-effects

## The `matcher` Field

Controls WHICH tool calls trigger the hook:

```json
{"matcher": "Bash"}          // Only Bash tool calls
{"matcher": "Write"}         // Only Write tool calls
{"matcher": "Edit"}          // Only Edit tool calls
// No matcher = fires for ALL tool calls of that event type
```

## The `if` Field (Fine-Grained Filtering)

For even more precision within a matcher:

```json
{
  "type": "command",
  "command": "...",
  "if": "Bash(git *)"    // Only fires for git commands
}
```

This uses permission rule syntax — same patterns as the `allow` list.

## Key Design Principles

1. **Command hooks for deterministic checks** — fast, reliable, no token cost
2. **Prompt hooks for nuanced evaluation** — when shell scripts can't capture the logic
3. **Agent hooks for complex verification** — when you need to read files and run tests
4. **HTTP hooks for external integration** — notifications, dashboards, audit systems
5. **MCP hooks for tool-based side effects** — leverage your existing MCP servers

6. **async: true for non-blocking** — audit logs shouldn't slow down the agent
7. **once: true for one-shot** — setup tasks that only need to run once
8. **statusMessage for UX** — tell the user what's happening during the check

## Token Cost Model

| Hook Type | Token Cost | Latency | Reliability |
|-----------|-----------|---------|-------------|
| Command | 0 (outside LLM) | <100ms | 100% deterministic |
| HTTP | 0 (outside LLM) | 100-2000ms | Network dependent |
| MCP Tool | 0 (outside LLM) | 100-500ms | Server dependent |
| Prompt | ~200-500 tokens | 500-2000ms | ~95% (LLM judgment) |
| Agent | ~1000-5000 tokens | 2-30s | ~90% (complex task) |

Rule: Use the cheapest hook type that gets the job done.
Shell scripts > HTTP > MCP > Prompt > Agent
