"""
agent-lab: A Python toolkit for building AI agent systems with Claude Code.

Provides:
- MCP server scaffolding (FastMCP-based templates)
- Agent orchestration patterns (coordinator, researcher, executor, validator)
- Skill and hook generators for Claude Code projects
- Context engineering utilities
"""

__version__ = "0.1.0"

from agent_lab.hooks.generator import generate_hook
from agent_lab.mcp.server import create_mcp_server
from agent_lab.orchestrator.agents import Coordinator, Executor, Planner, Researcher, Validator
from agent_lab.orchestrator.pipeline import Pipeline, PipelineStep
from agent_lab.skills.generator import generate_skill

__all__ = [
    "Researcher",
    "Planner",
    "Executor",
    "Validator",
    "Coordinator",
    "Pipeline",
    "PipelineStep",
    "create_mcp_server",
    "generate_skill",
    "generate_hook",
]
