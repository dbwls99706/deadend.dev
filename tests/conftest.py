"""Shared test fixtures for deadend.dev tests."""

import copy

import pytest

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


@pytest.fixture
def valid_canon():
    """Return a deep copy of a valid ErrorCanon."""
    return copy.deepcopy(VALID_CANON)


@pytest.fixture
def make_canon():
    """Factory fixture to create canons with overrides."""

    def _make(**overrides):
        canon = copy.deepcopy(VALID_CANON)
        for key, value in overrides.items():
            if isinstance(value, dict) and key in canon and isinstance(canon[key], dict):
                canon[key].update(value)
            else:
                canon[key] = value
        return canon

    return _make
