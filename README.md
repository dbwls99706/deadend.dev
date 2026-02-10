# deadend.dev

Structured failure knowledge infrastructure for AI agents.

When AI agents hit errors, they search the web. But search results are unstructured,
environment-unaware, and often wrong for specific conditions.

**deadend.dev** provides:
- **Dead ends** — what NOT to try (and why it fails)
- **Workarounds** — what works (with success rates and tradeoffs)
- **Error chains** — what error comes next
- **Environment-specific** — same error, different GPU = different solution

## For AI Agents

Every page includes:
- `JSON-LD` structured data in `<head>`
- Plain-text `ai-summary` block
- JSON API at `/api/v1/{domain}/{error-slug}/{env-hash}.json`

URL pattern: `https://deadend.dev/{domain}/{error-slug}/{env-hash}`

## Development

```bash
pip install -e ".[dev]"
python -m generator.validate --data-only
python -m generator.build_site
pytest tests/ -v
```

## Pipeline

```
Step 1: collect_signatures.py  — Collect error signatures from SO/GitHub
Step 2: generate_pairs.py     — Generate environment combinations
Step 3: collect_evidence.py   — Gather evidence for each error+env pair
Step 4: generate_canons.py    — Generate ErrorCanon JSON via Claude API
Step 5: build_site.py         — Build static HTML from JSON
Step 6: validate.py           — Validate data and generated site
```

## Contributing

Add error data as JSON files in `data/canons/`. See existing files for format.
Run `python -m generator.validate --data-only` before submitting.

## License

MIT (code) · CC BY 4.0 (data)
