"""Vercel serverless MCP endpoint for Smithery.

Handles MCP protocol over HTTP (JSON-RPC POST requests).
Uses shared mcp.core module for all logic.
Deploy: vercel --prod
"""

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Ensure project root is importable for Vercel serverless
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.core import (  # noqa: E402
    DOMAIN_COUNT,
    SERVER_NAME,
    SERVER_VERSION,
    TOOLS,
    _get_canons,
    handle_request,
)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"error": "Invalid JSON"}).encode()
            )
            return

        canons = _get_canons()
        result = handle_request(
            request.get("method", ""),
            request.get("params", {}),
            canons,
        )

        if result is None:
            self.send_response(204)
            self.end_headers()
            return

        response = {"jsonrpc": "2.0", "id": request.get("id")}
        if "error" in result:
            response["error"] = result["error"]
        else:
            response["result"] = result

        body_out = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "POST, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers", "Content-Type"
        )
        self.end_headers()
        self.wfile.write(body_out)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "POST, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers", "Content-Type"
        )
        self.end_headers()

    def do_GET(self):
        canons = _get_canons()
        info = {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
            "description": (
                "Structured failure knowledge for AI agents "
                "— dead ends, workarounds, error chains"
            ),
            "total_errors": len(canons),
            "domains": DOMAIN_COUNT,
            "tools": [t["name"] for t in TOOLS],
            "homepage": "https://deadends.dev",
            "protocol": "MCP (Model Context Protocol)",
        }
        body_out = json.dumps(info, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body_out)
