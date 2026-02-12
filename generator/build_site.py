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
# Base path for subpath hosting (e.g., "/deadends.dev" for github.io/deadends.dev/)
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
    content = f"""# deadends.dev - Structured failure knowledge for AI agents
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
"""
    (SITE_DIR / "robots.txt").write_text(content, encoding="utf-8")
    print("  Generated: robots.txt")


def build_404_page() -> None:
    """Generate a custom 404 page."""
    html = (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head>\n'
        '<meta charset="utf-8"><title>404 | deadends.dev</title>\n'
        "<style>\n"
        "body{font-family:system-ui;max-width:800px;margin:2rem auto;\n"
        "padding:0 1rem;color:#e0e0e0;background:#0d1117;}\n"
        "a{color:#58a6ff;}\n"
        "</style>\n"
        "</head><body>\n"
        "<h1>404 — Error Not Found (Ironic, isn't it?)</h1>\n"
        '<p>This error page doesn\'t exist yet.'
        f' <a href="{BASE_PATH}/">Browse existing errors</a> or\n'
        '<a href="https://github.com/dbwls99706/deadends.dev/issues/new">'
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
        "# deadends.dev",
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
                            "content": {"application/json": {}},
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
                                "confidence": {"type": "string"},
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

    # security.txt (RFC 9116)
    security_txt = (
        "Contact: https://github.com/dbwls99706/deadends.dev/issues\n"
        "Expires: 2027-01-01T00:00:00Z\n"
        "Preferred-Languages: en, ko\n"
        f"Canonical: {BASE_URL}/.well-known/security.txt\n"
    )
    (well_known_dir / "security.txt").write_text(security_txt, encoding="utf-8")
    print("  Generated: .well-known/security.txt")


def build_stats_json(canons: list[dict]) -> None:
    """Generate /api/v1/stats.json — detailed dataset statistics for AI agents."""
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
            conf[c["verdict"]["confidence"]] = conf.get(c["verdict"]["confidence"], 0) + 1
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
    """Generate /api/v1/version.json — service metadata for AI agents."""
    domains = sorted({c["error"]["domain"] for c in canons})
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    version_data = {
        "service": "deadends.dev",
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

    # Copy .well-known directory (MCP Registry domain verification, etc.)
    wellknown_src = PROJECT_ROOT / ".well-known"
    if wellknown_src.is_dir():
        wellknown_dst = SITE_DIR / ".well-known"
        if wellknown_dst.exists():
            shutil.rmtree(wellknown_dst)
        shutil.copytree(wellknown_src, wellknown_dst)
        copied += len(list(wellknown_src.iterdir()))

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

    print("Generating IndexNow support...")
    build_indexnow(canons)
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
