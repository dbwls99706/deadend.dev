"""Tests for the pipeline steps (collect_signatures, generate_pairs)."""

import pytest

try:
    from generator.collect_signatures import (
        SEED_SIGNATURES,
        build_regex_from_signature,
        deduplicate_signatures,
        normalize_signature,
        signature_hash,
    )
    from generator.generate_pairs import (
        ENVIRONMENT_MATRIX,
        generate_env_hash,
        generate_env_slug,
        is_valid_combo,
        slugify_signature,
    )
except ImportError:
    pytest.skip(
        "pipeline dependencies not installed (pip install -e '.[pipeline]')",
        allow_module_level=True,
    )


class TestNormalizeSignature:
    def test_strips_file_paths(self):
        sig = "Error: /usr/local/lib/python3.11/site-packages/torch/cuda/__init__.py failed"
        result = normalize_signature(sig)
        assert "/usr/local" not in result
        assert "X" in result

    def test_strips_hex_addresses(self):
        sig = "Error at 0x7fff5fbff8c0: segfault"
        result = normalize_signature(sig)
        assert "0x7fff" not in result
        assert "X" in result

    def test_strips_line_numbers(self):
        sig = "SyntaxError at line 42: unexpected token"
        result = normalize_signature(sig)
        assert "line X" in result
        assert "line 42" not in result

    def test_normalizes_whitespace(self):
        sig = "Error:    too   many    spaces"
        result = normalize_signature(sig)
        assert "  " not in result

    def test_strips_ansi_codes(self):
        sig = "\033[31mError: red\033[0m"
        result = normalize_signature(sig)
        assert "\033" not in result


class TestSignatureHash:
    def test_same_signature_same_hash(self):
        h1 = signature_hash("Error: test", "python")
        h2 = signature_hash("Error: test", "python")
        assert h1 == h2

    def test_different_domain_different_hash(self):
        h1 = signature_hash("Error: test", "python")
        h2 = signature_hash("Error: test", "node")
        assert h1 != h2

    def test_hash_is_short(self):
        h = signature_hash("Error: test", "python")
        assert len(h) == 16


class TestDeduplication:
    def test_removes_exact_duplicates(self):
        sigs = [
            {"signature": "Error: test", "domain": "python", "score": 10},
            {"signature": "Error: test", "domain": "python", "score": 5},
        ]
        result = deduplicate_signatures(sigs)
        assert len(result) == 1
        assert result[0]["score"] == 10  # Keeps higher-scored

    def test_keeps_different_signatures(self):
        sigs = [
            {"signature": "Error: test", "domain": "python"},
            {"signature": "Error: other", "domain": "python"},
        ]
        result = deduplicate_signatures(sigs)
        assert len(result) == 2


class TestBuildRegex:
    def test_basic_regex(self):
        regex = build_regex_from_signature("Error: X")
        assert ".+" in regex

    def test_escapes_special_chars(self):
        regex = build_regex_from_signature("Error: [test]")
        assert "\\[" in regex


class TestSeedSignatures:
    def test_seed_signatures_not_empty(self):
        assert len(SEED_SIGNATURES) > 0

    def test_all_seeds_have_required_fields(self):
        for seed in SEED_SIGNATURES:
            assert "signature" in seed
            assert "regex" in seed
            assert "domain" in seed
            assert "category" in seed
            assert "source" in seed

    def test_all_seed_domains_in_schema(self):
        valid_domains = {
            "python", "cuda", "node", "pip", "docker",
            "git", "mcp", "http", "auth", "db", "rust", "llm",
        }
        for seed in SEED_SIGNATURES:
            assert seed["domain"] in valid_domains, (
                f"Seed domain '{seed['domain']}' not in valid domains"
            )


class TestGenerateEnvHash:
    def test_deterministic(self):
        env = {"runtime": {"name": "python", "version_range": ">=3.10"}, "os": "linux"}
        h1 = generate_env_hash(env)
        h2 = generate_env_hash(env)
        assert h1 == h2

    def test_different_os_different_hash(self):
        env1 = {"runtime": {"name": "python", "version_range": ">=3.10"}, "os": "linux"}
        env2 = {"runtime": {"name": "python", "version_range": ">=3.10"}, "os": "macos"}
        assert generate_env_hash(env1) != generate_env_hash(env2)


class TestGenerateEnvSlug:
    def test_basic_slug(self):
        env = {"runtime": {"name": "python", "version_range": ">=3.10"}, "os": "linux"}
        slug = generate_env_slug(env)
        assert "python" in slug
        assert "linux" in slug

    def test_gpu_in_slug(self):
        env = {
            "runtime": {"name": "cuda", "version_range": ">=12.0"},
            "os": "linux",
            "hardware": {"gpu": "A100-40GB", "vram_gb": 40},
        }
        slug = generate_env_slug(env)
        assert "a100" in slug.lower()

    def test_arch_in_slug(self):
        env = {
            "runtime": {"name": "python", "version_range": ">=3.11"},
            "os": "linux",
            "additional": {"architecture": "arm64"},
        }
        slug = generate_env_slug(env)
        assert "arm64" in slug


class TestIsValidCombo:
    def test_cuda_on_linux_valid(self):
        sig = {"domain": "cuda"}
        env = {"os": "linux"}
        assert is_valid_combo(sig, env)

    def test_cuda_on_macos_invalid(self):
        sig = {"domain": "cuda"}
        env = {"os": "macos"}
        assert not is_valid_combo(sig, env)

    def test_python_on_any_os_valid(self):
        sig = {"domain": "python"}
        for os_name in ["linux", "macos", "windows"]:
            assert is_valid_combo(sig, {"os": os_name})


class TestSlugifySignature:
    def test_python_error(self):
        slug = slugify_signature("RuntimeError: CUDA out of memory")
        assert "runtimeerror" in slug
        assert "cuda" in slug.lower()

    def test_max_length(self):
        slug = slugify_signature("Error: " + "x" * 200)
        assert len(slug) <= 60

    def test_clean_characters(self):
        slug = slugify_signature("Error: something [weird] (here)")
        assert "[" not in slug
        assert "]" not in slug
        assert "(" not in slug


class TestEnvironmentMatrix:
    def test_all_domains_have_matrix(self):
        expected = {"python", "cuda", "node", "docker", "pip", "git"}
        assert expected.issubset(set(ENVIRONMENT_MATRIX.keys()))

    def test_all_envs_have_runtime(self):
        for domain, envs in ENVIRONMENT_MATRIX.items():
            for env in envs:
                assert "runtime" in env, f"Missing runtime in {domain} env"
                assert "name" in env["runtime"]
                assert "version_range" in env["runtime"]

    def test_all_envs_have_os(self):
        for domain, envs in ENVIRONMENT_MATRIX.items():
            for env in envs:
                assert "os" in env, f"Missing os in {domain} env"
