# deadend.dev

**Structured failure knowledge for AI coding agents.**

87 error entries across 14 domains. When AI agents encounter errors, they waste tokens on approaches that are known to fail. deadend.dev tells agents what NOT to try, what actually works, and what error comes next.

## Quick Start — Python SDK

```python
from generator.lookup import lookup

result = lookup("ModuleNotFoundError: No module named 'torch'")

# What NOT to try (saves tokens and time)
for d in result["dead_ends"]:
    print(f"AVOID: {d['action']} — fails {int(d['fail_rate']*100)}%")

# What actually works
for w in result["workarounds"]:
    print(f"TRY: {w['action']} — works {int(w['success_rate']*100)}%")
```

## Quick Start — CLI

```bash
pip install -e .
python -m generator.lookup "CUDA error: out of memory"
python -m generator.lookup --list  # show all known errors
```

## Quick Start — MCP Server (Claude Desktop / Cursor)

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

Then Claude will automatically check deadend.dev when encountering errors.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| [`/api/v1/match.json`](https://deadends.dev/api/v1/match.json) | Lightweight regex matching (fits in context window) |
| [`/api/v1/index.json`](https://deadends.dev/api/v1/index.json) | Full error index with all metadata |
| `/api/v1/{domain}/{slug}/{env}.json` | Individual error canon |
| [`/api/v1/openapi.json`](https://deadends.dev/api/v1/openapi.json) | OpenAPI 3.1 spec |
| [`/llms.txt`](https://deadends.dev/llms.txt) | LLM-optimized error listing ([llmstxt.org](https://llmstxt.org) standard) |
| [`/llms-full.txt`](https://deadends.dev/llms-full.txt) | Complete database dump |
| [`/.well-known/ai-plugin.json`](https://deadends.dev/.well-known/ai-plugin.json) | AI plugin manifest |

## Covered Domains (14)

| Domain | Errors | Examples |
|--------|--------|----------|
| python | 20 | ModuleNotFoundError, TypeError, KeyError, MemoryError |
| node | 11 | ERR_MODULE_NOT_FOUND, EACCES, ERR_REQUIRE_ESM, heap OOM |
| docker | 10 | permission denied, no space left, exec format error |
| cuda | 9 | OOM, version mismatch, device-side assert, NCCL timeout |
| git | 6 | failed to push refs, merge conflicts, pathspec errors |
| pip | 6 | build wheel failed, conflicting dependencies |
| typescript | 4 | TS2307, TS2322, TS2345, TS7006 |
| rust | 3 | E0382 borrow, E0308 mismatch, E0277 trait bound |
| go | 3 | undefined reference, imported not used, type mismatch |
| kubernetes | 3 | CrashLoopBackOff, ImagePullBackOff, OOMKilled |
| terraform | 3 | state lock, provider not present, cycle |
| aws | 3 | AccessDenied, ExpiredToken, ResourceNotFound |
| nextjs | 3 | hydration failed, module not found, server component hooks |
| react | 3 | invalid hook call, too many re-renders, update while rendering |

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

## AI Agent Integration

Every page on deadend.dev includes 8 machine-readable formats:

1. **JSON API** — RESTful error data at `/api/v1/{id}.json`
2. **match.json** — Compact regex-only file (load entire DB into context)
3. **JSON-LD** — Schema.org TechArticle + FAQPage in every `<head>`
4. **ai-summary** — `<pre id="ai-summary">` with KEY=VALUE pairs
5. **llms.txt** — [llmstxt.org](https://llmstxt.org) standard
6. **OpenAPI** — Full API specification
7. **ai-plugin.json** — Plugin discovery manifest
8. **robots.txt** — All AI crawlers explicitly welcomed

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
