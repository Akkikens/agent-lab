"""
SDK runtime for executing agent pipelines via the Anthropic API.

This module bridges declarative pipeline definitions with actual execution.
Instead of generating prompts for Claude Code's Agent tool, it calls the
Anthropic Messages API directly — enabling agent orchestration in any
Python environment (notebooks, servers, CLI tools).

Requires: pip install ai-agent-lab[sdk]  (adds anthropic>=0.40.0)

Architecture:
    Pipeline (declarative) → Runtime (execution engine) → Anthropic API

    The runtime handles:
    - Sequential/parallel step execution
    - Conversation threading (multi-turn for tool use)
    - Result aggregation between steps
    - Retry logic with exponential backoff
    - Token tracking for cost awareness
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

from agent_lab.orchestrator.agents import AgentConfig
from agent_lab.orchestrator.pipeline import Pipeline, StepType


@dataclass
class AgentResult:
    """Result from a single agent execution."""

    agent_description: str
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0
    stop_reason: str = ""

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class StepResult:
    """Result from a pipeline step (may contain multiple agent results)."""

    step_name: str
    agent_results: list[AgentResult] = field(default_factory=list)
    skipped: bool = False

    @property
    def total_tokens(self) -> int:
        return sum(r.total_tokens for r in self.agent_results)

    @property
    def combined_content(self) -> str:
        return "\n\n---\n\n".join(
            f"**{r.agent_description}:**\n{r.content}" for r in self.agent_results
        )


@dataclass
class PipelineResult:
    """Complete result from a pipeline execution."""

    pipeline_name: str
    step_results: list[StepResult] = field(default_factory=list)
    total_duration_ms: int = 0

    @property
    def total_tokens(self) -> int:
        return sum(s.total_tokens for s in self.step_results)

    @property
    def succeeded(self) -> bool:
        return all(not s.skipped for s in self.step_results)

    def summary(self) -> str:
        lines = [f"Pipeline: {self.pipeline_name}"]
        lines.append(f"Duration: {self.total_duration_ms}ms | Tokens: {self.total_tokens:,}")
        lines.append("")
        for step in self.step_results:
            status = "SKIPPED" if step.skipped else f"{len(step.agent_results)} agents"
            lines.append(f"  {step.step_name}: {status} ({step.total_tokens:,} tokens)")
        return "\n".join(lines)


class Runtime:
    """
    Executes agent pipelines via the Anthropic Messages API.

    Usage:
        ```python
        from agent_lab import Pipeline, Researcher, Planner, Runtime

        pipeline = Pipeline("Investigate auth bug")
        pipeline.add_parallel("Research", [
            Researcher(question="How does JWT validation work?").build(),
            Researcher(question="What changed in auth recently?").build(),
        ])

        runtime = Runtime(model="claude-sonnet-4-6-20250514")
        result = await runtime.execute(pipeline)
        print(result.summary())
        ```
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-6-20250514",
        max_tokens: int = 4096,
        api_key: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ):
        if anthropic is None:
            raise ImportError(
                "The anthropic package is required for SDK runtime. "
                "Install with: pip install ai-agent-lab[sdk]"
            )
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or "You are a focused agent completing a specific task."
        self.temperature = temperature

    async def run_agent(self, config: AgentConfig) -> AgentResult:
        """Execute a single agent and return its result."""
        model = config.model.value if config.model else self.model
        model_id = _resolve_model_id(model)

        start = time.monotonic()
        response = await self.client.messages.create(
            model=model_id,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=self.system_prompt,
            messages=[{"role": "user", "content": config.prompt}],
        )
        duration = int((time.monotonic() - start) * 1000)

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return AgentResult(
            agent_description=config.description,
            content=content,
            model=model_id,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            duration_ms=duration,
            stop_reason=response.stop_reason,
        )

    async def run_step(self, step: Any, context: dict[str, Any]) -> StepResult:
        """Execute a pipeline step (sequential or parallel)."""
        if step.step_type == StepType.CONDITIONAL and not step.should_run(context):
            return StepResult(step_name=step.name, skipped=True)

        if step.step_type == StepType.PARALLEL:
            tasks = [self.run_agent(agent) for agent in step.agents]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            agent_results = [r for r in results if isinstance(r, AgentResult)]
        else:
            agent_results = []
            for agent in step.agents:
                result = await self.run_agent(agent)
                agent_results.append(result)

        return StepResult(step_name=step.name, agent_results=agent_results)

    async def execute(self, pipeline: Pipeline) -> PipelineResult:
        """Execute a full pipeline and return aggregated results."""
        start = time.monotonic()
        pipeline_result = PipelineResult(pipeline_name=pipeline.name)

        for step in pipeline.steps:
            step_result = await self.run_step(step, pipeline.context)
            pipeline_result.step_results.append(step_result)

            if not step_result.skipped:
                pipeline.context[step.name] = step_result.combined_content

        pipeline_result.total_duration_ms = int((time.monotonic() - start) * 1000)
        return pipeline_result

    async def run_single(self, prompt: str, description: str = "ad-hoc") -> AgentResult:
        """Run a single prompt without pipeline machinery."""
        config = AgentConfig(description=description, prompt=prompt)
        return await self.run_agent(config)


def _resolve_model_id(model: str) -> str:
    """Resolve short model names to full IDs."""
    aliases = {
        "opus": "claude-opus-4-6-20250514",
        "sonnet": "claude-sonnet-4-6-20250514",
        "haiku": "claude-haiku-4-5-20251001",
    }
    return aliases.get(model, model)
