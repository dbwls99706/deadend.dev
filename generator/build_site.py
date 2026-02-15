"""Build static site from ErrorCanon JSON data files."""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "canons"
SITE_DIR = PROJECT_ROOT / "site"
TEMPLATE_DIR = PROJECT_ROOT / "generator" / "templates"
BASE_URL = "https://deadends.dev"
# Base path for subpath hosting (e.g., "/deadends.dev" for github.io/deadends.dev/)
# Empty string when hosted at root domain
BASE_PATH = ""

# Domain display names for proper capitalization in titles/breadcrumbs
DOMAIN_DISPLAY_NAMES = {
    "aws": "AWS",
    "cuda": "CUDA",
    "cicd": "CI/CD",
    "php": "PHP",
    "dotnet": ".NET",
    "nextjs": "Next.js",
    "typescript": "TypeScript",
    "pip": "pip",
}


def domain_display_name(domain: str) -> str:
    """Return proper display name for a domain slug."""
    return DOMAIN_DISPLAY_NAMES.get(domain, domain.capitalize())


# Search engine verification codes — replace with actual codes after registering
GOOGLE_VERIFICATION = "bOa6r9d87jFHgTQb7iuN5QokGsgy99_NYrz0x1jsSmk"
BING_VERIFICATION = ""  # e.g., "ABCDEF1234567890"

# IndexNow key — generated deterministically for the site
INDEXNOW_KEY = "deadend-dev-indexnow-key"


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


def build_error_pages(canons: list[dict], jinja_env: Environment) -> None:
    """Generate individual error pages."""
    template = jinja_env.get_template("page.html")
    known_ids = {c["id"] for c in canons}

    # Build per-domain summary links for internal linking
    # Key: domain, Value: list of {slug_key, signature}  (deduplicated)
    domain_summaries: dict[str, list[dict]] = {}
    for c in canons:
        domain = c["error"]["domain"]
        slug_key = c["id"].rsplit("/", 1)[0]
        if domain not in domain_summaries:
            domain_summaries[domain] = []
        seen = {e["slug_key"] for e in domain_summaries[domain]}
        if slug_key not in seen:
            domain_summaries[domain].append({
                "slug_key": slug_key,
                "signature": c["error"]["signature"],
            })

    for canon in canons:
        error_id = canon["id"]
        env_summary = build_env_summary(canon)
        all_sources = collect_sources(canon)

        # Build JSON-LD with Schema.org TechArticle + custom ErrorCanon
        page_url = canon["url"]
        if not page_url.endswith("/"):
            page_url += "/"
        json_ld_data = {
            "@context": [
                "https://schema.org",
                {"deadend": f"{BASE_URL}/schema/v1#"},
            ],
            "@type": "TechArticle",
            "name": canon["error"]["signature"],
            "headline": f"Fix {canon['error']['signature']}",
            "description": canon["verdict"]["summary"],
            "url": page_url,
            "datePublished": canon["error"].get(
                "first_seen", canon["metadata"].get("generation_date", "")
            ),
            "dateModified": canon["verdict"]["last_updated"],
            "image": f"{BASE_URL}/og-image.png",
            "publisher": {
                "@type": "Organization",
                "name": "deadends.dev",
                "url": BASE_URL,
            },
            "about": {
                "@type": "SoftwareSourceCode",
                "programmingLanguage": canon["error"]["domain"],
            },
            # Full ErrorCanon data embedded
            "deadend:errorCanon": canon,
        }
        json_ld = json.dumps(json_ld_data, indent=2, ensure_ascii=False)

        # FAQPage schema — dead ends as FAQ questions for Google rich snippets
        faq_entities = []
        sig = canon["error"]["signature"]
        for de in canon["dead_ends"]:
            faq_entities.append({
                "@type": "Question",
                "name": f"Why doesn't '{de['action']}' fix {sig}?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": de["why_fails"],
                },
            })
        faq_json_ld_data = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_entities,
        }
        faq_json_ld = json.dumps(
            faq_json_ld_data, indent=2, ensure_ascii=False
        )

        # HowTo schema — workarounds as step-by-step fix instructions
        howto_json_ld = ""
        workarounds = canon.get("workarounds", [])
        if workarounds:
            howto_steps = []
            for i, wa in enumerate(workarounds, 1):
                step = {
                    "@type": "HowToStep",
                    "position": i,
                    "name": wa["action"],
                    "text": wa.get("how", wa["action"]),
                }
                if wa.get("tradeoff"):
                    step["text"] += f" (Tradeoff: {wa['tradeoff']})"
                howto_steps.append(step)
            howto_data = {
                "@context": "https://schema.org",
                "@type": "HowTo",
                "name": f"How to fix {sig}",
                "description": canon["verdict"]["summary"],
                "step": howto_steps,
            }
            howto_json_ld = json.dumps(
                howto_data, indent=2, ensure_ascii=False
            )

        # Same-domain errors for internal linking (exclude self)
        current_slug = error_id.rsplit("/", 1)[0]
        same_domain = [
            e for e in domain_summaries.get(
                canon["error"]["domain"], []
            )
            if e["slug_key"] != current_slug
        ][:10]

        html = template.render(
            env_summary=env_summary,
            all_sources=all_sources,
            json_ld=json_ld,
            faq_json_ld=faq_json_ld,
            howto_json_ld=howto_json_ld,
            known_ids=known_ids,
            domain_errors=same_domain,
            **canon,
        )

        # Write HTML page
        page_dir = SITE_DIR / error_id
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(html, encoding="utf-8")

        # Write JSON API endpoint (hierarchical path)
        api_file = SITE_DIR / "api" / "v1" / f"{error_id}.json"
        api_file.parent.mkdir(parents=True, exist_ok=True)
        api_file.write_text(
            json.dumps(canon, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"  Generated: {error_id}")


def build_domain_pages(canons: list[dict], jinja_env: Environment) -> None:
    """Generate domain listing pages (e.g., /python/, /node/)."""
    template = jinja_env.get_template("domain.html")

    # Group canons by domain
    by_domain: dict[str, list[dict]] = {}
    for canon in canons:
        domain = canon["error"]["domain"]
        by_domain.setdefault(domain, []).append(canon)

    for domain, domain_canons in by_domain.items():
        # Group by slug for summary-level entries
        by_slug: dict[str, list[dict]] = {}
        for c in sorted(domain_canons, key=lambda c: c["id"]):
            slug_key = c["id"].rsplit("/", 1)[0]
            by_slug.setdefault(slug_key, []).append(c)

        entries = []
        for slug_key, slug_canons in sorted(by_slug.items()):
            slug_rates = [
                c["verdict"]["fix_success_rate"] for c in slug_canons
            ]
            slug_de = sum(len(c["dead_ends"]) for c in slug_canons)
            slug_wa = sum(
                len(c.get("workarounds", [])) for c in slug_canons
            )
            entries.append({
                "slug_key": slug_key,
                "signature": slug_canons[0]["error"]["signature"],
                "env_count": len(slug_canons),
                "fix_success_rate": max(slug_rates),
                "dead_end_count": slug_de,
                "workaround_count": slug_wa,
            })

        # Domain-level stats
        rates = [c["verdict"]["fix_success_rate"] for c in domain_canons]
        resolvable_counts = {"true": 0, "partial": 0, "false": 0}
        for c in domain_canons:
            r = c["verdict"]["resolvable"]
            resolvable_counts[r] = resolvable_counts.get(r, 0) + 1
        total_de = sum(len(c["dead_ends"]) for c in domain_canons)
        total_wa = sum(len(c.get("workarounds", [])) for c in domain_canons)

        html = template.render(
            domain=domain,
            entries=entries,
            total=len(entries),
            avg_fix_rate=int(sum(rates) / len(rates) * 100),
            resolvable_counts=resolvable_counts,
            total_dead_ends=total_de,
            total_workarounds=total_wa,
        )

        domain_dir = SITE_DIR / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        (domain_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  Generated: /{domain}/")


def build_index_page(canons: list[dict], jinja_env: Environment) -> None:
    """Generate the main index page."""
    template = jinja_env.get_template("index.html")

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

    # Pick a representative example error for API/feature links
    example_error_id = recent_entries[0]["id"] if recent_entries else canons[0]["id"]

    html = template.render(
        total_errors=len(canons),
        domains=domains,
        domain_stats=domain_stats,
        recent_entries=recent_entries,
        example_error_id=example_error_id,
        google_verification=GOOGLE_VERIFICATION,
        bing_verification=BING_VERIFICATION,
    )

    (SITE_DIR / "index.html").write_text(html, encoding="utf-8")
    print("  Generated: index.html")


def _write_urlset(urlset: Element, path: Path) -> None:
    """Write a urlset element to an XML file."""
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_body = tostring(urlset, encoding="unicode")
    path.write_text(xml_declaration + xml_body, encoding="utf-8")


def build_sitemap(
    canons: list[dict],
    summary_urls: list[dict] | None = None,
) -> None:
    """Generate sitemap index with per-domain sub-sitemaps.

    Environment-specific pages are excluded from sitemaps because their
    canonical URL points to the summary page. Including them would waste
    crawl budget on pages Google will consolidate anyway.
    """
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # --- Main sitemap: index, search, domain pages ---
    main_urlset = Element("urlset", xmlns=ns)

    url_elem = SubElement(main_urlset, "url")
    SubElement(url_elem, "loc").text = BASE_URL
    SubElement(url_elem, "lastmod").text = now
    SubElement(url_elem, "changefreq").text = "weekly"
    SubElement(url_elem, "priority").text = "1.0"

    url_elem = SubElement(main_urlset, "url")
    SubElement(url_elem, "loc").text = f"{BASE_URL}/search/"
    SubElement(url_elem, "lastmod").text = now
    SubElement(url_elem, "changefreq").text = "weekly"
    SubElement(url_elem, "priority").text = "0.9"

    domains_seen = set()
    for canon in canons:
        domain = canon["error"]["domain"]
        if domain not in domains_seen:
            domains_seen.add(domain)
            url_elem = SubElement(main_urlset, "url")
            SubElement(url_elem, "loc").text = f"{BASE_URL}/{domain}/"
            SubElement(url_elem, "lastmod").text = now
            SubElement(url_elem, "changefreq").text = "weekly"
            SubElement(url_elem, "priority").text = "0.9"

    _write_urlset(main_urlset, SITE_DIR / "sitemap-main.xml")
    print("  Generated: sitemap-main.xml")

    # --- Per-domain sitemaps: summary pages only ---
    summaries_by_domain: dict[str, list[dict]] = {}
    for summary in summary_urls or []:
        domain = summary["slug_key"].split("/", 1)[0]
        summaries_by_domain.setdefault(domain, []).append(summary)

    domain_sitemap_files = ["sitemap-main.xml"]
    for domain in sorted(summaries_by_domain.keys()):
        domain_urlset = Element("urlset", xmlns=ns)
        for s in summaries_by_domain[domain]:
            url_elem = SubElement(domain_urlset, "url")
            SubElement(url_elem, "loc").text = s["url"]
            SubElement(url_elem, "lastmod").text = now
            SubElement(url_elem, "changefreq").text = "weekly"
            SubElement(url_elem, "priority").text = "0.8"

        fname = f"sitemap-{domain}.xml"
        _write_urlset(domain_urlset, SITE_DIR / fname)
        domain_sitemap_files.append(fname)
        print(f"  Generated: {fname}")

    # --- Sitemap index ---
    idx_ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    sitemap_index = Element("sitemapindex", xmlns=idx_ns)
    for fname in domain_sitemap_files:
        sm = SubElement(sitemap_index, "sitemap")
        SubElement(sm, "loc").text = f"{BASE_URL}/{fname}"
        SubElement(sm, "lastmod").text = now

    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_body = tostring(sitemap_index, encoding="unicode")
    (SITE_DIR / "sitemap.xml").write_text(
        xml_declaration + xml_body, encoding="utf-8"
    )
    total = sum(
        len(v) for v in summaries_by_domain.values()
    ) + 2 + len(domains_seen)
    print(f"  Generated: sitemap.xml (index, {total} URLs)")


def build_robots_txt() -> None:
    """Generate robots.txt with explicit AI crawler allowances."""
    content = f"""# deadends.dev - Structured failure knowledge for AI coding agents
# All crawlers welcome — this site is BUILT for AI consumption

User-agent: *
Allow: /

# AI training crawlers — full access
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Googlebot
Allow: /

User-agent: GoogleOther
Allow: /

User-agent: Bingbot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: cohere-ai
Allow: /

User-agent: Bytespider
Allow: /

User-agent: Meta-ExternalAgent
Allow: /

User-agent: Meta-ExternalFetcher
Allow: /

User-agent: CCBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: Amazonbot
Allow: /

User-agent: YouBot
Allow: /

User-agent: iaskspider
Allow: /

User-agent: DeepSeekBot
Allow: /

User-agent: PhindBot
Allow: /

User-agent: PetalBot
Allow: /

User-agent: Diffbot
Allow: /

User-agent: ImagesiftBot
Allow: /

User-agent: Omgilibot
Allow: /

User-agent: Timpibot
Allow: /

User-agent: Webzio-Extended
Allow: /

User-agent: AI2Bot
Allow: /

User-agent: Ai2Bot-Dolma
Allow: /

User-agent: GrokBot
Allow: /

User-agent: MistralBot
Allow: /

User-agent: Qwen
Allow: /

Sitemap: {BASE_URL}/sitemap.xml

# AI agent config files:
# CLAUDE.md:      {BASE_URL}/CLAUDE.md
# .cursorrules:   {BASE_URL}/.cursorrules
# .windsurfrules: {BASE_URL}/.windsurfrules

# AI agent discovery:
# Match errors:    {BASE_URL}/api/v1/match.json
# Error index:     {BASE_URL}/api/v1/index.json
# OpenAPI spec:    {BASE_URL}/api/v1/openapi.json
# Version info:    {BASE_URL}/api/v1/version.json
# Stats:           {BASE_URL}/api/v1/stats.json
# NDJSON stream:   {BASE_URL}/api/v1/errors.ndjson
# LLM-optimized:   {BASE_URL}/llms.txt
# Full data dump:  {BASE_URL}/llms-full.txt
# Plugin manifest: {BASE_URL}/.well-known/ai-plugin.json
# A2A agent card:  {BASE_URL}/.well-known/agent-card.json
# Security:        {BASE_URL}/.well-known/security.txt
# Atom feed:       {BASE_URL}/feed.xml
"""
    (SITE_DIR / "robots.txt").write_text(content, encoding="utf-8")
    print("  Generated: robots.txt")


def build_404_page() -> None:
    """Generate a custom 404 page with navigation and search."""
    html = (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="theme-color" content="#0d1117">\n'
        "<title>404 — Error Not Found | deadends.dev</title>\n"
        '<meta name="robots" content="noindex">\n'
        f'<link rel="icon" href="{BASE_PATH}/favicon.svg" type="image/svg+xml">\n'
        "<style>\n"
        "body{font-family:system-ui,-apple-system,sans-serif;max-width:800px;"
        "margin:2rem auto;padding:0 1rem;color:#e0e0e0;background:#0d1117;}\n"
        "a{color:#58a6ff;}h1{font-size:1.6rem;}"
        "nav a{color:#8b949e;text-decoration:none;}nav a:hover{color:#58a6ff;}\n"
        ".links{margin:2rem 0;}.links a{display:inline-block;margin:0.5rem 1rem 0.5rem 0;}\n"
        "</style>\n"
        "</head><body>\n"
        f'<nav><a href="{BASE_PATH}/">deadends.dev</a></nav>\n'
        "<h1>404 — Error Not Found</h1>\n"
        "<p>This error page doesn't exist yet. "
        "Ironic for a site that catalogs errors.</p>\n"
        '<div class="links">\n'
        f'<a href="{BASE_PATH}/search/">Search errors</a>\n'
        f'<a href="{BASE_PATH}/">Browse all domains</a>\n'
        '<a href="https://github.com/dbwls99706/deadends.dev/issues/new">'
        "Request this error</a>\n"
        "</div>\n"
        "</body></html>"
    )
    (SITE_DIR / "404.html").write_text(html, encoding="utf-8")
    print("  Generated: 404.html")



def build_cname() -> None:
    """Generate CNAME file for custom domain."""
    (SITE_DIR / "CNAME").write_text("deadends.dev\n", encoding="utf-8")
    print("  Generated: CNAME")


def build_stylesheet() -> None:
    """Generate shared CSS stylesheet for all pages.

    Extracting CSS to a shared file enables browser caching across
    page navigations, improving Core Web Vitals (LCP, FCP).
    """
    # CSS written as joined list to avoid E501 line-length violations
    css = "\n".join([
        "/* deadends.dev — shared stylesheet */",
        "body { font-family: system-ui, -apple-system, sans-serif;",
        "  max-width: 800px; margin: 2rem auto;",
        "  padding: 0 1rem; color: #e0e0e0; background: #0d1117; }",
        "a { color: #58a6ff; }",
        "h1 { font-size: 1.4rem; }",
        "h2 { font-size: 1.1rem;",
        "  border-bottom: 1px solid #30363d;",
        "  padding-bottom: 0.5rem; }",
        "code { background: #161b22;",
        "  padding: 0.2rem 0.4rem; border-radius: 3px; }",
        "pre { background: #161b22;",
        "  padding: 1rem; border-radius: 6px;",
        "  overflow-x: auto; }",
        ".meta { color: #8b949e; font-size: 0.85rem; }",
        "nav { margin-bottom: 1.5rem; }",
        "nav a { color: #8b949e; text-decoration: none; }",
        "nav a:hover { color: #58a6ff; }",
        "footer { margin-top: 3rem;",
        "  padding-top: 1rem;",
        "  border-top: 1px solid #30363d; }",
        "",
        "/* Page-specific heading sizes */",
        ".pg-index h1 { font-size: 1.8rem; }",
        ".pg-index h2 { font-size: 1.2rem; }",
        ".pg-domain h1, .pg-summary h1, .pg-search h1 { font-size: 1.6rem; }",
        "",
        "/* Verdict colors */",
        ".verdict-true { color: #3fb950; }",
        ".verdict-partial { color: #d29922; }",
        ".verdict-false { color: #f85149; }",
        ".pg-detail .verdict-true,",
        ".pg-detail .verdict-false,",
        ".pg-detail .verdict-partial { font-weight: bold; }",
        "",
        "/* Dead ends & workarounds */",
        ".dead-end { border-left: 4px solid #f85149;",
        "  padding-left: 1rem; margin: 1rem 0; }",
        ".workaround { border-left: 4px solid #3fb950;",
        "  padding-left: 1rem; margin: 1rem 0; }",
        ".fail-rate { color: #f85149; }",
        ".success-rate { color: #3fb950; }",
        "",
        "/* Index page */",
        ".domain-list { list-style: none; padding: 0; }",
        ".domain-list li { padding: 0.5rem 0;",
        "  border-bottom: 1px solid #161b22; }",
        ".domain-list li a {",
        "  text-decoration: none; font-size: 1.05rem; }",
        ".count { color: #8b949e; font-size: 0.9rem; }",
        ".hero { margin: 2rem 0; }",
        ".api-section code { font-size: 0.9rem; }",
        "",
        "/* Domain page */",
        ".entry { padding: 0.75rem 0;",
        "  border-bottom: 1px solid #161b22; }",
        "",
        "/* Error summary page */",
        ".env-card { border: 1px solid #30363d;",
        "  border-radius: 6px;",
        "  padding: 1rem; margin: 0.75rem 0; }",
        ".variation { display: inline-block;",
        "  background: #161b22;",
        "  padding: 0.2rem 0.6rem;",
        "  border-radius: 4px;",
        "  margin: 0.2rem; font-size: 0.85rem; }",
        "",
        "/* Search page */",
        "#search-input { width: 100%;",
        "  padding: 0.75rem; font-size: 1rem;",
        "  font-family: monospace;",
        "  background: #161b22; color: #e0e0e0;",
        "  border: 1px solid #30363d;",
        "  border-radius: 6px;",
        "  box-sizing: border-box; }",
        "#search-input:focus {",
        "  border-color: #58a6ff; outline: none; }",
        "#search-input::placeholder { color: #484f58; }",
        ".result { border: 1px solid #30363d;",
        "  border-radius: 6px;",
        "  padding: 1rem; margin: 0.75rem 0; }",
        ".result:hover { border-color: #58a6ff; }",
        ".result h3 {",
        "  margin: 0 0 0.5rem 0; font-size: 1rem; }",
        ".result .dead-end-count { color: #f85149; }",
        ".result .workaround-count { color: #3fb950; }",
        "#no-results { display: none; color: #8b949e;",
        "  padding: 2rem; text-align: center; }",
        "#all-errors { margin-top: 2rem; }",
        ".error-entry { padding: 0.4rem 0;",
        "  border-bottom: 1px solid #161b22; }",
        "",
    ])
    (SITE_DIR / "style.css").write_text(css, encoding="utf-8")
    print("  Generated: style.css")


def build_og_image() -> None:
    """Generate a branded OG image (1200x630 PNG) for social sharing.

    Creates a minimal valid PNG using Python stdlib (zlib + struct).
    Dark background with branded text area for social media previews.
    """
    import struct
    import zlib

    width, height = 1200, 630
    # Background: #0d1117 (matches site theme)
    bg_r, bg_g, bg_b = 0x0D, 0x11, 0x17
    # Accent bar: #58a6ff (link color)
    accent_r, accent_g, accent_b = 0x58, 0xA6, 0xFF
    # Red accent: #f85149 (dead end color)
    red_r, red_g, red_b = 0xF8, 0x51, 0x49

    # Build raw pixel data row by row
    raw_rows = []
    for y in range(height):
        row = b"\x00"  # PNG filter byte: None
        for x in range(width):
            # Top accent bar (0-6px)
            if y < 6:
                row += bytes([accent_r, accent_g, accent_b])
            # Bottom accent bar
            elif y >= height - 6:
                row += bytes([red_r, red_g, red_b])
            # Left accent stripe (0-6px)
            elif x < 6:
                row += bytes([accent_r, accent_g, accent_b])
            # Right accent stripe
            elif x >= width - 6:
                row += bytes([red_r, red_g, red_b])
            else:
                row += bytes([bg_r, bg_g, bg_b])
        raw_rows.append(row)

    raw_data = b"".join(raw_rows)
    compressed = zlib.compress(raw_data, 9)

    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + chunk + crc

    png = b"\x89PNG\r\n\x1a\n"
    # IHDR: width, height, bit_depth=8, color_type=2(RGB), compression, filter, interlace
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png += make_chunk(b"IHDR", ihdr_data)
    png += make_chunk(b"IDAT", compressed)
    png += make_chunk(b"IEND", b"")

    (SITE_DIR / "og-image.png").write_bytes(png)
    print("  Generated: og-image.png (1200x630)")


def build_favicon() -> None:
    """Generate a simple SVG favicon."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<rect width="100" height="100" rx="12" fill="#0d1117"/>'
        '<text x="50" y="68" font-size="56" text-anchor="middle" '
        'font-family="system-ui,sans-serif" font-weight="bold">'
        '<tspan fill="#f85149">&#x2718;</tspan>'
        '</text></svg>'
    )
    (SITE_DIR / "favicon.svg").write_text(svg, encoding="utf-8")
    print("  Generated: favicon.svg")


def _generate_variations(signature: str, regex: str, domain: str) -> list[str]:
    """Generate common text variations of an error signature.

    These help with SEO by covering different phrasings AI agents
    or developers might search for.
    """
    variations = []

    # Domain-specific variation patterns
    _VARIATION_FILLS: dict[str, list[str]] = {
        "python": ["torch", "numpy", "cv2", "pandas", "tensorflow", "sklearn"],
        "node": ["express", "react", "next", "axios", "webpack"],
        "pip": ["torch", "numpy", "opencv-python", "tensorflow", "scipy"],
        "docker": ["/var/run/docker.sock", "/dev/sda1", "172.17.0.0/16"],
        "cuda": ["0", "1", "cuda:0", "NVIDIA A100"],
        "git": ["main", "master", "origin/main", "develop"],
        "typescript": ["react", "./components", "@types/node", "lodash"],
        "rust": ["String", "&str", "Vec<T>", "Box<dyn Error>"],
        "go": ["main", "http", "fmt", "context"],
        "kubernetes": ["nginx", "postgres", "redis", "my-app"],
        "terraform": ["aws_instance", "azurerm_resource_group", "google_compute_instance"],
        "aws": ["s3:GetObject", "sts:AssumeRole", "ec2:DescribeInstances"],
        "nextjs": ["./components/Header", "react-dom", "next/image"],
        "react": ["useState", "useEffect", "useContext", "useReducer"],
    }

    fills = _VARIATION_FILLS.get(domain, [])

    # If signature has a placeholder pattern (like 'X' or quotes),
    # substitute common module/package names
    import re as _re

    # Check for common placeholder patterns
    placeholder_patterns = [
        (r"'([^']*)'", fills[:4]),  # single-quoted
        (r'"([^"]*)"', fills[:4]),  # double-quoted
        (r"'X'", fills[:4]),
    ]

    for pattern, substitutions in placeholder_patterns:
        match = _re.search(pattern, signature)
        if match:
            original = match.group(0)
            for sub in substitutions:
                new_sig = signature.replace(original, f"'{sub}'", 1)
                if new_sig != signature and new_sig not in variations:
                    variations.append(new_sig)
            break

    return variations[:6]  # Limit to 6 variations


def build_error_summary_pages(
    canons: list[dict], jinja_env: Environment
) -> list[dict]:
    """Generate environment-agnostic error summary pages.

    For each unique error slug (domain/slug), creates a landing page
    that aggregates all environments. Returns summary metadata for sitemap.
    """
    template = jinja_env.get_template("error_summary.html")
    known_ids = {c["id"] for c in canons}

    # Group canons by domain/slug (strip the env part of the id)
    by_slug: dict[str, list[dict]] = {}
    for canon in canons:
        parts = canon["id"].rsplit("/", 1)
        if len(parts) == 2:
            slug_key = parts[0]  # e.g., "python/modulenotfounderror"
        else:
            continue
        by_slug.setdefault(slug_key, []).append(canon)

    # Build per-domain summary list for cross-linking
    slug_signatures: dict[str, str] = {}
    for sk, sc in by_slug.items():
        slug_signatures[sk] = sc[0]["error"]["signature"]

    summaries = []
    for slug_key, slug_canons in by_slug.items():
        domain, slug = slug_key.split("/", 1)
        first = slug_canons[0]
        signature = first["error"]["signature"]
        regex = first["error"]["regex"]

        environments = []
        all_dead_ends = []
        all_workarounds = []
        verdict_summary = first["verdict"]["summary"]

        for c in sorted(slug_canons, key=lambda x: x["id"]):
            environments.append({
                "id": c["id"],
                "env_summary": build_env_summary(c),
                "resolvable": c["verdict"]["resolvable"],
                "fix_rate": c["verdict"]["fix_success_rate"],
                "dead_end_count": len(c["dead_ends"]),
                "workaround_count": len(c.get("workarounds", [])),
            })
            all_dead_ends.extend(c["dead_ends"])
            all_workarounds.extend(c.get("workarounds", []))

        # Deduplicate dead ends by action (keep highest fail_rate)
        seen_de: dict[str, dict] = {}
        for de in all_dead_ends:
            key = de["action"]
            if key not in seen_de or de["fail_rate"] > seen_de[key]["fail_rate"]:
                seen_de[key] = de
        common_dead_ends = sorted(
            seen_de.values(), key=lambda x: x["fail_rate"], reverse=True
        )

        # Deduplicate workarounds by action (keep highest success_rate)
        seen_wa: dict[str, dict] = {}
        for wa in all_workarounds:
            key = wa["action"]
            if (
                key not in seen_wa
                or wa["success_rate"] > seen_wa[key]["success_rate"]
            ):
                seen_wa[key] = wa
        common_workarounds = sorted(
            seen_wa.values(),
            key=lambda x: x["success_rate"],
            reverse=True,
        )

        rates = [c["verdict"]["fix_success_rate"] for c in slug_canons]
        min_rate = int(min(rates) * 100)
        max_rate = int(max(rates) * 100)

        # Aggregate transition_graph across all environments
        all_leads_to: dict[str, dict] = {}
        all_preceded_by: dict[str, dict] = {}
        all_confused_with: dict[str, dict] = {}
        for c in slug_canons:
            graph = c.get("transition_graph", {})
            for lt in graph.get("leads_to", []):
                eid = lt["error_id"]
                existing = all_leads_to.get(eid, {})
                if lt.get("probability", 0) > existing.get("probability", 0):
                    all_leads_to[eid] = lt
            for pb in graph.get("preceded_by", []):
                eid = pb["error_id"]
                existing = all_preceded_by.get(eid, {})
                if pb.get("probability", 0) > existing.get("probability", 0):
                    all_preceded_by[eid] = pb
            for fc in graph.get("frequently_confused_with", []):
                eid = fc["error_id"]
                if eid not in all_confused_with:
                    all_confused_with[eid] = fc

        aggregated_graph = {}
        if all_leads_to:
            aggregated_graph["leads_to"] = sorted(
                all_leads_to.values(),
                key=lambda x: x.get("probability", 0),
                reverse=True,
            )
        if all_preceded_by:
            aggregated_graph["preceded_by"] = sorted(
                all_preceded_by.values(),
                key=lambda x: x.get("probability", 0),
                reverse=True,
            )
        if all_confused_with:
            aggregated_graph["frequently_confused_with"] = list(
                all_confused_with.values()
            )

        # Generate common variations from the regex pattern
        common_variations = _generate_variations(signature, regex, domain)

        # TechArticle JSON-LD for error summary pages
        dates = [
            c["verdict"].get("last_updated", "")
            for c in slug_canons
        ]
        first_seen_dates = [
            c["error"].get("first_seen", "")
            for c in slug_canons
            if c["error"].get("first_seen")
        ]
        summary_json_ld = json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "TechArticle",
                "name": signature,
                "headline": f"Fix {signature}",
                "description": (
                    f"{len(environments)} environments, "
                    f"{len(common_dead_ends)} dead ends, "
                    f"{len(common_workarounds)} workarounds. "
                    f"Fix rates: {min_rate}%–{max_rate}%."
                ),
                "url": f"{BASE_URL}/{domain}/{slug}/",
                "datePublished": min(first_seen_dates)
                if first_seen_dates
                else "",
                "dateModified": max(dates) if dates else "",
                "image": f"{BASE_URL}/og-image.png",
                "publisher": {
                    "@type": "Organization",
                    "name": "deadends.dev",
                    "url": BASE_URL,
                },
                "about": {
                    "@type": "SoftwareSourceCode",
                    "programmingLanguage": domain,
                },
            },
            indent=2,
            ensure_ascii=False,
        )

        # Same-domain errors for cross-linking (exclude self)
        same_domain = [
            {"slug_key": sk, "signature": sig}
            for sk, sig in slug_signatures.items()
            if sk.startswith(f"{domain}/") and sk != slug_key
        ][:10]

        html = template.render(
            signature=signature,
            regex=regex,
            domain=domain,
            slug=slug,
            environments=environments,
            common_dead_ends=common_dead_ends,
            common_workarounds=common_workarounds,
            common_variations=common_variations,
            total_dead_ends=len(common_dead_ends),
            total_workarounds=len(common_workarounds),
            min_rate=min_rate,
            max_rate=max_rate,
            summary_json_ld=summary_json_ld,
            transition_graph=aggregated_graph,
            known_ids=known_ids,
            domain_errors=same_domain,
            verdict_summary=verdict_summary,
        )

        # Write to /{domain}/{slug}/index.html
        summary_dir = SITE_DIR / domain / slug
        summary_dir.mkdir(parents=True, exist_ok=True)
        (summary_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  Generated: /{domain}/{slug}/")

        summaries.append({
            "slug_key": slug_key,
            "url": f"{BASE_URL}/{domain}/{slug}/",
        })

    return summaries


def build_search_page(
    canons: list[dict], jinja_env: Environment
) -> None:
    """Generate client-side error matching search page."""
    template = jinja_env.get_template("search.html")

    # Build search data (subset of index for client-side use)
    search_data = []
    for canon in sorted(canons, key=lambda c: c["id"]):
        search_data.append({
            "id": canon["id"],
            "signature": canon["error"]["signature"],
            "regex": canon["error"]["regex"],
            "domain": canon["error"]["domain"],
            "resolvable": canon["verdict"]["resolvable"],
            "fix_success_rate": canon["verdict"]["fix_success_rate"],
            "dead_end_count": len(canon["dead_ends"]),
            "workaround_count": len(canon.get("workarounds", [])),
            "page_url": f"{BASE_PATH}/{canon['id']}",
        })

    # Group by domain for the "all errors" section
    by_domain: dict[str, list[dict]] = {}
    for entry in search_data:
        by_domain.setdefault(entry["domain"], []).append(entry)

    domain_errors = [
        {"name": domain, "errors": errors}
        for domain, errors in sorted(by_domain.items())
    ]

    html = template.render(
        total_errors=len(canons),
        domain_count=len(by_domain),
        domain_errors=domain_errors,
        search_data=json.dumps(search_data, ensure_ascii=False),
    )

    search_dir = SITE_DIR / "search"
    search_dir.mkdir(parents=True, exist_ok=True)
    (search_dir / "index.html").write_text(html, encoding="utf-8")
    print("  Generated: /search/")


def build_llms_txt(canons: list[dict]) -> None:
    """Generate llms.txt (llmstxt.org standard) and llms-full.txt."""
    # Group by domain for organized listing
    by_domain: dict[str, list[dict]] = {}
    for c in canons:
        by_domain.setdefault(c["error"]["domain"], []).append(c)

    # Deduplicate signatures for llms.txt (environment-agnostic)
    seen_signatures: dict[str, dict] = {}
    for c in sorted(canons, key=lambda x: x["id"]):
        sig = c["error"]["signature"]
        if sig not in seen_signatures:
            seen_signatures[sig] = c

    # llmstxt.org standard format
    lines = [
        "# deadends.dev",
        "",
        "> Structured failure knowledge for AI coding agents. "
        f"{len(canons)} error entries across {len(by_domain)} domains. "
        "Check dead ends before attempting a fix. "
        "Check workarounds for approaches that actually work.",
        "",
        "## Integration Methods (choose one)",
        "",
        "### Option 1: MCP Server (recommended for AI coding agents)",
        "",
        "```",
        "pip install deadends-dev",
        "python -m mcp.server  # stdio mode",
        "```",
        "",
        "Tools: `lookup_error`, `get_error_detail`, `search_errors`, "
        "`batch_lookup`, `get_error_chain`, `list_error_domains`, "
        "`list_errors_by_domain`, `get_domain_stats`",
        "",
        "### Option 2: REST API",
        "",
        f"- [Match Endpoint]({BASE_URL}/api/v1/match.json): "
        "Lightweight regex matching (fits in context window)",
        f"- [API Index]({BASE_URL}/api/v1/index.json): "
        "Full error index with API URLs",
        f"- [OpenAPI Spec]({BASE_URL}/api/v1/openapi.json): "
        "Full API specification",
        f"- [NDJSON Stream]({BASE_URL}/api/v1/errors.ndjson): "
        "Streaming format for batch processing",
        "",
        "### Option 3: Full Context Dump",
        "",
        f"- [Complete Database]({BASE_URL}/llms-full.txt): "
        "All errors in plaintext (load into context window)",
        "",
        "## How to Use",
        "",
        "1. Match your error against the regex patterns below",
        f"2. Fetch the full canon: `GET {BASE_URL}/api/v1/{{id}}.json`",
        "3. Read `dead_ends[]` — do NOT try these (saves time and tokens)",
        "4. Read `workarounds[]` — try these instead (includes success rates)",
        "5. Read `transition_graph` — know what error comes next",
        "",
    ]

    for domain in sorted(by_domain.keys()):
        domain_sigs = {}
        for c in sorted(by_domain[domain], key=lambda x: x["id"]):
            sig = c["error"]["signature"]
            if sig not in domain_sigs:
                domain_sigs[sig] = c

        lines.append(f"## {domain}")
        lines.append("")
        for sig, c in domain_sigs.items():
            slug_key = c["id"].rsplit("/", 1)[0]
            lines.append(
                f"- [{c['error']['signature']}]"
                f"({BASE_URL}/{slug_key}/): "
                f"{c['verdict']['summary']}"
            )
        lines.append("")

    (SITE_DIR / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    print("  Generated: llms.txt")

    # llms-full.txt — complete data dump for AI context windows
    full_lines = [
        "# deadends.dev — Complete Error Database",
        "",
        f"> {len(canons)} errors across {len(by_domain)} domains. "
        f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d')}.",
        "",
        "## Quick Reference",
        "",
        "- Match endpoint: `GET /api/v1/match.json`",
        "- Full canon: `GET /api/v1/{domain}/{slug}/{env}.json`",
        "",
    ]
    for canon in sorted(canons, key=lambda c: c["id"]):
        full_lines.append(f"## {canon['id']}")
        full_lines.append("")
        full_lines.append(f"- ERROR: {canon['error']['signature']}")
        full_lines.append(f"- REGEX: `{canon['error']['regex']}`")
        full_lines.append(f"- RESOLVABLE: {canon['verdict']['resolvable']}")
        full_lines.append(
            f"- FIX_RATE: {canon['verdict']['fix_success_rate']}"
        )
        full_lines.append(f"- SUMMARY: {canon['verdict']['summary']}")
        full_lines.append("")
        full_lines.append("### Dead Ends")
        full_lines.append("")
        for de in canon["dead_ends"]:
            full_lines.append(
                f"- {de['action']} (fail_rate={de['fail_rate']}): "
                f"{de['why_fails']}"
            )
        full_lines.append("")
        full_lines.append("### Workarounds")
        full_lines.append("")
        for wa in canon.get("workarounds", []):
            how_text = f" — `{wa['how']}`" if wa.get("how") else ""
            full_lines.append(
                f"- {wa['action']} "
                f"(success_rate={wa['success_rate']}){how_text}"
            )
        full_lines.append("")

    (SITE_DIR / "llms-full.txt").write_text(
        "\n".join(full_lines), encoding="utf-8"
    )
    print("  Generated: llms-full.txt")


def build_api_index(canons: list[dict]) -> None:
    """Generate /api/v1/index.json — master error index for AI agents."""
    index = {
        "schema_version": "1.0.0",
        "total": len(canons),
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "errors": [],
    }

    for canon in sorted(canons, key=lambda c: c["id"]):
        index["errors"].append({
            "id": canon["id"],
            "signature": canon["error"]["signature"],
            "regex": canon["error"]["regex"],
            "domain": canon["error"]["domain"],
            "category": canon["error"]["category"],
            "resolvable": canon["verdict"]["resolvable"],
            "fix_success_rate": canon["verdict"]["fix_success_rate"],
            "confidence": canon["verdict"]["confidence"],
            "dead_end_count": len(canon["dead_ends"]),
            "workaround_count": len(canon.get("workarounds", [])),
            "api_url": f"{BASE_URL}/api/v1/{canon['id']}.json",
            "page_url": canon["url"],
        })

    api_dir = SITE_DIR / "api" / "v1"
    api_dir.mkdir(parents=True, exist_ok=True)
    (api_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("  Generated: /api/v1/index.json")


def build_openapi_spec(canons: list[dict]) -> None:
    """Generate OpenAPI 3.1 spec for the JSON API."""
    domains = sorted({c["error"]["domain"] for c in canons})
    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": "deadends.dev API",
            "description": (
                "Structured failure knowledge for AI agents. "
                "Query error signatures to find dead ends, workarounds, "
                "and error transition graphs."
            ),
            "version": "1.0.0",
            "contact": {"url": "https://github.com/dbwls99706/deadends.dev"},
        },
        "servers": [{"url": f"{BASE_URL}/api/v1"}],
        "paths": {
            "/index.json": {
                "get": {
                    "summary": "List all known errors",
                    "description": (
                        "Returns an index of all error signatures with "
                        "regex patterns, verdicts, and API URLs."
                    ),
                    "operationId": "listErrors",
                    "responses": {
                        "200": {
                            "description": "Error index",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "total": {"type": "integer"},
                                            "errors": {
                                                "type": "array",
                                                "items": {
                                                    "$ref": "#/components/schemas/ErrorSummary"
                                                },
                                            },
                                        },
                                    },
                                    "example": {
                                        "schema_version": "1.0.0",
                                        "total": len(canons),
                                        "errors": [{
                                            "id": "python/modulenotfounderror/py311-linux",
                                            "signature": "ModuleNotFoundError: No module named 'X'",
                                            "regex": "ModuleNotFoundError.*No module named",
                                            "domain": "python",
                                            "resolvable": "true",
                                            "fix_success_rate": 0.85,
                                            "api_url": (
                                                f"{BASE_URL}/api/v1/python/"
                                                "modulenotfounderror/py311-linux.json"
                                            ),
                                        }],
                                    },
                                }
                            },
                        }
                    },
                }
            },
            "/match.json": {
                "get": {
                    "summary": "Lightweight error matching",
                    "description": (
                        "Compact file with all error signatures and regexes. "
                        "Load into context window and regex-match your error. "
                        "On match, fetch the full canon via the api_url."
                    ),
                    "operationId": "matchErrors",
                    "responses": {
                        "200": {
                            "description": "Compact matching patterns",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "version": {"type": "string"},
                                            "total": {"type": "integer"},
                                            "generated": {
                                                "type": "string",
                                                "format": "date-time",
                                            },
                                            "usage": {"type": "string"},
                                            "patterns": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {
                                                            "type": "string",
                                                            "description": (
                                                                "Canon ID"
                                                            ),
                                                        },
                                                        "sig": {
                                                            "type": "string",
                                                            "description": (
                                                                "Error signature"
                                                            ),
                                                        },
                                                        "re": {
                                                            "type": "string",
                                                            "description": (
                                                                "Regex pattern"
                                                            ),
                                                        },
                                                        "domain": {
                                                            "type": "string",
                                                        },
                                                        "ok": {
                                                            "type": "string",
                                                            "enum": [
                                                                "true",
                                                                "partial",
                                                                "false",
                                                            ],
                                                            "description": (
                                                                "Resolvable"
                                                            ),
                                                        },
                                                        "rate": {
                                                            "type": "number",
                                                            "description": (
                                                                "Fix success rate"
                                                            ),
                                                        },
                                                        "conf": {
                                                            "type": "number",
                                                            "description": (
                                                                "Confidence score"
                                                            ),
                                                        },
                                                        "de": {
                                                            "type": "integer",
                                                            "description": (
                                                                "Dead end count"
                                                            ),
                                                        },
                                                        "wa": {
                                                            "type": "integer",
                                                            "description": (
                                                                "Workaround count"
                                                            ),
                                                        },
                                                        "url": {
                                                            "type": "string",
                                                            "format": "uri",
                                                            "description": (
                                                                "Full JSON API URL"
                                                            ),
                                                        },
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        }
                    },
                }
            },
            "/stats.json": {
                "get": {
                    "summary": "Dataset statistics by domain",
                    "description": (
                        "Detailed statistics: error counts, average fix rates, "
                        "resolvability breakdowns, confidence levels per domain. "
                        "Use this to assess data quality before relying on it."
                    ),
                    "operationId": "getStats",
                    "responses": {
                        "200": {
                            "description": "Dataset statistics",
                            "content": {"application/json": {}},
                        }
                    },
                }
            },
            "/errors.ndjson": {
                "get": {
                    "summary": "Stream all errors as NDJSON",
                    "description": (
                        "Newline-delimited JSON. Each line is a complete "
                        "ErrorCanon object. Use for streaming/batch processing "
                        "without loading entire dataset into memory."
                    ),
                    "operationId": "streamErrors",
                    "responses": {
                        "200": {
                            "description": "NDJSON stream",
                            "content": {"application/x-ndjson": {}},
                        }
                    },
                }
            },
            "/{domain}/{slug}/{env}.json": {
                "get": {
                    "summary": "Get full ErrorCanon data",
                    "description": (
                        "Returns the complete ErrorCanon for a specific "
                        "error in a specific environment."
                    ),
                    "operationId": "getErrorCanon",
                    "parameters": [
                        {
                            "name": "domain",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "enum": domains,
                            },
                        },
                        {
                            "name": "slug",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "env",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Full ErrorCanon",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorCanon"
                                    }
                                }
                            },
                        }
                    },
                }
            },
        },
        "components": {
            "schemas": {
                "ErrorSummary": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "signature": {"type": "string"},
                        "regex": {"type": "string"},
                        "domain": {"type": "string"},
                        "resolvable": {
                            "type": "string",
                            "enum": ["true", "partial", "false"],
                        },
                        "fix_success_rate": {"type": "number"},
                        "api_url": {"type": "string", "format": "uri"},
                    },
                },
                "ErrorCanon": {
                    "type": "object",
                    "description": (
                        "Complete structured failure knowledge for one "
                        "error in one environment."
                    ),
                    "properties": {
                        "id": {"type": "string"},
                        "error": {
                            "type": "object",
                            "properties": {
                                "signature": {"type": "string"},
                                "regex": {"type": "string"},
                                "domain": {"type": "string"},
                                "category": {"type": "string"},
                            },
                        },
                        "environment": {"type": "object"},
                        "verdict": {
                            "type": "object",
                            "properties": {
                                "resolvable": {
                                    "type": "string",
                                    "enum": ["true", "partial", "false"],
                                },
                                "fix_success_rate": {"type": "number"},
                                "confidence": {
                                    "type": "number",
                                    "description": "0.0-1.0 score",
                                },
                                "summary": {"type": "string"},
                            },
                        },
                        "dead_ends": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string"},
                                    "why_fails": {"type": "string"},
                                    "fail_rate": {"type": "number"},
                                },
                            },
                        },
                        "workarounds": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string"},
                                    "how": {"type": "string"},
                                    "success_rate": {"type": "number"},
                                },
                            },
                        },
                        "transition_graph": {
                            "type": "object",
                            "properties": {
                                "leads_to": {"type": "array"},
                                "preceded_by": {"type": "array"},
                                "frequently_confused_with": {"type": "array"},
                            },
                        },
                    },
                },
            }
        },
    }

    api_dir = SITE_DIR / "api" / "v1"
    api_dir.mkdir(parents=True, exist_ok=True)
    (api_dir / "openapi.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("  Generated: /api/v1/openapi.json")


def build_well_known(canons: list[dict]) -> None:
    """Generate .well-known/ discovery files for AI agents."""
    well_known_dir = SITE_DIR / ".well-known"
    well_known_dir.mkdir(parents=True, exist_ok=True)

    domains = sorted({c["error"]["domain"] for c in canons})

    # ai-plugin.json (OpenAI legacy format)
    plugin = {
        "schema_version": "v1",
        "name_for_human": "deadends.dev",
        "name_for_model": "deadend_error_knowledge",
        "description_for_human": (
            "Structured failure knowledge — check what NOT to try "
            "before debugging an error."
        ),
        "description_for_model": (
            "Error knowledge database with "
            f"{len(canons)} patterns across {len(domains)} domains "
            f"({', '.join(domains)}). "
            "Query flow: (1) GET /api/v1/match.json (350KB, "
            "load once, regex-match locally). "
            "(2) On match, GET /api/v1/{id}.json for full details. "
            "Each error returns: dead_ends[] (what fails, with "
            "fail_rate), workarounds[] (what works, with "
            "success_rate and how), transition_graph "
            "(leads_to, preceded_by, frequently_confused_with). "
            "Alt: GET /llms.txt for text summary, "
            "GET /api/v1/errors.ndjson for streaming, "
            "or use MCP server (8 tools). No auth required."
        ),
        "auth": {"type": "none"},
        "api": {
            "type": "openapi",
            "url": f"{BASE_URL}/api/v1/openapi.json",
        },
        "logo_url": f"{BASE_URL}/favicon.svg",
        "contact_email": "dbwls99706@github.io",
        "legal_info_url": f"{BASE_URL}/",
    }

    (well_known_dir / "ai-plugin.json").write_text(
        json.dumps(plugin, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("  Generated: .well-known/ai-plugin.json")

    # agent-card.json (Google A2A protocol)
    agent_card = {
        "name": "deadends.dev",
        "description": (
            f"Structured error knowledge database for AI coding agents. "
            f"{len(canons)} error patterns across {len(domains)} domains "
            f"({', '.join(domains)}). Query error messages to get dead ends "
            f"(what NOT to try), workarounds (what works with success rates), "
            f"and error transition graphs (what error comes next)."
        ),
        "version": "1.0.0",
        "url": BASE_URL,
        "provider": {
            "organization": "deadends.dev",
            "url": BASE_URL,
        },
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
        },
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "skills": [
            {
                "id": "match-error",
                "name": "Match Error Message",
                "description": (
                    f"Match an error message against {len(canons)} known "
                    f"patterns across {len(domains)} domains. Returns dead "
                    f"ends, workarounds with success rates, and error chains."
                ),
                "tags": [
                    "errors",
                    "debugging",
                    "troubleshooting",
                    "dead-ends",
                    "workarounds",
                ],
                "examples": [
                    "ModuleNotFoundError: No module named 'torch'",
                    "CUDA error: out of memory",
                    "CrashLoopBackOff",
                    "TS2307: Cannot find module",
                ],
                "inputModes": ["text"],
                "outputModes": ["text"],
            },
            {
                "id": "get-error-detail",
                "name": "Get Error Details",
                "description": (
                    "Get full structured failure knowledge for a specific "
                    "error by its ID. Returns complete dead ends, "
                    "workarounds, transition graphs, and source evidence."
                ),
                "tags": ["errors", "lookup", "api"],
                "inputModes": ["text"],
                "outputModes": ["text"],
            },
            {
                "id": "list-domains",
                "name": "List Error Domains",
                "description": (
                    f"List all {len(domains)} error domains with counts."
                ),
                "tags": ["domains", "index"],
                "inputModes": ["text"],
                "outputModes": ["text"],
            },
            {
                "id": "search-errors",
                "name": "Search Errors",
                "description": (
                    "Fuzzy keyword search across all errors. Use when "
                    "you have a vague description rather than an exact "
                    "error message."
                ),
                "tags": ["search", "errors"],
                "inputModes": ["text"],
                "outputModes": ["text"],
            },
            {
                "id": "list-by-domain",
                "name": "List Errors By Domain",
                "description": (
                    "List all errors in a specific domain with fix rates."
                ),
                "tags": ["domain", "list"],
                "inputModes": ["text"],
                "outputModes": ["text"],
            },
            {
                "id": "batch-lookup",
                "name": "Batch Lookup",
                "description": (
                    "Look up multiple error messages at once (max 10). "
                    "Use for debugging error chains or log analysis."
                ),
                "tags": ["batch", "errors"],
                "inputModes": ["text"],
                "outputModes": ["text"],
            },
            {
                "id": "domain-stats",
                "name": "Domain Statistics",
                "description": (
                    "Get quality metrics for a domain: error counts, "
                    "fix rates, resolvability, confidence levels."
                ),
                "tags": ["stats", "quality"],
                "inputModes": ["text"],
                "outputModes": ["text"],
            },
            {
                "id": "error-chain",
                "name": "Error Chain Traversal",
                "description": (
                    "Get the transition graph for an error: what errors "
                    "follow, what precedes it, what gets confused with it."
                ),
                "tags": ["chain", "graph", "transitions"],
                "inputModes": ["text"],
                "outputModes": ["text"],
            },
        ],
        "authentication": {"schemes": ["none"]},
        "documentationUrl": f"{BASE_URL}/api/v1/openapi.json",
        "feedUrl": f"{BASE_URL}/feed.xml",
    }

    (well_known_dir / "agent-card.json").write_text(
        json.dumps(agent_card, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("  Generated: .well-known/agent-card.json")

    # security.txt (RFC 9116)
    security_txt = (
        "Contact: https://github.com/dbwls99706/deadends.dev/issues\n"
        "Expires: 2027-01-01T00:00:00Z\n"
        "Preferred-Languages: en, ko\n"
        f"Canonical: {BASE_URL}/.well-known/security.txt\n"
    )
    (well_known_dir / "security.txt").write_text(security_txt, encoding="utf-8")
    print("  Generated: .well-known/security.txt")

    # Copy MCP Registry domain verification file if it exists
    mcp_auth_src = PROJECT_ROOT / ".well-known" / "mcp-registry-auth"
    if mcp_auth_src.exists():
        shutil.copy2(mcp_auth_src, well_known_dir / "mcp-registry-auth")
        print("  Generated: .well-known/mcp-registry-auth")


def build_stats_json(canons: list[dict]) -> None:
    """Generate /api/v1/stats.json — dataset statistics for AI coding agents."""
    domains: dict[str, list[dict]] = {}
    for c in canons:
        domains.setdefault(c["error"]["domain"], []).append(c)

    domain_stats = {}
    for domain, dcanons in sorted(domains.items()):
        rates = [c["verdict"]["fix_success_rate"] for c in dcanons]
        res = {"true": 0, "partial": 0, "false": 0}
        conf = {"high": 0, "medium": 0, "low": 0}
        cats: dict[str, int] = {}
        for c in dcanons:
            res[c["verdict"]["resolvable"]] = res.get(c["verdict"]["resolvable"], 0) + 1
            raw_conf = c["verdict"]["confidence"]
            if isinstance(raw_conf, (int, float)):
                conf_label = (
                    "high" if raw_conf >= 0.8
                    else "medium" if raw_conf >= 0.5
                    else "low"
                )
            else:
                conf_label = str(raw_conf)
            conf[conf_label] = conf.get(conf_label, 0) + 1
            cat = c["error"]["category"]
            cats[cat] = cats.get(cat, 0) + 1

        domain_stats[domain] = {
            "count": len(dcanons),
            "avg_fix_rate": round(sum(rates) / len(rates), 3),
            "resolvability": res,
            "confidence": conf,
            "top_categories": dict(
                sorted(cats.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
        }

    all_rates = [c["verdict"]["fix_success_rate"] for c in canons]
    stats = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_errors": len(canons),
        "total_domains": len(domains),
        "avg_fix_rate": round(sum(all_rates) / len(all_rates), 3),
        "domains": domain_stats,
    }

    api_dir = SITE_DIR / "api" / "v1"
    api_dir.mkdir(parents=True, exist_ok=True)
    (api_dir / "stats.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("  Generated: /api/v1/stats.json")


def build_ndjson(canons: list[dict]) -> None:
    """Generate /api/v1/errors.ndjson — newline-delimited JSON for streaming.

    Each line is a complete error canon JSON object. AI agents can stream-process
    this file without buffering the entire dataset into memory.
    """
    api_dir = SITE_DIR / "api" / "v1"
    api_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for canon in sorted(canons, key=lambda c: c["id"]):
        lines.append(json.dumps(canon, ensure_ascii=False, separators=(",", ":")))
    (api_dir / "errors.ndjson").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(f"  Generated: /api/v1/errors.ndjson ({len(lines)} records)")


def build_version_json(canons: list[dict]) -> None:
    """Generate /api/v1/version.json — service metadata for AI coding agents."""
    domains = sorted({c["error"]["domain"] for c in canons})
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    version_data = {
        "service": "deadends.dev",
        "version": "1.4.0",
        "description": (
            "Structured failure knowledge for AI coding agents. "
            "Dead ends, workarounds, and error chains."
        ),
        "last_updated": now,
        "stats": {
            "total_errors": len(canons),
            "domains": len(domains),
            "domain_list": domains,
        },
        "endpoints": {
            "match": f"{BASE_URL}/api/v1/match.json",
            "index": f"{BASE_URL}/api/v1/index.json",
            "openapi": f"{BASE_URL}/api/v1/openapi.json",
            "version": f"{BASE_URL}/api/v1/version.json",
            "error_detail": f"{BASE_URL}/api/v1/{{domain}}/{{slug}}/{{env}}.json",
            "llms_txt": f"{BASE_URL}/llms.txt",
            "llms_full": f"{BASE_URL}/llms-full.txt",
            "stats": f"{BASE_URL}/api/v1/stats.json",
            "ndjson_stream": f"{BASE_URL}/api/v1/errors.ndjson",
        },
        "discovery": {
            "ai_plugin": f"{BASE_URL}/.well-known/ai-plugin.json",
            "agent_card": f"{BASE_URL}/.well-known/agent-card.json",
            "mcp_server": "pip install deadends-dev && python -m mcp.server",
        },
    }

    api_dir = SITE_DIR / "api" / "v1"
    api_dir.mkdir(parents=True, exist_ok=True)
    (api_dir / "version.json").write_text(
        json.dumps(version_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("  Generated: /api/v1/version.json")


def build_match_json(canons: list[dict]) -> None:
    """Generate /api/v1/match.json — ultra-lightweight matching file.

    Contains only signatures and regexes so AI agents can load the entire
    file into their context window and match errors without fetching
    individual pages.
    """
    match_data = {
        "version": "1.0.0",
        "total": len(canons),
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "usage": (
            "Match your error message against the regex patterns below. "
            "On match, fetch the api_url for full dead_ends and workarounds."
        ),
        "patterns": [],
    }

    for canon in sorted(canons, key=lambda c: c["id"]):
        match_data["patterns"].append({
            "id": canon["id"],
            "sig": canon["error"]["signature"],
            "re": canon["error"]["regex"],
            "domain": canon["error"]["domain"],
            "ok": canon["verdict"]["resolvable"],
            "rate": canon["verdict"]["fix_success_rate"],
            "conf": canon["verdict"]["confidence"],
            "de": len(canon["dead_ends"]),
            "wa": len(canon.get("workarounds", [])),
            "url": f"{BASE_URL}/api/v1/{canon['id']}.json",
        })

    api_dir = SITE_DIR / "api" / "v1"
    api_dir.mkdir(parents=True, exist_ok=True)
    # Compact JSON to minimize token usage for AI agents
    (api_dir / "match.json").write_text(
        json.dumps(match_data, separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8",
    )
    print("  Generated: /api/v1/match.json")


def build_ai_config_files() -> None:
    """Copy AI agent config files to site root.

    These files are auto-discovered by AI coding agents:
    CLAUDE.md (Claude Code), .cursorrules (Cursor), .windsurfrules (Windsurf),
    AGENTS.md (OpenAI Codex CLI), .clinerules (Cline).
    """
    config_files = [
        "CLAUDE.md", ".cursorrules", ".windsurfrules",
        "AGENTS.md", ".clinerules",
    ]
    copied = 0
    for fname in config_files:
        src = PROJECT_ROOT / fname
        if src.exists():
            shutil.copy2(src, SITE_DIR / fname)
            copied += 1

    # Copy .well-known files from project root (MCP Registry domain verification, etc.)
    # Merge into existing .well-known/ dir (don't destroy files from build_well_known())
    wellknown_src = PROJECT_ROOT / ".well-known"
    if wellknown_src.is_dir():
        wellknown_dst = SITE_DIR / ".well-known"
        wellknown_dst.mkdir(parents=True, exist_ok=True)
        for src_file in wellknown_src.iterdir():
            if src_file.is_file():
                shutil.copy2(src_file, wellknown_dst / src_file.name)
                copied += 1

    print(f"  Copied {copied} AI config files to site/")


def build_indexnow(canons: list[dict]) -> None:
    """Generate IndexNow key file and URL list for search engine notification."""
    # IndexNow key verification file
    (SITE_DIR / f"{INDEXNOW_KEY}.txt").write_text(
        INDEXNOW_KEY, encoding="utf-8"
    )

    # URL list for IndexNow submission
    urls = [BASE_URL]
    urls.append(f"{BASE_URL}/search/")

    domains_seen = set()
    for canon in canons:
        domain = canon["error"]["domain"]
        if domain not in domains_seen:
            domains_seen.add(domain)
            urls.append(f"{BASE_URL}/{domain}/")

    for canon in sorted(canons, key=lambda c: c["id"]):
        urls.append(canon["url"])

    urls.append(f"{BASE_URL}/api/v1/index.json")
    urls.append(f"{BASE_URL}/llms.txt")

    (SITE_DIR / "indexnow-urls.txt").write_text(
        "\n".join(urls), encoding="utf-8"
    )
    print(f"  Generated: {INDEXNOW_KEY}.txt + indexnow-urls.txt ({len(urls)} URLs)")


def build_feed(canons: list[dict]) -> None:
    """Generate Atom feed (feed.xml) for AI agent subscriptions."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Sort by generation date (newest first), take top 50
    dated = sorted(
        canons,
        key=lambda c: c["metadata"].get("generation_date", "2020-01-01"),
        reverse=True,
    )[:50]

    ns = "http://www.w3.org/2005/Atom"
    feed = Element("feed", xmlns=ns)
    SubElement(feed, "title").text = (
        "deadends.dev — New Error Patterns"
    )
    SubElement(feed, "subtitle").text = (
        "Structured failure knowledge for AI coding agents"
    )
    link_self = SubElement(feed, "link")
    link_self.set("href", f"{BASE_URL}/feed.xml")
    link_self.set("rel", "self")
    link_self.set("type", "application/atom+xml")
    link_alt = SubElement(feed, "link")
    link_alt.set("href", BASE_URL)
    link_alt.set("rel", "alternate")
    SubElement(feed, "id").text = f"{BASE_URL}/"
    SubElement(feed, "updated").text = now
    author = SubElement(feed, "author")
    SubElement(author, "name").text = "deadends.dev"

    for canon in dated:
        entry = SubElement(feed, "entry")
        cid = canon["id"]
        sig = canon["error"]["signature"]
        domain = canon["error"]["domain"]
        rate = int(canon["verdict"]["fix_success_rate"] * 100)
        resolvable = canon["verdict"]["resolvable"]
        de_count = len(canon["dead_ends"])
        wa_count = len(canon.get("workarounds", []))
        gen_date = canon["metadata"].get(
            "generation_date", "2026-01-01"
        )

        SubElement(entry, "title").text = f"[{domain}] {sig}"
        elink = SubElement(entry, "link")
        elink.set("href", f"{BASE_URL}/{cid}")
        elink.set("rel", "alternate")
        SubElement(entry, "id").text = f"{BASE_URL}/{cid}"
        SubElement(entry, "updated").text = f"{gen_date}T00:00:00Z"

        summary_text = (
            f"Resolvable: {resolvable} | "
            f"Fix rate: {rate}% | "
            f"Dead ends: {de_count} | "
            f"Workarounds: {wa_count}\n\n"
            f"{canon['verdict']['summary']}\n\n"
            f"JSON API: {BASE_URL}/api/v1/{cid}.json"
        )
        content = SubElement(entry, "content")
        content.set("type", "text")
        content.text = summary_text

        cat = SubElement(entry, "category")
        cat.set("term", domain)

    xml_bytes = tostring(feed, encoding="unicode", xml_declaration=False)
    xml_out = '<?xml version="1.0" encoding="utf-8"?>\n' + xml_bytes

    (SITE_DIR / "feed.xml").write_text(xml_out, encoding="utf-8")
    print(f"  Generated: feed.xml ({len(dated)} entries)")


def main():
    print("Building deadends.dev static site...\n")

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
    jinja_env.globals["base_path"] = BASE_PATH
    jinja_env.globals["base_url"] = BASE_URL
    jinja_env.filters["display_name"] = domain_display_name
    def _json_escape(s: str) -> Markup:
        """JSON-safe string for use inside JSON-LD <script> blocks.
        Returns Markup to bypass Jinja2 autoescape (the value is already
        properly escaped by json.dumps). Also escapes </ to prevent XSS."""
        escaped = json.dumps(s)[1:-1]  # strip outer quotes
        escaped = escaped.replace("</", r"<\/")  # prevent </script> breakout
        return Markup(escaped)

    jinja_env.filters["json_escape"] = _json_escape

    # Build pages
    print("Generating error pages...")
    build_error_pages(canons, jinja_env)
    print()

    print("Generating domain pages...")
    build_domain_pages(canons, jinja_env)
    print()

    print("Generating error summary pages...")
    summary_urls = build_error_summary_pages(canons, jinja_env)
    print()

    print("Generating search page...")
    build_search_page(canons, jinja_env)
    print()

    print("Generating index page...")
    build_index_page(canons, jinja_env)
    print()

    print("Generating sitemap.xml...")
    build_sitemap(canons, summary_urls)
    print()

    print("Generating robots.txt...")
    build_robots_txt()
    print()

    print("Generating 404.html...")
    build_404_page()
    print()

    print("Generating CNAME...")
    build_cname()
    print()

    print("Generating llms.txt + llms-full.txt...")
    build_llms_txt(canons)
    print()

    print("Generating API index...")
    build_api_index(canons)
    print()

    print("Generating OpenAPI spec...")
    build_openapi_spec(canons)
    print()

    print("Generating .well-known/ai-plugin.json...")
    build_well_known(canons)
    print()

    print("Generating match.json (lightweight AI matching)...")
    build_match_json(canons)
    print()

    print("Generating version.json...")
    build_version_json(canons)
    print()

    print("Generating stats.json...")
    build_stats_json(canons)
    print()

    print("Generating errors.ndjson (streaming)...")
    build_ndjson(canons)
    print()

    print("Generating Atom feed...")
    build_feed(canons)
    print()

    print("Generating IndexNow support...")
    build_indexnow(canons)
    print()

    print("Generating shared stylesheet...")
    build_stylesheet()
    print()

    print("Generating OG image for social sharing...")
    build_og_image()
    print()

    print("Generating favicon...")
    build_favicon()
    print()

    print("Copying AI agent config files...")
    build_ai_config_files()
    print()

    print(f"Build complete! {len(canons)} error pages generated in site/")


if __name__ == "__main__":
    main()
