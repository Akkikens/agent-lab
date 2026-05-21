"""
Production MCP Server: Task Tracker

Demonstrates the full MCP protocol using the official Python SDK:
- Tools: CRUD operations on tasks
- Resources: Expose task data as readable resources
- Prompts: Pre-built prompt templates for common operations

Architecture Lesson:
─────────────────────
This server uses the HIGH-LEVEL SDK (FastMCP) which handles:
- JSON-RPC framing automatically
- Schema generation from type hints
- Transport negotiation (stdio vs SSE)
- Error handling and validation

vs our previous raw implementation which manually handled all JSON-RPC.
The SDK approach is ~5x less code and handles edge cases.

Runtime behavior:
1. Claude Code spawns this as a subprocess
2. Communicates via stdin/stdout (stdio transport)
3. Server stays alive for the session duration
4. State persists in tasks.json between tool calls

Token implications:
- 4 tools × ~150 tokens each = ~600 tokens injected into context
- Each tool call result adds ~50-200 tokens
- Resources are only fetched when explicitly read (lazy)
"""

import json
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

TASKS_FILE = Path(__file__).parent / "tasks.json"

mcp = FastMCP(
    "task-tracker",
    instructions="Manage project tasks with priorities, tags, and status tracking",
)


def load_tasks() -> list[dict]:
    if TASKS_FILE.exists():
        return json.loads(TASKS_FILE.read_text())
    return []


def save_tasks(tasks: list[dict]) -> None:
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))


# ─── TOOLS ───────────────────────────────────────────────────────────────────
# Tools are actions the LLM can invoke. Each becomes a callable tool in Claude's context.


@mcp.tool()
def add_task(title: str, priority: str = "medium", tags: list[str] | None = None) -> str:
    """Add a new task to the tracker.

    Args:
        title: What needs to be done
        priority: low, medium, or high
        tags: Optional categorization tags
    """
    tasks = load_tasks()
    new_id = max((t["id"] for t in tasks), default=0) + 1
    task = {
        "id": new_id,
        "title": title,
        "priority": priority,
        "tags": tags or [],
        "done": False,
        "created": datetime.now().isoformat(),
        "completed": None,
    }
    tasks.append(task)
    save_tasks(tasks)
    return f"Created task #{new_id}: {title} [{priority}]"


@mcp.tool()
def list_tasks(status: str = "all", tag: str | None = None) -> str:
    """List tasks with optional filtering.

    Args:
        status: Filter by 'all', 'pending', or 'done'
        tag: Optional tag to filter by
    """
    tasks = load_tasks()

    if status == "pending":
        tasks = [t for t in tasks if not t["done"]]
    elif status == "done":
        tasks = [t for t in tasks if t["done"]]

    if tag:
        tasks = [t for t in tasks if tag in t.get("tags", [])]

    if not tasks:
        return "No tasks found."

    lines = []
    for t in tasks:
        mark = "x" if t["done"] else " "
        tags_str = f" [{', '.join(t.get('tags', []))}]" if t.get("tags") else ""
        lines.append(f"[{mark}] #{t['id']} ({t['priority']}) {t['title']}{tags_str}")
    return "\n".join(lines)


@mcp.tool()
def complete_task(task_id: int) -> str:
    """Mark a task as completed.

    Args:
        task_id: The ID number of the task to complete
    """
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            t["completed"] = datetime.now().isoformat()
            save_tasks(tasks)
            return f"Completed task #{task_id}: {t['title']}"
    return f"Task #{task_id} not found"


@mcp.tool()
def delete_task(task_id: int) -> str:
    """Delete a task permanently.

    Args:
        task_id: The ID number of the task to delete
    """
    tasks = load_tasks()
    original_len = len(tasks)
    tasks = [t for t in tasks if t["id"] != task_id]
    if len(tasks) == original_len:
        return f"Task #{task_id} not found"
    save_tasks(tasks)
    return f"Deleted task #{task_id}"


@mcp.tool()
def get_summary() -> str:
    """Get a summary of all tasks by status and priority."""
    tasks = load_tasks()
    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    pending = total - done

    by_priority = {}
    for t in tasks:
        if not t["done"]:
            by_priority[t["priority"]] = by_priority.get(t["priority"], 0) + 1

    all_tags = set()
    for t in tasks:
        all_tags.update(t.get("tags", []))

    lines = [
        f"Total: {total} | Done: {done} | Pending: {pending}",
    ]
    if by_priority:
        lines.append("By priority: " + ", ".join(f"{k}: {v}" for k, v in sorted(by_priority.items())))
    if all_tags:
        lines.append("Tags in use: " + ", ".join(sorted(all_tags)))
    return "\n".join(lines)


@mcp.tool()
def bulk_add(tasks_text: str, default_priority: str = "medium") -> str:
    """Add multiple tasks at once from a newline-separated list.

    Args:
        tasks_text: One task title per line
        default_priority: Priority for all tasks (low/medium/high)
    """
    titles = [line.strip() for line in tasks_text.strip().split("\n") if line.strip()]
    results = []
    for title in titles:
        results.append(add_task(title, default_priority))
    return f"Added {len(results)} tasks:\n" + "\n".join(results)


# ─── RESOURCES ───────────────────────────────────────────────────────────────
# Resources are data the LLM can READ (like files). They're lazy — only fetched when accessed.
# This is how you expose structured data without paying context cost upfront.


@mcp.resource("tasks://all")
def all_tasks_resource() -> str:
    """All tasks as JSON — useful for detailed analysis."""
    tasks = load_tasks()
    return json.dumps(tasks, indent=2)


@mcp.resource("tasks://pending")
def pending_tasks_resource() -> str:
    """Only pending tasks as JSON."""
    tasks = load_tasks()
    return json.dumps([t for t in tasks if not t["done"]], indent=2)


@mcp.resource("tasks://summary")
def summary_resource() -> str:
    """Quick text summary of task state."""
    return get_summary()


# ─── PROMPTS ─────────────────────────────────────────────────────────────────
# Prompts are reusable prompt templates the LLM can select.
# They're like "stored procedures" for common AI workflows.


@mcp.prompt()
def daily_standup() -> str:
    """Generate a daily standup report from current task state."""
    tasks = load_tasks()
    done_today = [t for t in tasks if t["done"] and t.get("completed", "").startswith(datetime.now().strftime("%Y-%m-%d"))]
    pending = [t for t in tasks if not t["done"]]
    high_priority = [t for t in pending if t["priority"] == "high"]

    return f"""Based on the current task state, generate a standup update:

**Completed today:** {len(done_today)} tasks
{chr(10).join(f"- {t['title']}" for t in done_today) or "- None yet"}

**In progress / Pending:** {len(pending)} tasks
{chr(10).join(f"- [{t['priority']}] {t['title']}" for t in pending[:5])}
{"..." if len(pending) > 5 else ""}

**Blockers:** {len(high_priority)} high-priority items
{chr(10).join(f"- {t['title']}" for t in high_priority) or "- None"}

Summarize this into a concise standup format: what was done, what's next, any blockers."""


@mcp.prompt()
def prioritize() -> str:
    """Help prioritize the current task list."""
    tasks = load_tasks()
    pending = [t for t in tasks if not t["done"]]

    return f"""Here are the current pending tasks:

{chr(10).join(f"- #{t['id']} [{t['priority']}] {t['title']} (tags: {', '.join(t.get('tags', []))})" for t in pending)}

Suggest a prioritized order considering:
1. Current priority labels
2. Dependencies between tasks (inferred from titles)
3. Quick wins vs deep work
4. Tag groupings for batch efficiency

Provide a recommended execution order with reasoning."""


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
