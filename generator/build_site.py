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
BASE_URL = "https://deadends.dev"
# Base path for subpath hosting (e.g., "/deadend.dev" for github.io/deadend.dev/)
# Empty string when hosted at root domain
BASE_PATH = ""

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

    for canon in canons:
        error_id = canon["id"]
        env_summary = build_env_summary(canon)
        all_sources = collect_sources(canon)

        # Build JSON-LD with Schema.org TechArticle + custom ErrorCanon
        json_ld_data = {
            "@context": [
                "https://schema.org",
                {"deadend": f"{BASE_URL}/schema/v1#"},
            ],
            "@type": "TechArticle",
            "name": canon["error"]["signature"],
            "description": canon["verdict"]["summary"],
            "url": canon["url"],
            "dateModified": canon["verdict"]["last_updated"],
            "publisher": {
                "@type": "Organization",
                "name": "deadend.dev",
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

        html = template.render(
            env_summary=env_summary,
            all_sources=all_sources,
            json_ld=json_ld,
            faq_json_ld=faq_json_ld,
            known_ids=known_ids,
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
        entries = [
            {
                "id": c["id"],
                "signature": c["error"]["signature"],
                "env_summary": build_env_summary(c),
                "resolvable": c["verdict"]["resolvable"],
                "fix_success_rate": c["verdict"]["fix_success_rate"],
            }
            for c in sorted(domain_canons, key=lambda c: c["id"])
        ]

        html = template.render(
            domain=domain,
            entries=entries,
            total=len(entries),
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

    html = template.render(
        total_errors=len(canons),
        domains=domains,
        domain_stats=domain_stats,
        recent_entries=recent_entries,
        google_verification=GOOGLE_VERIFICATION,
        bing_verification=BING_VERIFICATION,
    )

    (SITE_DIR / "index.html").write_text(html, encoding="utf-8")
    print("  Generated: index.html")


def build_sitemap(
    canons: list[dict],
    summary_urls: list[dict] | None = None,
) -> None:
    """Generate sitemap.xml with all page types."""
    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Index page
    url_elem = SubElement(urlset, "url")
    SubElement(url_elem, "loc").text = BASE_URL
    SubElement(url_elem, "lastmod").text = now
    SubElement(url_elem, "changefreq").text = "weekly"
    SubElement(url_elem, "priority").text = "1.0"

    # Search page
    url_elem = SubElement(urlset, "url")
    SubElement(url_elem, "loc").text = f"{BASE_URL}/search/"
    SubElement(url_elem, "lastmod").text = now
    SubElement(url_elem, "changefreq").text = "weekly"
    SubElement(url_elem, "priority").text = "0.9"

    # Domain pages
    domains_seen = set()
    for canon in canons:
        domain = canon["error"]["domain"]
        if domain not in domains_seen:
            domains_seen.add(domain)
            url_elem = SubElement(urlset, "url")
            SubElement(url_elem, "loc").text = f"{BASE_URL}/{domain}/"
            SubElement(url_elem, "lastmod").text = now
            SubElement(url_elem, "changefreq").text = "weekly"
            SubElement(url_elem, "priority").text = "0.9"

    # Error summary pages (environment-agnostic)
    for summary in summary_urls or []:
        url_elem = SubElement(urlset, "url")
        SubElement(url_elem, "loc").text = summary["url"]
        SubElement(url_elem, "lastmod").text = now
        SubElement(url_elem, "changefreq").text = "weekly"
        SubElement(url_elem, "priority").text = "0.85"

    # Error pages (environment-specific)
    for canon in canons:
        url_elem = SubElement(urlset, "url")
        SubElement(url_elem, "loc").text = canon["url"]
        last_updated = canon["verdict"].get("last_updated", now)
        SubElement(url_elem, "lastmod").text = last_updated
        SubElement(url_elem, "changefreq").text = "monthly"
        SubElement(url_elem, "priority").text = "0.8"

    # API endpoints
    url_elem = SubElement(urlset, "url")
    SubElement(url_elem, "loc").text = f"{BASE_URL}/api/v1/index.json"
    SubElement(url_elem, "lastmod").text = now
    SubElement(url_elem, "changefreq").text = "weekly"
    SubElement(url_elem, "priority").text = "0.7"

    # llms.txt
    url_elem = SubElement(urlset, "url")
    SubElement(url_elem, "loc").text = f"{BASE_URL}/llms.txt"
    SubElement(url_elem, "lastmod").text = now
    SubElement(url_elem, "changefreq").text = "weekly"
    SubElement(url_elem, "priority").text = "0.7"

    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_body = tostring(urlset, encoding="unicode")
    (SITE_DIR / "sitemap.xml").write_text(
        xml_declaration + xml_body, encoding="utf-8"
    )
    print("  Generated: sitemap.xml")


def build_robots_txt() -> None:
    """Generate robots.txt with explicit AI crawler allowances."""
    content = f"""# deadend.dev - Structured failure knowledge for AI agents
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

Sitemap: {BASE_URL}/sitemap.xml

# AI agent discovery:
# Match errors:    {BASE_URL}/api/v1/match.json
# Error index:     {BASE_URL}/api/v1/index.json
# OpenAPI spec:    {BASE_URL}/api/v1/openapi.json
# Version info:    {BASE_URL}/api/v1/version.json
# LLM-optimized:   {BASE_URL}/llms.txt
# Full data dump:  {BASE_URL}/llms-full.txt
# Plugin manifest: {BASE_URL}/.well-known/ai-plugin.json
# A2A agent card:  {BASE_URL}/.well-known/agent-card.json
"""
    (SITE_DIR / "robots.txt").write_text(content, encoding="utf-8")
    print("  Generated: robots.txt")


def build_404_page() -> None:
    """Generate a custom 404 page."""
    html = (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head>\n'
        '<meta charset="utf-8"><title>404 | deadend.dev</title>\n'
        "<style>\n"
        "body{font-family:system-ui;max-width:800px;margin:2rem auto;\n"
        "padding:0 1rem;color:#e0e0e0;background:#0d1117;}\n"
        "a{color:#58a6ff;}\n"
        "</style>\n"
        "</head><body>\n"
        "<h1>404 — Error Not Found (Ironic, isn't it?)</h1>\n"
        '<p>This error page doesn\'t exist yet.'
        f' <a href="{BASE_PATH}/">Browse existing errors</a> or\n'
        '<a href="https://github.com/dbwls99706/deadend.dev/issues/new">'
        "request it</a>.</p>\n"
        "</body></html>"
    )
    (SITE_DIR / "404.html").write_text(html, encoding="utf-8")
    print("  Generated: 404.html")



def build_cname() -> None:
    """Generate CNAME file for custom domain."""
    (SITE_DIR / "CNAME").write_text("deadends.dev\n", encoding="utf-8")
    print("  Generated: CNAME")


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

    # Group canons by domain/slug (strip the env part of the id)
    by_slug: dict[str, list[dict]] = {}
    for canon in canons:
        parts = canon["id"].rsplit("/", 1)
        if len(parts) == 2:
            slug_key = parts[0]  # e.g., "python/modulenotfounderror"
        else:
            continue
        by_slug.setdefault(slug_key, []).append(canon)

    summaries = []
    for slug_key, slug_canons in by_slug.items():
        domain, slug = slug_key.split("/", 1)
        first = slug_canons[0]
        signature = first["error"]["signature"]
        regex = first["error"]["regex"]

        environments = []
        all_dead_ends = []
        all_workarounds = []

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

        # Generate common variations from the regex pattern
        common_variations = _generate_variations(signature, regex, domain)

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
        "# deadend.dev",
        "",
        "> Structured failure knowledge for AI coding agents. "
        f"{len(canons)} error entries across {len(by_domain)} domains. "
        "Check dead ends before attempting a fix. "
        "Check workarounds for approaches that actually work.",
        "",
        "## About",
        "",
        f"- [API Index]({BASE_URL}/api/v1/index.json): "
        "All errors with regex patterns and API URLs",
        f"- [Match Endpoint]({BASE_URL}/api/v1/match.json): "
        "Lightweight regex-only matching (fits in context window)",
        f"- [OpenAPI Spec]({BASE_URL}/api/v1/openapi.json): "
        "Full API specification",
        f"- [Complete Database]({BASE_URL}/llms-full.txt): "
        "Full error dump in plaintext",
        f"- [Error Search]({BASE_URL}/search/): "
        "Client-side error matching",
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
        "# deadend.dev — Complete Error Database",
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
            "title": "deadend.dev API",
            "description": (
                "Structured failure knowledge for AI agents. "
                "Query error signatures to find dead ends, workarounds, "
                "and error transition graphs."
            ),
            "version": "1.0.0",
            "contact": {"url": "https://github.com/dbwls99706/deadend.dev"},
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
                                    }
                                }
                            },
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
                        "error": {"type": "object"},
                        "environment": {"type": "object"},
                        "verdict": {"type": "object"},
                        "dead_ends": {"type": "array"},
                        "workarounds": {"type": "array"},
                        "transition_graph": {"type": "object"},
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
        "name_for_human": "deadend.dev",
        "name_for_model": "deadend_error_knowledge",
        "description_for_human": (
            "Structured failure knowledge — check what NOT to try "
            "before debugging an error."
        ),
        "description_for_model": (
            "When you encounter a software error, query this service "
            "to find: (1) dead ends — approaches that are known to fail, "
            "(2) workarounds — approaches that actually work with success "
            "rates, (3) error chains — what error typically comes next. "
            "Fetch /api/v1/index.json for the full error list, then "
            "fetch /api/v1/{id}.json for details. "
            "Match your error message against the regex patterns."
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
        "name": "deadend.dev",
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
            "organization": "deadend.dev",
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
            },
            {
                "id": "get-error-detail",
                "name": "Get Error Details",
                "description": (
                    "Get full structured failure knowledge for a specific "
                    "error by its ID. Returns complete dead ends, workarounds, "
                    "transition graphs, and source evidence."
                ),
                "tags": ["errors", "lookup", "api"],
            },
            {
                "id": "list-domains",
                "name": "List Error Domains",
                "description": (
                    f"List all {len(domains)} error domains with counts."
                ),
                "tags": ["domains", "index"],
            },
        ],
        "auth": {"type": "none"},
    }

    (well_known_dir / "agent-card.json").write_text(
        json.dumps(agent_card, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("  Generated: .well-known/agent-card.json")


def build_version_json(canons: list[dict]) -> None:
    """Generate /api/v1/version.json — service metadata for AI agents."""
    domains = sorted({c["error"]["domain"] for c in canons})
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    version_data = {
        "service": "deadend.dev",
        "version": "1.1.0",
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
        },
        "discovery": {
            "ai_plugin": f"{BASE_URL}/.well-known/ai-plugin.json",
            "agent_card": f"{BASE_URL}/.well-known/agent-card.json",
            "mcp_server": "pip install deadend-dev && python -m mcp.server",
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
    jinja_env.globals["base_path"] = BASE_PATH
    jinja_env.globals["base_url"] = BASE_URL

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

    print("Generating IndexNow support...")
    build_indexnow(canons)
    print()

    print("Generating favicon...")
    build_favicon()
    print()

    print(f"Build complete! {len(canons)} error pages generated in site/")


if __name__ == "__main__":
    main()
