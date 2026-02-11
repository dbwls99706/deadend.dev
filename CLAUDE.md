# deadend.dev

Structured failure knowledge database for AI coding agents.
87 error entries across 14 domains (python, node, docker, cuda, git, pip, typescript, rust, go, kubernetes, terraform, aws, nextjs, react).

## Architecture

- `data/canons/` — ErrorCanon JSON files (source of truth)
- `generator/` — Build system, validation, bulk generation
- `generator/templates/` — Jinja2 HTML templates
- `site/` — Generated static site (do not edit directly)
- `mcp/` — Model Context Protocol server for AI agent integration
- `tests/` — pytest test suite

## Key Commands

```bash
python -m generator.pipeline          # Full pipeline (validate → generate → build → test)
python -m generator.build_site        # Build static site only
python -m generator.bulk_generate     # Generate canon JSON from seeds
python -m generator.validate          # Validate data + site
python -m pytest tests/ -v            # Run tests
python -m generator.lookup "error"    # Look up an error
python -m mcp.server                  # Run MCP server (stdio)
```

## ErrorCanon Schema

Each error has: `error` (signature, regex, domain), `verdict` (resolvable, fix_success_rate), `dead_ends[]` (what NOT to try), `workarounds[]` (what works), `transition_graph` (leads_to, preceded_by, frequently_confused_with).

## Conventions

- Canon IDs follow `{domain}/{slug}/{env}` pattern (e.g., `python/modulenotfounderror/py311-linux`)
- Always validate after changes: `python -m generator.validate --data-only`
- Bulk-generated canons are in `generator/bulk_generate.py` — add new errors there
- Templates use Jinja2 with autoescape enabled
- All HTML pages include machine-readable `<pre id="ai-summary">` blocks and JSON-LD
- API responses at `/api/v1/{id}.json` mirror the canon JSON exactly
- Lint with ruff: `ruff check .`

## Error Lookup (for AI agents working in this repo)

When encountering errors while developing, use the lookup SDK:
```python
from generator.lookup import lookup
result = lookup("your error message")
# result["dead_ends"] = what NOT to try
# result["workarounds"] = what works
```
