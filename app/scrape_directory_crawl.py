from typing import List, Optional, Set, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .scrape_directory import HEADERS, _norm_to_domain


def _discover_profile_slugs(directory_url: str, max_pages: int = 3) -> List[str]:
    slugs: Set[str] = set()
    base = directory_url.rstrip("/")
    pages = [base]
    # The experts directory paginates with ?page=2, ?page=3...
    for p in range(2, max_pages + 1):
        pages.append(f"{base}?page={p}")

    for page_url in pages:
        try:
            r = requests.get(page_url, headers=HEADERS, timeout=30)
            r.raise_for_status()
        except Exception:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a[href]"):
            href = a.get("href") or ""
            if not href or href.startswith("http"):
                continue
            if href.count("/") == 1 and href.startswith("/"):
                # Looks like /<slug>
                slug = href.strip("/")
                if slug and slug not in ("contact", "review"):
                    slugs.add(slug)
    return sorted(slugs)


def _extract_domain_from_profile(profile_url: str) -> Optional[str]:
    r = requests.get(profile_url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Prefer explicit "View website" anchor
    for a in soup.select("a[href]"):
        txt = (a.get_text() or "").strip().lower()
        if "view website" in txt:
            d = _norm_to_domain(a.get("href") or "")
            if d:
                return d

    # Fallback: any external http link not on experts.n8n.io
    for a in soup.select("a[href^='http']"):
        href = a.get("href") or ""
        if "experts.n8n.io" in href:
            continue
        d = _norm_to_domain(href)
        if d:
            return d
    return None


def crawl_directory(directory_url: str, limit_profiles: int = 100) -> List[str]:
    slugs = _discover_profile_slugs(directory_url, max_pages=5)
    if not slugs:
        return []
    base = directory_url.rstrip("/")
    found: List[str] = []
    seen: Set[str] = set()
    for slug in slugs[: max(1, limit_profiles)]:
        profile_url = urljoin(base + "/", slug)
        try:
            domain = _extract_domain_from_profile(profile_url)
        except Exception:
            domain = None
        if not domain:
            continue
        if domain in seen:
            continue
        seen.add(domain)
        found.append(domain)
    return sorted(found)


