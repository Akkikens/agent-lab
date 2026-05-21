# Experiment 05: Memory & Context Engineering

## What This Teaches

- How memory injection works at the protocol level
- Token budgeting strategies
- Scoped context injection patterns
- How to minimize wasted context
- Memory vs CLAUDE.md vs conversation vs files

## The Context Injection Hierarchy

Every turn, Claude Code assembles the context window from multiple sources:

```
Priority  Source              When Loaded         Token Cost    Persistence
────────  ──────────────────  ──────────────────  ────────────  ───────────
1 (top)   System prompt       Always              ~4,000        Permanent
2         CLAUDE.md           Always              Variable      Until changed
3         Memory index        Always              ~200-500      Until changed
4         Skill descriptions  Always              ~50-100 each  Until changed
5         Tool schemas        On demand/loaded    ~100-300 each Until unloaded
6         Conversation        Growing             Variable      Until compacted
7         Tool results        Per call            Variable      Until compacted
8         Skill instructions  On invocation       ~500-2000     One turn
9         Memory content      On recall           Variable      One turn
```

## Memory Architecture

```
~/.claude/projects/<project-path>/memory/
├── MEMORY.md                    ← INDEX (always in context, ~200 lines max)
├── user_role.md                 ← Who the user is
├── feedback_testing.md          ← How to approach tests
├── project_auth-rewrite.md      ← Current initiative context
└── reference_linear-board.md    ← Where to find external info
```

### How It Works at Runtime

1. **MEMORY.md** is loaded into context EVERY TURN (like CLAUDE.md)
   - This is why it must be SHORT (just an index of pointers)
   - Each line costs tokens on every single message

2. **Individual memory files** are loaded ON DEMAND
   - When I decide a memory is relevant, I read the file
   - Cost: only when accessed, not perpetual

3. **This creates a two-tier system:**
   ```
   MEMORY.md (always present, cheap pointers) 
     → individual files (loaded when relevant, full content)
   ```

## Token Budgeting Strategy

### The Budget

Assume ~200K token context window. Plan like this:

| Component | Target Budget | Actual Strategy |
|-----------|--------------|-----------------|
| Fixed overhead (system) | 4-5K | Can't change |
| CLAUDE.md | <2K | Be ruthless — every line costs every turn |
| Memory index | <500 | One-line entries, 200 line max |
| Skill descriptions | <2K | ~50 tokens each, keep list focused |
| Tool schemas | 2-4K | Deferred loading helps |
| **Working space** | **~185K** | For conversation + tool results |

### The Working Space Problem

That 185K sounds like a lot, but:
- A single large file read: 5-20K tokens
- An agent result: 200-1000 tokens
- Your message + my response: 200-2000 tokens
- After 50 turns of conversation: ~50-100K tokens used

This is why **context compaction** exists — when you hit ~80% full,
older messages get summarized (lossy compression).

## What Goes Where — Decision Framework

```
"Where should this information live?"

Is it needed EVERY turn?
├── Yes → CLAUDE.md (project rules, build commands, structure)
└── No → Continue...

Is it needed ACROSS sessions?
├── Yes → Memory file
└── No → Continue...

Is it derivable from the code?
├── Yes → NOWHERE (just read the code when needed)
└── No → Continue...

Is it about the user's preferences?
├── Yes → Memory (type: user or feedback)
└── No → Continue...

Is it about current work-in-progress?
├── Yes → Task system or conversation (NOT memory)
└── No → Continue...

Is it a reference to external systems?
├── Yes → Memory (type: reference)
└── No → Probably don't need to store it
```

## Anti-Patterns That Waste Context

### 1. Bloated CLAUDE.md
```
BAD:  500 lines of every convention, pattern, and rule
GOOD: 30 lines — build commands, critical rules, project-specific gotchas
```
Why: 500 lines × every turn = massive waste. Most of it is derivable from code.

### 2. Storing Code Patterns in Memory
```
BAD:  "The project uses React hooks with this pattern: [50 lines of code]"
GOOD: Don't store this — I can read the code
```
Why: Code changes. Memory becomes stale. Just read the actual code.

### 3. Full Content in MEMORY.md
```
BAD:  MEMORY.md with paragraphs of information per entry
GOOD: MEMORY.md with one-line pointers, full content in separate files
```
Why: MEMORY.md loads every turn. Paragraphs × every turn = budget blown.

### 4. Storing Ephemeral State in Memory
```
BAD:  Memory: "Currently working on PR #42 which adds user auth"
GOOD: This belongs in conversation context or tasks
```
Why: Memory persists across sessions. This is stale in 2 hours.

## Scoped Context Injection

Advanced pattern: inject DIFFERENT context based on what you're doing.

```
Working on frontend code?
  → Load: frontend conventions, component patterns
  → Skip: database schema, API patterns

Working on API endpoints?
  → Load: API conventions, error handling rules
  → Skip: frontend patterns, CSS guidelines

Debugging?
  → Load: logging locations, common failure modes
  → Skip: style guides, architecture docs
```

Claude Code does this partially via skill loading (skills inject context only
when triggered). You can amplify it by:
1. Writing focused memory files per domain
2. Using descriptive names so the right ones get recalled
3. Keeping CLAUDE.md minimal (universal rules only)

## Skill Loading as Context Injection

Skills are LAZY context injection:

```
Before /deep-review:
  Context = system + CLAUDE.md + memory index + skill descriptions (50 tokens)
  
After /deep-review:
  Context = system + CLAUDE.md + memory index + skill descriptions + FULL SKILL.MD (~1500 tokens)
```

The skill's description acts as a ROUTING SIGNAL:
- Bad description: "helps with code" (too vague, might load for wrong tasks)
- Good description: "Perform a thorough code review using multi-agent pipeline" (precise trigger)

## Compaction Survival Guide

When compaction happens, older messages get summarized. To survive:

1. **Critical state in files** — not just in conversation
2. **Tasks track progress** — readable after compaction
3. **Don't rely on "we discussed earlier"** — it may be summarized away
4. **CLAUDE.md and Memory persist** — they're re-injected after compaction
5. **PreCompact hook** — save state before it's lost

## Memory File Best Practices

```markdown
---
name: short-kebab-slug
description: one line that helps decide relevance (SPECIFIC, not generic)
metadata:
  type: user|feedback|project|reference
---

Brief content. Link related memories with [[other-name]].

For feedback/project types:
**Why:** the reason this matters
**How to apply:** when/where this guidance kicks in
```

- `description` is the ROUTING METADATA — it determines when this memory gets recalled
- Keep it specific: "prefers single PR for refactors" not "PR preferences"
- Link related memories: builds a knowledge graph over time
