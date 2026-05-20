# Experiment 02: The Skill System

## What This Teaches

- How Claude Code discovers and loads skills
- How skill descriptions drive routing
- The lazy-loading token optimization
- How to write effective skill triggers

## How Skills Work at Runtime

```
Conversation Start:
┌──────────────────────────────────────────┐
│ System prompt includes skill DESCRIPTIONS │  ← ~50-100 tokens each
│ (just the first paragraph of SKILL.md)    │
│                                           │
│ Skills available:                         │
│ - deep-review: Perform a thorough...      │
│ - frontend-design: Create distinctive...  │
└──────────────────────────────────────────┘

User types: "/deep-review" or task matches description
┌──────────────────────────────────────────┐
│ Full SKILL.md content is NOW loaded       │  ← entire instructions injected
│ into the context via the Skill tool       │
│                                           │
│ Claude follows the skill's instructions   │
└──────────────────────────────────────────┘
```

## Key Insight: Descriptions Are Routing Metadata

The skill description (first paragraph of SKILL.md) serves TWO purposes:

1. **Shown to the user** in help/listings
2. **Used by the system** to decide when to suggest/invoke the skill

This means your description must be:
- Specific enough to trigger correctly (not "helps with code")
- General enough to catch valid use cases
- Action-oriented (starts with a verb)

## Token Economics

| State | Cost |
|-------|------|
| Skill NOT invoked | ~50-100 tokens (description only) |
| Skill invoked | ~500-2000 tokens (full SKILL.md loaded) |
| Skill with sub-agents | Full skill + agent results |

This is why skills are lazy-loaded: if you have 20 skills, that's only
~1-2K tokens for descriptions, vs ~20-40K if all were loaded.

## Skill File Format

```
skills/
  my-skill/
    SKILL.md          ← REQUIRED: description (first paragraph) + instructions
```

The first paragraph before any heading is the description/trigger text.
Everything after (usually under ## Instructions) is the execution instructions.

## Skill vs CLAUDE.md vs Agent Prompt

| Mechanism | When It Loads | Use For |
|-----------|---------------|---------|
| CLAUDE.md | Every turn | Project conventions, always-on rules |
| Skill | On invocation | Reusable multi-step workflows |
| Agent prompt | On spawn | One-off delegated tasks |

## Custom Slash Commands (Alternative)

Claude Code also supports `.claude/commands/` as custom slash commands:

```
.claude/commands/
  review.md       ← invoked as /project:review
  debug.md        ← invoked as /project:debug
```

These are similar to skills but:
- Scoped to a project (not global)
- Invoked explicitly by name
- No automatic trigger matching
- Simpler format (just markdown instructions)

## Our Deep Review Skill Architecture

```
/deep-review invoked
    │
    ├─→ [Context Researcher Agent]  ─┐
    │                                 │  parallel
    ├─→ [Security Auditor Agent]    ─┘
    │
    ▼
Coordinator synthesizes findings
    │
    ▼
Structured review output to user
```

This demonstrates:
1. Skill as entry point (reusable workflow)
2. Sub-agents for parallel research (context isolation)
3. Coordinator pattern (parent synthesizes, doesn't delegate understanding)
