import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import tldextract

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MotivoScraper/1.0; +https://getmotivo.ai)"
}

SOCIAL_DOMAINS = {
    "linkedin.com", "facebook.com", "twitter.com", "x.com", "instagram.com",
    "youtube.com", "github.com", "medium.com"
}


def normalize_domain(href: str) -> str | None:
    """Convert hrefs to clean domains."""
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


def scrape_directory_page(url: str) -> list[str]:
    """Extract partner domains from a single n8n Experts page."""
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    found = set()
    for a in soup.select("a[href]"):
        domain = normalize_domain(a.get("href", ""))
        if domain:
            found.add(domain)
    return sorted(found)


def scrape_directory(urls: list[str]) -> list[str]:
    """Scrape multiple pages (if pagination exists)."""
    all_domains = set()
    for u in urls:
        try:
            print(f"Scraping {u}...")
            all_domains.update(scrape_directory_page(u))
            time.sleep(1.0)
        except Exception as e:
            print(f"Error scraping {u}: {e}")
    return sorted(all_domains)
