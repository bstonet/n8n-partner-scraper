import json
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from .scrape_directory import HEADERS, _norm_to_domain


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
        if domain in seen:
            continue
        seen.add(domain)
        domains.append(domain)

    return sorted(domains)


