# Deep Code Review

Perform a thorough code review using an agent team: researcher gathers context, reviewer analyzes quality, security checker audits safety. Use when asked to deeply review code, audit a PR, or do a comprehensive code review that goes beyond surface-level linting.

## Instructions

You are performing a deep code review using a multi-agent approach. This gives higher quality results than a single-pass review because each agent has focused attention.

### Step 1: Identify the target

Determine what to review:
- If a PR number or branch is given, use `git diff` to get the changes
- If a file path is given, read the file
- If no target is specified, ask the user

### Step 2: Launch parallel research agents

Spawn TWO agents in parallel (in a single message):

**Agent 1 - Context Researcher:**
```
Research the surrounding code context for the files being changed.
For each modified file, find:
- What calls this code (dependents)
- What this code calls (dependencies)
- Related test files
- Similar patterns elsewhere in the codebase
Report: for each file, list dependents, dependencies, test coverage status, and similar patterns found.
Under 400 words.
```

**Agent 2 - Security Auditor:**
```
Audit these changes for security issues:
[paste the diff or file content]

Check for:
- Injection vulnerabilities (SQL, command, XSS)
- Authentication/authorization gaps
- Sensitive data exposure
- Input validation gaps
- Race conditions
- Dependency vulnerabilities

Report: list of findings with severity (Critical/High/Medium/Low), affected line, and fix suggestion.
If no issues found, say PASS. Under 300 words.
```

### Step 3: Synthesize and review

After both agents return, YOU (the coordinator) synthesize their findings and produce the final review covering:

1. **Summary** — What the change does (1-2 sentences)
2. **Architecture Impact** — How it fits into the system (informed by researcher)
3. **Security** — Issues found (informed by auditor)
4. **Code Quality** — Logic errors, naming, patterns, DRY violations
5. **Testing** — Is it tested? What's missing?
6. **Verdict** — APPROVE / REQUEST CHANGES / NEEDS DISCUSSION

### Output Format

```markdown
## Deep Review: [file or PR title]

### Summary
[what it does]

### Architecture Impact
[how it connects to the rest of the system]

### Security Findings
[from security auditor, with severity]

### Code Quality
[your analysis after reading the code with full context]

### Testing Gaps
[what's not tested that should be]

### Verdict: [APPROVE | REQUEST CHANGES | NEEDS DISCUSSION]
[1-2 sentence justification]
```
