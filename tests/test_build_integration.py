"""Integration tests for the full site build process."""

import json
import re
from pathlib import Path

import pytest

from generator.build_site import (
    build_domain_pages,
    build_error_pages,
    build_error_summary_pages,
    build_index_page,
    build_search_page,
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
        jinja_env.globals["base_path"] = bs.BASE_PATH
        jinja_env.globals["base_url"] = bs.BASE_URL
        jinja_env.filters["display_name"] = bs.domain_display_name

        from markupsafe import Markup

        def _json_escape(s: str) -> Markup:
            escaped = json.dumps(s)[1:-1]
            escaped = escaped.replace("</", r"<\/")
            return Markup(escaped)

        jinja_env.filters["json_escape"] = _json_escape

        build_error_pages(canons, jinja_env)
        build_domain_pages(canons, jinja_env)
        summary_urls = build_error_summary_pages(canons, jinja_env)
        build_search_page(canons, jinja_env)
        build_index_page(canons, jinja_env)
        build_sitemap(canons, summary_urls)

        return {
            "site_dir": site_dir,
            "canons": canons,
            "summary_urls": summary_urls,
        }
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
            with open(api_path, encoding="utf-8") as f:
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
        """Sitemap index should exist and reference sub-sitemaps."""
        sitemap_path = built_site["site_dir"] / "sitemap.xml"
        assert sitemap_path.exists()

        content = sitemap_path.read_text(encoding="utf-8")
        assert "sitemapindex" in content
        assert "sitemap-main.xml" in content

        # Summary pages should appear in domain sub-sitemaps
        all_sub_content = ""
        for f in built_site["site_dir"].glob("sitemap-*.xml"):
            all_sub_content += f.read_text(encoding="utf-8")
        for summary in built_site["summary_urls"]:
            assert summary["url"] in all_sub_content, (
                f"Missing URL in sub-sitemap: {summary['url']}"
            )

    def test_html_pages_have_json_ld(self, built_site):
        """Every error page should contain valid JSON-LD."""
        site_dir = built_site["site_dir"]
        for canon in built_site["canons"]:
            page_path = site_dir / canon["id"] / "index.html"
            content = page_path.read_text(encoding="utf-8")

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
            # JSON-LD uses Schema.org TechArticle with embedded ErrorCanon
            assert json_ld["@type"] == "TechArticle"
            assert json_ld["deadend:errorCanon"]["id"] == canon["id"]

    def test_html_pages_have_ai_summary(self, built_site):
        """Every error page should have an ai-summary section."""
        site_dir = built_site["site_dir"]
        for canon in built_site["canons"]:
            page_path = site_dir / canon["id"] / "index.html"
            content = page_path.read_text(encoding="utf-8")
            assert 'id="ai-summary"' in content, (
                f"Missing ai-summary in {canon['id']}"
            )

    def test_html_pages_have_faq_schema(self, built_site):
        """Every error page should have FAQPage JSON-LD."""
        site_dir = built_site["site_dir"]
        for canon in built_site["canons"]:
            page_path = site_dir / canon["id"] / "index.html"
            content = page_path.read_text(encoding="utf-8")
            assert "FAQPage" in content, (
                f"Missing FAQPage schema in {canon['id']}"
            )

    def test_error_summary_pages_created(self, built_site):
        """Each unique error slug should have a summary page."""
        site_dir = built_site["site_dir"]
        slugs = set()
        for canon in built_site["canons"]:
            parts = canon["id"].rsplit("/", 1)
            if len(parts) == 2:
                slugs.add(parts[0])
        for slug in slugs:
            page_path = site_dir / slug / "index.html"
            assert page_path.exists(), f"Missing summary page for {slug}"

    def test_search_page_created(self, built_site):
        """The search page should exist and contain search data."""
        search_path = built_site["site_dir"] / "search" / "index.html"
        assert search_path.exists()
        content = search_path.read_text(encoding="utf-8")
        assert "search-input" in content
        assert "regex" in content

    def test_sitemap_includes_search_and_summaries(self, built_site):
        """Sub-sitemaps should include search page and summary pages."""
        main_path = built_site["site_dir"] / "sitemap-main.xml"
        main_content = main_path.read_text(encoding="utf-8")
        assert "/search/" in main_content

        all_sub_content = ""
        for f in built_site["site_dir"].glob("sitemap-*.xml"):
            all_sub_content += f.read_text(encoding="utf-8")
        for summary in built_site["summary_urls"]:
            assert summary["url"] in all_sub_content


class TestDataValidation:
    def test_all_canons_pass_validation(self):
        """All canon JSON files should pass validation."""
        success = validate_all(data_dir=DATA_DIR, site_dir=None)
        assert success, "Canon data validation failed"
