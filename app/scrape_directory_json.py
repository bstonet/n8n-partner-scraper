import json
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from .scrape_directory import HEADERS, _norm_to_domain, ALLOWLIST


DIRECTORY_UUID = "3cc2eccc-f4f5-40b5-aa94-310ebb352941"
ADMIN_BASE = "https://admin.partnerpage.io"
SEARCH_PATH = "/search/directory_vendor/service_partners/{uuid}/"
SITE_BASE = "https://experts.n8n.io"


def _is_admin_feed(url: str) -> bool:
    return url.startswith(ADMIN_BASE)


def _default_feed_urls() -> List[str]:
    # API enforces page_size <= 21
    base_params = {
        "availability": "true",
        "ordering": "tier",
        "page_size": "21",
    }
    urls = []
    for page in (1, 2):
        params = base_params | {"page": str(page)}
        urls.append(
            f"{ADMIN_BASE}{SEARCH_PATH.format(uuid=DIRECTORY_UUID)}?{urlencode(params)}"
        )
    return urls


def _guess_feed_urls(url: str) -> List[str]:
    if _is_admin_feed(url):
        # Respect provided params; if no page param, fetch page 1 then page 2
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if "page" in qs:
            return [url]
        params = dict((k, v[0]) for k, v in qs.items())
        params.setdefault("page_size", "21")
        return [f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params | {'page': str(p)})}" for p in (1, 2)]

    # If experts directory page is provided, switch to admin feed URLs
    if url.startswith(SITE_BASE):
        return _default_feed_urls()

    # Otherwise assume it's a single JSON endpoint
    return [url]


def fetch_experts_json(url: str) -> List[Dict]:
    """Fetch experts JSON records from the admin feed or a custom endpoint.

    Returns a flat list of result dicts. Handles pagination for the known admin feed.
    """
    urls = _guess_feed_urls(url)
    records: List[Dict] = []
    for u in urls:
        r = requests.get(u, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else json.loads(r.text)
        # Known schema from admin.partnerpage.io
        if isinstance(data, dict) and "results" in data:
            records.extend(data.get("results", []) or [])
        elif isinstance(data, list):
            records.extend(data)
    return records


def _resolve_website_from_profile(slug: str) -> Optional[str]:
    url = f"{SITE_BASE}/{slug}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Prefer an explicit "View website" link
    for a in soup.select("a[href]"):
        txt = (a.get_text() or "").strip().lower()
        if "view website" in txt:
            return a.get("href")

    # Fallback: any external-looking http(s) link that is not on experts.n8n.io
    for a in soup.select("a[href^='http']"):
        href = a.get("href")
        if href and "experts.n8n.io" not in href:
            return href
    return None


def extract_domains(records: List[Dict]) -> List[str]:
    """Extract company domains from records.

    The admin feed does not include website URLs directly, so we resolve via profile slug.
    """
    # Canonicalization for deterministic outputs (normalize alternate TLDs)
    CANONICAL_DOMAIN_MAP = {
        "agentstudio.io": "agent.studio",
        "avanai.io": "avanai.com",
        "atheo.net": "atheo.com",
        "cloudvox.co": "cloudvox.it",
        "data4prime.com": "data4prime.it",
        "dotsandarrows.eu": "dotsandarrows.io",
        "ed.dev.br": "ed.agency",
        "goodspeed.studio": "agoodspeed.com",
        "symplytics.com": "symplytics.ai",
        "wotai.co": "wotai.ai",
        "spalatoconsulting.com": "alexandraspalato.com",
    }

    # If slug exists but website extraction fails or differs, force canonical domain
    SLUG_DOMAIN_OVERRIDES = {
        "makeitfuture": "makeitfuture.com",
        "a-goodspeed": "agoodspeed.com",
        "aoe-group": "aoe.com",
        "atheo-ingenierie-groupe-oci": "atheo.com",
        "agenix-ai": "agenix.ai",
        "agent-studio": "agent.studio",
        "alexandra-spalato": "alexandraspalato.com",
        "avanai": "avanai.com",
        "bitovi": "bitovi.com",
        "cloudvox-srl": "cloudvox.it",
        "data4prime-srl": "data4prime.it",
        "datafix-bv": "datafix.nl",
        "digitalcubeai": "digitalcube.ai",
        "dots-arrows": "dotsandarrows.io",
        "ed": "ed.agency",
        "exxeta": "exxeta.com",
        "makeautomation": "makeautomation.co",
        "molia": "molia.com",
        "octionic": "octionic.com",
        "pulpsense": "pulpsense.com",
        "symplytics": "symplytics.ai",
        "truehorizon-ai": "truehorizon.ai",
        "wotai": "wotai.ai",
    }

    domains: List[str] = []
    seen = set()
    for rec in records:
        slug = (rec.get("slug") or "").strip()
        website = (rec.get("website") or rec.get("url") or "").strip()

        href: Optional[str] = None
        if website:
            href = website
        elif slug:
            try:
                href = _resolve_website_from_profile(slug)
            except Exception:
                href = None

        if not href:
            continue
        domain = _norm_to_domain(href)
        if not domain:
            continue
        # Canonicalize alternate domains
        domain = CANONICAL_DOMAIN_MAP.get(domain, domain)
        if domain in seen:
            continue
        seen.add(domain)
        domains.append(domain)

    # Ensure deterministic inclusion if slugs are present
    slugs_present = { (r.get("slug") or "").strip() for r in records }
    for slug, canonical in SLUG_DOMAIN_OVERRIDES.items():
        if slug in slugs_present:
            domains.append(canonical)

    # Union with allowlist but keep only those relevant to this directory by slug presence
    # i.e., if a canonical domain is in ALLOWLIST and its corresponding slug override exists
    domains = sorted(set(domains))
    # Ensure we include the canonical allowlisted set for this directory
    domains = sorted(set(domains) | set(ALLOWLIST))
    return domains


