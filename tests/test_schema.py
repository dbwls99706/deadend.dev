"""Tests for the ErrorCanon JSON schema edge cases."""

import copy

from jsonschema import ValidationError, validate

from generator.schema import ERRORCANON_SCHEMA

MINIMAL_VALID = {
    "schema_version": "1.0.0",
    "id": "python/test-error/env1",
    "url": "https://deadend.dev/python/test-error/env1",
    "error": {
        "signature": "Error: test",
        "regex": "Error: .+",
        "domain": "python",
        "category": "test",
    },
    "environment": {
        "runtime": {"name": "python", "version_range": ">=3.10"},
        "os": "linux",
    },
    "verdict": {
        "resolvable": "partial",
        "fix_success_rate": 0.5,
        "confidence": 0.7,
        "last_updated": "2025-01-01",
        "summary": "Test.",
    },
    "dead_ends": [
        {"action": "test", "why_fails": "because", "fail_rate": 0.9}
    ],
    "workarounds": [],
    "transition_graph": {
        "leads_to": [],
        "preceded_by": [],
        "frequently_confused_with": [],
    },
    "metadata": {
        "generated_by": "test",
        "generation_date": "2025-01-01",
        "review_status": "auto_generated",
        "evidence_count": 5,
    },
}


class TestSchemaEdgeCases:
    def test_minimal_valid_passes(self):
        validate(instance=MINIMAL_VALID, schema=ERRORCANON_SCHEMA)

    def test_all_valid_domains(self):
        valid_domains = [
            "python", "cuda", "node", "pip", "docker",
            "git", "mcp", "http", "auth", "db", "rust", "llm",
        ]
        for domain in valid_domains:
            canon = copy.deepcopy(MINIMAL_VALID)
            canon["error"]["domain"] = domain
            validate(instance=canon, schema=ERRORCANON_SCHEMA)

    def test_fix_rate_boundary_zero(self):
        canon = copy.deepcopy(MINIMAL_VALID)
        canon["verdict"]["fix_success_rate"] = 0.0
        validate(instance=canon, schema=ERRORCANON_SCHEMA)

    def test_fix_rate_boundary_one(self):
        canon = copy.deepcopy(MINIMAL_VALID)
        canon["verdict"]["fix_success_rate"] = 1.0
        validate(instance=canon, schema=ERRORCANON_SCHEMA)

    def test_fix_rate_over_one_fails(self):
        canon = copy.deepcopy(MINIMAL_VALID)
        canon["verdict"]["fix_success_rate"] = 1.1
        try:
            validate(instance=canon, schema=ERRORCANON_SCHEMA)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass

    def test_fix_rate_negative_fails(self):
        canon = copy.deepcopy(MINIMAL_VALID)
        canon["verdict"]["fix_success_rate"] = -0.1
        try:
            validate(instance=canon, schema=ERRORCANON_SCHEMA)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass

    def test_schema_version_format(self):
        canon = copy.deepcopy(MINIMAL_VALID)
        canon["schema_version"] = "not-semver"
        try:
            validate(instance=canon, schema=ERRORCANON_SCHEMA)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass

    def test_id_format_requires_three_segments(self):
        canon = copy.deepcopy(MINIMAL_VALID)
        canon["id"] = "only-two/segments"
        try:
            validate(instance=canon, schema=ERRORCANON_SCHEMA)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass

    def test_date_format_validation(self):
        canon = copy.deepcopy(MINIMAL_VALID)
        canon["verdict"]["last_updated"] = "not-a-date"
        try:
            validate(instance=canon, schema=ERRORCANON_SCHEMA)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass

    def test_transition_graph_requires_all_subfields(self):
        canon = copy.deepcopy(MINIMAL_VALID)
        canon["transition_graph"] = {"leads_to": []}  # missing preceded_by, etc.
        try:
            validate(instance=canon, schema=ERRORCANON_SCHEMA)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass

    def test_workarounds_empty_array_valid(self):
        canon = copy.deepcopy(MINIMAL_VALID)
        canon["workarounds"] = []
        validate(instance=canon, schema=ERRORCANON_SCHEMA)

    def test_environment_os_required(self):
        canon = copy.deepcopy(MINIMAL_VALID)
        del canon["environment"]["os"]
        try:
            validate(instance=canon, schema=ERRORCANON_SCHEMA)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass

    def test_resolvable_enum_values(self):
        for val in ["true", "partial", "false"]:
            canon = copy.deepcopy(MINIMAL_VALID)
            canon["verdict"]["resolvable"] = val
            validate(instance=canon, schema=ERRORCANON_SCHEMA)
