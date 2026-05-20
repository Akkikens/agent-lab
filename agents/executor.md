# Executor Agent

## Purpose
Takes a concrete plan and implements it. Does NOT decide what to build — only how.

## When to Use
- After planner has produced an approved plan
- For isolated changes that won't affect the parent's work
- When using worktree isolation for safety

## Architecture Notes

Executors are the "hands" of the agent team:

```
[Planner output] → [Executor] → code changes → [Validator]
```

Key properties:
- **Scoped**: Each executor handles ONE logical change
- **Isolated**: Use `isolation: "worktree"` for risky changes
- **Verifiable**: Each executor's output can be independently checked
- **Parallelizable**: Independent changes can execute simultaneously

## Invocation Pattern

```
Agent({
  description: "Implement: [specific change]",
  subagent_type: "general-purpose",
  isolation: "worktree",  // optional — use for risky changes
  prompt: `
    Task: [specific implementation task]
    
    File: [exact file path]
    Current state: [what's there now]
    Desired state: [what it should become]
    
    Constraints:
    - Follow existing patterns in the file
    - Do not modify other files
    - [any other constraints]
    
    After implementing, verify by: [test command or check]
  `
})
```

## Worktree Isolation

When you pass `isolation: "worktree"`, the executor:
1. Gets a fresh git worktree (separate working directory)
2. Makes changes there without affecting your main checkout
3. If it makes changes, returns the worktree path and branch name
4. If it makes NO changes, the worktree is auto-cleaned

This is the safest way to let an agent write code. You can review the changes
before merging them into your working tree.

## Parallelization Pattern

For independent changes, launch multiple executors simultaneously:

```
// In a single message, call Agent multiple times:
Agent({ description: "Implement: add auth middleware", ... })
Agent({ description: "Implement: add rate limiter", ... })
Agent({ description: "Implement: add logging", ... })
```

These run in parallel, each in their own context, each potentially in their own worktree.

## Anti-patterns

- DON'T give an executor vague goals ("make it better")
- DON'T let it decide architecture (that's the planner's job)
- DON'T skip the verification step
- DON'T use without worktree for destructive operations
