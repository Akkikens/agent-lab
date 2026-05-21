"""
Pipeline execution engine for agent orchestration.

This module provides two modes:
1. DECLARATIVE MODE: Define pipelines that Claude Code's runtime executes
2. SDK MODE: Execute pipelines directly via the Anthropic Python SDK

The declarative mode generates Agent tool configs.
The SDK mode actually runs the agents (requires anthropic API key).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from agent_lab.orchestrator.agents import AgentConfig


class StepType(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


@dataclass
class PipelineStep:
    """A single step in the execution pipeline."""

    name: str
    agents: list[AgentConfig]
    step_type: StepType = StepType.SEQUENTIAL
    condition: Callable[[dict], bool] | None = None
    max_retries: int = 0

    def is_parallel(self) -> bool:
        return self.step_type == StepType.PARALLEL

    def should_run(self, context: dict) -> bool:
        if self.condition is None:
            return True
        return self.condition(context)


@dataclass
class Pipeline:
    """
    Orchestration pipeline that composes agents into a workflow.

    Design philosophy:
        Unlike static LangChain chains, this pipeline supports
        RUNTIME DECISIONS between steps. Steps can be conditional,
        parallel, or sequential based on intermediate results.

    Example:
        ```python
        pipeline = Pipeline("Fix bug in auth")
        pipeline.add_parallel("Research", [
            Researcher(question="How does auth middleware work?").build(),
            Researcher(question="What changed in last 5 commits?").build(),
        ])
        pipeline.add_sequential("Plan", [
            Planner(goal="Fix JWT validation", context="...").build(),
        ])
        pipeline.add_conditional("Execute",
            agents=[Executor(task="...", file_path="...", instructions="...").build()],
            condition=lambda ctx: ctx.get("plan_approved", False)
        )
        pipeline.add_sequential("Validate", [
            Validator(target="src/auth.ts", requirements=["JWT validates"]).build(),
        ])
        ```
    """

    name: str
    steps: list[PipelineStep] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def add_sequential(self, name: str, agents: list[AgentConfig], max_retries: int = 0) -> "Pipeline":
        self.steps.append(PipelineStep(
            name=name,
            agents=agents,
            step_type=StepType.SEQUENTIAL,
            max_retries=max_retries,
        ))
        return self

    def add_parallel(self, name: str, agents: list[AgentConfig]) -> "Pipeline":
        self.steps.append(PipelineStep(
            name=name,
            agents=agents,
            step_type=StepType.PARALLEL,
        ))
        return self

    def add_conditional(
        self,
        name: str,
        agents: list[AgentConfig],
        condition: Callable[[dict], bool],
        max_retries: int = 0,
    ) -> "Pipeline":
        self.steps.append(PipelineStep(
            name=name,
            agents=agents,
            step_type=StepType.CONDITIONAL,
            condition=condition,
            max_retries=max_retries,
        ))
        return self

    def describe(self) -> str:
        """Human-readable pipeline visualization."""
        lines = [f"Pipeline: {self.name}", "=" * (len(self.name) + 10), ""]
        for i, step in enumerate(self.steps, 1):
            prefix = "├" if i < len(self.steps) else "└"
            step_icon = {
                StepType.SEQUENTIAL: "→",
                StepType.PARALLEL: "⇉",
                StepType.CONDITIONAL: "?→",
            }[step.step_type]

            lines.append(f"  {prefix}─ Step {i}: {step_icon} {step.name}")
            for agent in step.agents:
                lines.append(f"  │    └─ [{agent.subagent_type.value}] {agent.description}")
            lines.append("")
        return "\n".join(lines)

    def to_claude_code_plan(self) -> str:
        """
        Generate a Claude Code execution plan as markdown.

        This output can be pasted into a Claude Code session
        and it will know how to execute each step using the Agent tool.
        """
        lines = [f"# Execution Plan: {self.name}", ""]

        for i, step in enumerate(self.steps, 1):
            lines.append(f"## Step {i}: {step.name}")
            if step.step_type == StepType.PARALLEL:
                lines.append("*Launch these agents simultaneously (single message):*")
            elif step.step_type == StepType.CONDITIONAL:
                lines.append("*Only proceed if previous step succeeded:*")
            lines.append("")

            for agent in step.agents:
                lines.append(f"### Agent: {agent.description}")
                lines.append(f"- Type: `{agent.subagent_type.value}`")
                if agent.model:
                    lines.append(f"- Model: `{agent.model.value}`")
                if agent.isolation:
                    lines.append(f"- Isolation: `{agent.isolation}`")
                lines.append("- Prompt:")
                lines.append("```")
                lines.append(agent.prompt)
                lines.append("```")
                lines.append("")

            if step.max_retries > 0:
                lines.append(f"*Retry up to {step.max_retries} times if validation fails.*")
                lines.append("")

        return "\n".join(lines)

    def estimate_tokens(self) -> dict[str, int]:
        """Estimate token cost for this pipeline."""
        estimates = {
            "fixed_overhead_per_agent": 4000,
            "prompt_tokens": 0,
            "estimated_result_tokens": 0,
            "total_agents": 0,
        }

        for step in self.steps:
            for agent in step.agents:
                estimates["total_agents"] += 1
                estimates["prompt_tokens"] += len(agent.prompt) // 4
                estimates["estimated_result_tokens"] += 300

        estimates["total_estimated"] = (
            estimates["fixed_overhead_per_agent"] * estimates["total_agents"]
            + estimates["prompt_tokens"]
            + estimates["estimated_result_tokens"]
        )

        return estimates
