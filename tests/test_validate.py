"""Tests for ErrorCanon validation logic."""

import copy

from generator.validate import validate_canon_json, validate_cross_references

# Minimal valid canon for testing
VALID_CANON = {
    "schema_version": "1.0.0",
    "id": "python/test-error/env1",
    "url": "https://deadend.dev/python/test-error/env1",
    "error": {
        "signature": "TestError: something failed",
        "regex": "TestError: .+",
        "domain": "python",
        "category": "test",
        "first_seen": "2025-01-01",
        "last_confirmed": "2025-06-01",
    },
    "environment": {
        "runtime": {"name": "python", "version_range": ">=3.10"},
        "os": "linux",
    },
    "verdict": {
        "resolvable": "partial",
        "fix_success_rate": 0.50,
        "confidence": 0.70,
        "last_updated": "2025-06-01",
        "summary": "Test error with partial resolution.",
    },
    "dead_ends": [
        {
            "action": "Do not do this",
            "why_fails": "Because it fails",
            "fail_rate": 0.90,
            "sources": ["https://example.com/issue/1"],
        }
    ],
    "workarounds": [
        {
            "action": "Try this instead",
            "success_rate": 0.60,
            "how": "run the command",
        }
    ],
    "transition_graph": {
        "leads_to": [],
        "preceded_by": [],
        "frequently_confused_with": [],
    },
    "metadata": {
        "generated_by": "test",
        "generation_date": "2025-06-01",
        "review_status": "auto_generated",
        "evidence_count": 10,
        "page_views": 0,
        "ai_agent_hits": 0,
        "human_hits": 0,
        "last_verification": "2025-06-01",
    },
}


def make_canon(**overrides):
    """Create a canon with optional overrides (shallow merge)."""
    canon = copy.deepcopy(VALID_CANON)
    for key, value in overrides.items():
        if isinstance(value, dict) and key in canon and isinstance(canon[key], dict):
            canon[key].update(value)
        else:
            canon[key] = value
    return canon


class TestValidCanon:
    def test_valid_canon_passes(self):
        errors, warnings = validate_canon_json(VALID_CANON)
        assert errors == []

    def test_valid_canon_with_empty_workarounds(self):
        canon = make_canon(workarounds=[])
        errors, warnings = validate_canon_json(canon)
        assert errors == []

    def test_valid_canon_with_empty_transition_graph(self):
        canon = make_canon(
            transition_graph={
                "leads_to": [],
                "preceded_by": [],
                "frequently_confused_with": [],
            }
        )
        errors, warnings = validate_canon_json(canon)
        assert errors == []


class TestSchemaErrors:
    def test_missing_required_field(self):
        canon = copy.deepcopy(VALID_CANON)
        del canon["dead_ends"]
        errors, _ = validate_canon_json(canon)
        assert len(errors) > 0
        assert "dead_ends" in errors[0].lower() or "required" in errors[0].lower()

    def test_missing_workarounds_field(self):
        canon = copy.deepcopy(VALID_CANON)
        del canon["workarounds"]
        errors, _ = validate_canon_json(canon)
        assert len(errors) > 0

    def test_missing_transition_graph_field(self):
        canon = copy.deepcopy(VALID_CANON)
        del canon["transition_graph"]
        errors, _ = validate_canon_json(canon)
        assert len(errors) > 0

    def test_missing_environment_os(self):
        canon = copy.deepcopy(VALID_CANON)
        del canon["environment"]["os"]
        errors, _ = validate_canon_json(canon)
        assert len(errors) > 0

    def test_invalid_domain(self):
        canon = copy.deepcopy(VALID_CANON)
        canon["error"]["domain"] = "invalid_domain"
        errors, _ = validate_canon_json(canon)
        assert len(errors) > 0

    def test_empty_dead_ends(self):
        canon = make_canon(dead_ends=[])
        errors, _ = validate_canon_json(canon)
        assert len(errors) > 0

    def test_invalid_resolvable_enum(self):
        canon = copy.deepcopy(VALID_CANON)
        canon["verdict"]["resolvable"] = "maybe"
        errors, _ = validate_canon_json(canon)
        assert len(errors) > 0


class TestBusinessRules:
    def test_url_mismatch(self):
        canon = make_canon(url="https://deadend.dev/wrong/path/here")
        errors, _ = validate_canon_json(canon)
        assert any("URL mismatch" in e for e in errors)

    def test_verdict_true_requires_high_rate(self):
        canon = copy.deepcopy(VALID_CANON)
        canon["verdict"]["resolvable"] = "true"
        canon["verdict"]["fix_success_rate"] = 0.50
        canon["verdict"]["confidence"] = 0.80
        errors, _ = validate_canon_json(canon)
        assert any("verdict 'true'" in e for e in errors)

    def test_verdict_true_valid(self):
        canon = copy.deepcopy(VALID_CANON)
        canon["verdict"]["resolvable"] = "true"
        canon["verdict"]["fix_success_rate"] = 0.80
        canon["verdict"]["confidence"] = 0.70
        errors, _ = validate_canon_json(canon)
        assert not any("verdict 'true'" in e for e in errors)

    def test_verdict_false_requires_low_rate(self):
        canon = copy.deepcopy(VALID_CANON)
        canon["verdict"]["resolvable"] = "false"
        canon["verdict"]["fix_success_rate"] = 0.30
        canon["verdict"]["confidence"] = 0.80
        errors, _ = validate_canon_json(canon)
        assert any("verdict 'false'" in e for e in errors)

    def test_low_evidence_high_confidence(self):
        canon = copy.deepcopy(VALID_CANON)
        canon["metadata"]["evidence_count"] = 2
        canon["verdict"]["confidence"] = 0.80
        errors, _ = validate_canon_json(canon)
        assert any("evidence_count" in e for e in errors)

    def test_invalid_regex(self):
        canon = copy.deepcopy(VALID_CANON)
        canon["error"]["regex"] = "[invalid regex("
        errors, _ = validate_canon_json(canon)
        assert any("regex" in e.lower() for e in errors)

    def test_fail_rate_out_of_range(self):
        canon = copy.deepcopy(VALID_CANON)
        canon["dead_ends"][0]["fail_rate"] = 1.5
        errors, _ = validate_canon_json(canon)
        # Caught by schema validation (maximum: 1.0)
        assert len(errors) > 0


class TestWarnings:
    def test_empty_sources_warning(self):
        canon = copy.deepcopy(VALID_CANON)
        canon["dead_ends"][0]["sources"] = []
        _, warnings = validate_canon_json(canon)
        assert any("no sources" in w for w in warnings)

    def test_evidence_count_vs_sources_warning(self):
        canon = copy.deepcopy(VALID_CANON)
        canon["metadata"]["evidence_count"] = 50
        canon["dead_ends"][0]["sources"] = []
        canon["workarounds"][0]["sources"] = []
        # Remove any default sources
        for de in canon["dead_ends"]:
            de["sources"] = []
        for wa in canon["workarounds"]:
            if "sources" in wa:
                wa["sources"] = []
        _, warnings = validate_canon_json(canon)
        assert any("evidence_count" in w and "no source URLs" in w for w in warnings)


class TestCrossReferences:
    def test_valid_cross_reference(self):
        canon1 = make_canon(
            id="python/error-a/env1",
            url="https://deadend.dev/python/error-a/env1",
            transition_graph={
                "leads_to": [{"error_id": "python/error-b/env1", "probability": 0.5}],
                "preceded_by": [],
                "frequently_confused_with": [],
            },
        )
        canon2 = make_canon(
            id="python/error-b/env1",
            url="https://deadend.dev/python/error-b/env1",
        )
        warnings = validate_cross_references([canon1, canon2])
        assert len(warnings) == 0

    def test_missing_cross_reference(self):
        canon1 = make_canon(
            transition_graph={
                "leads_to": [
                    {"error_id": "python/nonexistent/env1", "probability": 0.5}
                ],
                "preceded_by": [],
                "frequently_confused_with": [],
            },
        )
        warnings = validate_cross_references([canon1])
        assert len(warnings) == 1
        assert "non-existent" in warnings[0]

    def test_missing_confused_with_reference(self):
        canon1 = make_canon(
            transition_graph={
                "leads_to": [],
                "preceded_by": [],
                "frequently_confused_with": [
                    {"error_id": "python/nope/env1", "distinction": "different"}
                ],
            },
        )
        warnings = validate_cross_references([canon1])
        assert len(warnings) == 1
