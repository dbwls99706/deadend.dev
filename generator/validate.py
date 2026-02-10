"""Validation script for ErrorCanon JSON files and generated HTML pages."""

import json
import re
import sys
from pathlib import Path

from jsonschema import ValidationError, validate

from generator.schema import ERRORCANON_SCHEMA

BASE_URL = "https://deadend.dev"


def validate_canon_json(data: dict) -> list[str]:
    """Validate an ErrorCanon JSON object against the schema and business rules.

    Returns a list of error messages (empty if valid).
    """
    errors = []

    # Schema validation
    try:
        validate(instance=data, schema=ERRORCANON_SCHEMA)
    except ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")
        return errors  # No point checking business rules if schema fails

    # Business rule: dead_ends must have at least 1 item
    if len(data.get("dead_ends", [])) < 1:
        errors.append("dead_ends must contain at least 1 item")

    # Business rule: id must match URL pattern
    expected_url = f"{BASE_URL}/{data['id']}"
    if data["url"] != expected_url:
        errors.append(f"URL mismatch: expected {expected_url}, got {data['url']}")

    # Business rule: verdict.resolvable consistency
    verdict = data["verdict"]
    rate = verdict["fix_success_rate"]
    conf = verdict["confidence"]
    resolvable = verdict["resolvable"]

    if resolvable == "true" and (rate < 0.7 or conf < 0.6):
        errors.append(
            f"verdict 'true' requires fix_success_rate >= 0.7 and confidence >= 0.6, "
            f"got rate={rate}, confidence={conf}"
        )
    if resolvable == "false" and (rate >= 0.2 or conf < 0.6):
        errors.append(
            f"verdict 'false' requires fix_success_rate < 0.2 and confidence >= 0.6, "
            f"got rate={rate}, confidence={conf}"
        )

    # Business rule: low evidence warning
    evidence_count = data["metadata"].get("evidence_count", 0)
    if evidence_count < 3 and conf > 0.3:
        errors.append(
            f"evidence_count={evidence_count} < 3 but confidence={conf} > 0.3. "
            "Low evidence should have confidence <= 0.3."
        )

    # Business rule: all numeric rates in 0.0-1.0 range
    for i, de in enumerate(data.get("dead_ends", [])):
        if not 0.0 <= de["fail_rate"] <= 1.0:
            errors.append(f"dead_ends[{i}].fail_rate out of range: {de['fail_rate']}")

    for i, wa in enumerate(data.get("workarounds", [])):
        if not 0.0 <= wa["success_rate"] <= 1.0:
            errors.append(f"workarounds[{i}].success_rate out of range: {wa['success_rate']}")

    # Business rule: regex should be valid
    try:
        re.compile(data["error"]["regex"])
    except re.error as e:
        errors.append(f"Invalid error regex: {e}")

    return errors


def validate_html(html_path: Path) -> list[str]:
    """Validate a generated HTML page."""
    errors = []
    content = html_path.read_text(encoding="utf-8")

    # Must contain JSON-LD
    if 'application/ld+json' not in content:
        errors.append(f"{html_path}: Missing JSON-LD structured data")

    # Must contain canonical link
    if 'rel="canonical"' not in content:
        errors.append(f"{html_path}: Missing canonical link")

    # Must contain ai-summary
    if 'id="ai-summary"' not in content:
        errors.append(f"{html_path}: Missing ai-summary section")

    # Must contain dead-ends section
    if 'id="dead-ends"' not in content:
        errors.append(f"{html_path}: Missing dead-ends section")

    # Extract and validate embedded JSON-LD
    json_ld_match = re.search(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        content,
        re.DOTALL,
    )
    if json_ld_match:
        try:
            json.loads(json_ld_match.group(1))
        except json.JSONDecodeError as e:
            errors.append(f"{html_path}: Invalid JSON-LD: {e}")
    else:
        errors.append(f"{html_path}: Could not extract JSON-LD")

    return errors


def validate_all(data_dir: Path, site_dir: Path | None = None) -> bool:
    """Validate all canon JSON files and optionally generated HTML.

    Returns True if all validations pass.
    """
    all_errors = []

    # Validate canon JSON files
    canon_files = list(data_dir.rglob("*.json"))
    if not canon_files:
        print("WARNING: No canon JSON files found")
        return True

    for canon_file in canon_files:
        try:
            with open(canon_file, encoding="utf-8") as f:
                data = json.load(f)
            errors = validate_canon_json(data)
            for error in errors:
                all_errors.append(f"{canon_file}: {error}")
                print(f"  FAIL: {canon_file}: {error}")
            if not errors:
                print(f"  OK: {canon_file}")
        except json.JSONDecodeError as e:
            all_errors.append(f"{canon_file}: Invalid JSON: {e}")
            print(f"  FAIL: {canon_file}: Invalid JSON: {e}")

    # Validate HTML files if site_dir provided
    if site_dir and site_dir.exists():
        html_files = list(site_dir.rglob("index.html"))
        # Exclude top-level index.html
        html_files = [f for f in html_files if f.parent != site_dir]
        for html_file in html_files:
            errors = validate_html(html_file)
            for error in errors:
                all_errors.append(error)
                print(f"  FAIL: {error}")
            if not errors:
                print(f"  OK: {html_file}")

    if all_errors:
        print(f"\nValidation FAILED: {len(all_errors)} error(s)")
        return False
    else:
        print("\nValidation PASSED")
        return True


def main():
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "canons"
    site_dir = project_root / "site"

    print("Validating ErrorCanon data and site...\n")

    site_path = site_dir if site_dir.exists() else None
    success = validate_all(data_dir, site_path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
