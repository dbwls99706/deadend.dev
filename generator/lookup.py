"""deadends.dev error lookup SDK.

Programmatic error lookup for AI coding agents and developer tools.
Works offline with bundled data or online via the deadends.dev API.

Usage:
    from generator.lookup import lookup, lookup_all

    # Single best match
    result = lookup("ModuleNotFoundError: No module named 'torch'")
    print(result["dead_ends"])      # What NOT to try
    print(result["workarounds"])    # What works

    # All matches
    results = lookup_all("CUDA error: out of memory")

CLI Usage:
    python -m generator.lookup "ModuleNotFoundError: No module named 'torch'"
"""

import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"

_CANONS_CACHE: list[dict] | None = None


def _load_canons() -> list[dict]:
    """Load all canon data (cached after first call)."""
    global _CANONS_CACHE
    if _CANONS_CACHE is not None:
        return _CANONS_CACHE

    canons = []
    for f in sorted(DATA_DIR.rglob("*.json")):
        with open(f, encoding="utf-8") as fh:
            canons.append(json.load(fh))
    _CANONS_CACHE = canons
    return canons


_STOPWORDS = frozenset({
    "", "the", "a", "an", "is", "of", "in", "to", "for", "and", "or",
    "no", "not", "on", "at", "by", "it", "be", "as", "do", "if",
    "error", "failed", "exception", "cannot", "can", "could",
    "was", "were", "been", "being", "has", "have", "had",
    "with", "from", "this", "that", "when", "which", "while",
})


def lookup_all(error_message: str) -> list[dict]:
    """Match an error message against all known patterns.

    Returns a list of matching canons sorted by relevance, each containing:
    - id, signature, domain, resolvable, fix_success_rate, summary
    - dead_ends: list of {action, why_fails, fail_rate}
    - workarounds: list of {action, success_rate, how}
    """
    if not error_message or not error_message.strip():
        return []

    canons = _load_canons()
    matches = []

    for canon in canons:
        try:
            pattern = re.compile(canon["error"]["regex"], re.IGNORECASE)
        except re.error:
            continue

        score = 0

        # Regex match (highest priority)
        if pattern.search(error_message):
            score += 100

        # Signature substring match
        sig = canon["error"]["signature"].lower()
        msg = error_message.lower()
        if sig in msg or msg in sig:
            score += 50

        # Word overlap (excluding stopwords)
        sig_words = set(re.split(r"\W+", sig))
        msg_words = set(re.split(r"\W+", msg))
        overlap = (sig_words & msg_words) - _STOPWORDS
        score += len(overlap) * 5

        if score > 0:
            matches.append({
                "score": score,
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
                "url": canon["url"],
            })

    # Sort by: score DESC, then fix_success_rate DESC
    matches.sort(
        key=lambda m: (m["score"], m["fix_success_rate"]),
        reverse=True,
    )
    return matches


def lookup(error_message: str) -> dict | None:
    """Return the single best matching canon for an error message.

    Returns None if no match found.
    """
    matches = lookup_all(error_message)
    return matches[0] if matches else None


def batch_lookup(error_messages: list[str]) -> list[dict | None]:
    """Look up multiple error messages at once.

    Returns a list of best matches (or None) for each input message.
    More efficient than calling lookup() in a loop because canon data
    is loaded only once.

    Usage:
        from generator.lookup import batch_lookup

        results = batch_lookup([
            "ModuleNotFoundError: No module named 'torch'",
            "CUDA error: out of memory",
            "CrashLoopBackOff",
        ])
        for msg, result in zip(error_messages, results):
            if result:
                print(f"{msg} -> {result['signature']}")
    """
    _load_canons()  # ensure loaded once
    return [lookup(msg) for msg in error_messages]


def search(query: str, domain: str | None = None, limit: int = 10) -> list[dict]:
    """Search errors by keyword across all domains.

    Unlike lookup_all (regex matching), this does fuzzy keyword search
    across signatures, summaries, dead ends, and workarounds.

    Usage:
        from generator.lookup import search

        results = search("memory limit", domain="docker", limit=5)
    """
    canons = _load_canons()
    q_words = set(query.lower().split())
    scored = []

    for canon in canons:
        if domain and canon["error"]["domain"] != domain:
            continue
        score = 0
        sig = canon["error"]["signature"].lower()
        summary = canon["verdict"]["summary"].lower()
        for w in q_words:
            if w in sig:
                score += 10
            if w in summary:
                score += 5
            for de in canon["dead_ends"]:
                if w in de["action"].lower() or w in de["why_fails"].lower():
                    score += 3
            for wa in canon.get("workarounds", []):
                if w in wa["action"].lower():
                    score += 3
        if score > 0:
            scored.append({
                "score": score,
                "id": canon["id"],
                "signature": canon["error"]["signature"],
                "domain": canon["error"]["domain"],
                "resolvable": canon["verdict"]["resolvable"],
                "fix_success_rate": canon["verdict"]["fix_success_rate"],
                "summary": canon["verdict"]["summary"],
            })

    scored.sort(key=lambda m: m["score"], reverse=True)
    return scored[:limit]


def main():
    """CLI interface for error lookup."""
    if len(sys.argv) < 2:
        print("Usage: python -m generator.lookup 'ERROR MESSAGE'")
        print("       python -m generator.lookup --list")
        sys.exit(1)

    if sys.argv[1] == "--list":
        canons = _load_canons()
        domains: dict[str, list[str]] = {}
        for c in canons:
            d = c["error"]["domain"]
            domains.setdefault(d, []).append(c["error"]["signature"])
        for domain in sorted(domains):
            print(f"\n{domain} ({len(domains[domain])} errors):")
            for sig in sorted(set(domains[domain])):
                print(f"  {sig}")
        sys.exit(0)

    error_msg = " ".join(sys.argv[1:])
    matches = lookup_all(error_msg)

    if not matches:
        print(f"No matches for: {error_msg}")
        sys.exit(1)

    for m in matches[:3]:
        print(f"\n{'='*60}")
        print(f"  {m['signature']}")
        print(f"  Resolvable: {m['resolvable']} | "
              f"Fix rate: {int(m['fix_success_rate']*100)}%")
        print(f"  {m['summary']}")
        print(f"{'='*60}")

        print("\n  DEAD ENDS (do NOT try):")
        for d in m["dead_ends"]:
            print(f"    X {d['action']} — fails {int(d['fail_rate']*100)}%")
            print(f"      {d['why_fails']}")

        print("\n  WORKAROUNDS (try these):")
        for w in m["workarounds"]:
            print(f"    > {w['action']} — works {int(w['success_rate']*100)}%")
            if w["how"]:
                print(f"      {w['how']}")

        print(f"\n  Details: {m['url']}")


if __name__ == "__main__":
    main()
