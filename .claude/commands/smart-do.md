Intelligently route a task to the right level of agent complexity based on what's actually needed.

## Instructions

The user wants: $ARGUMENTS

You are a DYNAMIC ROUTER. Before doing anything, classify the task complexity and route appropriately.
The key insight: over-engineering simple tasks wastes tokens; under-engineering complex tasks wastes time.

### Classification

Analyze the request and classify:

**TRIVIAL** (1-2 tool calls, do directly):
- "What does this function do?" → Read the file, answer
- "Fix this typo" → Edit the file
- "Run the tests" → Bash command
- "What's the git status?" → Bash command

**MODERATE** (3-10 tool calls, single focused agent):
- "Add error handling to this endpoint" → One agent, one file, done
- "Find all usages of X" → One Explore agent
- "Write a test for this function" → One agent reads context + writes test

**COMPLEX** (10+ tool calls, multi-agent pipeline):
- "Refactor the auth system" → Research → Plan → Execute → Validate
- "Why is this endpoint slow?" → Multiple hypothesis agents in parallel
- "Implement this feature from the spec" → Full team pipeline

### Routing

Based on classification:

**If TRIVIAL:**
Just do it directly. No agents. No ceremony. Maximum 2 tool calls.

**If MODERATE:**
Spawn ONE focused agent with a clear, complete prompt:
```
Agent({
  description: "[task summary]",
  prompt: "Complete this task: [full context + constraints]
    [include file paths, relevant code, patterns to follow]
    Report what you changed and how to verify."
})
```

**If COMPLEX:**
Use the full pipeline:
1. Spawn parallel research agents
2. Synthesize findings
3. Plan (with user checkpoint)
4. Execute (with worktree isolation for risky changes)
5. Validate

### Why This Matters

Token budget reality:
- TRIVIAL handled directly: ~500 tokens total cost
- TRIVIAL over-engineered with agents: ~5,000 tokens (10x waste)
- COMPLEX handled directly: context overflow, missed edge cases
- COMPLEX handled with team: ~3,000 tokens, correct result

The right level of machinery for the right job.

### Output

After completing the task, report:
- Complexity classification chosen and why
- What was done
- Result or changes made
