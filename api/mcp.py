"""Vercel serverless MCP endpoint for Smithery.

Handles MCP protocol over HTTP (JSON-RPC POST requests).
Deploy: vercel --prod
"""

import json
import re
from http.server import BaseHTTPRequestHandler
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"

_CANONS = None


def _load_canons():
    global _CANONS
    if _CANONS is not None:
        return _CANONS
    canons = []
    for f in sorted(DATA_DIR.rglob("*.json")):
        with open(f, encoding="utf-8") as fh:
            canons.append(json.load(fh))
    _CANONS = canons
    return canons


def match_error(error_message, canons):
    matches = []
    for canon in canons:
        try:
            pattern = re.compile(canon["error"]["regex"], re.IGNORECASE)
            if pattern.search(error_message):
                matches.append({
                    "id": canon["id"],
                    "signature": canon["error"]["signature"],
                    "domain": canon["error"]["domain"],
                    "resolvable": canon["verdict"]["resolvable"],
                    "fix_success_rate": canon["verdict"]["fix_success_rate"],
                    "summary": canon["verdict"]["summary"],
                    "dead_ends": [
                        {"action": d["action"], "why_fails": d["why_fails"], "fail_rate": d["fail_rate"]}
                        for d in canon["dead_ends"]
                    ],
                    "workarounds": [
                        {"action": w["action"], "success_rate": w["success_rate"], "how": w.get("how", "")}
                        for w in canon.get("workarounds", [])
                    ],
                    "leads_to": [lt["error_id"] for lt in canon.get("transition_graph", {}).get("leads_to", [])],
                    "url": canon["url"],
                })
        except re.error:
            continue
    matches.sort(key=lambda m: m["fix_success_rate"], reverse=True)
    return matches


TOOLS = [
    {
        "name": "lookup_error",
        "description": (
            "Match an error message against deadends.dev's database of known errors. "
            "Returns dead ends (what NOT to try), workarounds (what works), and error chains. "
            "Covers 14 domains: python, node, docker, git, cuda, pip, typescript, rust, go, "
            "kubernetes, terraform, aws, nextjs, react."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_message": {"type": "string", "description": "The full error message to look up"}
            },
            "required": ["error_message"],
        },
    },
    {
        "name": "get_error_detail",
        "description": "Get full details for a specific error by its ID (e.g., 'python/modulenotfounderror/py311-linux').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_id": {"type": "string", "description": "The error ID (domain/slug/env)"}
            },
            "required": ["error_id"],
        },
    },
    {
        "name": "list_error_domains",
        "description": "List all error domains and counts in the deadends.dev database.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def handle_mcp(method, params, canons):
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "deadends-dev", "version": "1.2.0"},
        }
    elif method == "tools/list":
        return {"tools": TOOLS}
    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})

        if tool_name == "lookup_error":
            matches = match_error(args.get("error_message", ""), canons)
            if not matches:
                text = f"No matching errors in deadends.dev ({len(canons)} patterns across 14 domains)."
            else:
                parts = []
                for m in matches[:5]:
                    parts.append(f"## {m['signature']}")
                    parts.append(f"Resolvable: {m['resolvable']} | Fix rate: {m['fix_success_rate']}")
                    parts.append(f"Summary: {m['summary']}\n")
                    parts.append("### Dead Ends (DO NOT TRY):")
                    for d in m["dead_ends"]:
                        parts.append(f"- {d['action']} (fails {int(d['fail_rate']*100)}%): {d['why_fails']}")
                    parts.append("\n### Workarounds (TRY THESE):")
                    for w in m["workarounds"]:
                        how = f" — `{w['how']}`" if w["how"] else ""
                        parts.append(f"- {w['action']} (works {int(w['success_rate']*100)}%){how}")
                    if m.get("leads_to"):
                        parts.append("\n### Next Errors:")
                        for lt in m["leads_to"]:
                            parts.append(f"- {lt}")
                    parts.append(f"\nFull details: {m['url']}\n")
                text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "get_error_detail":
            error_id = args.get("error_id", "")
            canon = next((c for c in canons if c["id"] == error_id), None)
            if canon:
                text = json.dumps(canon, indent=2, ensure_ascii=False)
            else:
                partial = [c for c in canons if error_id in c["id"]]
                if partial:
                    text = f"Not found: {error_id}\nDid you mean:\n" + "\n".join(f"- {c['id']}" for c in partial[:5])
                else:
                    text = f"Not found: {error_id}. Use list_error_domains to see available domains."
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "list_error_domains":
            domains = {}
            for c in canons:
                d = c["error"]["domain"]
                domains[d] = domains.get(d, 0) + 1
            text = f"Total errors: {len(canons)}\n\n"
            for domain, count in sorted(domains.items()):
                text += f"- {domain}: {count} errors\n"
            return {"content": [{"type": "text", "text": text}]}

        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}

    elif method == "notifications/initialized":
        return None

    return {"error": {"code": -32601, "message": f"Unknown method: {method}"}}


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
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return

        canons = _load_canons()
        result = handle_mcp(request.get("method", ""), request.get("params", {}), canons)

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
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body_out)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        canons = _load_canons()
        info = {
            "name": "deadends-dev",
            "version": "1.2.0",
            "description": "Structured failure knowledge for AI agents — dead ends, workarounds, error chains",
            "total_errors": len(canons),
            "domains": 14,
            "homepage": "https://deadends.dev",
            "protocol": "MCP (Model Context Protocol)",
            "tools": ["lookup_error", "get_error_detail", "list_error_domains"],
        }
        body_out = json.dumps(info, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body_out)
