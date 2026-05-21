Audit the current context window utilization and identify optimization opportunities.

## Instructions

Perform a context window health check for the current session. Report:

### 1. Fixed Costs (loaded every turn)

Check and estimate token cost for:
- CLAUDE.md content → read the file, count approximate tokens (chars/4)
- Memory index (MEMORY.md) → read the file, estimate
- Number of skills with descriptions loaded (from your system prompt)
- Number of tool schemas currently loaded

### 2. Variable Costs (current session)

Estimate based on conversation length:
- Approximate conversation turns so far
- Whether compaction has likely occurred
- Largest tool results in recent history

### 3. Optimization Recommendations

Based on the audit:
- Is CLAUDE.md too long? (>500 tokens = yellow, >1000 = red)
- Is MEMORY.md too long? (>100 lines = warning)
- Are there unused tool schemas loaded?
- Should some content be in memory instead of CLAUDE.md?
- Would sub-agents help isolate expensive operations?

### Output Format

```
## Context Audit

### Fixed Costs (per turn)
| Component | Est. Tokens | Status |
|-----------|-------------|--------|
| System prompt | ~4000 | fixed |
| CLAUDE.md | ~XXX | [ok/warning/high] |
| Memory index | ~XXX | [ok/warning/high] |
| Skill descriptions | ~XXX | ok |
| Tool schemas | ~XXX | ok |
| **Total fixed** | **~XXX** | |

### Variable State
- Conversation depth: ~X turns
- Compaction: [likely/unlikely]
- Available headroom: ~[estimate]

### Recommendations
- [actionable suggestions]
```
