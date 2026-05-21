"""
Agent definitions for the coordinator-worker pattern.

These classes define agent ROLES, not implementations. They generate
prompts and configurations for Claude Code's native sub-agent system.

Architecture:
    Unlike LangChain agents which wrap LLM calls in Python,
    these agents generate PROMPTS that Claude Code's Agent tool executes.
    The execution happens in Claude Code's runtime, not in Python.

    This is intentional — Claude Code's runtime handles:
    - Context window management
    - Tool permissions
    - Worktree isolation
    - Parallel execution

    We just define the roles and prompt templates.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentType(Enum):
    EXPLORE = "Explore"
    PLAN = "Plan"
    GENERAL = "general-purpose"


class ModelTier(Enum):
    OPUS = "opus"
    SONNET = "sonnet"
    HAIKU = "haiku"


@dataclass
class AgentConfig:
    """Configuration for spawning a sub-agent in Claude Code."""

    description: str
    prompt: str
    subagent_type: AgentType = AgentType.GENERAL
    model: ModelTier | None = None
    isolation: str | None = None
    run_in_background: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to the format Claude Code's Agent tool expects."""
        result: dict[str, Any] = {
            "description": self.description,
            "prompt": self.prompt,
            "subagent_type": self.subagent_type.value,
        }
        if self.model:
            result["model"] = self.model.value
        if self.isolation:
            result["isolation"] = self.isolation
        if self.run_in_background:
            result["run_in_background"] = True
        return result


@dataclass
class Researcher:
    """
    Research agent — explores codebases and gathers information.

    Use when you need to understand something without polluting
    the parent context with dozens of file reads.

    Token economics:
        - Spawns with ~4K system overhead
        - Reads N files internally (cost stays in child)
        - Returns ~200-500 token summary to parent
        - Net savings: avoids 5-20K tokens in parent context
    """

    question: str
    scope: str = ""
    max_words: int = 200
    search_type: AgentType = AgentType.EXPLORE

    def build(self) -> AgentConfig:
        prompt = f"""Research question: {self.question}

{f"Scope: {self.scope}" if self.scope else ""}

Report format:
- Answer (2-3 sentences)
- Key files found (paths + purpose)
- Architecture insight (how it connects)
- Gotchas (non-obvious things)

Keep response under {self.max_words} words."""

        return AgentConfig(
            description=f"Research: {self.question[:50]}",
            prompt=prompt,
            subagent_type=self.search_type,
        )


@dataclass
class Planner:
    """
    Planning agent — creates implementation plans from research findings.

    Critical rule: The caller must SYNTHESIZE research findings before
    passing them to the planner. Never pipe raw agent output directly.

    Token economics:
        - Input: ~500-1000 tokens (your synthesis + goal)
        - Output: ~300-800 tokens (structured plan)
        - Runs once per task
    """

    goal: str
    context: str
    constraints: list[str] = field(default_factory=list)

    def build(self) -> AgentConfig:
        constraints_text = "\n".join(f"- {c}" for c in self.constraints) if self.constraints else "None specified."

        prompt = f"""Goal: {self.goal}

Context from research:
{self.context}

Constraints:
{constraints_text}

Produce:
1. Ordered list of changes (file path + what changes)
2. Dependencies between steps (what must happen first)
3. Risk assessment (what could go wrong)
4. Test strategy (how to verify each step)

Be specific — include exact file paths and function names."""

        return AgentConfig(
            description=f"Plan: {self.goal[:50]}",
            prompt=prompt,
            subagent_type=AgentType.PLAN,
        )


@dataclass
class Executor:
    """
    Execution agent — implements a specific, well-defined change.

    Executors are scoped to ONE logical change. For multiple changes,
    spawn multiple executors (parallel if independent).

    Use `isolated=True` for risky changes — creates a git worktree
    so changes can be reviewed before merging.

    Token economics:
        - Input: ~300-500 tokens (specific instructions)
        - Internal: variable (reads files, writes code)
        - Output: ~200-400 tokens (what was done)
        - Worktree adds ~0 tokens but enables safe rollback
    """

    task: str
    file_path: str
    instructions: str
    patterns: str = ""
    isolated: bool = False
    verify_command: str = ""

    def build(self) -> AgentConfig:
        prompt = f"""Task: {self.task}

File: {self.file_path}
{f"Follow these patterns: {self.patterns}" if self.patterns else ""}

Instructions:
{self.instructions}

{f"After implementing, verify by running: {self.verify_command}" if self.verify_command else ""}

Report what you changed and any issues encountered."""

        return AgentConfig(
            description=f"Implement: {self.task[:50]}",
            prompt=prompt,
            subagent_type=AgentType.GENERAL,
            isolation="worktree" if self.isolated else None,
        )


@dataclass
class Validator:
    """
    Validation agent — independently verifies executed work.

    Critical property: The validator NEVER sees the executor's reasoning.
    It only sees the resulting code. This prevents confirmation bias.

    Token economics:
        - Input: ~300-500 tokens (requirements + file paths)
        - Internal: reads changed files, possibly runs tests
        - Output: ~200-400 tokens (PASS/FAIL + issues)
    """

    target: str
    requirements: list[str]
    check_security: bool = True
    check_patterns: bool = True

    def build(self) -> AgentConfig:
        requirements_text = "\n".join(f"  {i+1}. {r}" for i, r in enumerate(self.requirements))

        checks = ["Correctness: Does it do what's required?"]
        if self.check_security:
            checks.append("Safety: Any security issues? (injection, XSS, auth bypass)")
        if self.check_patterns:
            checks.append("Consistency: Does it match existing patterns?")
        checks.append("Edge cases: What inputs could break it?")
        checks_text = "\n".join(f"- {c}" for c in checks)

        prompt = f"""Review the changes at: {self.target}

Requirements that must be met:
{requirements_text}

Check for:
{checks_text}

Report:
- PASS or FAIL
- Issues found (with file:line references)
- Suggested fixes (if FAIL)

Be strict. False negatives (missing bugs) are worse than false positives."""

        return AgentConfig(
            description=f"Validate: {self.target[:50]}",
            prompt=prompt,
            subagent_type=AgentType.GENERAL,
        )


@dataclass
class Coordinator:
    """
    Coordinator pattern — NOT a separate agent, but a pipeline builder.

    The coordinator assembles agent configs into an execution plan.
    In Claude Code, the PARENT CONTEXT is the coordinator. This class
    helps you define the pipeline structure, but execution happens
    in the Claude Code runtime.

    For Python-native execution (outside Claude Code), use with
    the Anthropic SDK directly.
    """

    task: str
    agents: list[AgentConfig] = field(default_factory=list)

    def add_research(self, question: str, scope: str = "") -> "Coordinator":
        self.agents.append(Researcher(question=question, scope=scope).build())
        return self

    def add_plan(self, goal: str, context: str, constraints: list[str] | None = None) -> "Coordinator":
        self.agents.append(Planner(goal=goal, context=context, constraints=constraints or []).build())
        return self

    def add_execution(
        self, task: str, file_path: str, instructions: str, isolated: bool = False
    ) -> "Coordinator":
        self.agents.append(
            Executor(task=task, file_path=file_path, instructions=instructions, isolated=isolated).build()
        )
        return self

    def add_validation(self, target: str, requirements: list[str]) -> "Coordinator":
        self.agents.append(Validator(target=target, requirements=requirements).build())
        return self

    def get_pipeline(self) -> list[dict[str, Any]]:
        """Get the full pipeline as a list of agent configs."""
        return [a.to_dict() for a in self.agents]

    def describe(self) -> str:
        """Human-readable pipeline description."""
        lines = [f"Pipeline: {self.task}", ""]
        for i, agent in enumerate(self.agents, 1):
            lines.append(f"  Step {i}: [{agent.subagent_type.value}] {agent.description}")
        return "\n".join(lines)
