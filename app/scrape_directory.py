import time
from typing import Iterable, List, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import tldextract

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MotivoScraper/1.0; +https://getmotivo.ai)"}

BLOCKLIST = {
    # self & clouds
    "n8n.io","n8n.cloud","vercel.app","cloudflare.com","gstatic.com",
    # social / community
    "x.com","twitter.com","linkedin.com","facebook.com","instagram.com",
    "youtube.com","tiktok.com","reddit.com","discord.com","discord.gg",
    # analytics / tracking / cdn
    "posthog.com","google-analytics.com","analytics.google.com","doubleclick.net",
    "cookie-script.com","hotjar.com","clarity.ms","safety.google",
    # comms / support / chat
    "intercom.com","crisp.chat","freshdesk.com","zendesk.com",
    # payments / billing
    "paddle.com","stripe.com",
    # event / calendaring
    "lu.ma","cal.com","calendly.com",
    # docs / publishing
    "medium.com","wordpress.org","ghost.org","substack.com",
    # platforms / obvious non-agencies
    "adobe.com","amazon.com","aws.amazon.com","microsoft.com","azure.com",
    "google.com","webflow.com","shopify.com","typeform.com",
    "airtable.com","notion.so","notion.site","slack.com",
    "zapier.com","make.com","workato.com","segment.com","hubspot.com","salesforce.com",
    # media/storage
    "flickr.com","dropbox.com","drive.google.com","box.com"
}

def _norm(url_or_host: str) -> Optional[str]:
    if not url_or_host or url_or_host.startswith(("mailto:","tel:")):
        return None
    parsed = urlparse(url_or_host if "://" in url_or_host else f"http://{url_or_host}")
    host = (parsed.netloc or parsed.path).split(":")[0].lower().strip(".")
    if not host:
        return None
    ext = tldextract.extract(host)
    if not ext.domain or not ext.suffix:
        return None
    domain = f"{ext.domain}.{ext.suffix}"
    if domain in BLOCKLIST:
        return None
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

def scrape_directory(urls: List[str], use_js: bool = False, renderer=None, renderer_hrefs=None, wait_ms: int = 1500):
    """
    Returns (domains, mode, raw_len) where:
      - domains: filtered, unique partner domains
      - mode: 'js-hrefs' or 'html'
      - raw_len: number of hrefs/anchors considered before normalization/filter
    """
    mode = "html"
    all_domains = set()
    raw_len = 0

    for u in urls:
        try:
            if use_js and renderer_hrefs:
                hrefs = renderer_hrefs(u, wait_ms)
                raw_len += len(hrefs)
                domains = _from_hrefs(hrefs)
                mode = "js-hrefs"
            else:
                html = fetch_html(u)
                # approximate raw anchors for debug
                raw_len += html.count("<a ")
                domains = _from_html(html)

            for d in domains:
                if d not in BLOCKLIST:
                    all_domains.add(d)

            time.sleep(0.6)
        except Exception as e:
            print(f"[scrape_directory] Error on {u}: {e}")
            continue

    return sorted(all_domains), mode, raw_len
