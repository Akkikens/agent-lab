# AI Agent Systems Lab

A hands-on learning environment for modern AI agent engineering using Claude Code's native runtime — skills, hooks, sub-agents, MCP servers, agent teams, and context engineering.

Built to practice the patterns that are replacing static LangChain-style prompt pipelines with runtime-native orchestration.

## What's Inside

### Skills (Reusable Agent Workflows)

| Skill | What It Does |
|-------|-------------|
| `deep-review` | Multi-agent code review (context researcher + security auditor + synthesis) |
| `debug-agent` | Hypothesis-driven debugging with parallel investigation agents |
| `onboard-repo` | 4-agent parallel codebase mapping for unfamiliar repos |
| `pr-analyzer` | PR quality analysis (logic + design + risk assessment) |
| `feature-builder` | End-to-end feature delivery with plan→execute→validate pipeline |
| `build-skill` | Meta-skill for creating new skills |

### Hooks (Deterministic Lifecycle Guardrails)

| Hook | Event | Purpose |
|------|-------|---------|
| `safety-check.sh` | PreToolUse | Block force pushes, destructive rm, dangerous git ops |
| `env-protection.sh` | PreToolUse | Block secrets in file writes, detect hardcoded API keys |
| `audit-log.sh` | PostToolUse | Async logging of all tool executions |
| `compaction-saver.sh` | PreCompact | Save state before context window compaction |
| `quality-gate.sh` | Stop | Notify when agent completes work |

### MCP Server (Custom Tool Extension)

`mcp-servers/task-tracker/` — A production MCP server built with the official Python SDK (FastMCP):
- 6 tools: add, list, complete, delete, bulk_add, get_summary
- Resources: lazy-loaded task data
- Prompts: standup report generator, prioritization helper
- Full integration test harness

### Slash Commands (Project Workflows)

| Command | What It Does |
|---------|-------------|
| `/project:agent-team` | Full research→plan→execute→validate pipeline |
| `/project:smart-do` | Dynamic routing — classifies complexity, deploys right level of machinery |
| `/project:research` | Parallel sub-agent research with synthesis |
| `/project:explain` | Explains agent concepts with diagrams and token implications |
| `/project:context-audit` | Audits current context window utilization |

### Agent Definitions

Documented patterns for building agent teams:
- **Researcher** — Deep codebase exploration without context pollution
- **Planner** — Concrete implementation plans from synthesized research
- **Executor** — Isolated code changes (worktree support)
- **Validator** — Independent verification (fresh eyes, no confirmation bias)
- **Coordinator** — Runtime orchestration pattern (the parent context)

## Architecture

```
┌── Claude Code Session (Coordinator) ─────────────────────────┐
│                                                               │
│  Context Window                                               │
│  ├── System prompt (~4K tokens)                              │
│  ├── CLAUDE.md (project rules, always loaded)                │
│  ├── Memory index (cross-session knowledge)                  │
│  ├── Skill descriptions (lazy routing metadata)              │
│  └── Conversation + tool results (growing, compacted)        │
│                                                               │
│  Orchestration: runtime decisions between phases              │
│  ├── Spawn sub-agents (isolated context windows)             │
│  ├── Fan-out parallel research                               │
│  ├── Synthesize findings (never delegate understanding)      │
│  └── Checkpoint with user at critical junctures              │
│                                                               │
│  External:                                                    │
│  ├── Hooks (deterministic, zero token cost, shell scripts)   │
│  ├── MCP servers (tool extension via stdio protocol)         │
│  └── Files (persistence beyond context compaction)           │
└───────────────────────────────────────────────────────────────┘
```

## Key Concepts

### Why Runtime Orchestration > Static Pipelines

```python
# OLD: Static pipeline (LangChain-style)
chain = research | plan | execute | validate  # same path every time
chain.invoke("add a semicolon")               # overkill
chain.invoke("rewrite auth system")           # underkill

# NEW: Runtime orchestration (agent-native)
# Coordinator classifies, adapts, skips, retries based on actual results
# "Add semicolon" → direct edit (500 tokens)
# "Rewrite auth" → full team pipeline (3000 tokens, correct result)
```

### Context Engineering Principles

- **CLAUDE.md** = always loaded → keep it SHORT (build commands + critical rules only)
- **Memory** = cross-session knowledge → index is cheap, content loads on demand
- **Skills** = lazy-loaded workflows → descriptions route, full instructions load on invoke
- **Sub-agents** = context isolation → intermediate results stay in child, parent gets summary
- **Hooks** = zero context cost → deterministic enforcement outside the LLM

### Token Budget Mental Model

| Component | Cost | When |
|-----------|------|------|
| Sub-agent result | 200-1000 tokens | Once when it returns |
| File read | 500-5000 tokens | Once per read |
| CLAUDE.md | 200-2000 tokens | EVERY turn |
| Skill invocation | 500-2000 tokens | On invoke |
| Hook execution | 0 tokens | Always free |

## Getting Started

### Use the lab

```bash
cd ~/Documents/GitHub/agent-lab
# Claude Code auto-loads .claude/settings.json, CLAUDE.md, .mcp.json
# All hooks, permissions, and MCP servers activate automatically
```

### Try the commands

```
/project:research MCP protocol architecture
/project:explain context compaction
/project:smart-do add a health check endpoint
/project:agent-team implement user preferences feature
/project:context-audit
```

### Connect the MCP server

The task-tracker MCP server connects automatically when you start Claude Code in this directory. Approve it when prompted.

```bash
# Test it manually:
cd mcp-servers/task-tracker
uv run python test_server.py
```

## Project Structure

```
agent-lab/
├── CLAUDE.md                    ← Project conventions (always loaded)
├── .mcp.json                    ← MCP server configurations
├── .claude/
│   ├── settings.json            ← Hooks, permissions, project config
│   └── commands/                ← Slash commands (/project:*)
├── skills/                      ← Reusable skill definitions (SKILL.md)
├── agents/                      ← Agent architecture documentation
├── hooks/                       ← Shell scripts for lifecycle events
├── mcp-servers/
│   └── task-tracker/            ← Working MCP server (Python/FastMCP)
├── experiments/
│   ├── 01-context-engineering/  ← How the context window works
│   ├── 02-skill-system/         ← Skill loading & routing
│   ├── 03-hooks/                ← All hook types & lifecycle events
│   ├── 05-memory-engineering/   ← Memory architecture & examples
│   └── 06-runtime-orchestration/← Runtime vs static pipelines
└── docs/
    ├── architecture.md          ← Master architecture reference
    └── quick-reference.md       ← Decision cheatsheet
```

## Learning Path

1. **Context Engineering** → `experiments/01-context-engineering/`
2. **Sub-Agents** → `agents/researcher.md`, `agents/coordinator.md`
3. **Skills** → `experiments/02-skill-system/`, `skills/*/SKILL.md`
4. **Hooks** → `experiments/03-hooks/HOOK_TYPES.md`, `hooks/*.sh`
5. **MCP** → `experiments/04-mcp-architecture/`, `mcp-servers/task-tracker/`
6. **Memory** → `experiments/05-memory-engineering/`
7. **Runtime Orchestration** → `experiments/06-runtime-orchestration/`

## Resources

**Core Documentation:**
- [Claude Code Docs](https://code.claude.com/docs/en/overview)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview)
- [MCP Specification](https://modelcontextprotocol.io/docs/getting-started/intro)

**Agent Harness Comparison:**
- [Three Kingdoms of CLI Agents](https://yun123.io/en/blog/cli-coding-agents-comparison/) — Claude Code vs OpenCode vs Pi philosophy comparison (read first)
- [OpenCode](https://opencode.ai/) (sst) — configurable agent product
- [Pi](https://pi.dev/) (Mario Zechner) — minimal programmable harness

**Deep Dives:**
- [Skills Complete Guide (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)
- [Hooks Mastery](https://github.com/disler/claude-code-hooks-mastery)
- [Sub-agents & Skills Guide](https://dev.to/owen_fox/claude-code-hooks-subagents-and-skills-complete-guide-hjm)
- [Agent Teams Guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/guide/workflows/agent-teams.md)
- [Agent Loops & Tool Calls](https://www.augmentcode.com/guides/claude-agent-sdk-agent-loops-tool-calls)
- [Build Custom Agent Framework](https://nader.substack.com/p/how-to-build-a-custom-agent-framework)
- [Claude Code Skills, Subagents, Hooks Overview](https://boringbot.substack.com/p/claude-code-skills-subagents-hooks)

## License

MIT
