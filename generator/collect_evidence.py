"""Step 3: Collect evidence for error-environment pairs.

Uses StackOverflow API and GitHub API to collect related questions, answers,
and issues for each error-environment pair.

Output: data/pipeline/evidence/{pair_id}.json

Usage:
    python -m generator.collect_evidence [--input pairs.jsonl] [--resume]
"""

import argparse
import json
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).parent.parent
PIPELINE_DIR = PROJECT_ROOT / "data" / "pipeline"
PAIRS_FILE = PIPELINE_DIR / "pairs.jsonl"
EVIDENCE_DIR = PIPELINE_DIR / "evidence"

SO_API_BASE = "https://api.stackexchange.com/2.3"
GH_API_BASE = "https://api.github.com"

# Rate limiting config
SO_REQUESTS_PER_SECOND = 0.5  # Conservative
GH_REQUESTS_PER_SECOND = 1.0

# Domain → search terms for finding related content
DOMAIN_SEARCH_CONFIG = {
    "python": {
        "so_tags": ["python", "python-3.x"],
        "gh_repos": ["python/cpython"],
    },
    "cuda": {
        "so_tags": ["cuda", "pytorch"],
        "gh_repos": ["pytorch/pytorch", "NVIDIA/cuda-samples"],
    },
    "node": {
        "so_tags": ["node.js", "npm"],
        "gh_repos": ["nodejs/node"],
    },
    "docker": {
        "so_tags": ["docker", "docker-compose"],
        "gh_repos": ["moby/moby"],
    },
    "pip": {
        "so_tags": ["pip", "python-packaging"],
        "gh_repos": ["pypa/pip"],
    },
    "git": {
        "so_tags": ["git"],
        "gh_repos": ["git/git"],
    },
}


def search_so(query: str, tags: list[str], so_key: str | None = None,
              pagesize: int = 10) -> list[dict]:
    """Search StackOverflow for questions matching the query."""
    params = {
        "order": "desc",
        "sort": "relevance",
        "q": query,
        "tagged": ";".join(tags),
        "filter": "withbody",
        "site": "stackoverflow",
        "pagesize": pagesize,
    }
    if so_key:
        params["key"] = so_key

    try:
        resp = requests.get(f"{SO_API_BASE}/search/advanced", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("backoff"):
            time.sleep(data["backoff"])

        return data.get("items", [])
    except requests.RequestException as e:
        print(f"    SO search failed: {e}")
        return []


def fetch_so_answers(question_id: int, so_key: str | None = None) -> list[dict]:
    """Fetch answers for a StackOverflow question."""
    params = {
        "order": "desc",
        "sort": "votes",
        "filter": "withbody",
        "site": "stackoverflow",
    }
    if so_key:
        params["key"] = so_key

    try:
        resp = requests.get(
            f"{SO_API_BASE}/questions/{question_id}/answers",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("backoff"):
            time.sleep(data["backoff"])

        return data.get("items", [])
    except requests.RequestException as e:
        print(f"    SO answers fetch failed: {e}")
        return []


def search_gh_issues(query: str, repo: str, gh_token: str | None = None,
                     per_page: int = 10) -> list[dict]:
    """Search GitHub issues for a query within a specific repo."""
    headers = {"Accept": "application/vnd.github+json"}
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"

    params = {
        "q": f"{query} repo:{repo} is:issue",
        "sort": "reactions",
        "order": "desc",
        "per_page": per_page,
    }

    try:
        resp = requests.get(
            f"{GH_API_BASE}/search/issues",
            headers=headers,
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("items", [])
    except requests.RequestException as e:
        print(f"    GH search failed: {e}")
        return []


def collect_evidence_for_pair(pair: dict, so_key: str | None = None,
                              gh_token: str | None = None) -> dict:
    """Collect all available evidence for a single error-environment pair."""
    domain = pair["signature"]["domain"]
    signature = pair["signature"]["signature"]
    config = DOMAIN_SEARCH_CONFIG.get(domain, {"so_tags": [], "gh_repos": []})

    evidence = {
        "pair_id": pair["id"],
        "signature": signature,
        "domain": domain,
        "environment": pair["environment"],
        "stackoverflow": [],
        "github_issues": [],
        "collection_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # Search StackOverflow
    so_tags = config.get("so_tags", [])
    if so_tags:
        # Extract key words from signature for search
        search_query = signature[:200]  # SO query length limit
        questions = search_so(search_query, so_tags, so_key=so_key, pagesize=5)
        time.sleep(1 / SO_REQUESTS_PER_SECOND)

        for q in questions:
            q_data = {
                "question_id": q["question_id"],
                "title": q.get("title", ""),
                "body": q.get("body", "")[:2000],  # Truncate for storage
                "score": q.get("score", 0),
                "view_count": q.get("view_count", 0),
                "answer_count": q.get("answer_count", 0),
                "is_answered": q.get("is_answered", False),
                "link": q.get("link", ""),
                "tags": q.get("tags", []),
                "answers": [],
            }

            # Fetch top answers if the question has them
            if q.get("answer_count", 0) > 0:
                answers = fetch_so_answers(q["question_id"], so_key=so_key)
                time.sleep(1 / SO_REQUESTS_PER_SECOND)

                for a in answers[:3]:  # Top 3 answers
                    q_data["answers"].append({
                        "answer_id": a.get("answer_id"),
                        "body": a.get("body", "")[:2000],
                        "score": a.get("score", 0),
                        "is_accepted": a.get("is_accepted", False),
                    })

            evidence["stackoverflow"].append(q_data)

    # Search GitHub Issues
    for repo in config.get("gh_repos", []):
        search_query = signature[:256]
        issues = search_gh_issues(search_query, repo, gh_token=gh_token, per_page=5)
        time.sleep(1 / GH_REQUESTS_PER_SECOND)

        for issue in issues:
            evidence["github_issues"].append({
                "number": issue.get("number"),
                "title": issue.get("title", ""),
                "body": (issue.get("body", "") or "")[:2000],
                "state": issue.get("state", ""),
                "comments": issue.get("comments", 0),
                "reactions": issue.get("reactions", {}).get("total_count", 0),
                "html_url": issue.get("html_url", ""),
                "labels": [lbl.get("name", "") for lbl in issue.get("labels", [])],
            })

    total = len(evidence["stackoverflow"]) + len(evidence["github_issues"])
    evidence["total_sources"] = total

    return evidence


def main():
    parser = argparse.ArgumentParser(description="Collect evidence for error-env pairs")
    parser.add_argument("--input", type=Path, default=PAIRS_FILE, help="Input pairs file")
    parser.add_argument("--output-dir", type=Path, default=EVIDENCE_DIR, help="Output directory")
    parser.add_argument("--so-key", default=None, help="StackOverflow API key")
    parser.add_argument("--gh-token", default=None, help="GitHub API token")
    parser.add_argument("--resume", action="store_true",
                        help="Skip pairs that already have evidence files")
    parser.add_argument("--limit", type=int, default=0, help="Max pairs to process (0=all)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be collected")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Load pairs
    pairs = []
    with open(args.input, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))

    print(f"Loaded {len(pairs)} pairs")

    # Filter already-processed if resuming
    if args.resume:
        remaining = []
        for pair in pairs:
            evidence_file = args.output_dir / f"{pair['id'].replace('/', '_')}.json"
            if not evidence_file.exists():
                remaining.append(pair)
        print(f"  Resuming: {len(pairs) - len(remaining)} already done, {len(remaining)} remaining")
        pairs = remaining

    if args.limit > 0:
        pairs = pairs[:args.limit]
        print(f"  Limited to {len(pairs)} pairs")

    if args.dry_run:
        for pair in pairs:
            print(f"  Would collect: {pair['id']}")
        return

    # Collect evidence
    for i, pair in enumerate(pairs):
        pair_id = pair["id"]
        print(f"[{i + 1}/{len(pairs)}] Collecting evidence for {pair_id}...")

        evidence = collect_evidence_for_pair(pair, so_key=args.so_key, gh_token=args.gh_token)

        # Save evidence
        evidence_file = args.output_dir / f"{pair_id.replace('/', '_')}.json"
        evidence_file.parent.mkdir(parents=True, exist_ok=True)
        with open(evidence_file, "w", encoding="utf-8") as f:
            json.dump(evidence, f, indent=2, ensure_ascii=False)

        print(f"  Collected {evidence['total_sources']} sources")

    print(f"\nDone! Evidence collected for {len(pairs)} pairs in {args.output_dir}")


if __name__ == "__main__":
    main()
