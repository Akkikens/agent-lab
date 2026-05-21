# Quick Reference — Agent Engineering Patterns

## Decision Cheatsheet

### "Should I use a sub-agent?"
- >3 tool calls for a subtask? → YES
- Need raw intermediate output? → NO (do it directly)
- Independent parallel work? → YES (fan-out)
- 1-2 quick operations? → NO (direct)

### "Which agent type?"
- Searching/reading many files → `subagent_type: "Explore"`
- Architecture/planning → `subagent_type: "Plan"`
- General implementation → `subagent_type: "general-purpose"`
- Need faster/cheaper → `model: "haiku"`
- Need most capable → `model: "opus"`

### "Should this be a skill?"
- Will I do this workflow again? → SKILL
- One-off task? → Just do it
- Project-specific recurring task? → `.claude/commands/`
- Cross-project reusable? → `skills/` or plugin

### "Should this be a hook?"
- MUST always be enforced? → Hook (deterministic)
- Soft preference? → CLAUDE.md
- Needs to validate tool inputs? → PreToolUse
- Needs to audit/log? → PostToolUse (async)
- Complex evaluation needed? → Prompt hook (uses LLM)

### "Where does this info live?"
- Needed every turn? → CLAUDE.md
- Needed across sessions, not every turn? → Memory
- Derivable from code? → NOWHERE
- About current task only? → Tasks/conversation
- External system pointer? → Memory (type: reference)

## Token Cost Reference

| Action | Approximate Cost |
|--------|-----------------|
| Sub-agent spawn + result | 200-1000 tokens |
| File read (typical) | 500-5000 tokens |
| CLAUDE.md (per turn) | 200-2000 tokens |
| Skill invocation | 500-2000 tokens |
| Tool schema (loaded) | 100-300 tokens |
| Hook execution | 0 tokens (external) |
| Hook block message | ~50 tokens |

## Common Patterns

### Parallel Research
```
Agent("Research A", ...) + Agent("Research B", ...) → synthesize → answer
```

### Plan-Execute-Validate
```
research → plan → user approves → execute(worktree) → validate → report
```

### Dynamic Routing
```
classify(task) → trivial: direct | moderate: 1 agent | complex: pipeline
```

### Iterative Refinement
```
execute → validate → fail? → fix → validate → pass
(max 2 retries, then escalate)
```

## File Layout

```
project/
├── CLAUDE.md              ← Short! Build cmds + critical rules only
├── .mcp.json              ← MCP server configs
├── .claude/
│   ├── settings.json      ← Hooks, permissions, project config
│   └── commands/          ← Project slash commands
├── skills/                ← Reusable skill definitions
│   └── my-skill/SKILL.md
├── hooks/                 ← Hook scripts
└── agents/                ← Agent prompt docs (reference)

~/.claude/
├── settings.json          ← Global config
├── settings.local.json    ← Personal overrides
├── projects/<path>/
│   └── memory/
│       ├── MEMORY.md      ← Index (always loaded)
│       └── *.md           ← Individual memories
└── skills/                ← Global skills
```

## Hook Event Quick Reference

| Need | Event | Type |
|------|-------|------|
| Block dangerous commands | PreToolUse | command |
| Audit all actions | PostToolUse | command (async) |
| Save state before compaction | PreCompact | command |
| Notify when done | Stop | command (async) |
| Validate on submit | UserPromptSubmit | command |
| Complex safety check | PreToolUse | prompt |
| Run tests after code | PostToolUse | agent |
| External webhook | PostToolUse | http |
| Track with MCP server | PostToolUse | mcp_tool |
