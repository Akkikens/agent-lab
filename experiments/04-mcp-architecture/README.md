# Experiment 04: MCP (Model Context Protocol) Architecture

## What This Teaches

- How MCP extends Claude Code's capabilities
- The client-server architecture
- Security model and permissions
- When to build custom MCP vs use existing tools
- How MCP tools appear in the context window

## What Is MCP?

MCP is a protocol that lets you give Claude Code new tools by running external servers.
Think of it like USB for AI — a standard way to plug in capabilities.

```
Claude Code (MCP Client)
    │
    ├── connects to → GitHub MCP Server (provides: create_pr, list_issues, ...)
    ├── connects to → Slack MCP Server (provides: send_message, read_channel, ...)
    ├── connects to → Database MCP Server (provides: query, schema, ...)
    └── connects to → Your Custom Server (provides: whatever you build)
```

## Architecture

```
┌─ Claude Code Process ─────────────────────────────┐
│                                                    │
│  Context Window                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ ...                                          │ │
│  │ MCP Tool: github_create_pr(title, body, ...) │ │  ← tool schemas injected
│  │ MCP Tool: slack_send(channel, message)       │ │
│  │ ...                                          │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  Tool Router                                       │
│  ┌──────────────────────────────────────────────┐ │
│  │ "github_*" → GitHub MCP Server (stdio/SSE)   │ │
│  │ "slack_*"  → Slack MCP Server (stdio/SSE)    │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
└────────────────────────────────────────────────────┘
        │ stdio/SSE │
        ▼           ▼
┌─────────────┐  ┌─────────────┐
│ GitHub MCP  │  │ Slack MCP   │
│ Server      │  │ Server      │
│ (Node.js)   │  │ (Python)    │
└─────────────┘  └─────────────┘
```

## Token/Context Implications

Every MCP tool's schema gets injected into the context:
- Tool name + description: ~50-100 tokens
- Parameter schema: ~100-300 tokens per tool
- 10 MCP tools = ~1-3K tokens of context used EVERY turn

This is why you should:
1. Only connect MCP servers you actively need
2. Prefer servers with focused tool sets over "kitchen sink" servers
3. Use the deferred loading pattern when possible

## Transport Mechanisms

| Transport | How It Works | Use Case |
|-----------|-------------|----------|
| stdio | Server runs as subprocess, communicates via stdin/stdout | Local tools, fast, secure |
| SSE | Server runs as HTTP service, streams responses | Remote/shared servers |

stdio is preferred for local development — no network, no auth complexity.

## Configuration

In `.claude/settings.json` or global settings:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/path/to/server.js"],
      "env": {
        "API_KEY": "..."
      }
    }
  }
}
```

## Security Model

- MCP servers run with YOUR system permissions
- They can access files, network, databases
- Claude Code asks permission before calling MCP tools (unless allowed in settings)
- Environment variables pass secrets to servers (NOT in the context window)

Critical: API keys in `env` are NOT visible in the context. They go directly
to the server process. This is safer than putting keys in prompts.

## When to Build Custom MCP vs Other Approaches

| Need | Solution |
|------|----------|
| Call an external API once | Just use Bash + curl |
| Repeatedly query a database | MCP server (persistent connection) |
| Integrate with a system across sessions | MCP server |
| Complex multi-step external workflow | MCP server with specialized tools |
| Simple file/git operations | Built-in tools (Read, Edit, Bash) |

Build MCP when: you'd otherwise repeat the same curl/API setup across many tasks.
Don't build MCP when: a simple bash command suffices.

## Building a Custom MCP Server (Minimal Example)

See: `mcp-servers/example-server/` for a working implementation.

The minimum viable MCP server:
1. Reads JSON-RPC messages from stdin
2. Responds with tool definitions on `initialize`
3. Executes tools on `tools/call`
4. Returns results as JSON

Languages: Any (Node.js and Python have the best SDK support)
