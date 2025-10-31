import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import tldextract

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MotivoScraper/1.0; +https://getmotivo.ai)"
}

SOCIAL_DOMAINS = {
    "linkedin.com","facebook.com","twitter.com","x.com","instagram.com",
    "youtube.com","github.com","medium.com"
}

def _normalize_domain(href: str) -> str | None:
    """Normalize links to a clean domain name."""
    if not href or href.startswith(("mailto:", "tel:")):
        return None
    parsed = urlparse(href if "://" in href else f"http://{href}")
    host = parsed.netloc or parsed.path
    if not host:
        return None
    host = host.split(":")[0].lower()
    ext = tldextract.extract(host)
    if not ext.domain or not ext.suffix:
        return None
    domain = f"{ext.domain}.{ext.suffix}"
    if domain in SOCIAL_DOMAINS or domain.endswith("n8n.io"):
        return None
    return domain

def extract_domains_from_html(html: str) -> list[str]:
    """Pull all external domains from provided HTML."""
    soup = BeautifulSoup(html, "html.parser")
    found = set()
    for a in soup.select("a[href]"):
        dom = _normalize_domain(a.get("href", ""))
        if dom:
            found.add(dom)
    return sorted(found)

def fetch_html(url: str) -> str:
    """Fetch HTML via standard HTTP request."""
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text

def scrape_directory(urls: list[str], use_js: bool = False, renderer=None, wait_ms: int = 1500) -> list[str]:
    """Scrape one or multiple pages; supports JS rendering if use_js=True."""
    all_domains = set()
    for u in urls:
        try:
            html = renderer(u, wait_ms) if use_js and renderer else fetch_html(u)
            all_domains.update(extract_domains_from_html(html))
            time.sleep(1.0)
        except Exception as e:
            print(f"Error scraping {u}: {e}")
            continue
    return sorted(all_domains)
