# Researcher Agent

## Purpose
Deep codebase research that produces a concise summary without polluting the caller's context.

## When to Use
- Exploring unfamiliar code (many file reads needed)
- Answering "how does X work?" questions
- Finding all usages/implementations of a pattern
- Understanding data flow across multiple files

## Architecture Notes

This agent:
- Receives a focused research question
- Has full access to Read, Bash (grep/find), and WebSearch
- Does as many tool calls as needed internally
- Returns ONLY a concise structured answer

The caller's context is protected from all intermediate file reads.

## Invocation Pattern

```
Agent({
  description: "Research: [topic]",
  subagent_type: "Explore",  // or "general-purpose" for broader work
  prompt: `
    Research question: [specific question]
    
    Codebase context: [relevant paths, language, framework]
    
    Report format:
    - Answer (2-3 sentences)
    - Key files (paths + what they do)
    - Architecture insight (how it fits together)
    - Gotchas (non-obvious things)
    
    Keep response under 300 words.
  `
})
```

## Why This Pattern Works

1. **Context protection**: 20 file reads happen in child, parent gets 300 words
2. **Parallelizable**: Launch multiple researchers for independent questions
3. **Composable**: Researcher output feeds into planner or executor
4. **Token efficient**: ~300 tokens result vs ~20K tokens of raw file content

## Anti-patterns

- DON'T use for work you'll need to continue (child has no continuity)
- DON'T use when you need to edit files (use executor instead)
- DON'T pass vague questions ("look at the code") — be specific
- DON'T ask it to do the thinking for you — synthesize its findings yourself
