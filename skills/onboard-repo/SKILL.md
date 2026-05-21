Quickly understand an unfamiliar codebase by mapping its architecture, conventions, and key systems. Use when entering a new project for the first time, or when someone asks "how does this repo work?" or "onboard me to this codebase."

## Instructions

You are a codebase cartographer. Your job is to build a mental map of a repository as fast as possible, focusing on what matters for someone who needs to start contributing.

### Step 1: Identify the Project

Determine the target directory. If not specified, use the current working directory.

### Step 2: Parallel Discovery (launch all simultaneously)

Spawn 4 research agents in a SINGLE message:

**Agent 1 — Stack & Dependencies:**
```
Look at the project at [path]. Identify:
- Languages and versions
- Package manager and key dependencies
- Build system and scripts
- Development tooling (linters, formatters, test frameworks)
Report as a bullet list. Under 200 words.
```

**Agent 2 — Architecture & Structure:**
```
Look at the project at [path]. Map:
- Top-level directory structure and purpose of each dir
- Entry points (main files, index files, app bootstrapping)
- Layering pattern (MVC, hexagonal, feature-based, etc.)
- Key architectural boundaries (frontend/backend, services, shared code)
Report as a structured outline. Under 250 words.
```

**Agent 3 — Data & State:**
```
Look at the project at [path]. Find:
- Database schema / ORM models (look for migrations, schema files, models/)
- State management approach (Redux, Zustand, context, etc.)
- External service integrations (APIs, message queues, caches)
- Configuration management (env vars, config files)
Report as a bullet list. Under 200 words.
```

**Agent 4 — Conventions & Patterns:**
```
Look at the project at [path]. Identify:
- Code style (naming conventions, file naming, export patterns)
- Testing patterns (test location, fixtures, mocking approach)
- Error handling patterns
- Common abstractions and utilities (shared helpers, base classes)
- Git conventions (commit style, branch naming) from recent git log
Report as a bullet list. Under 200 words.
```

### Step 3: Synthesize the Onboarding Map

Combine all agent findings into a single structured overview:

```markdown
## Repo Onboarding: [project name]

### Quick Start
- How to install dependencies
- How to run the project
- How to run tests

### Tech Stack
[from Agent 1]

### Architecture
[from Agent 2, with ASCII diagram if helpful]

### Data Layer
[from Agent 3]

### Conventions to Follow
[from Agent 4 — the unwritten rules]

### Key Files to Know
- [file]: [why it matters]
- [file]: [why it matters]
- (list 5-10 most important files)

### Gotchas
- [non-obvious things that would trip up a newcomer]
```

### Design Philosophy

This skill demonstrates:
1. **Parallel fan-out** — 4 agents run simultaneously = 4x faster than sequential
2. **Focused queries** — each agent has a narrow domain = better results
3. **Context protection** — agents read dozens of files, parent gets ~800 words total
4. **Synthesis by coordinator** — parent combines findings, doesn't delegate understanding
