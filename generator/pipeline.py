"""Unified pipeline: validate, bulk-generate, build, validate again.

Usage:
    python -m generator.pipeline          # Full pipeline
    python -m generator.pipeline --build  # Build only (skip generation)
    python -m generator.pipeline --gen    # Generate canons only
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

STEPS = {
    "validate-data": {
        "desc": "Validate existing canon data",
        "cmd": [sys.executable, "-m", "generator.validate", "--data-only"],
    },
    "bulk-generate": {
        "desc": "Generate new canons from seed definitions",
        "cmd": [sys.executable, "-m", "generator.bulk_generate"],
    },
    "build-site": {
        "desc": "Build static site from all canons",
        "cmd": [sys.executable, "-m", "generator.build_site"],
    },
    "validate-site": {
        "desc": "Validate generated HTML pages",
        "cmd": [sys.executable, "-m", "generator.validate", "--site-only"],
    },
    "run-tests": {
        "desc": "Run test suite",
        "cmd": [sys.executable, "-m", "pytest", "tests/", "-v"],
    },
}


def run_step(name: str, step: dict) -> bool:
    """Run a pipeline step and return True if successful."""
    print(f"\n{'='*60}")
    print(f"  STEP: {name} — {step['desc']}")
    print(f"{'='*60}\n")

    start = time.time()
    result = subprocess.run(
        step["cmd"],
        cwd=str(PROJECT_ROOT),
    )
    elapsed = time.time() - start

    status = "PASSED" if result.returncode == 0 else "FAILED"
    print(f"\n  [{status}] {name} ({elapsed:.1f}s)")
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="deadend.dev pipeline")
    parser.add_argument("--build", action="store_true", help="Build only")
    parser.add_argument("--gen", action="store_true", help="Generate only")
    args = parser.parse_args()

    print("=" * 60)
    print("  deadend.dev — Full Pipeline")
    print("=" * 60)

    if args.gen:
        steps_to_run = ["bulk-generate", "validate-data"]
    elif args.build:
        steps_to_run = ["build-site", "validate-site"]
    else:
        steps_to_run = list(STEPS.keys())

    results = {}
    for name in steps_to_run:
        ok = run_step(name, STEPS[name])
        results[name] = ok
        if not ok and name != "validate-site":
            # validate-site warnings shouldn't stop the pipeline
            print(f"\n  Pipeline stopped at step: {name}")
            break

    print(f"\n{'='*60}")
    print("  PIPELINE SUMMARY")
    print(f"{'='*60}")
    for name, ok in results.items():
        icon = "OK" if ok else "FAIL"
        print(f"  [{icon}] {name}")

    all_ok = all(results.values())
    print(f"\n  {'Pipeline PASSED' if all_ok else 'Pipeline FAILED'}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
