"""Tests for the ErrorCanon JSON schema edge cases."""

import pytest
from jsonschema import ValidationError, validate

from generator.schema import ERRORCANON_SCHEMA


class TestSchemaEdgeCases:
    def test_minimal_valid_passes(self, valid_canon):
        validate(instance=valid_canon, schema=ERRORCANON_SCHEMA)

    def test_all_valid_domains(self, make_canon):
        valid_domains = [
            "python", "cuda", "node", "pip", "docker",
            "git", "mcp", "http", "auth", "db", "rust", "llm",
        ]
        for domain in valid_domains:
            canon = make_canon()
            canon["error"]["domain"] = domain
            validate(instance=canon, schema=ERRORCANON_SCHEMA)

    def test_fix_rate_boundary_zero(self, valid_canon):
        valid_canon["verdict"]["fix_success_rate"] = 0.0
        validate(instance=valid_canon, schema=ERRORCANON_SCHEMA)

    def test_fix_rate_boundary_one(self, valid_canon):
        valid_canon["verdict"]["fix_success_rate"] = 1.0
        validate(instance=valid_canon, schema=ERRORCANON_SCHEMA)

    def test_fix_rate_over_one_fails(self, valid_canon):
        valid_canon["verdict"]["fix_success_rate"] = 1.1
        with pytest.raises(ValidationError):
            validate(instance=valid_canon, schema=ERRORCANON_SCHEMA)

    def test_fix_rate_negative_fails(self, valid_canon):
        valid_canon["verdict"]["fix_success_rate"] = -0.1
        with pytest.raises(ValidationError):
            validate(instance=valid_canon, schema=ERRORCANON_SCHEMA)

    def test_schema_version_format(self, valid_canon):
        valid_canon["schema_version"] = "not-semver"
        with pytest.raises(ValidationError):
            validate(instance=valid_canon, schema=ERRORCANON_SCHEMA)

    def test_id_format_requires_three_segments(self, valid_canon):
        valid_canon["id"] = "only-two/segments"
        with pytest.raises(ValidationError):
            validate(instance=valid_canon, schema=ERRORCANON_SCHEMA)

    def test_date_format_validation(self, valid_canon):
        valid_canon["verdict"]["last_updated"] = "not-a-date"
        with pytest.raises(ValidationError):
            validate(instance=valid_canon, schema=ERRORCANON_SCHEMA)

    def test_transition_graph_requires_all_subfields(self, valid_canon):
        valid_canon["transition_graph"] = {"leads_to": []}
        with pytest.raises(ValidationError):
            validate(instance=valid_canon, schema=ERRORCANON_SCHEMA)

    def test_workarounds_empty_array_valid(self, make_canon):
        canon = make_canon(workarounds=[])
        validate(instance=canon, schema=ERRORCANON_SCHEMA)

    def test_environment_os_required(self, valid_canon):
        del valid_canon["environment"]["os"]
        with pytest.raises(ValidationError):
            validate(instance=valid_canon, schema=ERRORCANON_SCHEMA)

    def test_resolvable_enum_values(self, make_canon):
        for val in ["true", "partial", "false"]:
            canon = make_canon()
            canon["verdict"]["resolvable"] = val
            validate(instance=canon, schema=ERRORCANON_SCHEMA)
