Analyze a pull request for quality, risk, and improvement opportunities using multi-agent review. Use when asked to review a PR, check PR quality, or analyze changes before merging.

## Instructions

You analyze pull requests by examining the diff, understanding context, and providing actionable feedback.

### Step 1: Get the PR

Determine the PR to review:
- If a PR URL or number is provided, use `gh pr view [number] --json title,body,files,additions,deletions` and `gh pr diff [number]`
- If on a branch, use `git diff main...HEAD` (adjust base branch as needed)
- If a diff is pasted, use that directly

### Step 2: Classify the Change

Determine change type (affects review focus):
- **Feature**: Focus on completeness, edge cases, testing
- **Bug fix**: Focus on root cause correctness, regression risk
- **Refactor**: Focus on behavior preservation, test coverage
- **Config/Infra**: Focus on environment safety, rollback plan
- **Dependencies**: Focus on security, breaking changes, bundle size

### Step 3: Multi-Agent Analysis

Launch 3 agents in parallel:

**Agent 1 — Logic Review:**
```
Review this diff for logic errors, edge cases, and correctness issues:

[paste relevant diff sections]

Check:
- Off-by-one errors
- Null/undefined handling
- Race conditions
- Missing error handling at boundaries
- Incomplete state transitions

Report issues with file:line references. Under 300 words.
```

**Agent 2 — Design Review:**
```
Review this diff for design quality:

[paste relevant diff sections]

Context: This is a [feature/bugfix/refactor] in a [tech stack] project.

Check:
- Does it follow existing patterns in the codebase?
- Are abstractions appropriate (not over/under-engineered)?
- Is the API surface clean?
- Are there naming issues?
- DRY violations?

Report as bullet points. Under 250 words.
```

**Agent 3 — Risk Assessment:**
```
Assess the risk profile of this change:

Files changed: [list]
Lines: +[additions] / -[deletions]

Evaluate:
- Blast radius (what could break)
- Rollback difficulty
- Data migration risk
- Performance implications
- Security surface changes

Rate overall risk: LOW / MEDIUM / HIGH with justification. Under 200 words.
```

### Step 4: Final Report

```markdown
## PR Analysis: [title]

### Summary
[1-2 sentence description of what this PR does]

### Change Type: [Feature|Bug Fix|Refactor|Config|Deps]

### Logic Issues
[from Agent 1 — issues with file:line references]

### Design Feedback
[from Agent 2 — improvement suggestions]

### Risk Assessment: [LOW|MEDIUM|HIGH]
[from Agent 3 — key risks]

### Testing Checklist
- [ ] [specific test scenarios based on the changes]
- [ ] [edge cases identified]
- [ ] [regression scenarios]

### Verdict
[APPROVE / REQUEST CHANGES / DISCUSS]
[1 sentence why]
```
