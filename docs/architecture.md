# Agent Systems Architecture — Claude Code Native Patterns

## The Runtime Model

Claude Code is an **agent runtime**. Understanding this changes how you think about everything:

```
Traditional Software              Agent Runtime
────────────────────────          ────────────────────────
CPU executes instructions         LLM generates next action
RAM holds working state           Context window holds ALL state
Disk provides persistence         Files/memory provide persistence
Function calls are instant        Tool calls cost tokens + time
Threads provide parallelism       Sub-agents provide parallelism
Libraries extend capability       MCP/skills extend capability
Tests verify correctness          Validators verify correctness
```

## The Five Primitives

Everything in Claude Code agent engineering reduces to five primitives:

### 1. Context (the execution environment)
- System prompt + CLAUDE.md + memory + conversation + tool results
- Hard ceiling (~200K tokens), soft sweet spot (<80K)
- Managed through: compaction, sub-agents, lazy loading

### 2. Tools (how the agent acts on the world)
- Built-in: Read, Write, Edit, Bash, Agent
- MCP: External tools via protocol
- Deferred: Schema loaded on demand
- Permission model controls what's allowed

### 3. Sub-Agents (parallelism + context isolation)
- Separate context windows
- Return summaries, discard intermediate state
- Types: Explore, Plan, general-purpose, model overrides
- Worktree isolation for safe code execution

### 4. Skills (reusable workflows)
- Lazy-loaded instruction sets
- Description-based routing
- Composable (can spawn agents, call tools)
- Zero cost until invoked

### 5. Hooks (deterministic guardrails)
- Shell scripts triggered by lifecycle events
- Run OUTSIDE the LLM (100% reliable)
- Zero context cost until triggered
- Block or allow, cannot modify

## Composition Patterns

### Pattern 1: Research Pipeline
```
User question → Researcher agents (parallel) → Synthesize → Answer
```
When: Understanding something complex with minimal context cost

### Pattern 2: Plan-Execute-Validate
```
Goal → Planner → User checkpoint → Executor → Validator → Done
```
When: Non-trivial code changes that need safety

### Pattern 3: Dynamic Routing
```
Request → Classify complexity → Route to appropriate depth:
  Trivial: handle directly
  Moderate: single focused agent
  Complex: full team pipeline
```
When: You want efficiency (don't over-engineer simple tasks)

### Pattern 4: Fan-Out/Fan-In
```
Question → spawn N agents in parallel → collect results → synthesize
```
When: Multiple independent research questions

### Pattern 5: Iterative Refinement
```
Attempt → Validate → Fix → Validate → ... → Pass
```
When: Complex implementation with uncertain correctness

## Why Runtime > Static Pipelines

Old orchestration (LangChain, etc.):
```python
chain = step1 | step2 | step3  # Fixed at definition time
result = chain.invoke(input)    # No adaptation
```

Problems:
1. Can't skip steps that aren't needed
2. Can't add steps discovered at runtime
3. Can't change strategy based on intermediate results
4. Error handling is bolted-on, not native

Runtime orchestration (Claude Code native):
```
1. Start task
2. Discover it's simpler than expected → skip planning, just execute
   OR discover a dependency → research that first
   OR discover a blocker → ask user
3. Each step informed by previous results
4. Naturally adaptive
```

The parent context makes DECISIONS between steps. This is intelligence, not routing.

## Token Budget Reference

| Component | Typical Cost | Frequency |
|-----------|-------------|-----------|
| System prompt | ~4K tokens | Every turn |
| CLAUDE.md | ~500-2K tokens | Every turn |
| Memory index | ~200-500 tokens | Every turn |
| Skill descriptions | ~50-100 each | Every turn |
| Tool schemas (loaded) | ~100-300 each | Every turn once loaded |
| Tool schemas (deferred) | ~20 each | Every turn (names only) |
| Sub-agent result | ~200-500 | Once when it returns |
| File read (typical) | ~500-5K | Once per read |
| Conversation message | ~100-500 | Persists until compaction |

Budget rule: Keep fixed costs (CLAUDE.md + memory + skills + tools) under 10K.
Leave ~190K for actual work.

## Decision Framework

```
"Should I use a sub-agent for this?"
├─ Will it take >3 tool calls? → Yes, use agent
├─ Do I need the raw output? → No, use agent (get summary)
├─ Is it independent of other work? → Can parallelize with agents
└─ Is it 1-2 quick operations? → Do it directly

"Should this be a skill?"
├─ Will I do this workflow again? → Yes, make a skill
├─ Is it a one-off task? → No, just do it
├─ Does it have a clear trigger? → Yes, skill with good description
└─ Is it project-specific? → Use .claude/commands/ instead

"Should this be a hook?"
├─ Must it ALWAYS be enforced? → Yes, hook (deterministic)
├─ Is it a soft preference? → No, put in CLAUDE.md
├─ Does it validate tool inputs? → PreToolUse hook
├─ Does it audit/log? → PostToolUse hook

"Should this be MCP?"
├─ External system integration? → If repeated, yes
├─ One-off API call? → Just use curl in Bash
├─ Needs persistent connection? → Yes, MCP
├─ Standard tool (file/git/search)? → Use built-in tools
```
