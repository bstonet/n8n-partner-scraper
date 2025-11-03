import time
from typing import Iterable, List, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import tldextract

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MotivoScraper/1.0; +https://getmotivo.ai)"}

# Drop obvious platforms/social/self
BLOCKLIST = {
    "n8n.io","x.com","twitter.com","linkedin.com","facebook.com","instagram.com",
    "youtube.com","github.com","medium.com","discord.com","google.com","goo.gl",
    "shopify.com","typeform.com","airtable.com","notion.so","slack.com",
    "webflow.com","zapier.com","make.com","hubspot.com","salesforce.com"
}

def _norm(url_or_host: str) -> Optional[str]:
    if not url_or_host or url_or_host.startswith(("mailto:","tel:")): return None
    parsed = urlparse(url_or_host if "://" in url_or_host else f"http://{url_or_host}")
    host = (parsed.netloc or parsed.path).split(":")[0].lower()
    if not host: return None
    ext = tldextract.extract(host)
    if not ext.domain or not ext.suffix: return None
    domain = f"{ext.domain}.{ext.suffix}"
    if domain in BLOCKLIST: return None
    return domain

def _from_html(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    found = {d for a in soup.select("a[href]") if (d := _norm(a.get("href","")))}
    return sorted(found)

def _from_hrefs(hrefs: Iterable[str]) -> List[str]:
    found = {d for h in hrefs if (d := _norm(h))}
    return sorted(found)

def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def scrape_directory(urls: List[str], use_js: bool = False, renderer=None, renderer_hrefs=None, wait_ms: int = 1500) -> List[str]:
    all_domains = set()
    for u in urls:
        try:
            if use_js and renderer_hrefs:
                hrefs = renderer_hrefs(u, wait_ms)
                domains = _from_hrefs(hrefs)
            else:
                html = fetch_html(u)
                domains = _from_html(html)
            for d in domains:
                if d not in BLOCKLIST:
                    all_domains.add(d)
            time.sleep(0.8)
        except Exception as e:
            print(f"[scrape_directory] Error on {u}: {e}")
            continue
    return sorted(all_domains)
