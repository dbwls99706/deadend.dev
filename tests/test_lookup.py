"""Tests for generator.lookup — error lookup SDK."""

import copy

from tests.conftest import VALID_CANON
from tests.conftest import make_canons as _make_canons


def _swap_cache(lookup_mod, canons):
    """Swap both canon cache and compiled patterns for testing."""
    old_canons = lookup_mod._CANONS_CACHE
    old_patterns = lookup_mod._COMPILED_PATTERNS
    lookup_mod._CANONS_CACHE = canons
    lookup_mod._COMPILED_PATTERNS = None  # force recompile for new canons
    return old_canons, old_patterns


def _restore_cache(lookup_mod, old_canons, old_patterns):
    """Restore original caches after testing."""
    lookup_mod._CANONS_CACHE = old_canons
    lookup_mod._COMPILED_PATTERNS = old_patterns


class TestLookupAll:
    def test_empty_message(self):
        import generator.lookup as lookup_mod

        old_canons, old_patterns = _swap_cache(lookup_mod, _make_canons(1))
        try:
            result = lookup_mod.lookup_all("")
            assert result == []
            result = lookup_mod.lookup_all("   ")
            assert result == []
        finally:
            _restore_cache(lookup_mod, old_canons, old_patterns)

    def test_regex_match(self):
        import generator.lookup as lookup_mod

        old_canons, old_patterns = _swap_cache(lookup_mod, _make_canons(2))
        try:
            result = lookup_mod.lookup_all("TestError0: something broke")
            assert len(result) >= 1
            assert result[0]["id"] == "python/test-error-0/env1"
        finally:
            _restore_cache(lookup_mod, old_canons, old_patterns)

    def test_returns_expected_fields(self):
        import generator.lookup as lookup_mod

        old_canons, old_patterns = _swap_cache(lookup_mod, _make_canons(1))
        try:
            result = lookup_mod.lookup_all("TestError0: x")
            assert len(result) >= 1
            m = result[0]
            assert "id" in m
            assert "signature" in m
            assert "domain" in m
            assert "dead_ends" in m
            assert "workarounds" in m
            assert "score" in m
        finally:
            _restore_cache(lookup_mod, old_canons, old_patterns)

    def test_sorted_by_score(self):
        import generator.lookup as lookup_mod

        canons = _make_canons(2)
        canons[0]["error"]["regex"] = ".*"  # Matches anything
        canons[0]["verdict"]["fix_success_rate"] = 0.3
        canons[1]["error"]["regex"] = "TestError1.*"  # Only matches TestError1
        canons[1]["verdict"]["fix_success_rate"] = 0.9

        old_canons, old_patterns = _swap_cache(lookup_mod, canons)
        try:
            result = lookup_mod.lookup_all("TestError1: failed")
            # TestError1 should rank higher (regex + signature match)
            assert len(result) >= 1
            assert result[0]["id"] == "python/test-error-1/env1"
        finally:
            _restore_cache(lookup_mod, old_canons, old_patterns)


class TestLookup:
    def test_returns_best_match(self):
        import generator.lookup as lookup_mod

        old_canons, old_patterns = _swap_cache(lookup_mod, _make_canons(2))
        try:
            result = lookup_mod.lookup("TestError0: boom")
            assert result is not None
            assert result["id"] == "python/test-error-0/env1"
        finally:
            _restore_cache(lookup_mod, old_canons, old_patterns)

    def test_no_match_returns_none(self):
        import generator.lookup as lookup_mod

        old_canons, old_patterns = _swap_cache(lookup_mod, _make_canons(1))
        try:
            result = lookup_mod.lookup("")
            assert result is None
        finally:
            _restore_cache(lookup_mod, old_canons, old_patterns)


class TestBatchLookup:
    def test_batch(self):
        import generator.lookup as lookup_mod

        old_canons, old_patterns = _swap_cache(lookup_mod, _make_canons(2))
        try:
            results = lookup_mod.batch_lookup([
                "TestError0: x",
                "TestError1: y",
                "NoSuchError: z",
            ])
            assert len(results) == 3
            assert results[0] is not None
            assert results[0]["id"] == "python/test-error-0/env1"
            assert results[1] is not None
            assert results[1]["id"] == "python/test-error-1/env1"
            # Third may or may not match depending on word overlap
        finally:
            _restore_cache(lookup_mod, old_canons, old_patterns)


class TestSearch:
    def test_keyword_search(self):
        import generator.lookup as lookup_mod

        old_canons, old_patterns = _swap_cache(lookup_mod, _make_canons(3))
        try:
            result = lookup_mod.search("TestError0")
            assert len(result) >= 1
            assert result[0]["id"] == "python/test-error-0/env1"
        finally:
            _restore_cache(lookup_mod, old_canons, old_patterns)

    def test_domain_filter(self):
        import generator.lookup as lookup_mod

        canons = _make_canons(2, "python")
        node_canon = copy.deepcopy(VALID_CANON)
        node_canon["id"] = "node/test-error/env1"
        node_canon["url"] = "https://deadends.dev/node/test-error/env1"
        node_canon["error"]["domain"] = "node"
        node_canon["error"]["signature"] = "TestError: node thing"
        node_canon["error"]["regex"] = "TestError.*node.*"
        canons.append(node_canon)

        old_canons, old_patterns = _swap_cache(lookup_mod, canons)
        try:
            result = lookup_mod.search("TestError", domain="node")
            assert len(result) >= 1
            for r in result:
                assert r["domain"] == "node"
        finally:
            _restore_cache(lookup_mod, old_canons, old_patterns)

    def test_limit(self):
        import generator.lookup as lookup_mod

        old_canons, old_patterns = _swap_cache(lookup_mod, _make_canons(10))
        try:
            result = lookup_mod.search("something", limit=3)
            assert len(result) <= 3
        finally:
            _restore_cache(lookup_mod, old_canons, old_patterns)
