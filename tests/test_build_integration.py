"""Integration tests for the full site build process."""

import json
import re
from pathlib import Path

import pytest

from generator.build_site import (
    build_domain_pages,
    build_error_pages,
    build_index_page,
    build_sitemap,
    load_canons,
)
from generator.validate import validate_all

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"


@pytest.fixture(scope="module")
def built_site(tmp_path_factory):
    """Build the full site into a temp directory and return the path."""

    from jinja2 import Environment, FileSystemLoader

    project_root = Path(__file__).parent.parent
    template_dir = project_root / "generator" / "templates"
    site_dir = tmp_path_factory.mktemp("site")

    # Monkey-patch SITE_DIR for the build
    import generator.build_site as bs
    original_site_dir = bs.SITE_DIR
    bs.SITE_DIR = site_dir

    try:
        canons = load_canons(DATA_DIR)
        assert len(canons) >= 3, "Need at least 3 canons for integration test"

        jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True,
        )

        build_error_pages(canons, jinja_env)
        build_domain_pages(canons, jinja_env)
        build_index_page(canons, jinja_env)
        build_sitemap(canons)

        return {"site_dir": site_dir, "canons": canons}
    finally:
        bs.SITE_DIR = original_site_dir


class TestSiteBuildIntegration:
    def test_error_pages_created(self, built_site):
        """Each canon should have an index.html page."""
        site_dir = built_site["site_dir"]
        for canon in built_site["canons"]:
            page_path = site_dir / canon["id"] / "index.html"
            assert page_path.exists(), f"Missing page for {canon['id']}"

    def test_api_endpoints_created(self, built_site):
        """Each canon should have a JSON API endpoint."""
        site_dir = built_site["site_dir"]
        for canon in built_site["canons"]:
            api_path = site_dir / "api" / "v1" / f"{canon['id']}.json"
            assert api_path.exists(), f"Missing API file for {canon['id']}"

            # Verify the API JSON is valid and matches the canon
            with open(api_path) as f:
                api_data = json.load(f)
            assert api_data["id"] == canon["id"]
            assert api_data["verdict"]["resolvable"] == canon["verdict"]["resolvable"]

    def test_domain_pages_created(self, built_site):
        """Each domain should have a listing page."""
        site_dir = built_site["site_dir"]
        domains = {c["error"]["domain"] for c in built_site["canons"]}
        for domain in domains:
            page_path = site_dir / domain / "index.html"
            assert page_path.exists(), f"Missing domain page for {domain}"

    def test_index_page_created(self, built_site):
        """The main index page should exist."""
        assert (built_site["site_dir"] / "index.html").exists()

    def test_sitemap_created(self, built_site):
        """Sitemap should exist and contain all canon URLs."""
        sitemap_path = built_site["site_dir"] / "sitemap.xml"
        assert sitemap_path.exists()

        content = sitemap_path.read_text()
        for canon in built_site["canons"]:
            assert canon["url"] in content, f"Missing URL in sitemap: {canon['url']}"

    def test_html_pages_have_json_ld(self, built_site):
        """Every error page should contain valid JSON-LD."""
        site_dir = built_site["site_dir"]
        for canon in built_site["canons"]:
            page_path = site_dir / canon["id"] / "index.html"
            content = page_path.read_text()

            assert 'application/ld+json' in content, (
                f"Missing JSON-LD in {canon['id']}"
            )

            # Extract and parse JSON-LD
            match = re.search(
                r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
                content,
                re.DOTALL,
            )
            assert match, f"Could not extract JSON-LD from {canon['id']}"
            json_ld = json.loads(match.group(1))
            assert json_ld["id"] == canon["id"]

    def test_html_pages_have_ai_summary(self, built_site):
        """Every error page should have an ai-summary section."""
        site_dir = built_site["site_dir"]
        for canon in built_site["canons"]:
            page_path = site_dir / canon["id"] / "index.html"
            content = page_path.read_text()
            assert 'id="ai-summary"' in content, (
                f"Missing ai-summary in {canon['id']}"
            )


class TestDataValidation:
    def test_all_canons_pass_validation(self):
        """All canon JSON files should pass validation."""
        success = validate_all(data_dir=DATA_DIR, site_dir=None)
        assert success, "Canon data validation failed"
