Create a new reusable Claude Code skill with proper structure, trigger description, and agent orchestration. Use when the user wants to create a new skill, define a new workflow, or automate a recurring multi-step process.

## Instructions

You are building a new skill. A skill is a reusable instruction set that loads into Claude's context on demand.

### Step 1: Define the Skill

Ask the user (or infer from context):
1. **What does this skill do?** (the workflow)
2. **When should it trigger?** (the description/routing signal)
3. **What tools/agents does it need?** (the implementation)

### Step 2: Write the SKILL.md

Create a file at `skills/<skill-name>/SKILL.md` with this structure:

```markdown
[First paragraph — the DESCRIPTION. This is routing metadata.
It determines when the skill triggers. Make it:
- Action-oriented (starts with a verb)
- Specific (not "helps with code" — what exactly?)
- Trigger-aware (include keywords users would say)]

## Instructions

[The full workflow Claude should follow when this skill is invoked]
```

### Skill Architecture Guidelines

**Description (first paragraph):**
- Maximum 2 sentences
- Must contain the key trigger words
- Think: "what would the user say that should invoke this?"
- Bad: "A helpful tool for code" (too vague)
- Good: "Systematically debug an issue using hypothesis-driven investigation with sub-agents"

**Instructions section:**
- Numbered steps (Claude follows them in order)
- Include sub-agent patterns where appropriate
- Specify output format
- List anti-patterns

**When to use sub-agents in a skill:**
- Research that requires reading many files → Explore agent
- Parallel independent investigations → multiple agents
- Code execution in isolation → worktree agent
- Single focused task → one general-purpose agent
- Simple direct action → no agent, just do it

### Step 3: Token Impact Assessment

Report to the user:
- Description cost: ~X tokens per turn (always loaded)
- Full skill cost: ~X tokens when invoked
- Sub-agent cost: ~X tokens per agent spawned
- Total typical invocation: ~X tokens

### Step 4: Create the File

Write the skill to the appropriate location:
- Global skills: `~/.claude/skills/<name>/SKILL.md`
- Project skills: `skills/<name>/SKILL.md`
- Slash commands: `.claude/commands/<name>.md`

### Skill vs Slash Command Decision

| Skill (SKILL.md) | Slash Command (.claude/commands/) |
|---|---|
| Can auto-trigger from description | Explicit invocation only |
| Global or plugin-based | Project-scoped |
| Complex routing logic | Simple direct workflows |
| Composable with other skills | Standalone |

### Template for Common Skill Patterns

**Research Skill:**
```
[description]
## Instructions
1. Identify target
2. Spawn parallel research agents
3. Synthesize findings
4. Report structured result
```

**Action Skill:**
```
[description]
## Instructions
1. Validate preconditions
2. Plan changes
3. Execute (with worktree if risky)
4. Validate result
5. Report
```

**Analysis Skill:**
```
[description]
## Instructions
1. Gather data (agents for large scope)
2. Classify/categorize
3. Identify patterns
4. Report with recommendations
```
