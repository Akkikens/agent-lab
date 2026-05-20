# Validator Agent

## Purpose
Independently verifies that executed work meets requirements.
Provides a second opinion — catches what the executor missed.

## When to Use
- After executor completes changes
- Before presenting work to the user as "done"
- For security-sensitive changes
- When you need confidence before merging worktree changes

## Architecture Notes

The validator is the "reviewer" in the pipeline:

```
[Executor output] → [Validator] → pass/fail + issues → [User or retry]
```

Critical property: The validator NEVER sees the executor's reasoning.
It only sees the resulting code. This prevents confirmation bias.

## Invocation Pattern

```
Agent({
  description: "Validate: [what to check]",
  subagent_type: "general-purpose",
  prompt: `
    Review the changes in [file/branch/worktree path].
    
    Requirements that must be met:
    1. [requirement 1]
    2. [requirement 2]
    3. [requirement 3]
    
    Check for:
    - Correctness: Does it do what's required?
    - Safety: Any security issues? (injection, XSS, auth bypass)
    - Consistency: Does it match existing patterns?
    - Edge cases: What inputs could break it?
    
    Report:
    - PASS or FAIL
    - Issues found (with file:line references)
    - Suggested fixes (if FAIL)
    
    Be strict. False negatives (missing bugs) are worse than false positives.
  `
})
```

## Why Independent Validation Matters

The executor has "anchoring bias" — it wrote the code, so it's predisposed
to see it as correct. A fresh context with fresh eyes catches:
- Logic errors the executor rationalized away
- Security issues hidden by "it works" satisfaction
- Pattern violations the executor didn't notice
- Missing edge cases

## Composition with Retry

```
loop:
  executor produces changes
  validator reviews changes
  if PASS: done
  if FAIL: feed issues back to executor (new agent call with fix instructions)
  max 2 retries, then escalate to user
```

This executor→validator loop is the core of reliable agent work.
