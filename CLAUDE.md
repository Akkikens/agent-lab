# Agent Systems Lab

A hands-on learning environment for modern AI agent engineering patterns using Claude Code's native runtime.

## Project Structure

```
.claude/
  settings.json          # Project-level permissions and hooks
  commands/              # Custom slash commands (skill-like)
skills/                  # Reusable skill definitions
agents/                  # Sub-agent prompt definitions
hooks/                   # Hook scripts
mcp-servers/             # Custom MCP server implementations
experiments/             # Standalone experiments and explorations
docs/                    # Architecture notes and learnings
```

## Conventions

- Each system we build gets its own directory with a README explaining the architecture
- Experiments are numbered: `experiments/01-context-window/`, `experiments/02-sub-agents/`
- Agent prompts live in `agents/` as markdown files
- Skills follow Claude Code's SKILL.md format in `skills/`
- Hooks are shell scripts in `hooks/` referenced by `.claude/settings.json`

## Working Patterns

- Use sub-agents for parallel research and isolated execution
- Use hooks for validation and safety guardrails
- Use MCP for external system integration
- Use skills for reusable, composable capabilities
- Prefer runtime orchestration over static pipelines
