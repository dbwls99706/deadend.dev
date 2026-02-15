"""Tests for mcp.core — shared MCP logic."""

import copy

from tests.conftest import VALID_CANON


def _make_canons(count=3, domain="python"):
    """Create a list of test canons."""
    canons = []
    for i in range(count):
        c = copy.deepcopy(VALID_CANON)
        c["id"] = f"{domain}/test-error-{i}/env1"
        c["url"] = f"https://deadends.dev/{domain}/test-error-{i}/env1"
        c["error"]["signature"] = f"TestError{i}: something failed"
        c["error"]["regex"] = f"TestError{i}.*"
        c["error"]["domain"] = domain
        canons.append(c)
    return canons


class TestMatchError:
    def test_empty_message_returns_empty(self):
        from mcp.core import match_error

        assert match_error("", []) == []
        assert match_error("  ", []) == []

    def test_matches_by_regex(self):
        from mcp.core import match_error

        canons = _make_canons(1)
        result = match_error("TestError0: something failed badly", canons)
        assert len(result) == 1
        assert result[0]["id"] == "python/test-error-0/env1"

    def test_no_match_returns_empty(self):
        from mcp.core import match_error

        canons = _make_canons(1)
        result = match_error("UnrelatedError: nope", canons)
        assert len(result) == 0

    def test_multiple_matches_sorted_by_rate(self):
        from mcp.core import match_error

        canons = _make_canons(2)
        canons[0]["error"]["regex"] = "Test.*"
        canons[1]["error"]["regex"] = "Test.*"
        canons[0]["verdict"]["fix_success_rate"] = 0.3
        canons[1]["verdict"]["fix_success_rate"] = 0.9
        result = match_error("TestError: x", canons)
        assert len(result) == 2
        assert result[0]["fix_success_rate"] == 0.9

    def test_invalid_regex_skipped(self):
        from mcp.core import match_error

        canons = _make_canons(1)
        canons[0]["error"]["regex"] = "[invalid"
        result = match_error("anything", canons)
        assert len(result) == 0

    def test_match_contains_expected_fields(self):
        from mcp.core import match_error

        canons = _make_canons(1)
        result = match_error("TestError0: failed", canons)
        assert len(result) == 1
        m = result[0]
        assert "id" in m
        assert "signature" in m
        assert "domain" in m
        assert "resolvable" in m
        assert "fix_success_rate" in m
        assert "summary" in m
        assert "dead_ends" in m
        assert "workarounds" in m
        assert "leads_to" in m
        assert "url" in m


class TestLookupById:
    def test_found(self):
        from mcp.core import lookup_by_id

        canons = _make_canons(3)
        result = lookup_by_id("python/test-error-1/env1", canons)
        assert result is not None
        assert result["id"] == "python/test-error-1/env1"

    def test_not_found(self):
        from mcp.core import lookup_by_id

        canons = _make_canons(1)
        result = lookup_by_id("nonexistent/error/env1", canons)
        assert result is None


class TestListDomains:
    def test_counts_domains(self):
        from mcp.core import list_domains

        canons = _make_canons(2, "python") + _make_canons(1, "node")
        canons[2]["error"]["domain"] = "node"
        result = list_domains(canons)
        assert result["total"] == 3
        assert result["domains"]["python"] == 2
        assert result["domains"]["node"] == 1


class TestSuggestDomains:
    def test_suggests_python(self):
        from mcp.core import _suggest_domains

        result = _suggest_domains("import torch failed")
        assert "python" in result

    def test_suggests_docker(self):
        from mcp.core import _suggest_domains

        result = _suggest_domains("docker daemon not running")
        assert "docker" in result

    def test_unknown_for_gibberish(self):
        from mcp.core import _suggest_domains

        result = _suggest_domains("xyzzy foobar baz")
        assert result == "unknown"


class TestHandleRequest:
    def test_initialize(self):
        from mcp.core import PROTOCOL_VERSION, SERVER_VERSION, handle_request

        result = handle_request("initialize", {}, [])
        assert result["protocolVersion"] == PROTOCOL_VERSION
        assert result["serverInfo"]["version"] == SERVER_VERSION

    def test_ping(self):
        from mcp.core import handle_request

        result = handle_request("ping", {}, [])
        assert result == {}

    def test_tools_list(self):
        from mcp.core import handle_request

        result = handle_request("tools/list", {}, [])
        assert "tools" in result
        tool_names = [t["name"] for t in result["tools"]]
        assert "lookup_error" in tool_names
        assert "get_error_chain" in tool_names
        assert "get_domain_stats" in tool_names

    def test_unknown_method(self):
        from mcp.core import handle_request

        result = handle_request("nonexistent/method", {}, [])
        assert "error" in result
        assert result["error"]["code"] == -32601

    def test_notification_returns_none(self):
        from mcp.core import handle_request

        result = handle_request("notifications/initialized", {}, [])
        assert result is None

    def test_resources_list(self):
        from mcp.core import handle_request

        result = handle_request("resources/list", {}, [])
        assert result == {"resources": []}

    def test_prompts_list(self):
        from mcp.core import handle_request

        result = handle_request("prompts/list", {}, [])
        assert result == {"prompts": []}

    def test_tool_call_unknown_tool(self):
        from mcp.core import handle_request

        result = handle_request(
            "tools/call",
            {"name": "nonexistent_tool", "arguments": {}},
            [],
        )
        assert result["isError"] is True

    def test_tool_call_lookup_error_empty(self):
        from mcp.core import handle_request

        result = handle_request(
            "tools/call",
            {"name": "lookup_error", "arguments": {"error_message": ""}},
            [],
        )
        assert "content" in result
        assert "Empty error message" in result["content"][0]["text"]

    def test_tool_call_lookup_error_no_match(self):
        from mcp.core import handle_request

        result = handle_request(
            "tools/call",
            {"name": "lookup_error", "arguments": {"error_message": "xyzzy"}},
            _make_canons(1),
        )
        assert "No matching errors" in result["content"][0]["text"]

    def test_tool_call_lookup_error_with_match(self):
        from mcp.core import handle_request

        canons = _make_canons(1)
        result = handle_request(
            "tools/call",
            {"name": "lookup_error", "arguments": {"error_message": "TestError0: oops"}},
            canons,
        )
        assert "TestError0" in result["content"][0]["text"]
        assert "Dead Ends" in result["content"][0]["text"]

    def test_tool_call_list_error_domains(self):
        from mcp.core import handle_request

        canons = _make_canons(2)
        result = handle_request(
            "tools/call",
            {"name": "list_error_domains", "arguments": {}},
            canons,
        )
        assert "python" in result["content"][0]["text"]

    def test_tool_call_search_errors_empty_query(self):
        from mcp.core import handle_request

        result = handle_request(
            "tools/call",
            {"name": "search_errors", "arguments": {"query": ""}},
            [],
        )
        assert "Empty search query" in result["content"][0]["text"]

    def test_tool_call_search_errors(self):
        from mcp.core import handle_request

        canons = _make_canons(2)
        result = handle_request(
            "tools/call",
            {"name": "search_errors", "arguments": {"query": "TestError0"}},
            canons,
        )
        assert "TestError0" in result["content"][0]["text"]

    def test_tool_call_list_errors_by_domain(self):
        from mcp.core import handle_request

        canons = _make_canons(2)
        result = handle_request(
            "tools/call",
            {"name": "list_errors_by_domain", "arguments": {"domain": "python"}},
            canons,
        )
        assert "python" in result["content"][0]["text"]

    def test_tool_call_list_errors_by_unknown_domain(self):
        from mcp.core import handle_request

        canons = _make_canons(1)
        result = handle_request(
            "tools/call",
            {"name": "list_errors_by_domain", "arguments": {"domain": "haskell"}},
            canons,
        )
        assert "Unknown domain" in result["content"][0]["text"]

    def test_tool_call_batch_lookup(self):
        from mcp.core import handle_request

        canons = _make_canons(2)
        result = handle_request(
            "tools/call",
            {
                "name": "batch_lookup",
                "arguments": {
                    "error_messages": ["TestError0: x", "UnknownError: y"],
                },
            },
            canons,
        )
        text = result["content"][0]["text"]
        assert "Batch lookup: 2 errors" in text
        assert "No match found" in text

    def test_tool_call_get_domain_stats(self):
        from mcp.core import handle_request

        canons = _make_canons(3)
        result = handle_request(
            "tools/call",
            {"name": "get_domain_stats", "arguments": {"domain": "python"}},
            canons,
        )
        text = result["content"][0]["text"]
        assert "Domain Statistics" in text
        assert "Total errors: 3" in text

    def test_tool_call_get_domain_stats_unknown(self):
        from mcp.core import handle_request

        result = handle_request(
            "tools/call",
            {"name": "get_domain_stats", "arguments": {"domain": "haskell"}},
            _make_canons(1),
        )
        assert "Unknown domain" in result["content"][0]["text"]

    def test_tool_call_get_error_detail_found(self):
        from mcp.core import handle_request

        canons = _make_canons(2)
        result = handle_request(
            "tools/call",
            {"name": "get_error_detail", "arguments": {"error_id": "python/test-error-0/env1"}},
            canons,
        )
        text = result["content"][0]["text"]
        assert "test-error-0" in text

    def test_tool_call_get_error_detail_not_found(self):
        from mcp.core import handle_request

        canons = _make_canons(1)
        result = handle_request(
            "tools/call",
            {"name": "get_error_detail", "arguments": {"error_id": "x/y/z"}},
            canons,
        )
        assert "Error ID not found" in result["content"][0]["text"]

    def test_tool_call_get_error_chain(self):
        from mcp.core import handle_request

        canons = _make_canons(2)
        canons[0]["transition_graph"] = {
            "leads_to": [{"error_id": "python/test-error-1/env1", "probability": 0.5}],
            "preceded_by": [],
            "frequently_confused_with": [],
        }
        result = handle_request(
            "tools/call",
            {"name": "get_error_chain", "arguments": {"error_id": "python/test-error-0/env1"}},
            canons,
        )
        text = result["content"][0]["text"]
        assert "Error Chain" in text
        assert "leads to" in text.lower()

    def test_tool_call_get_error_chain_not_found(self):
        from mcp.core import handle_request

        canons = _make_canons(1)
        result = handle_request(
            "tools/call",
            {"name": "get_error_chain", "arguments": {"error_id": "x/y/z"}},
            canons,
        )
        assert "Error ID not found" in result["content"][0]["text"]
