# Experiment 06: Runtime Orchestration vs Static Pipelines

## What This Teaches

- Why runtime decisions beat pre-defined chains
- How to generate prompts dynamically based on intermediate results
- The fundamental advantage of agent-native orchestration
- When static pipelines are still appropriate

## The Core Problem with Static Pipelines

LangChain/CrewAI/AutoGen pattern:
```python
# Defined at COMPILE TIME — before seeing the actual input
pipeline = (
    research_agent
    | planning_agent
    | coding_agent
    | review_agent
)

# Every input goes through ALL stages, same order, same depth
result = pipeline.invoke("fix the login bug")
result = pipeline.invoke("add a semicolon")  # same 4 stages!
```

Problems:
1. "Add a semicolon" doesn't need research or planning
2. "Rewrite the auth system" might need 3 rounds of research
3. Pipeline can't skip, repeat, or reorder stages
4. Intermediate failures require complex error-routing infrastructure
5. Each stage gets a FIXED prompt, regardless of what previous stages found

## Runtime Orchestration (Claude Code Native)

```
User: "fix the login bug"

Turn 1 (Coordinator thinks):
  "Login bug could be frontend or backend. Let me check both in parallel."
  → Spawns 2 research agents (frontend + backend)

Turn 2 (Results come back):
  "Backend agent found: auth middleware returns 401 for valid tokens
   after the recent JWT library upgrade."
  "Frontend is fine — the issue is backend-only."
  
  Decision: Skip frontend investigation. No planning needed — it's a 
  one-line fix in the JWT verification options.
  
  → Spawns executor directly (skipping planner — RUNTIME DECISION)

Turn 3 (Executor returns):
  "Fixed: added `algorithms: ['RS256']` to jwt.verify options"
  
  → Spawns validator
  
Turn 4 (Validator returns):
  "PASS — fix is correct and matches JWT library v4 API"
  
  → Reports to user
```

Compare: the static pipeline would have done Research → Plan → Code → Review
even though this only needed Research → Code → Verify.

## The Key Concept: Runtime-Generated Prompts

Static pipeline:
```
research_prompt = "Research the codebase"  # same every time
```

Runtime orchestration:
```
# Prompt generated AFTER seeing the actual task and initial findings:
research_prompt = f"""
  The login bug is in auth middleware (src/middleware/auth.ts).
  JWT verification fails for valid RS256 tokens since the v4 upgrade.
  
  Confirm: does jwt.verify() in that file specify the algorithms option?
  Check: are there other jwt.verify() calls that might have the same issue?
"""
```

The runtime prompt is:
- Informed by previous findings
- Targeted to the specific situation
- Much more likely to produce useful results
- Adapts to what was actually discovered

## When Static Pipelines ARE Appropriate

Static pipelines work when:
1. Every input needs the same processing (e.g., CI pipeline)
2. Steps have no meaningful decision points between them
3. The pipeline is simple (2-3 steps max)
4. Failure modes are well-known and handlers are pre-defined

Examples where static is fine:
- Format → Lint → Test → Deploy (CI/CD)
- Parse → Validate → Store (data pipeline)
- Transcribe → Translate → Summarize (content pipeline)

## Implementation Patterns

### Pattern 1: Conditional Depth

```
classify_complexity(task):
  trivial → do directly
  moderate → single agent
  complex → full pipeline

# The SAME system handles all complexity levels
# The decision is made AT RUNTIME based on the actual task
```

### Pattern 2: Iterative Deepening

```
attempt = research(broad_question)
if attempt.is_conclusive:
  proceed_to_execution
else:
  # Generate MORE SPECIFIC questions based on what we learned
  deeper_questions = generate_from(attempt.findings)
  attempt2 = research(deeper_questions)  # RUNTIME-GENERATED prompt
```

### Pattern 3: Adaptive Fan-Out

```
initial_research = quick_scan(codebase)

# Based on what the scan found, decide HOW MANY agents to spawn
if involves_frontend AND backend:
  spawn(frontend_agent, backend_agent)  # 2 agents
elif involves_multiple_services:
  spawn(agent_per_service)  # N agents, N determined at runtime
else:
  single_agent()  # 1 agent is enough
```

### Pattern 4: Bail-Out

```
plan = create_plan(task)
user_approves(plan)
result = execute(plan)
validation = validate(result)

if validation.failed:
  if validation.fixable:
    fix_and_retry()  # runtime decision to retry
  else:
    escalate_to_user(validation.issues)  # runtime decision to bail
    # Static pipeline would just fail or loop forever
```

## Why This Matters for Production

Static pipelines fail in production because:
- Real tasks have variable complexity
- Edge cases require different paths
- Intermediate failures need intelligent recovery
- Token budgets vary by task (can't waste budget on simple tasks)
- Users expect adaptive behavior, not rigid procedures

Runtime orchestration succeeds because:
- Each decision is informed by actual results
- Prompts are generated with full context
- Unnecessary steps are skipped (saving tokens and time)
- Failures are handled contextually
- The system adapts to what it discovers

## The Mental Model

Think of the coordinator as a SENIOR ENGINEER, not a PIPELINE:

Pipeline thinks: "Step 1 done, proceed to Step 2, proceed to Step 3..."
Senior engineer thinks: "What do I know now? What's the most efficient next action?"

The senior engineer might:
- Skip steps that aren't needed
- Go back and research more
- Ask for clarification
- Combine two steps into one
- Bail out early if the task is impossible

That's runtime orchestration.
