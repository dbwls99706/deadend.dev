"""Tests for the site build process."""

from pathlib import Path

from generator.build_site import (
    build_env_summary,
    collect_sources,
    load_canons,
)

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"


class TestLoadCanons:
    def test_loads_all_canons(self):
        canons = load_canons(DATA_DIR)
        assert len(canons) >= 3

    def test_all_canons_have_id(self):
        canons = load_canons(DATA_DIR)
        for canon in canons:
            assert "id" in canon
            assert "/" in canon["id"]


class TestBuildEnvSummary:
    def test_python_cuda_summary(self):
        canon = {
            "environment": {
                "runtime": {"name": "pytorch", "version_range": ">=2.0,<2.3"},
                "hardware": {"gpu": "A100-40GB", "vram_gb": 40},
                "os": "linux",
                "python": ">=3.9,<3.13",
            }
        }
        summary = build_env_summary(canon)
        assert "pytorch" in summary
        assert "A100-40GB" in summary
        assert "linux" in summary

    def test_node_summary(self):
        canon = {
            "environment": {
                "runtime": {"name": "node", "version_range": ">=18,<23"},
                "os": "linux",
                "additional": {"architecture": "arm64"},
            }
        }
        summary = build_env_summary(canon)
        assert "node" in summary
        assert "arm64" in summary

    def test_minimal_summary(self):
        canon = {
            "environment": {
                "runtime": {"name": "python", "version_range": ">=3.10"},
                "os": "linux",
            }
        }
        summary = build_env_summary(canon)
        assert "python" in summary


class TestCollectSources:
    def test_collects_from_dead_ends(self):
        canon = {
            "dead_ends": [
                {"sources": ["https://example.com/a", "https://example.com/b"]},
                {"sources": ["https://example.com/c"]},
            ],
            "workarounds": [],
        }
        sources = collect_sources(canon)
        assert len(sources) == 3

    def test_collects_from_workarounds(self):
        canon = {
            "dead_ends": [{"sources": []}],
            "workarounds": [{"sources": ["https://example.com/d"]}],
        }
        sources = collect_sources(canon)
        assert len(sources) == 1

    def test_deduplicates(self):
        canon = {
            "dead_ends": [{"sources": ["https://example.com/a"]}],
            "workarounds": [{"sources": ["https://example.com/a"]}],
        }
        sources = collect_sources(canon)
        assert len(sources) == 1

    def test_filters_empty_strings(self):
        canon = {
            "dead_ends": [{"sources": ["", "https://example.com/a"]}],
            "workarounds": [],
        }
        sources = collect_sources(canon)
        assert len(sources) == 1
