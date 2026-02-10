"""Step 4: Generate ErrorCanon entries from collected evidence.

Uses Claude API to analyze evidence and generate structured ErrorCanon JSON
with dead_ends, workarounds, verdicts, and transition_graph edges.

Output: data/canons/{domain}/{slug}/{env}.json

Usage:
    python -m generator.generate_canons [--input-dir evidence/] [--validate]
"""

import argparse
import json
import time
from pathlib import Path

import anthropic
from jsonschema import ValidationError, validate

from generator.schema import ERRORCANON_SCHEMA
from generator.validate import validate_canon_json

PROJECT_ROOT = Path(__file__).parent.parent
PIPELINE_DIR = PROJECT_ROOT / "data" / "pipeline"
EVIDENCE_DIR = PIPELINE_DIR / "evidence"
CANONS_DIR = PROJECT_ROOT / "data" / "canons"

CANON_GENERATION_PROMPT = """\
You are an expert at analyzing software errors. Given evidence about an error \
in a specific environment, generate a structured ErrorCanon JSON entry.

## Error Signature
{signature}

## Environment
{environment}

## Evidence from StackOverflow
{so_evidence}

## Evidence from GitHub Issues
{gh_evidence}

## Instructions

Generate a complete ErrorCanon JSON object with the following structure. \
Be factual and specific. Base your analysis on the evidence provided.

{{
  "schema_version": "1.0.0",
  "id": "{pair_id}",
  "url": "https://deadend.dev/{pair_id}",
  "error": {{
    "signature": "<exact error message pattern>",
    "regex": "<valid Python regex matching this error>",
    "domain": "{domain}",
    "category": "<category like: resource_exhaustion, import, filesystem, etc>",
    "first_seen": "<YYYY-MM-DD>",
    "last_confirmed": "<YYYY-MM-DD>"
  }},
  "environment": {environment_json},
  "verdict": {{
    "resolvable": "<true|partial|false>",
    "fix_success_rate": <0.0-1.0>,
    "confidence": <0.0-1.0>,
    "last_updated": "<YYYY-MM-DD>",
    "summary": "<2-3 sentence summary of the situation>"
  }},
  "dead_ends": [
    {{
      "action": "<what people try that doesn't work>",
      "why_fails": "<technical explanation>",
      "fail_rate": <0.0-1.0>,
      "sources": ["<url>"],
      "common_misconception": "<optional: why people think this works>"
    }}
  ],
  "workarounds": [
    {{
      "action": "<what actually works>",
      "how": "<specific command or steps>",
      "success_rate": <0.0-1.0>,
      "tradeoff": "<what you give up>",
      "condition": "<when this applies>",
      "sources": ["<url>"]
    }}
  ],
  "transition_graph": {{
    "leads_to": [],
    "preceded_by": [],
    "frequently_confused_with": []
  }},
  "metadata": {{
    "generated_by": "deadend-pipeline-v1",
    "generation_date": "{today}",
    "review_status": "auto_generated",
    "evidence_count": {evidence_count},
    "page_views": 0,
    "ai_agent_hits": 0,
    "human_hits": 0,
    "last_verification": "{today}"
  }}
}}

Rules:
- dead_ends must have at least 1 item
- All rates must be between 0.0 and 1.0
- If resolvable="true": fix_success_rate >= 0.7 and confidence >= 0.6
- If resolvable="false": fix_success_rate < 0.2 and confidence >= 0.6
- regex must be a valid Python regular expression
- Focus on NEGATIVE KNOWLEDGE: what doesn't work is more valuable than what does
- Be specific about environment conditions that affect the outcome
- Include source URLs from the evidence where available

Return ONLY the JSON object, no markdown fences or explanation.
"""


def format_so_evidence(evidence: dict) -> str:
    """Format StackOverflow evidence for the prompt."""
    if not evidence.get("stackoverflow"):
        return "No StackOverflow evidence available."

    parts = []
    for q in evidence["stackoverflow"][:5]:
        part = f"### Q: {q['title']} (score: {q['score']}, views: {q['view_count']})\n"
        part += f"{q['body'][:500]}\n"
        if q.get("link"):
            part += f"URL: {q['link']}\n"

        for a in q.get("answers", [])[:2]:
            accepted = " [ACCEPTED]" if a.get("is_accepted") else ""
            part += f"\n**Answer{accepted} (score: {a['score']}):**\n{a['body'][:500]}\n"

        parts.append(part)

    return "\n---\n".join(parts)


def format_gh_evidence(evidence: dict) -> str:
    """Format GitHub evidence for the prompt."""
    if not evidence.get("github_issues"):
        return "No GitHub Issues evidence available."

    parts = []
    for issue in evidence["github_issues"][:5]:
        part = f"### Issue #{issue['number']}: {issue['title']} ({issue['state']})\n"
        part += f"Comments: {issue['comments']}, Reactions: {issue['reactions']}\n"
        if issue.get("labels"):
            part += f"Labels: {', '.join(issue['labels'])}\n"
        part += f"{issue['body'][:500]}\n"
        if issue.get("html_url"):
            part += f"URL: {issue['html_url']}\n"
        parts.append(part)

    return "\n---\n".join(parts)


def generate_canon_from_evidence(evidence: dict, client: anthropic.Anthropic,
                                 model: str = "claude-sonnet-4-5-20250929") -> dict | None:
    """Use Claude API to generate an ErrorCanon from evidence."""
    today = time.strftime("%Y-%m-%d")

    prompt = CANON_GENERATION_PROMPT.format(
        signature=evidence["signature"],
        environment=json.dumps(evidence["environment"], indent=2),
        environment_json=json.dumps(evidence["environment"], indent=2),
        so_evidence=format_so_evidence(evidence),
        gh_evidence=format_gh_evidence(evidence),
        pair_id=evidence["pair_id"],
        domain=evidence["domain"],
        today=today,
        evidence_count=evidence.get("total_sources", 0),
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()

        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        canon = json.loads(text)
        return canon

    except json.JSONDecodeError as e:
        print(f"    Failed to parse Claude response as JSON: {e}")
        return None
    except anthropic.APIError as e:
        print(f"    Claude API error: {e}")
        return None


def validate_and_fix(canon: dict) -> tuple[dict, list[str]]:
    """Validate a generated canon and attempt auto-fixes for common issues."""
    issues = []

    # Ensure required metadata fields
    if "metadata" not in canon:
        canon["metadata"] = {}
    meta = canon["metadata"]
    meta.setdefault("generated_by", "deadend-pipeline-v1")
    meta.setdefault("generation_date", time.strftime("%Y-%m-%d"))
    meta.setdefault("review_status", "auto_generated")
    meta.setdefault("evidence_count", 0)
    meta.setdefault("page_views", 0)
    meta.setdefault("ai_agent_hits", 0)
    meta.setdefault("human_hits", 0)
    meta.setdefault("last_verification", time.strftime("%Y-%m-%d"))

    # Ensure transition_graph structure
    if "transition_graph" not in canon:
        canon["transition_graph"] = {
            "leads_to": [],
            "preceded_by": [],
            "frequently_confused_with": [],
        }
    tg = canon["transition_graph"]
    tg.setdefault("leads_to", [])
    tg.setdefault("preceded_by", [])
    tg.setdefault("frequently_confused_with", [])

    # Clamp numeric values
    if "verdict" in canon:
        v = canon["verdict"]
        for field in ["fix_success_rate", "confidence"]:
            if field in v:
                v[field] = max(0.0, min(1.0, v[field]))

    for de in canon.get("dead_ends", []):
        if "fail_rate" in de:
            de["fail_rate"] = max(0.0, min(1.0, de["fail_rate"]))

    for wa in canon.get("workarounds", []):
        if "success_rate" in wa:
            wa["success_rate"] = max(0.0, min(1.0, wa["success_rate"]))

    # Validate against schema
    try:
        validate(instance=canon, schema=ERRORCANON_SCHEMA)
    except ValidationError as e:
        issues.append(f"Schema validation: {e.message}")

    # Run business rule validation
    errors, warnings = validate_canon_json(canon)
    issues.extend(errors)

    return canon, issues


def main():
    parser = argparse.ArgumentParser(description="Generate ErrorCanon entries from evidence")
    parser.add_argument("--input-dir", type=Path, default=EVIDENCE_DIR,
                        help="Directory with evidence JSON files")
    parser.add_argument("--output-dir", type=Path, default=CANONS_DIR,
                        help="Output directory for canon files")
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929",
                        help="Claude model to use")
    parser.add_argument("--validate", action="store_true",
                        help="Validate generated canons against schema")
    parser.add_argument("--resume", action="store_true",
                        help="Skip canons that already exist")
    parser.add_argument("--limit", type=int, default=0, help="Max canons to generate (0=all)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    args = parser.parse_args()

    # Find evidence files
    evidence_files = sorted(args.input_dir.glob("*.json"))
    if not evidence_files:
        print(f"No evidence files found in {args.input_dir}")
        return

    print(f"Found {len(evidence_files)} evidence files")

    # Initialize Claude client
    if not args.dry_run:
        client = anthropic.Anthropic()

    generated = 0
    failed = 0

    for i, evidence_file in enumerate(evidence_files):
        with open(evidence_file, encoding="utf-8") as f:
            evidence = json.load(f)

        pair_id = evidence["pair_id"]

        # Build proper path: data/canons/{domain}/{slug}/{env}.json
        parts = pair_id.split("/")
        if len(parts) == 3:
            canon_path = args.output_dir / parts[0] / parts[1] / f"{parts[2]}.json"
        else:
            canon_path = args.output_dir / f"{pair_id.replace('/', '_')}.json"

        if args.resume and canon_path.exists():
            continue

        if args.limit > 0 and generated >= args.limit:
            break

        print(f"[{i + 1}/{len(evidence_files)}] Generating canon for {pair_id}...")

        if args.dry_run:
            print(f"  Would generate: {canon_path}")
            generated += 1
            continue

        canon = generate_canon_from_evidence(evidence, client, model=args.model)
        if canon is None:
            failed += 1
            continue

        if args.validate:
            canon, issues = validate_and_fix(canon)
            if issues:
                print("  Validation issues after auto-fix:")
                for issue in issues:
                    print(f"    - {issue}")
                failed += 1
                continue

        # Write canon
        canon_path.parent.mkdir(parents=True, exist_ok=True)
        with open(canon_path, "w", encoding="utf-8") as f:
            json.dump(canon, f, indent=2, ensure_ascii=False)
            f.write("\n")

        generated += 1
        print(f"  Generated: {canon_path}")

        # Rate limiting for API calls
        time.sleep(1)

    print(f"\nDone! Generated {generated} canons, {failed} failed")


if __name__ == "__main__":
    main()
