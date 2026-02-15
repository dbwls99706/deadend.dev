"""Shared MCP logic used by both stdio server and Vercel HTTP endpoint.

This module eliminates code duplication between mcp/server.py and api/mcp.py.
All error matching, lookup, and tool handling logic lives here.
"""

import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"

# Module-level caches — loaded once on first request
_CANONS: list[dict] | None = None
_DOMAIN_INDEX: dict[str, list[str]] | None = None
_ID_INDEX: dict[str, dict] | None = None
_COMPILED_PATTERNS: list[tuple[dict, re.Pattern | None]] | None = None

# Protocol and version constants
PROTOCOL_VERSION = "2025-03-26"
SERVER_NAME = "deadends-dev"
SERVER_VERSION = "1.4.0"

DOMAIN_COUNT = 20
DOMAIN_LIST = (
    "python, node, docker, git, cuda, pip, typescript, rust, go, "
    "kubernetes, terraform, aws, nextjs, react, java, database, "
    "cicd, php, dotnet, networking"
)


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


def _get_id_index() -> dict[str, dict]:
    """Build id -> canon index for O(1) lookups (cached)."""
    global _ID_INDEX
    if _ID_INDEX is not None:
        return _ID_INDEX

    canons = _get_canons()
    _ID_INDEX = {c["id"]: c for c in canons}
    return _ID_INDEX


def _get_compiled_patterns() -> list[tuple[dict, re.Pattern | None]]:
    """Pre-compile all regex patterns (cached after first call)."""
    global _COMPILED_PATTERNS
    if _COMPILED_PATTERNS is not None:
        return _COMPILED_PATTERNS

    canons = _get_canons()
    patterns = []
    for canon in canons:
        try:
            pattern = re.compile(canon["error"]["regex"], re.IGNORECASE)
        except re.error:
            sys.stderr.write(
                f"WARNING: Invalid regex in {canon['id']}: "
                f"{canon['error']['regex']}\n"
            )
            pattern = None
        patterns.append((canon, pattern))
    _COMPILED_PATTERNS = patterns
    return patterns


def _compile_patterns(canons: list[dict]) -> list[tuple[dict, re.Pattern | None]]:
    """Compile regex patterns for a list of canons."""
    patterns = []
    for canon in canons:
        try:
            pattern = re.compile(canon["error"]["regex"], re.IGNORECASE)
        except re.error:
            pattern = None
        patterns.append((canon, pattern))
    return patterns


def match_error(error_message: str, canons: list[dict]) -> list[dict]:
    """Match an error message against all known patterns.

    Returns matches sorted by fix_success_rate so exact regex hits
    always rank above partial keyword matches. Uses pre-compiled
    regex patterns for performance when using default canons.
    """
    if not error_message or not error_message.strip():
        return []

    # Use cached patterns if canons match the loaded data, otherwise compile fresh
    loaded = _CANONS
    if loaded is not None and canons is loaded:
        compiled = _get_compiled_patterns()
    else:
        compiled = _compile_patterns(canons)

    matches = []
    for canon, pattern in compiled:
        if pattern is None:
            continue
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

    matches.sort(key=lambda m: m["fix_success_rate"], reverse=True)
    return matches


def lookup_by_id(error_id: str, canons: list[dict]) -> dict | None:
    """Look up a specific error by its ID using O(1) dict index."""
    loaded = _CANONS
    if loaded is not None and canons is loaded:
        return _get_id_index().get(error_id)
    # Fall back to linear scan for non-default canons
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
        "nextjs": [
            "next.js", "nextjs", "next/", "getserverside",
            "getstaticprops", "app router",
        ],
        "react": ["react", "usestate", "useeffect", "jsx", "component"],
        "pip": ["pip install", "pip3", "pypi", "wheel", "sdist"],
        "java": [
            "java", "jvm", "maven", "gradle", "classnotfound",
            "nullpointerexception", "spring", ".jar",
        ],
        "database": [
            "sql", "mysql", "postgres", "mongodb", "redis",
            "sqlite", "deadlock", "connection pool",
        ],
        "cicd": [
            "github actions", "jenkins", "gitlab ci", "circleci",
            "pipeline", "workflow", "deploy", "artifact",
        ],
        "php": [
            "php", "laravel", "composer", "symfony",
            "artisan", "eloquent",
        ],
        "dotnet": [
            ".net", "dotnet", "c#", "csharp", "nuget",
            "aspnet", "blazor", "entity framework",
        ],
        "networking": [
            "connection refused", "timeout", "dns", "ssl",
            "tls", "certificate", "econnrefused", "socket",
        ],
    }
    for domain, keywords in keyword_map.items():
        for kw in keywords:
            if kw in msg:
                suggestions.append(domain)
                break
    return ", ".join(suggestions) if suggestions else "unknown"


# === MCP Tools Definition ===

TOOLS = [
    {
        "name": "lookup_error",
        "description": (
            "Match an error message against deadends.dev's database of known "
            "errors. Returns dead ends (what NOT to try), workarounds (what "
            "works), and error chains (what comes next). Use this BEFORE "
            "attempting to fix any error to avoid wasting time on approaches "
            f"that are known to fail. Covers {DOMAIN_COUNT} domains: "
            f"{DOMAIN_LIST}."
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
            f"Domains include: {DOMAIN_LIST}."
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
    {
        "name": "get_error_chain",
        "description": (
            "Traverse the error transition graph for a specific error. "
            "Shows what errors typically follow this one (leads_to), "
            "what errors usually precede it (preceded_by), and what "
            "errors are frequently confused with it. Use this to "
            "diagnose cascading failures and predict what comes next."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_id": {
                    "type": "string",
                    "description": (
                        "The error ID (domain/slug/env) to get the "
                        "transition graph for"
                    ),
                }
            },
            "required": ["error_id"],
        },
        "annotations": {
            "title": "Error chain",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
]


def handle_request(method: str, params: dict, canons: list[dict]) -> dict | None:
    """Handle a JSON-RPC MCP request. Shared by stdio and HTTP servers."""
    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
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
        return _handle_tool_call(tool_name, args, canons)

    elif method == "notifications/initialized":
        return None  # No response needed for notifications

    return {"error": {"code": -32601, "message": f"Unknown method: {method}"}}


def _handle_tool_call(tool_name: str, args: dict, canons: list[dict]) -> dict:
    """Route tool calls to appropriate handlers."""
    if tool_name == "lookup_error":
        return _tool_lookup_error(args, canons)
    elif tool_name == "get_error_detail":
        return _tool_get_error_detail(args, canons)
    elif tool_name == "list_error_domains":
        return _tool_list_error_domains(canons)
    elif tool_name == "search_errors":
        return _tool_search_errors(args, canons)
    elif tool_name == "list_errors_by_domain":
        return _tool_list_errors_by_domain(args, canons)
    elif tool_name == "batch_lookup":
        return _tool_batch_lookup(args, canons)
    elif tool_name == "get_domain_stats":
        return _tool_get_domain_stats(args, canons)
    elif tool_name == "get_error_chain":
        return _tool_get_error_chain(args, canons)
    return {
        "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
        "isError": True,
    }


def _tool_lookup_error(args: dict, canons: list[dict]) -> dict:
    error_msg = args.get("error_message", "").strip()
    if not error_msg:
        return {
            "content": [{
                "type": "text",
                "text": (
                    "Empty error message. Please provide the "
                    "full error message to look up."
                ),
            }],
        }
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


def _tool_get_error_detail(args: dict, canons: list[dict]) -> dict:
    error_id = args.get("error_id", "")
    canon = lookup_by_id(error_id, canons)
    if not canon:
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


def _tool_list_error_domains(canons: list[dict]) -> dict:
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


def _tool_search_errors(args: dict, canons: list[dict]) -> dict:
    query = args.get("query", "").strip().lower()
    if not query:
        return {
            "content": [{
                "type": "text",
                "text": "Empty search query. Provide keywords.",
            }],
        }
    domain_filter = args.get("domain", "")
    limit = min(args.get("limit", 10), 20)
    scored = []
    _stopwords = {
        "", "the", "a", "an", "is", "of", "in", "to",
        "for", "and", "or", "no", "not", "on", "at",
        "error", "failed", "exception", "cannot",
    }
    for c in canons:
        if domain_filter and c["error"]["domain"] != domain_filter:
            continue
        score = 0
        sig = c["error"]["signature"].lower()
        summary = c["verdict"]["summary"].lower()
        q_words = set(query.split()) - _stopwords
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


def _tool_list_errors_by_domain(args: dict, canons: list[dict]) -> dict:
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


def _tool_batch_lookup(args: dict, canons: list[dict]) -> dict:
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


def _tool_get_domain_stats(args: dict, canons: list[dict]) -> dict:
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
            if isinstance(conf, (int, float)):
                conf_label = (
                    "high" if conf >= 0.8
                    else "medium" if conf >= 0.5
                    else "low"
                )
            else:
                conf_label = str(conf)
            conf_levels[conf_label] = (
                conf_levels.get(conf_label, 0) + 1
            )
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


def _tool_get_error_chain(args: dict, canons: list[dict]) -> dict:
    error_id = args.get("error_id", "")
    canon = lookup_by_id(error_id, canons)
    if not canon:
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
            text = f"Error ID not found: {error_id}"
    else:
        graph = canon.get("transition_graph", {})
        parts = [
            f"## Error Chain: {canon['error']['signature']}",
            f"ID: {error_id}\n",
        ]
        leads_to = graph.get("leads_to", [])
        if leads_to:
            parts.append("### This error often leads to:")
            for lt in leads_to:
                lt_canon = lookup_by_id(lt["error_id"], canons)
                if lt_canon:
                    sig = lt_canon["error"]["signature"]
                    rate = int(
                        lt_canon["verdict"]["fix_success_rate"] * 100
                    )
                    parts.append(
                        f"- **{sig}** (p={lt['probability']}, "
                        f"fix rate: {rate}%) — {lt['error_id']}"
                    )
                else:
                    parts.append(
                        f"- {lt['error_id']} "
                        f"(p={lt['probability']})"
                    )
                if lt.get("condition"):
                    parts.append(
                        f"  Condition: {lt['condition']}"
                    )
            parts.append("")

        preceded = graph.get("preceded_by", [])
        if preceded:
            parts.append("### Usually preceded by:")
            for pb in preceded:
                pb_canon = lookup_by_id(pb["error_id"], canons)
                if pb_canon:
                    sig = pb_canon["error"]["signature"]
                    parts.append(
                        f"- **{sig}** (p={pb['probability']}) "
                        f"— {pb['error_id']}"
                    )
                else:
                    parts.append(
                        f"- {pb['error_id']} "
                        f"(p={pb['probability']})"
                    )
            parts.append("")

        confused = graph.get("frequently_confused_with", [])
        if confused:
            parts.append("### Frequently confused with:")
            for fc in confused:
                fc_canon = lookup_by_id(fc["error_id"], canons)
                if fc_canon:
                    sig = fc_canon["error"]["signature"]
                    parts.append(
                        f"- **{sig}** — {fc['error_id']}"
                    )
                else:
                    parts.append(f"- {fc['error_id']}")
                if fc.get("distinction"):
                    parts.append(
                        f"  Distinction: {fc['distinction']}"
                    )
            parts.append("")

        if not leads_to and not preceded and not confused:
            parts.append(
                "No transition graph data for this error. "
                "It may be a standalone error."
            )

        text = "\n".join(parts)
    return {"content": [{"type": "text", "text": text}]}
