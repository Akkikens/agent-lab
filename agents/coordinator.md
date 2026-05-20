# Coordinator Pattern

## Purpose
The coordinator is not a separate agent — it's the PARENT context (you, or the top-level Claude Code session).
This document describes the orchestration pattern, not a file to invoke.

## Why the Coordinator is the Parent

In Claude Code's runtime model, the coordinator IS the conversation you're in.
There's no separate "coordinator agent" — that would add an unnecessary layer.

```
┌─ Your Claude Code Session (THE COORDINATOR) ──────────────┐
│                                                            │
│  You receive user request                                  │
│  You decide: can I do this directly, or delegate?          │
│                                                            │
│  If delegate:                                              │
│    1. Spawn Researcher (what do I need to know?)           │
│    2. Synthesize findings (YOU do this, not another agent) │
│    3. Spawn Planner (how should we approach this?)         │
│    4. Present plan to user (checkpoint)                    │
│    5. Spawn Executor(s) (do the work)                      │
│    6. Spawn Validator (verify the work)                    │
│    7. Report results to user                               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## The Coordinator's Responsibilities

1. **Decompose**: Break user request into sub-tasks
2. **Route**: Decide which agent type handles each sub-task
3. **Synthesize**: Combine agent outputs (NEVER delegate this)
4. **Checkpoint**: Get user approval at critical junctures
5. **Retry**: Handle failures and feed corrections back

## Orchestration Patterns

### Sequential Pipeline
```
Research → Plan → Execute → Validate → Report
```
Use when: tasks are dependent, order matters

### Parallel Fan-Out
```
        ┌→ Researcher A ─┐
User → │→ Researcher B ─│→ Synthesize → Plan → Execute
        └→ Researcher C ─┘
```
Use when: multiple independent questions need answering

### Iterative Refinement
```
Execute → Validate → Fix → Validate → ... → Done
```
Use when: complex changes that may need correction

### Dynamic Routing
```
User request → Classify complexity:
  Simple (1-2 tool calls)  → Handle directly, no agents
  Medium (3-10 tool calls) → Single focused agent
  Complex (10+ tool calls) → Full pipeline with multiple agents
```

## Critical Rule: Never Delegate Understanding

The coordinator (parent context) must:
- Read and understand researcher output before passing to planner
- Read and understand planner output before passing to executor
- Read and understand validator output before reporting to user

If you just pipe agent A's output into agent B's prompt without processing it,
you've built a fragile pipeline that breaks silently.

## Runtime vs Static Orchestration

Old pattern (LangChain-style):
```python
chain = research | plan | execute | validate  # static pipeline
chain.invoke(input)  # can't adapt at runtime
```

Claude Code native pattern:
```
1. Research (might discover task is simpler than expected)
2. DECISION POINT: maybe skip planning, just execute directly
3. Execute (might discover a blocker)
4. DECISION POINT: maybe need more research, not validation
5. Adapt based on actual results
```

The parent context makes RUNTIME DECISIONS between steps.
This is why runtime orchestration > static pipelines.
Static pipelines can't adapt to what they discover.

## Anti-Patterns

- "Coordinator agent" as a separate spawned agent (unnecessary layer, wastes context)
- Piping output between agents without reading it
- Fixed pipelines that can't skip steps
- Over-delegating (spawning agents for 1-tool-call tasks)
- Under-delegating (doing 20 file reads in parent when a researcher would suffice)
