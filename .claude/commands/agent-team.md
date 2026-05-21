Execute a task using the full agent team pipeline: Research → Plan → Execute → Validate.

## Instructions

The user wants to accomplish: $ARGUMENTS

You are the COORDINATOR. Execute this task using the full agent team pipeline.
DO NOT skip steps. DO NOT delegate understanding — synthesize at each stage.

### Phase 1: Research

Determine what you need to know to accomplish this task.
Spawn 1-3 focused research agents in parallel:

```
Agent({
  description: "Research: [specific aspect]",
  subagent_type: "Explore",
  prompt: "[Focused question about the codebase/system relevant to the task]
    Report: key findings, file paths, patterns found. Under 200 words."
})
```

After agents return, SYNTHESIZE their findings. Write a brief summary of what you learned.

### Phase 2: Plan

Based on YOUR understanding from Phase 1, create a concrete plan.
Use the Plan agent type:

```
Agent({
  description: "Plan: [task]",
  subagent_type: "Plan",
  prompt: "Goal: [what we're doing]
    
    Context (from research):
    [YOUR synthesis — specific files, patterns, constraints you discovered]
    
    Produce: ordered steps, file paths, dependencies between steps, risks."
})
```

Present the plan to the user for approval before proceeding.

### Phase 3: Execute

After user approves, execute each step. For code changes, use isolated execution:

```
Agent({
  description: "Implement: [specific step]",
  subagent_type: "general-purpose",
  isolation: "worktree",
  prompt: "Task: [exact implementation with file paths and what to change]
    Constraints: [patterns to follow, things to avoid]
    Verify: [how to check it worked]"
})
```

For independent steps, launch multiple executors in parallel.

### Phase 4: Validate

After execution, spawn a validator that hasn't seen the executor's reasoning:

```
Agent({
  description: "Validate: [what to check]",
  subagent_type: "general-purpose",
  prompt: "Review changes at [path/branch].
    Requirements: [what must be true]
    Check: correctness, safety, consistency, edge cases.
    Report: PASS or FAIL with specifics."
})
```

### Phase 5: Report

Summarize to the user:
- What was accomplished
- What was changed (file paths)
- Any follow-up needed
- How to test/verify

### Critical Rules
1. NEVER skip the research phase — you need context before planning
2. NEVER pass raw agent output to another agent — synthesize first
3. ALWAYS present the plan for approval before executing
4. ALWAYS validate after executing
5. If validation FAILS: fix and re-validate (max 2 retries), then escalate
