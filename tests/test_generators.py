"""Tests for skill and hook generators."""

import tempfile

from agent_lab.hooks.generator import generate_hook, generate_settings_hooks
from agent_lab.mcp.server import create_mcp_server
from agent_lab.skills.generator import generate_skill, generate_slash_command


def test_generate_skill_research():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = generate_skill(
            name="test-skill",
            description="Test skill for unit tests.",
            output_dir=tmpdir,
            template="research",
            topic="testing",
        )

        assert path.exists()
        content = path.read_text()
        assert "Test skill for unit tests." in content
        assert "## Instructions" in content


def test_generate_skill_action():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = generate_skill(
            name="deploy",
            description="Deploy the application safely.",
            output_dir=tmpdir,
            template="action",
        )

        content = path.read_text()
        assert "Deploy the application safely." in content
        assert "Validate" in content


def test_generate_slash_command():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = generate_slash_command(
            name="test-cmd",
            description="A test command.",
            instructions="Do the thing with $ARGUMENTS",
            output_dir=tmpdir,
        )

        assert path.name == "test-cmd.md"
        content = path.read_text()
        assert "$ARGUMENTS" in content


def test_generate_hook_safety():
    with tempfile.TemporaryDirectory() as tmpdir:
        path, config = generate_hook(
            name="test-safety",
            output_dir=tmpdir,
            template="safety",
        )

        assert path.exists()
        assert path.stat().st_mode & 0o111  # executable
        assert config["event"] == "PreToolUse"
        assert config["config"]["matcher"] == "Bash"
        content = path.read_text()
        assert "force" in content.lower()


def test_generate_hook_audit():
    with tempfile.TemporaryDirectory() as tmpdir:
        path, config = generate_hook(
            name="test-audit",
            output_dir=tmpdir,
            template="audit",
        )

        assert config["event"] == "PostToolUse"
        assert config["config"]["hooks"][0]["async"] is True


def test_generate_settings_hooks():
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks = [
            generate_hook("safety", tmpdir, "safety"),
            generate_hook("audit", tmpdir, "audit"),
        ]

        settings = generate_settings_hooks(hooks)
        assert "hooks" in settings
        assert "PreToolUse" in settings["hooks"]
        assert "PostToolUse" in settings["hooks"]


def test_create_mcp_server():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = create_mcp_server(
            name="test-server",
            output_dir=tmpdir,
            tools=[
                {"name": "greet", "description": "Say hello", "params": {"name": "str"}},
                {"name": "add", "description": "Add numbers", "params": {"a": "int", "b": "int"}},
            ],
            description="A test MCP server",
        )

        assert (path / "server.py").exists()
        assert (path / "pyproject.toml").exists()
        assert (path / "test_server.py").exists()
        assert (path / "mcp-config-snippet.json").exists()

        server_content = (path / "server.py").read_text()
        assert "greet" in server_content
        assert "add" in server_content
        assert "FastMCP" in server_content
