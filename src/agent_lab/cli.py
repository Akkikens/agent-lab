"""
agent-lab CLI — scaffold agent engineering projects.

Usage:
    agent-lab init                    Initialize agent-lab in current project
    agent-lab mcp <name>             Generate a new MCP server
    agent-lab skill <name>           Generate a new skill
    agent-lab hook <template>        Generate a hook (safety/secrets/audit/notify)
    agent-lab pipeline <task>        Generate a pipeline plan
"""

import argparse
import json
import sys
from pathlib import Path

from agent_lab.hooks.generator import generate_hook
from agent_lab.mcp.server import create_mcp_server
from agent_lab.orchestrator.agents import Coordinator
from agent_lab.skills.generator import generate_skill


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize agent-lab structure in current directory."""
    base = Path.cwd()

    dirs = [
        base / ".claude" / "commands",
        base / "skills",
        base / "hooks",
        base / "agents",
        base / "mcp-servers",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {d.relative_to(base)}/")

    settings_path = base / ".claude" / "settings.json"
    if not settings_path.exists():
        settings = {
            "hooks": {},
            "permissions": {
                "allow": [
                    "Bash(ls *)",
                    "Bash(find *)",
                    "Bash(grep *)",
                    "Bash(git *)",
                    "Read(*)",
                    "Edit(*)",
                    "Write(*)",
                ]
            },
        }
        settings_path.write_text(json.dumps(settings, indent=2))
        print("  Created: .claude/settings.json")

    print("\nAgent lab initialized. Structure:")
    print("  .claude/commands/  — slash commands")
    print("  skills/            — reusable skills")
    print("  hooks/             — lifecycle hooks")
    print("  agents/            — agent documentation")
    print("  mcp-servers/       — MCP server implementations")


def cmd_mcp(args: argparse.Namespace) -> None:
    """Generate a new MCP server."""
    tools = []
    if args.tools:
        for tool_str in args.tools:
            parts = tool_str.split(":")
            name = parts[0]
            desc = parts[1] if len(parts) > 1 else f"The {name} tool"
            tools.append({"name": name, "description": desc, "params": {"input": "str"}})

    path = create_mcp_server(
        name=args.name,
        output_dir=args.output or "./mcp-servers",
        tools=tools or None,
        description=args.description or f"MCP server: {args.name}",
    )
    print(f"Created MCP server at: {path}")
    print("\nTo connect, add to .mcp.json:")
    snippet_path = path / "mcp-config-snippet.json"
    if snippet_path.exists():
        print(snippet_path.read_text())


def cmd_skill(args: argparse.Namespace) -> None:
    """Generate a new skill."""
    path = generate_skill(
        name=args.name,
        description=args.description or f"A skill for {args.name}.",
        output_dir=args.output or "./skills",
        template=args.template,
        topic=args.name,
    )
    print(f"Created skill at: {path}")
    print("\nEdit the SKILL.md to customize the workflow.")


def cmd_hook(args: argparse.Namespace) -> None:
    """Generate a hook script."""
    path, config = generate_hook(
        name=args.template,
        output_dir=args.output or "./hooks",
        template=args.template,
    )
    print(f"Created hook at: {path}")
    print(f"\nAdd to .claude/settings.json under hooks.{config['event']}:")
    print(json.dumps(config["config"], indent=2))


def cmd_pipeline(args: argparse.Namespace) -> None:
    """Generate a pipeline execution plan."""
    coord = Coordinator(task=args.task)
    coord.add_research(f"What do I need to know to: {args.task}")
    coord.add_plan(args.task, context="[Fill in research findings]")
    coord.add_execution(args.task, file_path="[target file]", instructions="[from plan]", isolated=True)
    coord.add_validation("[changed files]", requirements=[args.task])

    print(coord.describe())
    print("\n---\nPaste the above into Claude Code to execute with the Agent tool.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agent-lab",
        description="Scaffold AI agent engineering projects for Claude Code",
    )
    subparsers = parser.add_subparsers(dest="command")

    # init
    subparsers.add_parser("init", help="Initialize agent-lab in current project")

    # mcp
    mcp_parser = subparsers.add_parser("mcp", help="Generate a new MCP server")
    mcp_parser.add_argument("name", help="Server name")
    mcp_parser.add_argument("-d", "--description", help="Server description")
    mcp_parser.add_argument("-o", "--output", help="Output directory")
    mcp_parser.add_argument("-t", "--tools", nargs="*", help="Tools as name:description")

    # skill
    skill_parser = subparsers.add_parser("skill", help="Generate a new skill")
    skill_parser.add_argument("name", help="Skill name")
    skill_parser.add_argument("-d", "--description", help="Skill description")
    skill_parser.add_argument("-o", "--output", help="Output directory")
    skill_parser.add_argument("--template", choices=["research", "action", "analysis"], default="research")

    # hook
    hook_parser = subparsers.add_parser("hook", help="Generate a hook script")
    hook_parser.add_argument("template", choices=["safety", "secrets", "audit", "notify"])
    hook_parser.add_argument("-o", "--output", help="Output directory")

    # pipeline
    pipeline_parser = subparsers.add_parser("pipeline", help="Generate a pipeline plan")
    pipeline_parser.add_argument("task", help="Task description")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "init": cmd_init,
        "mcp": cmd_mcp,
        "skill": cmd_skill,
        "hook": cmd_hook,
        "pipeline": cmd_pipeline,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
