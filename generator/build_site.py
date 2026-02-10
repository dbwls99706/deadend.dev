"""Build static site from ErrorCanon JSON data files."""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

from jinja2 import Environment, FileSystemLoader

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "canons"
SITE_DIR = PROJECT_ROOT / "site"
TEMPLATE_DIR = PROJECT_ROOT / "generator" / "templates"
BASE_URL = "https://deadend.dev"


def load_canons(data_dir: Path) -> list[dict]:
    """Load all ErrorCanon JSON files from the data directory."""
    canons = []
    for json_file in sorted(data_dir.rglob("*.json")):
        with open(json_file, encoding="utf-8") as f:
            canon = json.load(f)
        canons.append(canon)
    return canons


def build_env_summary(canon: dict) -> str:
    """Build a human-readable environment summary string."""
    env = canon["environment"]
    parts = []

    runtime = env.get("runtime", {})
    if runtime:
        parts.append(f"{runtime['name']} {runtime['version_range']}")

    hw = env.get("hardware", {})
    if hw and hw.get("gpu"):
        parts.append(hw["gpu"])
        if hw.get("vram_gb"):
            parts.append(f"{hw['vram_gb']}GB")

    if env.get("os"):
        parts.append(env["os"])

    if env.get("python"):
        parts.append(f"Python {env['python']}")

    additional = env.get("additional", {})
    if additional.get("architecture"):
        parts.append(additional["architecture"])

    return " · ".join(parts)


def collect_sources(canon: dict) -> list[str]:
    """Collect all unique source URLs from a canon."""
    sources = set()
    for de in canon.get("dead_ends", []):
        for src in de.get("sources", []):
            if src:
                sources.add(src)
    for wa in canon.get("workarounds", []):
        for src in wa.get("sources", []):
            if src:
                sources.add(src)
    return sorted(sources)


def build_error_pages(canons: list[dict], env: Environment) -> None:
    """Generate individual error pages."""
    template = env.get_template("page.html")

    for canon in canons:
        error_id = canon["id"]
        env_summary = build_env_summary(canon)
        all_sources = collect_sources(canon)

        # Build JSON-LD (the full canon with context)
        json_ld_data = {
            "@context": "https://deadend.dev/schema/v1",
            "@type": "ErrorCanon",
            **canon,
        }
        json_ld = json.dumps(json_ld_data, indent=2, ensure_ascii=False)

        html = template.render(
            env_summary=env_summary,
            all_sources=all_sources,
            json_ld=json_ld,
            **canon,
        )

        # Write HTML page
        page_dir = SITE_DIR / error_id
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(html, encoding="utf-8")

        # Write JSON API endpoint
        api_dir = SITE_DIR / "api" / "v1"
        api_dir.mkdir(parents=True, exist_ok=True)
        api_file = api_dir / f"{error_id.replace('/', '_')}.json"
        api_file.parent.mkdir(parents=True, exist_ok=True)
        api_file.write_text(
            json.dumps(canon, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"  Generated: {error_id}")


def build_index_page(canons: list[dict], env: Environment) -> None:
    """Generate the main index page."""
    template = env.get_template("index.html")

    # Compute domain stats
    domain_counts: dict[str, int] = {}
    for canon in canons:
        domain = canon["error"]["domain"]
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    domain_stats = sorted(
        [{"slug": slug, "count": count} for slug, count in domain_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    domains = sorted(domain_counts.keys())

    # Recent entries (sorted by generation_date descending)
    recent = sorted(
        canons,
        key=lambda c: c["metadata"].get("generation_date", ""),
        reverse=True,
    )[:10]
    recent_entries = [
        {"id": c["id"], "error": c["error"], "env_summary": build_env_summary(c)}
        for c in recent
    ]

    html = template.render(
        total_errors=len(canons),
        domains=domains,
        domain_stats=domain_stats,
        recent_entries=recent_entries,
    )

    (SITE_DIR / "index.html").write_text(html, encoding="utf-8")
    print("  Generated: index.html")


def build_sitemap(canons: list[dict]) -> None:
    """Generate sitemap.xml."""
    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Index page
    url_elem = SubElement(urlset, "url")
    SubElement(url_elem, "loc").text = BASE_URL
    SubElement(url_elem, "lastmod").text = now
    SubElement(url_elem, "changefreq").text = "weekly"
    SubElement(url_elem, "priority").text = "1.0"

    # Error pages
    for canon in canons:
        url_elem = SubElement(urlset, "url")
        SubElement(url_elem, "loc").text = canon["url"]
        last_updated = canon["verdict"].get("last_updated", now)
        SubElement(url_elem, "lastmod").text = last_updated
        SubElement(url_elem, "changefreq").text = "monthly"
        SubElement(url_elem, "priority").text = "0.8"

    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_body = tostring(urlset, encoding="unicode")
    (SITE_DIR / "sitemap.xml").write_text(xml_declaration + xml_body, encoding="utf-8")
    print("  Generated: sitemap.xml")


def build_robots_txt() -> None:
    """Generate robots.txt with explicit AI crawler allowances."""
    content = """# deadend.dev - Structured failure knowledge for AI agents
# All crawlers welcome, including AI agents

User-agent: *
Allow: /

# AI crawlers explicitly welcome
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Googlebot
Allow: /

User-agent: PerplexityBot
Allow: /

Sitemap: https://deadend.dev/sitemap.xml
"""
    (SITE_DIR / "robots.txt").write_text(content, encoding="utf-8")
    print("  Generated: robots.txt")


def main():
    print("Building deadend.dev static site...\n")

    # Clean and recreate site directory
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)

    # Load canons
    print("Loading ErrorCanon data...")
    canons = load_canons(DATA_DIR)
    if not canons:
        print("ERROR: No canon data found in data/canons/")
        sys.exit(1)
    print(f"  Found {len(canons)} canon(s)\n")

    # Set up Jinja2
    jinja_env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )

    # Build pages
    print("Generating error pages...")
    build_error_pages(canons, jinja_env)
    print()

    print("Generating index page...")
    build_index_page(canons, jinja_env)
    print()

    print("Generating sitemap.xml...")
    build_sitemap(canons)
    print()

    print("Generating robots.txt...")
    build_robots_txt()
    print()

    print(f"Build complete! {len(canons)} error pages generated in site/")


if __name__ == "__main__":
    main()
