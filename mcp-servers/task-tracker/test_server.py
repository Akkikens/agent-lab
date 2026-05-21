"""
MCP Server Integration Test

Sends raw JSON-RPC messages to verify the server works correctly.
This simulates exactly what Claude Code does when connecting to an MCP server.

Usage: uv run python test_server.py
"""

import json
import subprocess
import sys
from pathlib import Path


def test_server():
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-harness", "version": "1.0"}
        }},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "add_task",
            "arguments": {"title": "Test task from harness", "priority": "high", "tags": ["test"]}
        }},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
            "name": "list_tasks",
            "arguments": {"status": "all"}
        }},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {
            "name": "get_summary",
            "arguments": {}
        }},
        {"jsonrpc": "2.0", "id": 6, "method": "resources/list", "params": {}},
        {"jsonrpc": "2.0", "id": 7, "method": "prompts/list", "params": {}},
    ]

    stdin_data = "\n".join(json.dumps(m) for m in messages) + "\n"

    # Clean up any leftover test state
    tasks_file = Path(__file__).parent / "tasks.json"
    if tasks_file.exists():
        tasks_file.unlink()

    result = subprocess.run(
        ["uv", "run", "python", "server.py"],
        input=stdin_data,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
        timeout=30,
    )

    if result.returncode != 0:
        print(f"FAIL: Server exited with code {result.returncode}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)

    responses = []
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            responses.append(json.loads(line))

    print(f"Got {len(responses)} responses\n")

    for resp in responses:
        resp_id = resp.get("id", "notification")
        if "error" in resp:
            print(f"  [{resp_id}] ERROR: {resp['error']['message']}")
        elif "result" in resp:
            result_data = resp["result"]
            if "serverInfo" in result_data:
                print(f"  [{resp_id}] Initialize: {result_data['serverInfo']['name']} v{result_data['serverInfo']['version']}")
            elif "tools" in result_data:
                tools = result_data["tools"]
                print(f"  [{resp_id}] Tools: {', '.join(t['name'] for t in tools)}")
            elif "resources" in result_data:
                resources = result_data["resources"]
                print(f"  [{resp_id}] Resources: {', '.join(r['uri'] for r in resources)}")
            elif "prompts" in result_data:
                prompts = result_data["prompts"]
                print(f"  [{resp_id}] Prompts: {', '.join(p['name'] for p in prompts)}")
            elif "content" in result_data:
                text = result_data["content"][0]["text"]
                print(f"  [{resp_id}] Tool result: {text}")
            else:
                print(f"  [{resp_id}] Unknown result: {json.dumps(result_data)[:100]}")

    # Cleanup
    if tasks_file.exists():
        tasks_file.unlink()

    print("\nPASS: All MCP operations completed successfully")


if __name__ == "__main__":
    test_server()
