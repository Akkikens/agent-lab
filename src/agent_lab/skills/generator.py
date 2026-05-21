"""
Skill generator for Claude Code projects.

Skills are reusable instruction sets that load into Claude's context
on demand. This module helps create properly structured skills with
good descriptions (routing metadata) and clear instructions.
"""

from pathlib import Path
from textwrap import dedent

SKILL_TEMPLATES = {
    "research": {
        "description_template": (
            "Research {topic} using parallel sub-agents for comprehensive codebase exploration."
            " Use when asked to investigate, explore, or understand {topic}."
        ),
        "instructions_template": dedent("""
            ## Instructions

            ### Step 1: Identify Scope
            Determine what to research and where to look.

            ### Step 2: Parallel Research
            Launch 2-3 focused research agents simultaneously:

            **Agent 1:** [Aspect A of the topic]
            **Agent 2:** [Aspect B of the topic]
            **Agent 3:** [Related context/implications]

            ### Step 3: Synthesize
            Combine findings into a structured report:
            - Key findings
            - Architecture insights
            - Recommendations
            - Gotchas

            Keep final output under 500 words.
        """),
    },
    "action": {
        "description_template": (
            "Execute {topic} with planning, implementation, and validation."
            " Use when asked to build, implement, or create {topic}."
        ),
        "instructions_template": dedent("""
            ## Instructions

            ### Step 1: Validate Preconditions
            Ensure everything needed is in place before starting.

            ### Step 2: Plan
            Create a concrete implementation plan with ordered steps.

            ### Step 3: Execute
            Implement changes using worktree isolation for safety.

            ### Step 4: Validate
            Spawn an independent validator to verify correctness.

            ### Step 5: Report
            Summarize what was done, files changed, and how to verify.
        """),
    },
    "analysis": {
        "description_template": (
            "Analyze {topic} for quality, patterns, and improvement opportunities."
            " Use when asked to review, audit, or assess {topic}."
        ),
        "instructions_template": dedent("""
            ## Instructions

            ### Step 1: Gather Data
            Use sub-agents to collect information from multiple sources in parallel.

            ### Step 2: Classify
            Categorize findings by severity/importance.

            ### Step 3: Identify Patterns
            Look for recurring issues or themes.

            ### Step 4: Report
            Structured output with findings, recommendations, and priority actions.
        """),
    },
}


def generate_skill(
    name: str,
    description: str,
    output_dir: str | Path,
    template: str = "research",
    topic: str = "",
    custom_instructions: str = "",
) -> Path:
    """
    Generate a new Claude Code skill.

    Args:
        name: Skill name (used as directory name)
        description: Trigger description (first paragraph of SKILL.md)
        output_dir: Where to create the skill directory
        template: One of 'research', 'action', 'analysis'
        topic: Topic to fill into template
        custom_instructions: Override template instructions

    Returns:
        Path to the created SKILL.md

    Example:
        ```python
        generate_skill(
            name="api-audit",
            description="Audit API endpoints for security and performance issues.",
            output_dir="./skills",
            template="analysis",
            topic="API endpoints",
        )
        ```
    """
    output_path = Path(output_dir) / name
    output_path.mkdir(parents=True, exist_ok=True)

    if custom_instructions:
        instructions = custom_instructions
    elif template in SKILL_TEMPLATES:
        instructions = SKILL_TEMPLATES[template]["instructions_template"]
        if topic:
            instructions = instructions.replace("{topic}", topic)
    else:
        instructions = SKILL_TEMPLATES["research"]["instructions_template"]

    content = f"{description}\n{instructions}"

    skill_file = output_path / "SKILL.md"
    skill_file.write_text(content)

    return skill_file


def generate_slash_command(
    name: str,
    description: str,
    instructions: str,
    output_dir: str | Path,
) -> Path:
    """
    Generate a Claude Code slash command (.claude/commands/).

    Slash commands are project-scoped, explicitly invoked as /project:<name>.

    Args:
        name: Command name (invoked as /project:<name>)
        description: What the command does (first line)
        instructions: Full instructions (supports $ARGUMENTS placeholder)
        output_dir: The .claude/commands/ directory

    Returns:
        Path to the created command file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    content = f"{description}\n\n## Instructions\n\n{instructions}"

    cmd_file = output_path / f"{name}.md"
    cmd_file.write_text(content)

    return cmd_file
