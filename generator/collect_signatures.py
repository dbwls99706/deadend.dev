"""Step 1: Collect error signatures from public sources.

Sources: StackOverflow API, GitHub Issues API, manual seed signatures.
Output: data/pipeline/signatures.jsonl

Usage:
    python -m generator.collect_signatures [--so-tag python] [--gh-repo pytorch/pytorch]
"""

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).parent.parent
PIPELINE_DIR = PROJECT_ROOT / "data" / "pipeline"
SIGNATURES_FILE = PIPELINE_DIR / "signatures.jsonl"

SO_API_BASE = "https://api.stackexchange.com/2.3"
GH_API_BASE = "https://api.github.com"

# Manual seed signatures for bootstrapping
SEED_SIGNATURES = [
    {
        "signature": "RuntimeError: CUDA out of memory. Tried to allocate X GiB",
        "regex": r"RuntimeError: CUDA out of memory\. Tried to allocate \d+\.\d+ [GM]iB",
        "domain": "python",
        "category": "resource_exhaustion",
        "source": "manual_seed",
    },
    {
        "signature": "ModuleNotFoundError: No module named 'X'",
        "regex": r"ModuleNotFoundError: No module named '.+'",
        "domain": "python",
        "category": "import",
        "source": "manual_seed",
    },
    {
        "signature": "Error: ENOENT: no such file or directory",
        "regex": r"Error: ENOENT: no such file or directory, (?:open|stat|lstat|access) '.+'",
        "domain": "node",
        "category": "filesystem",
        "source": "manual_seed",
    },
    {
        "signature": (
            "FATAL ERROR: CALL_AND_RETRY_LAST Allocation failed"
            " - JavaScript heap out of memory"
        ),
        "regex": r"FATAL ERROR: (?:CALL_AND_RETRY_LAST|Reached heap limit) Allocation failed",
        "domain": "node",
        "category": "resource_exhaustion",
        "source": "manual_seed",
    },
    {
        "signature": "Error: listen EADDRINUSE: address already in use",
        "regex": r"Error: listen EADDRINUSE: address already in use [:\d]+",
        "domain": "node",
        "category": "network",
        "source": "manual_seed",
    },
    {
        "signature": "Got permission denied while trying to connect to the Docker daemon socket",
        "regex": r"Got permission denied while trying to connect to the Docker daemon socket",
        "domain": "docker",
        "category": "permissions",
        "source": "manual_seed",
    },
    {
        "signature": "no space left on device",
        "regex": r"no space left on device",
        "domain": "docker",
        "category": "resource_exhaustion",
        "source": "manual_seed",
    },
    {
        "signature": (
            "ERROR: Cannot install X because these package versions"
            " have conflicting dependencies"
        ),
        "regex": (
            r"ERROR: Cannot install .+ because these package"
            r" versions have conflicting dependencies"
        ),
        "domain": "pip",
        "category": "dependency_resolution",
        "source": "manual_seed",
    },
    {
        "signature": "Failed building wheel for X",
        "regex": r"Failed building wheel for .+",
        "domain": "pip",
        "category": "build",
        "source": "manual_seed",
    },
    {
        "signature": "fatal: refusing to merge unrelated histories",
        "regex": r"fatal: refusing to merge unrelated histories",
        "domain": "git",
        "category": "merge",
        "source": "manual_seed",
    },
    {
        "signature": "RuntimeError: The current CUDA version is not compatible",
        "regex": r"RuntimeError: (?:The )?[Cc]urrent CUDA (?:version|runtime) is not compatible",
        "domain": "cuda",
        "category": "version_mismatch",
        "source": "manual_seed",
    },
    {
        "signature": "RuntimeError: CUBLAS_STATUS_NOT_INITIALIZED",
        "regex": r"RuntimeError: CUBLAS_STATUS_NOT_INITIALIZED",
        "domain": "cuda",
        "category": "initialization",
        "source": "manual_seed",
    },
    {
        "signature": "RuntimeError: NCCL communicator was aborted",
        "regex": r"RuntimeError: NCCL communicator was aborted",
        "domain": "cuda",
        "category": "distributed",
        "source": "manual_seed",
    },
    {
        "signature": "ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED]",
        "regex": r"ssl\.SSLCertVerificationError: \[SSL: CERTIFICATE_VERIFY_FAILED\]",
        "domain": "python",
        "category": "network",
        "source": "manual_seed",
    },
    {
        "signature": "RecursionError: maximum recursion depth exceeded",
        "regex": r"RecursionError: maximum recursion depth exceeded",
        "domain": "python",
        "category": "runtime",
        "source": "manual_seed",
    },
    {
        "signature": (
            "Error response from daemon: Pool overlaps with"
            " other one on this address space"
        ),
        "regex": (
            r"Error response from daemon: Pool overlaps with"
            r" other one on this address space"
        ),
        "domain": "docker",
        "category": "network",
        "source": "manual_seed",
    },
]

# StackOverflow tag → domain mapping
TAG_DOMAIN_MAP = {
    "python": "python",
    "pytorch": "python",
    "tensorflow": "python",
    "numpy": "python",
    "cuda": "cuda",
    "node.js": "node",
    "npm": "node",
    "docker": "docker",
    "pip": "pip",
    "git": "git",
}


def normalize_signature(raw: str) -> str:
    """Normalize an error signature for deduplication.

    - Strips file paths, line numbers, hex addresses
    - Replaces variable parts with X
    - Normalizes whitespace
    """
    sig = raw.strip()
    # Remove ANSI escape codes
    sig = re.sub(r"\033\[[0-9;]*m", "", sig)
    # Replace file paths
    sig = re.sub(r"(?:/[\w./\\-]+)+", " X ", sig)
    # Replace hex addresses
    sig = re.sub(r"0x[0-9a-fA-F]+", "X", sig)
    # Replace specific numbers but keep important ones in known patterns
    sig = re.sub(r"line \d+", "line X", sig)
    # Normalize whitespace
    sig = re.sub(r"\s+", " ", sig).strip()
    return sig


def signature_hash(signature: str, domain: str) -> str:
    """Generate a dedup key from normalized signature + domain."""
    key = f"{domain}:{normalize_signature(signature)}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def fetch_so_questions(tag: str, page: int = 1, pagesize: int = 100,
                       so_key: str | None = None) -> list[dict]:
    """Fetch questions from StackOverflow by tag, sorted by votes."""
    params = {
        "order": "desc",
        "sort": "votes",
        "tagged": tag,
        "filter": "withbody",
        "site": "stackoverflow",
        "page": page,
        "pagesize": pagesize,
    }
    if so_key:
        params["key"] = so_key

    resp = requests.get(f"{SO_API_BASE}/questions", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("backoff"):
        time.sleep(data["backoff"])

    return data.get("items", [])


def extract_signatures_from_so(questions: list[dict], domain: str) -> list[dict]:
    """Extract error signatures from StackOverflow question bodies and titles."""
    signatures = []
    # Common error patterns by domain
    error_patterns = {
        "python": [
            r"((?:RuntimeError|ModuleNotFoundError|ImportError|AttributeError|"
            r"TypeError|ValueError|FileNotFoundError|PermissionError|"
            r"RecursionError|ssl\.SSLCertVerificationError|"
            r"_pickle\.UnpicklingError):.+?)(?:\n|$)",
        ],
        "cuda": [
            r"(RuntimeError: (?:CUDA|CUBLAS|NCCL|cudnn).+?)(?:\n|$)",
        ],
        "node": [
            r"((?:Error|TypeError|RangeError): .+?)(?:\n|$)",
            r"(FATAL ERROR:.+?)(?:\n|$)",
        ],
        "docker": [
            r"((?:Error response from daemon|Got permission denied|"
            r"no space left on device).+?)(?:\n|$)",
        ],
        "pip": [
            r"(ERROR: (?:Cannot install|Could not).+?)(?:\n|$)",
            r"(Failed building wheel.+?)(?:\n|$)",
        ],
        "git": [
            r"(fatal: .+?)(?:\n|$)",
        ],
    }

    patterns = error_patterns.get(domain, [r"((?:Error|Exception):.+?)(?:\n|$)"])

    for q in questions:
        body = q.get("body", "")
        title = q.get("title", "")
        text = f"{title}\n{body}"

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                sig = match.strip()
                if len(sig) > 10:  # Skip very short matches
                    signatures.append({
                        "signature": sig,
                        "domain": domain,
                        "category": "auto_detected",
                        "source": f"stackoverflow:{q['question_id']}",
                        "score": q.get("score", 0),
                        "view_count": q.get("view_count", 0),
                    })

    return signatures


def fetch_gh_issues(repo: str, label: str = "bug", per_page: int = 100,
                    gh_token: str | None = None) -> list[dict]:
    """Fetch issues from a GitHub repository."""
    headers = {"Accept": "application/vnd.github+json"}
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"

    params = {
        "labels": label,
        "state": "all",
        "sort": "comments",
        "direction": "desc",
        "per_page": per_page,
    }

    resp = requests.get(
        f"{GH_API_BASE}/repos/{repo}/issues",
        headers=headers,
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def extract_signatures_from_gh(issues: list[dict], domain: str) -> list[dict]:
    """Extract error signatures from GitHub issue bodies."""
    signatures = []
    error_pattern = r"((?:Error|Exception|RuntimeError|TypeError|fatal):.+?)(?:\n|```|$)"

    for issue in issues:
        body = issue.get("body", "") or ""
        title = issue.get("title", "")
        text = f"{title}\n{body}"

        matches = re.findall(error_pattern, text, re.IGNORECASE)
        for match in matches:
            sig = match.strip()
            if len(sig) > 10:
                signatures.append({
                    "signature": sig,
                    "domain": domain,
                    "category": "auto_detected",
                    "source": f"github:{issue.get('html_url', '')}",
                    "comments": issue.get("comments", 0),
                })

    return signatures


def deduplicate_signatures(signatures: list[dict]) -> list[dict]:
    """Deduplicate signatures by normalized hash, keeping highest-scored."""
    by_hash: dict[str, dict] = {}

    for sig in signatures:
        h = signature_hash(sig["signature"], sig["domain"])
        existing = by_hash.get(h)
        if existing is None:
            by_hash[h] = {**sig, "dedup_hash": h}
        else:
            # Keep the one with more evidence (higher score/views)
            existing_score = existing.get("score", 0) + existing.get("view_count", 0)
            new_score = sig.get("score", 0) + sig.get("view_count", 0)
            if new_score > existing_score:
                by_hash[h] = {**sig, "dedup_hash": h}

    return list(by_hash.values())


def build_regex_from_signature(signature: str) -> str:
    """Generate a basic regex from a signature by escaping and wildcarding variable parts."""
    escaped = re.escape(signature)
    # Replace escaped 'X' placeholders with regex wildcards
    regex = escaped.replace(r"X", r".+")
    return regex


def main():
    parser = argparse.ArgumentParser(description="Collect error signatures from public sources")
    parser.add_argument("--so-tags", nargs="*", default=[], help="StackOverflow tags to search")
    parser.add_argument("--gh-repos", nargs="*", default=[], help="GitHub repos (owner/repo)")
    parser.add_argument("--so-key", default=None, help="StackOverflow API key")
    parser.add_argument("--gh-token", default=None, help="GitHub API token")
    parser.add_argument("--seeds-only", action="store_true", help="Only output manual seeds")
    parser.add_argument("--output", type=Path, default=SIGNATURES_FILE, help="Output file")
    args = parser.parse_args()

    PIPELINE_DIR.mkdir(parents=True, exist_ok=True)

    all_signatures: list[dict] = []

    # Always include manual seeds
    print(f"Loading {len(SEED_SIGNATURES)} manual seed signatures...")
    for seed in SEED_SIGNATURES:
        all_signatures.append({
            **seed,
            "dedup_hash": signature_hash(seed["signature"], seed["domain"]),
        })

    if not args.seeds_only:
        # Collect from StackOverflow
        for tag in args.so_tags:
            domain = TAG_DOMAIN_MAP.get(tag, tag)
            print(f"Fetching StackOverflow questions for tag '{tag}' (domain: {domain})...")
            try:
                questions = fetch_so_questions(tag, so_key=args.so_key)
                sigs = extract_signatures_from_so(questions, domain)
                print(f"  Found {len(sigs)} raw signatures")
                all_signatures.extend(sigs)
                time.sleep(1)  # Rate limiting
            except requests.RequestException as e:
                print(f"  WARNING: Failed to fetch SO data for '{tag}': {e}")

        # Collect from GitHub
        for repo in args.gh_repos:
            domain = TAG_DOMAIN_MAP.get(repo.split("/")[-1], "python")
            print(f"Fetching GitHub issues for '{repo}' (domain: {domain})...")
            try:
                issues = fetch_gh_issues(repo, gh_token=args.gh_token)
                sigs = extract_signatures_from_gh(issues, domain)
                print(f"  Found {len(sigs)} raw signatures")
                all_signatures.extend(sigs)
                time.sleep(1)  # Rate limiting
            except requests.RequestException as e:
                print(f"  WARNING: Failed to fetch GH data for '{repo}': {e}")

    # Deduplicate
    deduped = deduplicate_signatures(all_signatures)
    print(f"\nDeduplicated: {len(all_signatures)} → {len(deduped)} unique signatures")

    # Write output
    with open(args.output, "w", encoding="utf-8") as f:
        for sig in sorted(deduped, key=lambda s: s["domain"]):
            f.write(json.dumps(sig, ensure_ascii=False) + "\n")

    print(f"Wrote {len(deduped)} signatures to {args.output}")


if __name__ == "__main__":
    main()
