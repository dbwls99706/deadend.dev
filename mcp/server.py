"""deadends.dev MCP Server — Error knowledge for AI coding agents.

Exposes structured failure knowledge through the Model Context Protocol.
AI agents can query error signatures to get dead ends, workarounds,
and error chains without web search.

Usage:
    python -m mcp.server              # stdio mode (for Claude Desktop, Cursor)
    python -m mcp.server --port 8080  # HTTP mode

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
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"

# Module-level cache — loaded once on first request
_CANONS: list[dict] | None = None
_DOMAIN_INDEX: dict[str, list[str]] | None = None


def _get_canons() -> list[dict]:
    """Load all ErrorCanon JSON files (cached after first call)."""
    global _CANONS
    if _CANONS is not None:
        return _CANONS

    canons = []
    for f in sorted(DATA_DIR.rglob("*.json")):
        with open(f, encoding="utf-8") as fh:
            canons.append(json.load(fh))
    _CANONS = canons
    return canons


def _get_domain_index() -> dict[str, list[str]]:
    """Build domain -> [signature] index (cached)."""
    global _DOMAIN_INDEX
    if _DOMAIN_INDEX is not None:
        return _DOMAIN_INDEX

    canons = _get_canons()
    index: dict[str, list[str]] = {}
    for c in canons:
        d = c["error"]["domain"]
        sig = c["error"]["signature"]
        index.setdefault(d, [])
        if sig not in index[d]:
            index[d].append(sig)
    _DOMAIN_INDEX = index
    return index


def match_error(error_message: str, canons: list[dict]) -> list[dict]:
    """Match an error message against all known patterns."""
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
                        for lt in canon.get("transition_graph", {}).get(
                            "leads_to", []
                        )
                    ],
                    "url": canon["url"],
                })
        except re.error:
            continue

    matches.sort(key=lambda m: m["fix_success_rate"], reverse=True)
    return matches


def lookup_by_id(error_id: str, canons: list[dict]) -> dict | None:
    """Look up a specific error by its ID."""
    for canon in canons:
        if canon["id"] == error_id:
            return canon
    return None


def list_domains(canons: list[dict]) -> dict:
    """List all domains with error counts."""
    domains: dict[str, int] = {}
    for canon in canons:
        d = canon["error"]["domain"]
        domains[d] = domains.get(d, 0) + 1
    return {"total": len(canons), "domains": domains}


def _suggest_domains(error_message: str) -> str:
    """Suggest potentially relevant domains based on keywords."""
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


# === MCP Protocol Implementation (JSON-RPC over stdio) ===

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
    },
    {
        "name": "get_domain_stats",
        "description": (
            "Get detailed statistics for a domain: error counts, average fix "
            "rate, resolvability breakdown, top categories, and confidence levels. "
            "Use this to assess how trustworthy deadends.dev data is for a domain."
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
    },
]


def handle_request(method: str, params: dict, canons: list[dict]) -> dict:
    """Handle a JSON-RPC request."""
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "deadends-dev",
                "version": "1.2.0",
            },
        }
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
                    parts.append(f"Resolvable: {m['resolvable']} | "
                                 f"Fix rate: {m['fix_success_rate']}")
                    parts.append(f"Summary: {m['summary']}")
                    parts.append("")
                    parts.append("### Dead Ends (DO NOT TRY):")
                    for d in m["dead_ends"]:
                        parts.append(f"- {d['action']} "
                                     f"(fails {int(d['fail_rate']*100)}%): "
                                     f"{d['why_fails']}")
                    parts.append("")
                    parts.append("### Workarounds (TRY THESE):")
                    for w in m["workarounds"]:
                        how = f" — `{w['how']}`" if w["how"] else ""
                        parts.append(f"- {w['action']} "
                                     f"(works {int(w['success_rate']*100)}%)"
                                     f"{how}")
                    if m.get("leads_to"):
                        parts.append("")
                        parts.append("### Next Errors (after fixing this):")
                        for lt in m["leads_to"]:
                            parts.append(f"- {lt}")
                    parts.append(f"\nFull details: {m['url']}")
                    parts.append("")
                text = "\n".join(parts)
            return {
                "content": [{"type": "text", "text": text}],
            }

        elif tool_name == "get_error_detail":
            error_id = args.get("error_id", "")
            canon = lookup_by_id(error_id, canons)
            if not canon:
                # Try partial match
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
                        f"Use list_error_domains to see available domains, "
                        f"or lookup_error to search by error message."
                    )
            else:
                text = json.dumps(canon, indent=2, ensure_ascii=False)
            return {
                "content": [{"type": "text", "text": text}],
            }

        elif tool_name == "list_error_domains":
            info = list_domains(canons)
            text = f"Total errors: {info['total']}\n\n"
            for domain, count in sorted(info["domains"].items()):
                text += f"- {domain}: {count} errors\n"
            text += (
                "\nUse lookup_error to search by error message, "
                "or get_error_detail with an ID like "
                "'python/modulenotfounderror/py311-linux'."
            )
            return {
                "content": [{"type": "text", "text": text}],
            }

        elif tool_name == "search_errors":
            query = args.get("query", "").lower()
            domain_filter = args.get("domain", "")
            limit = min(args.get("limit", 10), 20)
            scored = []
            for c in canons:
                if domain_filter and c["error"]["domain"] != domain_filter:
                    continue
                # Score by keyword presence in signature, summary, dead ends
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
                parts = [f"Found {min(len(scored), limit)} results for '{query}':\n"]
                for score, c in scored[:limit]:
                    parts.append(
                        f"- **{c['error']['signature']}** [{c['error']['domain']}] "
                        f"(fix rate: {int(c['verdict']['fix_success_rate']*100)}%) "
                        f"— ID: {c['id']}"
                    )
                parts.append(
                    "\nUse get_error_detail with the ID for full dead ends and workarounds."
                )
                text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "list_errors_by_domain":
            domain = args.get("domain", "")
            sort_by = args.get("sort_by", "fix_rate")
            domain_canons = [c for c in canons if c["error"]["domain"] == domain]
            if not domain_canons:
                available = sorted({c["error"]["domain"] for c in canons})
                text = (
                    f"Unknown domain: '{domain}'\n\n"
                    f"Available domains: {', '.join(available)}"
                )
            else:
                if sort_by == "name":
                    domain_canons.sort(key=lambda c: c["error"]["signature"])
                elif sort_by == "confidence":
                    domain_canons.sort(
                        key=lambda c: c["verdict"]["confidence"], reverse=True
                    )
                else:
                    domain_canons.sort(
                        key=lambda c: c["verdict"]["fix_success_rate"], reverse=True
                    )
                parts = [f"## {domain} — {len(domain_canons)} errors\n"]
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
                            f"Top dead end: {m['dead_ends'][0]['action']}"
                        )
                    if m["workarounds"]:
                        parts.append(
                            f"Top workaround: {m['workarounds'][0]['action']}"
                        )
                    parts.append(f"ID: {m['id']}")
                else:
                    parts.append("No match found.")
                parts.append("")
            text = "\n".join(parts)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "get_domain_stats":
            domain = args.get("domain", "")
            dc = [c for c in canons if c["error"]["domain"] == domain]
            if not dc:
                available = sorted({c["error"]["domain"] for c in canons})
                text = (
                    f"Unknown domain: '{domain}'\n"
                    f"Available: {', '.join(available)}"
                )
            else:
                rates = [c["verdict"]["fix_success_rate"] for c in dc]
                avg_rate = sum(rates) / len(rates)
                res_counts = {"true": 0, "partial": 0, "false": 0}
                categories: dict[str, int] = {}
                conf_levels = {"high": 0, "medium": 0, "low": 0}
                for c in dc:
                    res_counts[c["verdict"]["resolvable"]] = (
                        res_counts.get(c["verdict"]["resolvable"], 0) + 1
                    )
                    cat = c["error"]["category"]
                    categories[cat] = categories.get(cat, 0) + 1
                    conf = c["verdict"]["confidence"]
                    conf_levels[conf] = conf_levels.get(conf, 0) + 1
                top_cats = sorted(
                    categories.items(), key=lambda x: x[1], reverse=True
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
            "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
            "isError": True,
        }

    elif method == "notifications/initialized":
        return None  # No response needed for notifications

    return {"error": {"code": -32601, "message": f"Unknown method: {method}"}}


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
