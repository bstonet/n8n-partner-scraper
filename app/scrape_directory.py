import time
from typing import Iterable, List, Optional, Tuple
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import tldextract

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MotivoScraper/1.0; +https://getmotivo.ai)"}

# Block obvious non-partner/platform/infra/social/etc.
BLOCKLIST = {
    # self / infra
    "experts.n8n.io","n8n.io","n8n.cloud","vercel.app","cloudflare.com","gstatic.com",
    # social / community
    "x.com","twitter.com","linkedin.com","facebook.com","instagram.com","youtube.com",
    "tiktok.com","reddit.com","discord.com","discord.gg","github.com","gitlab.com",
    # analytics / cdn / trackers
    "posthog.com","google-analytics.com","analytics.google.com","doubleclick.net",
    "cookie-script.com","hotjar.com","clarity.ms","safety.google","googletagmanager.com",
    # comms / support
    "intercom.com","crisp.chat","freshdesk.com","zendesk.com",
    # payments / events / calendars
    "paddle.com","stripe.com","lu.ma","cal.com","calendly.com",
    # publishing / generic app platforms
    "medium.com","wordpress.org","ghost.org","substack.com","read.cv",
    "adobe.com","amazon.com","aws.amazon.com","microsoft.com","azure.com",
    "google.com","webflow.com","shopify.com","typeform.com","airtable.com",
    "notion.so","notion.site","slack.com","zapier.com","make.com","workato.com",
    "segment.com","hubspot.com","salesforce.com",
    # storage / file
    "flickr.com","dropbox.com","drive.google.com","box.com"
}

def _host(url_or_host: str) -> Optional[str]:
    if not url_or_host or url_or_host.startswith(("mailto:", "tel:")):
        return None
    parsed = urlparse(url_or_host if "://" in url_or_host else f"http://{url_or_host}")
    host = (parsed.netloc or parsed.path).split(":")[0].lower().strip(".")
    return host or None

def _norm_to_domain(url_or_host: str) -> Optional[str]:
    host = _host(url_or_host)
    if not host: return None
    ext = tldextract.extract(host)
    if not ext.domain or not ext.suffix: return None
    return f"{ext.domain}.{ext.suffix}"

def _from_html(html: str, directory_host: str) -> Tuple[List[str], List[str]]:
    soup = BeautifulSoup(html, "html.parser")
    raw_hosts = []
    found = set()
    for a in soup.select("a[href]"):
        href = a.get("href","")
        h = _host(href)
        if not h: continue
        raw_hosts.append(h)
        # external-only: ignore internal links to the experts portal itself
        if h == directory_host: 
            continue
        d = _norm_to_domain(href)
        if d and d not in BLOCKLIST:
            found.add(d)
    return sorted(found), raw_hosts

def _from_hrefs(hrefs: Iterable[str], directory_host: str) -> Tuple[List[str], List[str]]:
    raw_hosts = []
    found = set()
    for href in hrefs:
        h = _host(href)
        if not h: continue
        raw_hosts.append(h)
        if h == directory_host:
            continue  # skip internal links to experts portal
        d = _norm_to_domain(href)
        if d and d not in BLOCKLIST:
            found.add(d)
    return sorted(found), raw_hosts

def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def scrape_directory(
    urls: List[str],
    use_js: bool = False,
    renderer=None,
    renderer_hrefs=None,
    wait_ms: int = 1500,
    directory_host: Optional[str] = None,
):
    """
    Scrape one or more directory pages.
    - Only returns external partner domains (host != directory_host).
    - Returns (domains, mode, raw_hosts_top) where raw_hosts_top shows the most common raw hosts seen.
    """
    all_domains = set()
    raw_hosts_all: List[str] = []
    mode = "html"

    # If not provided, infer directory_host from first URL
    if not directory_host and urls:
        directory_host = _host(urls[0]) or "experts.n8n.io"

    for u in urls:
        try:
            if use_js and renderer_hrefs:
                hrefs = renderer_hrefs(u, wait_ms)
                domains, raw_hosts = _from_hrefs(hrefs, directory_host)
                mode = "js-hrefs"
            else:
                html = fetch_html(u)
                domains, raw_hosts = _from_html(html, directory_host)
                mode = "html"

            raw_hosts_all.extend(raw_hosts)
            all_domains.update(domains)
            time.sleep(0.5)
        except Exception as e:
            print(f"[scrape_directory] Error on {u}: {e}")
            continue

    # top raw hosts for quick debugging
    from collections import Counter
    top_hosts = [f"{h}:{c}" for h, c in Counter(raw_hosts_all).most_common(12)]

    return sorted(all_domains), mode, top_hosts
