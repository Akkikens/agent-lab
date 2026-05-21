"""Tests for the orchestrator module."""

from agent_lab.orchestrator.agents import (
    AgentType,
    Coordinator,
    Executor,
    Planner,
    Researcher,
    Validator,
)
from agent_lab.orchestrator.pipeline import Pipeline, StepType


def test_researcher_build():
    r = Researcher(question="How does auth work?", scope="src/auth/")
    config = r.build()

    assert config.subagent_type == AgentType.EXPLORE
    assert "How does auth work?" in config.prompt
    assert "src/auth/" in config.prompt
    assert config.description.startswith("Research:")


def test_planner_build():
    p = Planner(
        goal="Add rate limiting",
        context="The API uses Express with middleware pattern",
        constraints=["Must not break existing routes", "Use Redis for state"],
    )
    config = p.build()

    assert config.subagent_type == AgentType.PLAN
    assert "Add rate limiting" in config.prompt
    assert "Express with middleware" in config.prompt
    assert "Redis for state" in config.prompt


def test_executor_build():
    e = Executor(
        task="Add rate limit middleware",
        file_path="src/middleware/rate-limit.ts",
        instructions="Create a new middleware using sliding window algorithm",
        isolated=True,
        verify_command="npm test",
    )
    config = e.build()

    assert config.subagent_type == AgentType.GENERAL
    assert config.isolation == "worktree"
    assert "rate-limit.ts" in config.prompt
    assert "npm test" in config.prompt


def test_executor_no_isolation():
    e = Executor(
        task="Fix typo",
        file_path="README.md",
        instructions="Change 'teh' to 'the'",
        isolated=False,
    )
    config = e.build()

    assert config.isolation is None


def test_validator_build():
    v = Validator(
        target="src/middleware/rate-limit.ts",
        requirements=["Returns 429 after limit exceeded", "Resets after window"],
        check_security=True,
    )
    config = v.build()

    assert "PASS or FAIL" in config.prompt
    assert "429" in config.prompt
    assert "security" in config.prompt.lower()


def test_coordinator_builder():
    coord = Coordinator(task="Add rate limiting")
    coord.add_research("How are middlewares structured?")
    coord.add_plan("Add rate limiting", context="Express middleware pattern")
    coord.add_execution("Create rate limiter", "src/rate-limit.ts", "Use sliding window")
    coord.add_validation("src/rate-limit.ts", ["Returns 429", "Resets correctly"])

    pipeline = coord.get_pipeline()
    assert len(pipeline) == 4
    assert pipeline[0]["subagent_type"] == "Explore"
    assert pipeline[1]["subagent_type"] == "Plan"
    assert pipeline[2]["subagent_type"] == "general-purpose"
    assert pipeline[3]["subagent_type"] == "general-purpose"


def test_coordinator_describe():
    coord = Coordinator(task="Fix auth bug")
    coord.add_research("What changed recently in auth?")
    coord.add_execution("Fix JWT validation", "src/auth.ts", "Add algorithms option")

    output = coord.describe()
    assert "Fix auth bug" in output
    assert "Explore" in output
    assert "general-purpose" in output


def test_pipeline_parallel():
    from agent_lab.orchestrator.agents import Researcher

    pipeline = Pipeline("Investigate bug")
    pipeline.add_parallel("Research", [
        Researcher(question="Frontend logs?").build(),
        Researcher(question="Backend logs?").build(),
    ])

    assert pipeline.steps[0].step_type == StepType.PARALLEL
    assert len(pipeline.steps[0].agents) == 2


def test_pipeline_conditional():
    from agent_lab.orchestrator.agents import Executor

    pipeline = Pipeline("Deploy feature")
    pipeline.add_conditional(
        "Deploy",
        agents=[Executor(task="deploy", file_path="infra/", instructions="run deploy").build()],
        condition=lambda ctx: ctx.get("tests_passed", False),
    )

    step = pipeline.steps[0]
    assert step.step_type == StepType.CONDITIONAL
    assert step.should_run({"tests_passed": True}) is True
    assert step.should_run({"tests_passed": False}) is False


def test_pipeline_describe():
    pipeline = Pipeline("My task")
    pipeline.add_parallel("Research", [
        Researcher(question="Q1").build(),
        Researcher(question="Q2").build(),
    ])
    pipeline.add_sequential("Execute", [
        Executor(task="do thing", file_path="f.py", instructions="...").build(),
    ])

    output = pipeline.describe()
    assert "My task" in output
    assert "Research" in output
    assert "Execute" in output


def test_pipeline_token_estimate():
    pipeline = Pipeline("Test")
    pipeline.add_parallel("Research", [
        Researcher(question="Q1").build(),
        Researcher(question="Q2").build(),
    ])

    estimate = pipeline.estimate_tokens()
    assert estimate["total_agents"] == 2
    assert estimate["total_estimated"] > 0


def test_pipeline_to_claude_code_plan():
    pipeline = Pipeline("Add feature")
    pipeline.add_sequential("Plan", [
        Planner(goal="add feature", context="context here").build(),
    ])

    plan = pipeline.to_claude_code_plan()
    assert "# Execution Plan: Add feature" in plan
    assert "Plan" in plan
    assert "context here" in plan
