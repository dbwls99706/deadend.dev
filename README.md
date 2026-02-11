# deadends.dev

**Structured failure knowledge for AI coding agents.**

501 error entries across 14 domains. When AI agents encounter errors, they waste tokens on approaches that are known to fail. deadends.dev tells agents what NOT to try, what actually works, and what error comes next.

## Installation

```bash
pip install deadends-dev
```

**Requirements:** Python 3.10+

## MCP Server

The MCP server exposes 7 tools for AI coding agents:

| Tool | Description |
|------|-------------|
| `lookup_error` | Match an error message against 501 known patterns. Returns dead ends, workarounds, and error chains. |
| `get_error_detail` | Get full details for a specific error by ID (e.g., `python/modulenotfounderror/py311-linux`). |
| `list_error_domains` | List all 14 error domains and their counts. |
| `search_errors` | Fuzzy keyword search across all domains (e.g., "memory limit", "permission denied"). |
| `list_errors_by_domain` | List all errors in a specific domain, sorted by fix rate, name, or confidence. |
| `batch_lookup` | Look up multiple error messages at once (max 10). |
| `get_domain_stats` | Get quality metrics for a domain: avg fix rate, resolvability, confidence breakdown. |

### Local (Claude Desktop / Cursor)

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "deadend": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "/path/to/deadend.dev"
    }
  }
}
```

### Hosted (Smithery)

Available on [Smithery](https://smithery.ai/server/deadend/deadends-dev) — no local setup required.

### Example Response

When an agent encounters `ModuleNotFoundError: No module named 'torch'`, the `lookup_error` tool returns:

```
## ModuleNotFoundError: No module named 'X' (Python 3.11+)
Resolvable: true | Fix rate: 0.88

### Dead Ends (DO NOT TRY):
- pip install X with system Python (fails 70%): venv not activated

### Workarounds (TRY THESE):
- Create venv, activate, then pip install (works 95%)
- Use python -m pip install instead of bare pip (works 90%)
```

## Quick Start — Python SDK

```python
from generator.lookup import lookup, batch_lookup, search

# Single error lookup
result = lookup("ModuleNotFoundError: No module named 'torch'")

# What NOT to try (saves tokens and time)
for d in result["dead_ends"]:
    print(f"AVOID: {d['action']} — fails {int(d['fail_rate']*100)}%")

# What actually works
for w in result["workarounds"]:
    print(f"TRY: {w['action']} — works {int(w['success_rate']*100)}%")

# Batch lookup (multiple errors at once)
results = batch_lookup([
    "ModuleNotFoundError: No module named 'torch'",
    "CUDA error: out of memory",
    "CrashLoopBackOff",
])

# Keyword search
hits = search("memory limit", domain="docker", limit=5)
```

## Quick Start — CLI

```bash
pip install deadends-dev
deadends "CUDA error: out of memory"
deadends --list  # show all known errors
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| [`/api/v1/match.json`](https://deadends.dev/api/v1/match.json) | Lightweight regex matching (fits in context window) |
| [`/api/v1/index.json`](https://deadends.dev/api/v1/index.json) | Full error index with all metadata |
| `/api/v1/{domain}/{slug}/{env}.json` | Individual error canon |
| [`/api/v1/openapi.json`](https://deadends.dev/api/v1/openapi.json) | OpenAPI 3.1 spec with response examples |
| [`/api/v1/stats.json`](https://deadends.dev/api/v1/stats.json) | Dataset quality metrics by domain |
| [`/api/v1/errors.ndjson`](https://deadends.dev/api/v1/errors.ndjson) | NDJSON streaming (one error per line) |
| [`/api/v1/version.json`](https://deadends.dev/api/v1/version.json) | Service metadata and endpoint directory |
| [`/llms.txt`](https://deadends.dev/llms.txt) | LLM-optimized error listing ([llmstxt.org](https://llmstxt.org) standard) |
| [`/llms-full.txt`](https://deadends.dev/llms-full.txt) | Complete database dump |
| [`/.well-known/ai-plugin.json`](https://deadends.dev/.well-known/ai-plugin.json) | AI plugin manifest |
| [`/.well-known/agent-card.json`](https://deadends.dev/.well-known/agent-card.json) | Google A2A agent card |
| [`/.well-known/security.txt`](https://deadends.dev/.well-known/security.txt) | Security contact (RFC 9116) |

## Covered Domains (14)

| Domain | Errors | Examples |
|--------|--------|----------|
| python | 86 | ModuleNotFoundError, TypeError, KeyError, MemoryError, RecursionError |
| node | 61 | ERR_MODULE_NOT_FOUND, EACCES, EADDRINUSE, heap OOM, ERR_REQUIRE_ESM |
| docker | 43 | no space left, exec format error, bind address in use, healthcheck |
| git | 34 | failed to push, merge conflicts, detached HEAD, stash apply, tags |
| kubernetes | 34 | CrashLoopBackOff, ImagePullBackOff, OOMKilled, RBAC forbidden, HPA |
| go | 32 | nil pointer, unused import, interface conversion, slice out of range |
| nextjs | 30 | hydration failed, dynamic server, searchParams, metadata, Suspense |
| aws | 29 | AccessDenied, S3 NoSuchBucket, Lambda timeout, SQS, Secrets Manager |
| react | 28 | invalid hook call, too many re-renders, unique key, context, act() |
| terraform | 27 | state lock, cycle, provider not found, moved block, backend init |
| cuda | 25 | OOM, device-side assert, NCCL, cuDNN, nvcc not found, kernel image |
| typescript | 25 | TS2307, TS2322, TS2345, TS2532, TS7053, TS2769, TS18048 |
| pip | 24 | build wheel failed, conflicting deps, externally-managed, hash mismatch |
| rust | 23 | E0382 borrow, E0308 mismatch, E0277 trait, E0106 lifetime, E0507 |

## ErrorCanon Data Format

Each error is a JSON file with:

```json
{
  "error": { "signature": "...", "regex": "...", "domain": "..." },
  "verdict": { "resolvable": "true|partial|false", "fix_success_rate": 0.88 },
  "dead_ends": [{ "action": "...", "why_fails": "...", "fail_rate": 0.75 }],
  "workarounds": [{ "action": "...", "success_rate": 0.92, "how": "..." }],
  "transition_graph": { "leads_to": [...], "preceded_by": [...] }
}
```

## AI Agent Integration — 15 Discovery Formats

Every page on deadends.dev includes machine-readable data in 15 formats:

| Format | Location | Purpose |
|--------|----------|---------|
| JSON API | `/api/v1/{id}.json` | RESTful error data per canon |
| match.json | `/api/v1/match.json` | Compact regex-only file (load entire DB into context) |
| index.json | `/api/v1/index.json` | Master error index with metadata |
| stats.json | `/api/v1/stats.json` | Dataset quality metrics per domain |
| errors.ndjson | `/api/v1/errors.ndjson` | Streaming NDJSON for batch processing |
| OpenAPI | `/api/v1/openapi.json` | Full API spec with response examples |
| JSON-LD | Every `<head>` | Schema.org TechArticle + FAQPage |
| ai-summary | Every page | `<pre id="ai-summary">` KEY=VALUE blocks |
| llms.txt | `/llms.txt` | llmstxt.org standard |
| llms-full.txt | `/llms-full.txt` | Complete database dump |
| ai-plugin.json | `/.well-known/` | OpenAI plugin manifest |
| agent-card.json | `/.well-known/` | Google A2A protocol |
| security.txt | `/.well-known/` | RFC 9116 security contact |
| robots.txt | `/robots.txt` | 34 AI crawlers explicitly welcomed |
| CLAUDE.md | `/CLAUDE.md` | AI coding agent instructions |

## Development

```bash
pip install -e ".[dev]"

# Full pipeline (validate → generate → build → test)
python -m generator.pipeline

# Individual steps
python -m generator.bulk_generate     # Generate canons from seeds
python -m generator.build_site        # Build static site
python -m generator.validate          # Validate data + site
python -m pytest tests/ -v            # Run tests
```

## Contributing

Add error definitions to `generator/bulk_generate.py` or create JSON files directly in `data/canons/`.

```bash
python -m generator.validate --data-only  # Validate before submitting
```

## License

MIT (code) · CC BY 4.0 (data)
