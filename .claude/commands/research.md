Research a topic using parallel sub-agents for context-efficient exploration.

## Instructions

The user wants to research: $ARGUMENTS

Launch 2-3 focused research agents in parallel (in a single message) to investigate different aspects of this topic. Each agent should:
- Have a specific, narrow question
- Search the codebase OR web as appropriate
- Return findings in under 200 words

After all agents return, synthesize their findings into a structured answer:

### Research: [topic]

**Key Findings:**
- [bullets]

**Architecture/Design Insight:**
- [how things connect]

**Recommended Next Steps:**
- [what to do with this knowledge]

Keep the final synthesis under 500 words. The goal is maximum insight with minimum context consumption.
