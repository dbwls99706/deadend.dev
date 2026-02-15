"""deadends.dev MCP Server — Error knowledge for AI coding agents.

Exposes structured failure knowledge through the Model Context Protocol.
AI coding agents can query error signatures to get dead ends, workarounds,
and error chains without web search.

Usage:
    python -m mcp.server              # stdio mode (for Claude Desktop, Cursor)

Claude Desktop config (~/.claude/claude_desktop_config.json):
{
  "mcpServers": {
    "deadend": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "/path/to/deadends.dev"
    }
  }
}

Cursor config (MCP settings):
{
  "mcpServers": {
    "deadend": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "/path/to/deadends.dev"
    }
  }
}
"""

import json
import sys

from mcp.core import _get_canons, _get_domain_index, handle_request


def main():
    """Run MCP server in stdio mode."""
    canons = _get_canons()
    sys.stderr.write(
        f"deadends.dev MCP server loaded: {len(canons)} errors "
        f"across {len(_get_domain_index())} domains\n"
    )

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        result = handle_request(
            request.get("method", ""),
            request.get("params", {}),
            canons,
        )

        if result is None:
            continue  # Notification, no response

        response = {
            "jsonrpc": "2.0",
            "id": request.get("id"),
        }

        if "error" in result:
            response["error"] = result["error"]
        else:
            response["result"] = result

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
