# Experiment 01: Context Engineering

## What This Teaches

- How the context window works as an agent's runtime
- What gets auto-injected and why
- Token budget implications of every design decision
- Why sub-agents exist (context isolation)

## Key Insight

The context window is not just "memory" — it's the agent's entire execution environment.
Everything you put in it competes for attention and capacity.

## Architecture Diagram

```
┌── Agent Turn ──────────────────────────────────────────────┐
│                                                            │
│  [System Prompt]     ← fixed cost, ~4K tokens             │
│  [CLAUDE.md]         ← fixed cost per project, injected   │
│  [Memory Index]      ← fixed cost, always present         │
│  [Skill Descriptions]← fixed cost, routing metadata       │
│  [Tool Schemas]      ← deferred until needed              │
│  [Conversation]      ← growing cost, compacted when full  │
│  [Tool Results]      ← variable, biggest swing factor     │
│                                                            │
│  Total available: ~200K tokens                             │
│  Effective sweet spot: <80K tokens                         │
│  Degradation zone: >120K tokens                            │
└────────────────────────────────────────────────────────────┘
```

## Design Principles Derived

1. CLAUDE.md should be surgical — every line costs tokens on every turn
2. Use sub-agents to isolate expensive operations (large file reads, research)
3. Memory index = pointers, not content
4. Skills load lazily — description quality determines routing accuracy
5. Prefer small, targeted tool calls over "read the whole file"
6. Context compaction is automatic but lossy — critical state should be in files, not conversation
