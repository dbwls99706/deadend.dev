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
_DOMAIN_INDEX = None


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


def _get_domain_index():
    global _DOMAIN_INDEX
    if _DOMAIN_INDEX is not None:
        return _DOMAIN_INDEX
    canons = _load_canons()
    index = {}
    for c in canons:
        d = c["error"]["domain"]
        sig = c["error"]["signature"]
        index.setdefault(d, [])
        if sig not in index[d]:
            index[d].append(sig)
    _DOMAIN_INDEX = index
    return index


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
                        {
                            "action": d["action"],
                            "why_fails": d["why_fails"],
                            "fail_rate": d["fail_rate"],
                        }
                        for d in canon["dead_ends"]
                    ],
                    "workarounds": [
                        {
                            "action": w["action"],
                            "success_rate": w["success_rate"],
                            "how": w.get("how", ""),
                        }
                        for w in canon.get("workarounds", [])
                    ],
                    "leads_to": [
                        lt["error_id"]
                        for lt in canon.get(
                            "transition_graph", {}
                        ).get("leads_to", [])
                    ],
                    "url": canon["url"],
                })
        except re.error:
            continue
    matches.sort(key=lambda m: m["fix_success_rate"], reverse=True)
    return matches


def _suggest_domains(error_message):
    msg = error_message.lower()
    suggestions = []
    keyword_map = {
        "python": ["python", "pip", "import", "module", "traceback", "def "],
        "node": ["node", "npm", "require", "module.exports", "package.json"],
        "docker": ["docker", "container", "image", "dockerfile", "daemon"],
        "git": ["git", "commit", "push", "merge", "branch", "repository"],
        "cuda": ["cuda", "gpu", "nvidia", "torch", "tensor", "nccl"],
        "typescript": ["typescript", "ts2", "ts7", "tsconfig", ".ts "],
        "rust": ["rust", "cargo", "borrow", "lifetime", "e0"],
        "go": ["go ", "golang", "goroutine", "go.mod", "go build"],
        "kubernetes": ["kubernetes", "k8s", "kubectl", "pod", "deploy"],
        "terraform": ["terraform", "tf ", "state", "provider", "hcl"],
        "aws": ["aws", "s3", "ec2", "iam", "lambda", "cloudformation"],
        "nextjs": ["next.js", "nextjs", "next/", "getserverside", "getstaticprops"],
        "react": ["react", "usestate", "useeffect", "jsx", "component"],
        "pip": ["pip install", "pip3", "pypi", "wheel", "sdist"],
    }
    for domain, keywords in keyword_map.items():
        for kw in keywords:
            if kw in msg:
                suggestions.append(domain)
                break
    return ", ".join(suggestions) if suggestions else "unknown"


TOOLS = [
    {
        "name": "lookup_error",
        "description": (
            "Match an error message against deadends.dev's database of known "
            "errors. Returns dead ends (what NOT to try), workarounds (what "
            "works), and error chains (what comes next). Use this BEFORE "
            "attempting to fix any error to avoid wasting time on approaches "
            "that are known to fail. Covers 14 domains: python, node, docker, "
            "git, cuda, pip, typescript, rust, go, kubernetes, terraform, aws, "
            "nextjs, react."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_message": {
                    "type": "string",
                    "description": "The full error message to look up",
                }
            },
            "required": ["error_message"],
        },
        "annotations": {
            "title": "Look up error",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "get_error_detail",
        "description": (
            "Get full details for a specific error by its ID "
            "(e.g., 'python/modulenotfounderror/py311-linux'). "
            "Includes all dead ends, workarounds, error chain info, "
            "and source evidence."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_id": {
                    "type": "string",
                    "description": "The error ID (domain/slug/env)",
                }
            },
            "required": ["error_id"],
        },
        "annotations": {
            "title": "Get error details",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "list_error_domains",
        "description": (
            "List all error domains and counts in the deadends.dev database. "
            "Domains include: python, node, docker, git, cuda, pip, "
            "typescript, rust, go, kubernetes, terraform, aws, nextjs, react."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
        "annotations": {
            "title": "List domains",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "search_errors",
        "description": (
            "Search errors by keyword across all domains. Unlike lookup_error "
            "(which uses regex matching), this does fuzzy keyword search. "
            "Use when you have a vague description like 'memory issues' or "
            "'permission denied' rather than an exact error message."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search keywords (e.g., 'memory limit', 'timeout', "
                        "'permission denied')"
                    ),
                },
                "domain": {
                    "type": "string",
                    "description": (
                        "Optional: filter to a specific domain "
                        "(e.g., 'python', 'docker')"
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default: 10)",
                },
            },
            "required": ["query"],
        },
        "annotations": {
            "title": "Search errors",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "list_errors_by_domain",
        "description": (
            "List all errors in a specific domain with their fix rates. "
            "Use this to understand coverage for a domain before relying on it."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": (
                        "The domain to list errors for "
                        "(e.g., 'python', 'kubernetes')"
                    ),
                },
                "sort_by": {
                    "type": "string",
                    "description": (
                        "Sort by: 'fix_rate' (default), 'name', or 'confidence'"
                    ),
                },
            },
            "required": ["domain"],
        },
        "annotations": {
            "title": "List domain errors",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "batch_lookup",
        "description": (
            "Look up multiple error messages at once. Returns the best match "
            "for each error. Use when debugging a chain of errors or analyzing "
            "a log with multiple failures."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_messages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of error messages to look up (max 10)",
                    "maxItems": 10,
                }
            },
            "required": ["error_messages"],
        },
        "annotations": {
            "title": "Batch lookup",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "get_domain_stats",
        "description": (
            "Get detailed statistics for a domain: error counts, average fix "
            "rate, resolvability breakdown, top categories, and confidence "
            "levels. Use this to assess how trustworthy deadends.dev data is "
            "for a domain."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "The domain to get stats for",
                }
            },
            "required": ["domain"],
        },
        "annotations": {
            "title": "Domain statistics",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
]


def handle_mcp(method, params, canons):
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
            },
            "serverInfo": {"name": "deadends-dev", "version": "1.3.0"},
        }
    elif method == "ping":
        return {}
    elif method == "resources/list":
        return {"resources": []}
    elif method == "prompts/list":
        return {"prompts": []}
    elif method == "tools/list":
        return {"tools": TOOLS}
    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})

        if tool_name == "lookup_error":
            error_msg = args.get("error_message", "")
            matches = match_error(error_msg, canons)
            if not matches:
                suggested = _suggest_domains(error_msg)
                text = (
                    "No matching errors found in deadends.dev database.\n\n"
                    f"Searched {len(canons)} error patterns across "
                    f"{len(_get_domain_index())} domains.\n"
                )
                if suggested != "unknown":
                    text += (
                        f"Likely domains based on keywords: {suggested}\n"
                        "The error may not be in our database yet.\n"
                    )
                text += (
                    "\nTip: Try the full error message including the "
                    "error type (e.g., 'ModuleNotFoundError: ...')."
                )
            else:
                parts = []
                for m in matches[:5]:
                    parts.append(f"## {m['signature']}")
                    parts.append(
                        f"Resolvable: {m['resolvable']} | "
                        f"Fix rate: {m['fix_success_rate']}"
                    )
                    parts.append(f"Summary: {m['summary']}")
                    parts.append("")
                    parts.append("### Dead Ends (DO NOT TRY):")
                    for d in m["dead_ends"]:
                        parts.append(
                            f"- {d['action']} "
                            f"(fails {int(d['fail_rate']*100)}%): "
                            f"{d['why_fails']}"
                        )
                    parts.append("")
                    parts.append("### Workarounds (TRY THESE):")
                    for w in m["workarounds"]:
                        how = f" — `{w['how']}`" if w["how"] else ""
                        parts.append(
                            f"- {w['action']} "
                            f"(works {int(w['success_rate']*100)}%)"
                            f"{how}"
                        )
                    if m.get("leads_to"):
                        parts.append("")
                        parts.append(
                            "### Next Errors (after fixing this):"
                        )
                        for lt in m["leads_to"]:
                            parts.append(f"- {lt}")
                    parts.append(f"\nFull details: {m['url']}")
                    parts.append("")
                text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "get_error_detail":
            error_id = args.get("error_id", "")
            canon = next((c for c in canons if c["id"] == error_id), None)
            if canon:
                text = json.dumps(canon, indent=2, ensure_ascii=False)
            else:
                partial = [
                    c for c in canons
                    if error_id in c["id"] or c["id"] in error_id
                ]
                if partial:
                    suggestions = [c["id"] for c in partial[:5]]
                    text = (
                        f"Error ID not found: {error_id}\n\n"
                        f"Did you mean one of these?\n"
                        + "\n".join(f"- {s}" for s in suggestions)
                    )
                else:
                    text = (
                        f"Error ID not found: {error_id}\n\n"
                        f"Use list_error_domains to see available "
                        f"domains, or lookup_error to search by "
                        f"error message."
                    )
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "list_error_domains":
            domains = {}
            for c in canons:
                d = c["error"]["domain"]
                domains[d] = domains.get(d, 0) + 1
            text = f"Total errors: {len(canons)}\n\n"
            for domain, count in sorted(domains.items()):
                text += f"- {domain}: {count} errors\n"
            text += (
                "\nUse lookup_error to search by error message, "
                "or get_error_detail with an ID like "
                "'python/modulenotfounderror/py311-linux'."
            )
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "search_errors":
            query = args.get("query", "").lower()
            domain_filter = args.get("domain", "")
            limit = min(args.get("limit", 10), 20)
            scored = []
            for c in canons:
                if domain_filter and c["error"]["domain"] != domain_filter:
                    continue
                score = 0
                sig = c["error"]["signature"].lower()
                summary = c["verdict"]["summary"].lower()
                q_words = set(query.split())
                for w in q_words:
                    if w in sig:
                        score += 10
                    if w in summary:
                        score += 5
                    for de in c["dead_ends"]:
                        if w in de["action"].lower():
                            score += 3
                        if w in de["why_fails"].lower():
                            score += 2
                    for wa in c.get("workarounds", []):
                        if w in wa["action"].lower():
                            score += 3
                if score > 0:
                    scored.append((score, c))
            scored.sort(key=lambda x: x[0], reverse=True)
            if not scored:
                text = f"No errors matching '{query}'"
                if domain_filter:
                    text += f" in domain '{domain_filter}'"
                text += (
                    ".\n\nTry broader keywords or use "
                    "lookup_error with the exact error message."
                )
            else:
                parts = [
                    f"Found {min(len(scored), limit)} "
                    f"results for '{query}':\n"
                ]
                for score, c in scored[:limit]:
                    parts.append(
                        f"- **{c['error']['signature']}** "
                        f"[{c['error']['domain']}] "
                        f"(fix rate: "
                        f"{int(c['verdict']['fix_success_rate']*100)}%) "
                        f"— ID: {c['id']}"
                    )
                parts.append(
                    "\nUse get_error_detail with the ID "
                    "for full dead ends and workarounds."
                )
                text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "list_errors_by_domain":
            domain = args.get("domain", "")
            sort_by = args.get("sort_by", "fix_rate")
            domain_canons = [
                c for c in canons if c["error"]["domain"] == domain
            ]
            if not domain_canons:
                available = sorted(
                    {c["error"]["domain"] for c in canons}
                )
                text = (
                    f"Unknown domain: '{domain}'\n\n"
                    f"Available domains: {', '.join(available)}"
                )
            else:
                if sort_by == "name":
                    domain_canons.sort(
                        key=lambda c: c["error"]["signature"]
                    )
                elif sort_by == "confidence":
                    domain_canons.sort(
                        key=lambda c: c["verdict"]["confidence"],
                        reverse=True,
                    )
                else:
                    domain_canons.sort(
                        key=lambda c: c["verdict"]["fix_success_rate"],
                        reverse=True,
                    )
                parts = [
                    f"## {domain} — {len(domain_canons)} errors\n"
                ]
                for c in domain_canons:
                    res = c["verdict"]["resolvable"]
                    rate = int(c["verdict"]["fix_success_rate"] * 100)
                    parts.append(
                        f"- [{res}] {c['error']['signature']} "
                        f"(fix: {rate}%) — {c['id']}"
                    )
                text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "batch_lookup":
            messages = args.get("error_messages", [])[:10]
            parts = [f"Batch lookup: {len(messages)} errors\n"]
            for i, msg in enumerate(messages):
                matches = match_error(msg, canons)
                parts.append(f"### Error {i+1}: {msg[:80]}")
                if matches:
                    m = matches[0]
                    parts.append(
                        f"Match: **{m['signature']}** "
                        f"[{m['resolvable']}] fix rate: "
                        f"{int(m['fix_success_rate']*100)}%"
                    )
                    if m["dead_ends"]:
                        parts.append(
                            f"Top dead end: "
                            f"{m['dead_ends'][0]['action']}"
                        )
                    if m["workarounds"]:
                        parts.append(
                            f"Top workaround: "
                            f"{m['workarounds'][0]['action']}"
                        )
                    parts.append(f"ID: {m['id']}")
                else:
                    parts.append("No match found.")
                parts.append("")
            text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "get_domain_stats":
            domain = args.get("domain", "")
            dc = [
                c for c in canons if c["error"]["domain"] == domain
            ]
            if not dc:
                available = sorted(
                    {c["error"]["domain"] for c in canons}
                )
                text = (
                    f"Unknown domain: '{domain}'\n"
                    f"Available: {', '.join(available)}"
                )
            else:
                rates = [c["verdict"]["fix_success_rate"] for c in dc]
                avg_rate = sum(rates) / len(rates)
                res_counts = {"true": 0, "partial": 0, "false": 0}
                categories = {}
                conf_levels = {"high": 0, "medium": 0, "low": 0}
                for c in dc:
                    rv = c["verdict"]["resolvable"]
                    res_counts[rv] = res_counts.get(rv, 0) + 1
                    cat = c["error"]["category"]
                    categories[cat] = categories.get(cat, 0) + 1
                    conf = c["verdict"]["confidence"]
                    conf_levels[conf] = conf_levels.get(conf, 0) + 1
                top_cats = sorted(
                    categories.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
                parts = [
                    f"## {domain} — Domain Statistics\n",
                    f"Total errors: {len(dc)}",
                    f"Average fix rate: {int(avg_rate*100)}%\n",
                    "Resolvability:",
                    f"  - Resolvable: {res_counts['true']}",
                    f"  - Partial: {res_counts['partial']}",
                    f"  - Not resolvable: {res_counts['false']}\n",
                    "Confidence:",
                    f"  - High: {conf_levels.get('high', 0)}",
                    f"  - Medium: {conf_levels.get('medium', 0)}",
                    f"  - Low: {conf_levels.get('low', 0)}\n",
                    "Top categories:",
                ]
                for cat, count in top_cats:
                    parts.append(f"  - {cat}: {count}")
                text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        return {
            "content": [
                {"type": "text", "text": f"Unknown tool: {tool_name}"}
            ],
            "isError": True,
        }

    elif method == "notifications/initialized":
        return None

    return {
        "error": {
            "code": -32601,
            "message": f"Unknown method: {method}",
        }
    }


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

        canons = _load_canons()
        result = handle_mcp(
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
        canons = _load_canons()
        info = {
            "name": "deadends-dev",
            "version": "1.3.0",
            "description": (
                "Structured failure knowledge for AI agents "
                "— dead ends, workarounds, error chains"
            ),
            "total_errors": len(canons),
            "domains": 14,
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
