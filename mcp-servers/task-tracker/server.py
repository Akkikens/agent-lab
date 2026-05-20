"""
Minimal MCP Server: Task Tracker

This is a learning example showing how MCP servers work.
It provides tools to manage a simple task list stored in a JSON file.

Architecture:
- Communicates via stdio (stdin/stdout JSON-RPC)
- Stores state in a local JSON file
- Exposes 4 tools: list_tasks, add_task, complete_task, get_summary

To use with Claude Code, add to .claude/settings.json:
{
  "mcpServers": {
    "task-tracker": {
      "command": "python3",
      "args": ["/Users/akshay/Documents/GitHub/agent-lab/mcp-servers/task-tracker/server.py"]
    }
  }
}
"""

import json
import sys
from datetime import datetime
from pathlib import Path

TASKS_FILE = Path(__file__).parent / "tasks.json"


def load_tasks():
    if TASKS_FILE.exists():
        return json.loads(TASKS_FILE.read_text())
    return []


def save_tasks(tasks):
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))


def handle_initialize(request_id):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "task-tracker", "version": "0.1.0"},
        },
    }


def handle_tools_list(request_id):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": [
                {
                    "name": "list_tasks",
                    "description": "List all tasks with their status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["all", "pending", "done"],
                                "description": "Filter by status",
                            }
                        },
                    },
                },
                {
                    "name": "add_task",
                    "description": "Add a new task",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Task title",
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "Task priority",
                            },
                        },
                        "required": ["title"],
                    },
                },
                {
                    "name": "complete_task",
                    "description": "Mark a task as completed",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "integer",
                                "description": "ID of the task to complete",
                            }
                        },
                        "required": ["task_id"],
                    },
                },
                {
                    "name": "get_summary",
                    "description": "Get a summary of task counts by status and priority",
                    "inputSchema": {"type": "object", "properties": {}},
                },
            ]
        },
    }


def handle_tool_call(request_id, tool_name, arguments):
    tasks = load_tasks()

    if tool_name == "list_tasks":
        status_filter = arguments.get("status", "all")
        if status_filter == "pending":
            filtered = [t for t in tasks if not t["done"]]
        elif status_filter == "done":
            filtered = [t for t in tasks if t["done"]]
        else:
            filtered = tasks

        if not filtered:
            text = "No tasks found."
        else:
            lines = []
            for t in filtered:
                mark = "x" if t["done"] else " "
                lines.append(f"[{mark}] #{t['id']} ({t['priority']}) {t['title']}")
            text = "\n".join(lines)

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": text}]}}

    elif tool_name == "add_task":
        new_id = max((t["id"] for t in tasks), default=0) + 1
        task = {
            "id": new_id,
            "title": arguments["title"],
            "priority": arguments.get("priority", "medium"),
            "done": False,
            "created": datetime.now().isoformat(),
        }
        tasks.append(task)
        save_tasks(tasks)
        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": f"Added task #{new_id}: {task['title']}"}]}}

    elif tool_name == "complete_task":
        task_id = arguments["task_id"]
        for t in tasks:
            if t["id"] == task_id:
                t["done"] = True
                t["completed"] = datetime.now().isoformat()
                save_tasks(tasks)
                return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": f"Completed task #{task_id}: {t['title']}"}]}}
        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": f"Task #{task_id} not found"}]}}

    elif tool_name == "get_summary":
        total = len(tasks)
        done = sum(1 for t in tasks if t["done"])
        pending = total - done
        by_priority = {}
        for t in tasks:
            if not t["done"]:
                by_priority[t["priority"]] = by_priority.get(t["priority"], 0) + 1
        summary = f"Total: {total} | Done: {done} | Pending: {pending}\n"
        if by_priority:
            summary += "Pending by priority: " + ", ".join(f"{k}: {v}" for k, v in sorted(by_priority.items()))
        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": summary}]}}

    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}


def main():
    """Main loop: read JSON-RPC from stdin, write responses to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = request.get("method", "")
        request_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            response = handle_initialize(request_id)
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            response = handle_tools_list(request_id)
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            response = handle_tool_call(request_id, tool_name, arguments)
        else:
            if request_id is not None:
                response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
            else:
                continue

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
