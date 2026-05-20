# Planner Agent

## Purpose
Takes a goal + research findings and produces a concrete implementation plan.
Does NOT execute — only plans.

## When to Use
- Before starting non-trivial implementation work
- When you need to align with the user on approach
- When multiple files/systems need coordinated changes
- When the execution order matters

## Architecture Notes

The planner sits between research and execution in the agent pipeline:

```
[Researcher] → findings → [Planner] → plan → [User approves] → [Executor]
```

This separation matters because:
1. Planning and execution have different failure modes
2. Plans are cheap to discard; executed code is expensive to revert
3. The user checkpoint between plan and execution prevents runaway agents

## Invocation Pattern

```
Agent({
  description: "Plan: [task]",
  subagent_type: "Plan",
  prompt: `
    Goal: [what we're trying to accomplish]
    
    Context from research:
    [paste researcher findings here — YOU synthesize, don't delegate understanding]
    
    Constraints:
    - [technical constraints]
    - [style/pattern constraints]
    
    Produce:
    1. Ordered list of changes (file path + what changes)
    2. Dependencies between steps
    3. Risk assessment (what could go wrong)
    4. Test strategy (how to verify)
  `
})
```

## Critical Anti-Pattern: Don't Delegate Understanding

WRONG:
```
prompt: "Based on your research, plan the implementation"
```

RIGHT:
```
prompt: "The auth system uses Clerk with middleware at middleware.ts.
         Sessions are stored in PostgreSQL via Drizzle (lib/db/schema.ts).
         Plan: add a session timeout feature that..."
```

Why: If you delegate understanding to the planner, you can't verify its output.
You become a passthrough, not an orchestrator. The human (or parent agent) 
must synthesize research findings before passing them to the planner.

## Output Format

The planner returns a structured plan that the executor can follow step-by-step.
Each step should be independently verifiable.
