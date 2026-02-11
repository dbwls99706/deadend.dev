"""Tests for ErrorCanon validation logic."""



from generator.validate import validate_canon_json, validate_cross_references


class TestValidCanon:
    def test_valid_canon_passes(self, valid_canon):
        errors, warnings = validate_canon_json(valid_canon)
        assert errors == []

    def test_valid_canon_with_empty_workarounds(self, make_canon):
        canon = make_canon(workarounds=[])
        errors, warnings = validate_canon_json(canon)
        assert errors == []

    def test_valid_canon_with_empty_transition_graph(self, make_canon):
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
    def test_missing_required_field(self, valid_canon):
        del valid_canon["dead_ends"]
        errors, _ = validate_canon_json(valid_canon)
        assert len(errors) > 0
        assert "dead_ends" in errors[0].lower() or "required" in errors[0].lower()

    def test_missing_workarounds_field(self, valid_canon):
        del valid_canon["workarounds"]
        errors, _ = validate_canon_json(valid_canon)
        assert len(errors) > 0

    def test_missing_transition_graph_field(self, valid_canon):
        del valid_canon["transition_graph"]
        errors, _ = validate_canon_json(valid_canon)
        assert len(errors) > 0

    def test_missing_environment_os(self, valid_canon):
        del valid_canon["environment"]["os"]
        errors, _ = validate_canon_json(valid_canon)
        assert len(errors) > 0

    def test_invalid_domain(self, valid_canon):
        valid_canon["error"]["domain"] = "invalid_domain"
        errors, _ = validate_canon_json(valid_canon)
        assert len(errors) > 0

    def test_empty_dead_ends(self, make_canon):
        canon = make_canon(dead_ends=[])
        errors, _ = validate_canon_json(canon)
        assert len(errors) > 0

    def test_invalid_resolvable_enum(self, valid_canon):
        valid_canon["verdict"]["resolvable"] = "maybe"
        errors, _ = validate_canon_json(valid_canon)
        assert len(errors) > 0


class TestBusinessRules:
    def test_url_mismatch(self, make_canon):
        canon = make_canon(url="https://deadends.dev/wrong/path/here")
        errors, _ = validate_canon_json(canon)
        assert any("URL mismatch" in e for e in errors)

    def test_verdict_true_requires_high_rate(self, valid_canon):
        valid_canon["verdict"]["resolvable"] = "true"
        valid_canon["verdict"]["fix_success_rate"] = 0.50
        valid_canon["verdict"]["confidence"] = 0.80
        errors, _ = validate_canon_json(valid_canon)
        assert any("verdict 'true'" in e for e in errors)

    def test_verdict_true_valid(self, valid_canon):
        valid_canon["verdict"]["resolvable"] = "true"
        valid_canon["verdict"]["fix_success_rate"] = 0.80
        valid_canon["verdict"]["confidence"] = 0.70
        errors, _ = validate_canon_json(valid_canon)
        assert not any("verdict 'true'" in e for e in errors)

    def test_verdict_false_requires_low_rate(self, valid_canon):
        valid_canon["verdict"]["resolvable"] = "false"
        valid_canon["verdict"]["fix_success_rate"] = 0.30
        valid_canon["verdict"]["confidence"] = 0.80
        errors, _ = validate_canon_json(valid_canon)
        assert any("verdict 'false'" in e for e in errors)

    def test_low_evidence_high_confidence(self, valid_canon):
        valid_canon["metadata"]["evidence_count"] = 2
        valid_canon["verdict"]["confidence"] = 0.80
        errors, _ = validate_canon_json(valid_canon)
        assert any("evidence_count" in e for e in errors)

    def test_invalid_regex(self, valid_canon):
        valid_canon["error"]["regex"] = "[invalid regex("
        errors, _ = validate_canon_json(valid_canon)
        assert any("regex" in e.lower() for e in errors)

    def test_fail_rate_out_of_range(self, valid_canon):
        valid_canon["dead_ends"][0]["fail_rate"] = 1.5
        errors, _ = validate_canon_json(valid_canon)
        # Caught by schema validation (maximum: 1.0)
        assert len(errors) > 0


class TestWarnings:
    def test_empty_sources_warning(self, valid_canon):
        valid_canon["dead_ends"][0]["sources"] = []
        _, warnings = validate_canon_json(valid_canon)
        assert any("no sources" in w for w in warnings)

    def test_evidence_count_vs_sources_warning(self, valid_canon):
        valid_canon["metadata"]["evidence_count"] = 50
        for de in valid_canon["dead_ends"]:
            de["sources"] = []
        for wa in valid_canon["workarounds"]:
            if "sources" in wa:
                wa["sources"] = []
        _, warnings = validate_canon_json(valid_canon)
        assert any("evidence_count" in w and "no source URLs" in w for w in warnings)


class TestCrossReferences:
    def test_valid_cross_reference(self, make_canon):
        canon1 = make_canon(
            id="python/error-a/env1",
            url="https://deadends.dev/python/error-a/env1",
            transition_graph={
                "leads_to": [{"error_id": "python/error-b/env1", "probability": 0.5}],
                "preceded_by": [],
                "frequently_confused_with": [],
            },
        )
        canon2 = make_canon(
            id="python/error-b/env1",
            url="https://deadends.dev/python/error-b/env1",
        )
        warnings = validate_cross_references([canon1, canon2])
        assert len(warnings) == 0

    def test_missing_cross_reference(self, make_canon):
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

    def test_missing_confused_with_reference(self, make_canon):
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
