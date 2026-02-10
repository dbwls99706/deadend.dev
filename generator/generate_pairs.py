"""Step 2: Generate environment combination pairs.

Takes signatures.jsonl + environment matrix, produces error-env pairs.
Output: data/pipeline/pairs.jsonl

Usage:
    python -m generator.generate_pairs [--input signatures.jsonl] [--output pairs.jsonl]
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PIPELINE_DIR = PROJECT_ROOT / "data" / "pipeline"
SIGNATURES_FILE = PIPELINE_DIR / "signatures.jsonl"
PAIRS_FILE = PIPELINE_DIR / "pairs.jsonl"

# Environment matrix per domain
ENVIRONMENT_MATRIX = {
    "python": [
        {"runtime": {"name": "python", "version_range": ">=3.10,<3.12"}, "os": "linux"},
        {"runtime": {"name": "python", "version_range": ">=3.10,<3.12"}, "os": "macos"},
        {"runtime": {"name": "python", "version_range": ">=3.11,<3.13"}, "os": "linux",
         "additional": {"architecture": "arm64"}},
    ],
    "cuda": [
        {"runtime": {"name": "cuda", "version_range": ">=11.8,<12.0"}, "os": "linux",
         "hardware": {"gpu": "RTX 3090", "vram_gb": 24}},
        {"runtime": {"name": "cuda", "version_range": ">=12.0,<12.3"}, "os": "linux",
         "hardware": {"gpu": "A100-40GB", "vram_gb": 40}},
        {"runtime": {"name": "cuda", "version_range": ">=12.0,<12.3"}, "os": "linux",
         "hardware": {"gpu": "RTX 4090", "vram_gb": 24}},
    ],
    "node": [
        {"runtime": {"name": "node", "version_range": ">=18,<19"}, "os": "linux"},
        {"runtime": {"name": "node", "version_range": ">=20,<21"}, "os": "linux"},
        {"runtime": {"name": "node", "version_range": ">=20,<21"}, "os": "macos"},
        {"runtime": {"name": "node", "version_range": ">=20,<21"}, "os": "linux",
         "additional": {"architecture": "arm64"}},
    ],
    "docker": [
        {"runtime": {"name": "docker", "version_range": ">=24,<26"}, "os": "linux"},
        {"runtime": {"name": "docker", "version_range": ">=24,<26"}, "os": "macos"},
        {"runtime": {"name": "docker", "version_range": ">=24,<26"}, "os": "windows",
         "additional": {"subsystem": "wsl2"}},
    ],
    "pip": [
        {"runtime": {"name": "pip", "version_range": ">=23,<25"}, "os": "linux"},
        {"runtime": {"name": "pip", "version_range": ">=23,<25"}, "os": "macos"},
        {"runtime": {"name": "pip", "version_range": ">=23,<25"}, "os": "linux",
         "additional": {"architecture": "arm64"}},
    ],
    "git": [
        {"runtime": {"name": "git", "version_range": ">=2.38,<2.45"}, "os": "linux"},
        {"runtime": {"name": "git", "version_range": ">=2.38,<2.45"}, "os": "macos"},
    ],
}

# Invalid combinations to filter out
INVALID_COMBOS = [
    # CUDA doesn't run on macOS or Windows natively
    lambda sig, env: sig["domain"] == "cuda" and env["os"] != "linux",
]


def generate_env_hash(env: dict) -> str:
    """Generate a short deterministic hash for an environment config."""
    runtime = env.get("runtime", {})
    parts = [
        runtime.get("name", ""),
        runtime.get("version_range", ""),
        env.get("os", ""),
    ]

    hw = env.get("hardware", {})
    if hw:
        parts.append(hw.get("gpu", ""))

    additional = env.get("additional", {})
    if additional:
        parts.extend(sorted(f"{k}={v}" for k, v in additional.items()))

    key = "|".join(parts)
    return hashlib.sha256(key.encode()).hexdigest()[:8]


def generate_env_slug(env: dict) -> str:
    """Generate a human-readable slug for an environment."""
    runtime = env.get("runtime", {})
    name = runtime.get("name", "unknown")
    version = runtime.get("version_range", "")
    os_name = env.get("os", "")

    # Extract major version number
    version_match = re.search(r"(\d+\.?\d*)", version)
    ver = version_match.group(1) if version_match else "x"

    parts = [f"{name}{ver}"]

    hw = env.get("hardware", {})
    if hw.get("gpu"):
        gpu_slug = hw["gpu"].lower().replace(" ", "").replace("-", "")
        parts.append(gpu_slug)

    parts.append(os_name)

    additional = env.get("additional", {})
    if additional.get("architecture"):
        parts.append(additional["architecture"])
    if additional.get("subsystem"):
        parts.append(additional["subsystem"])

    return "-".join(parts)


def is_valid_combo(signature: dict, env: dict) -> bool:
    """Check whether this signature-environment combination is valid."""
    for check in INVALID_COMBOS:
        if check(signature, env):
            return False
    return True


def slugify_signature(signature: str) -> str:
    """Convert an error signature to a URL slug."""
    # Take the error type/class name
    pattern = r"(?:(\w+Error|\w+Exception|FATAL ERROR|ERROR|fatal|Error):?\s*)(.*)"
    match = re.match(pattern, signature)
    if match:
        error_type = match.group(1).lower()
        detail = match.group(2).strip()
    else:
        error_type = "error"
        detail = signature

    # Build slug from error type and first few meaningful words
    detail_words = re.findall(r"[a-zA-Z]+", detail)[:4]
    slug_parts = [error_type] + [w.lower() for w in detail_words]
    slug = "-".join(slug_parts)

    # Clean up
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")

    return slug[:60]  # Max length


def main():
    parser = argparse.ArgumentParser(description="Generate error-environment pairs")
    parser.add_argument("--input", type=Path, default=SIGNATURES_FILE, help="Input signatures file")
    parser.add_argument("--output", type=Path, default=PAIRS_FILE, help="Output pairs file")
    parser.add_argument("--max-per-sig", type=int, default=5, help="Max envs per signature")
    args = parser.parse_args()

    # Load signatures
    signatures = []
    with open(args.input, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                signatures.append(json.loads(line))

    print(f"Loaded {len(signatures)} signatures")

    # Generate pairs
    pairs = []
    skipped = 0

    for sig in signatures:
        domain = sig["domain"]
        envs = ENVIRONMENT_MATRIX.get(domain, [])

        if not envs:
            print(f"  WARNING: No environment matrix for domain '{domain}'")
            continue

        count = 0
        for env in envs:
            if count >= args.max_per_sig:
                break

            if not is_valid_combo(sig, env):
                skipped += 1
                continue

            env_slug = generate_env_slug(env)
            sig_slug = slugify_signature(sig["signature"])
            pair_id = f"{domain}/{sig_slug}/{env_slug}"

            pair = {
                "id": pair_id,
                "url": f"https://deadend.dev/{pair_id}",
                "signature": sig,
                "environment": env,
                "env_hash": generate_env_hash(env),
            }
            pairs.append(pair)
            count += 1

    print(f"Generated {len(pairs)} pairs ({skipped} invalid combos skipped)")

    # Write output
    PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    print(f"Wrote {len(pairs)} pairs to {args.output}")


if __name__ == "__main__":
    main()
