"""Tests for the SDK runtime module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_lab.orchestrator.agents import AgentConfig, Researcher
from agent_lab.orchestrator.pipeline import Pipeline
from agent_lab.orchestrator.runtime import (
    AgentResult,
    PipelineResult,
    Runtime,
    StepResult,
    _resolve_model_id,
)


def _mock_response(text="Agent response", input_tokens=100, output_tokens=50):
    """Create a mock Anthropic API response."""
    mock = MagicMock()
    mock.content = [MagicMock(type="text", text=text)]
    mock.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    mock.stop_reason = "end_turn"
    return mock


def test_resolve_model_id():
    assert _resolve_model_id("opus") == "claude-opus-4-6-20250514"
    assert _resolve_model_id("sonnet") == "claude-sonnet-4-6-20250514"
    assert _resolve_model_id("haiku") == "claude-haiku-4-5-20251001"
    assert _resolve_model_id("claude-sonnet-4-6-20250514") == "claude-sonnet-4-6-20250514"


def test_agent_result_total_tokens():
    result = AgentResult(
        agent_description="test",
        content="hello",
        model="sonnet",
        input_tokens=100,
        output_tokens=50,
    )
    assert result.total_tokens == 150


def test_step_result_combined_content():
    step = StepResult(
        step_name="Research",
        agent_results=[
            AgentResult(agent_description="Agent A", content="Found X", model="s", input_tokens=10, output_tokens=5),
            AgentResult(agent_description="Agent B", content="Found Y", model="s", input_tokens=10, output_tokens=5),
        ],
    )
    combined = step.combined_content
    assert "Agent A" in combined
    assert "Found X" in combined
    assert "Agent B" in combined
    assert "Found Y" in combined


def test_step_result_total_tokens():
    step = StepResult(
        step_name="Test",
        agent_results=[
            AgentResult(agent_description="A", content="", model="s", input_tokens=100, output_tokens=50),
            AgentResult(agent_description="B", content="", model="s", input_tokens=200, output_tokens=100),
        ],
    )
    assert step.total_tokens == 450


def test_pipeline_result_summary():
    result = PipelineResult(
        pipeline_name="Test Pipeline",
        step_results=[
            StepResult(step_name="Step 1", agent_results=[
                AgentResult(agent_description="A", content="", model="s", input_tokens=100, output_tokens=50),
            ]),
            StepResult(step_name="Step 2", skipped=True),
        ],
        total_duration_ms=500,
    )
    summary = result.summary()
    assert "Test Pipeline" in summary
    assert "500ms" in summary
    assert "SKIPPED" in summary
    assert result.succeeded is False


def test_pipeline_result_all_succeeded():
    result = PipelineResult(
        pipeline_name="Good",
        step_results=[
            StepResult(step_name="A", agent_results=[
                AgentResult(agent_description="x", content="", model="s", input_tokens=10, output_tokens=5),
            ]),
        ],
    )
    assert result.succeeded is True


@pytest.mark.asyncio
async def test_runtime_run_agent():
    with patch("agent_lab.orchestrator.runtime.anthropic") as mock_anthropic:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=_mock_response("Result text"))
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        runtime = Runtime(model="sonnet")
        config = AgentConfig(description="Test agent", prompt="Do something")
        result = await runtime.run_agent(config)

        assert result.content == "Result text"
        assert result.agent_description == "Test agent"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        mock_client.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_runtime_execute_pipeline():
    with patch("agent_lab.orchestrator.runtime.anthropic") as mock_anthropic:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=[
                _mock_response("Research result 1"),
                _mock_response("Research result 2"),
                _mock_response("Plan result"),
            ]
        )
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        runtime = Runtime(model="sonnet")
        pipeline = Pipeline("Test task")
        pipeline.add_parallel("Research", [
            Researcher(question="Q1").build(),
            Researcher(question="Q2").build(),
        ])
        pipeline.add_sequential("Plan", [
            AgentConfig(description="Plan it", prompt="Make a plan"),
        ])

        result = await runtime.execute(pipeline)

        assert result.pipeline_name == "Test task"
        assert len(result.step_results) == 2
        assert result.step_results[0].step_name == "Research"
        assert len(result.step_results[0].agent_results) == 2
        assert result.step_results[1].step_name == "Plan"
        assert "Research" in pipeline.context


@pytest.mark.asyncio
async def test_runtime_conditional_skip():
    with patch("agent_lab.orchestrator.runtime.anthropic") as mock_anthropic:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=_mock_response("done"))
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        runtime = Runtime(model="sonnet")
        pipeline = Pipeline("Conditional test")
        pipeline.add_conditional(
            "Maybe",
            agents=[AgentConfig(description="opt", prompt="do it")],
            condition=lambda ctx: ctx.get("go", False),
        )

        result = await runtime.execute(pipeline)
        assert result.step_results[0].skipped is True
        mock_client.messages.create.assert_not_called()


@pytest.mark.asyncio
async def test_runtime_run_single():
    with patch("agent_lab.orchestrator.runtime.anthropic") as mock_anthropic:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=_mock_response("Quick answer"))
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        runtime = Runtime()
        result = await runtime.run_single("What is 2+2?", description="math")

        assert result.content == "Quick answer"
        assert result.agent_description == "math"


def test_runtime_requires_anthropic():
    with patch("agent_lab.orchestrator.runtime.anthropic", None):
        with pytest.raises(ImportError, match="anthropic package is required"):
            Runtime()
