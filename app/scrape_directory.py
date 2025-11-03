import time
from typing import Iterable, List, Optional, Tuple
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import tldextract
from collections import Counter

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MotivoScraper/1.0; +https://getmotivo.ai)"}

BLOCKLIST = {
    "experts.n8n.io","n8n.io","n8n.cloud","vercel.app","cloudflare.com","gstatic.com",
    "x.com","twitter.com","linkedin.com","facebook.com","instagram.com","youtube.com",
    "tiktok.com","reddit.com","discord.com","discord.gg","github.com","gitlab.com",
    "posthog.com","google-analytics.com","analytics.google.com","doubleclick.net",
    "cookie-script.com","hotjar.com","clarity.ms","safety.google","googletagmanager.com",
    "intercom.com","crisp.chat","freshdesk.com","zendesk.com",
    "paddle.com","stripe.com","lu.ma","cal.com","calendly.com",
    "medium.com","wordpress.org","ghost.org","substack.com","read.cv",
    "adobe.com","amazon.com","aws.amazon.com","microsoft.com","azure.com",
    "google.com","webflow.com","shopify.com","typeform.com","airtable.com",
    "notion.so","notion.site","slack.com","zapier.com","make.com","workato.com",
    "segment.com","hubspot.com","salesforce.com",
    "flickr.com","dropbox.com","drive.google.com","box.com"
}

def _host(url_or_host: str) -> Optional[str]:
    if not url_or_host or url_or_host.startswith(("mailto:", "tel:")):
        return None
    parsed = urlparse(url_or_host if "://" in url_or_host else f"http://{url_or_host}")
    host = (parsed.netloc or parsed.path).split(":")[0].lower().strip(".")
    return host or None

def _norm_to_domain(url_or_host: str) -> Optional[str]:
    h = _host(url_or_host)
    if not h: return None
    ext = tldextract.extract(h)
    if not ext.domain or not ext.suffix: return None
    domain = f"{ext.domain}.{ext.suffix}"
    if domain in BLOCKLIST: return None
    return domain

def _from_hrefs(hrefs: Iterable[str], directory_host: str) -> Tuple[List[str], List[str]]:
    raw_hosts = []
    found = set()
    for href in hrefs:
        h = _host(href)
        if not h: continue
        raw_hosts.append(h)
        if h == directory_host:  # internal links to experts portal
            continue
        d = _norm_to_domain(href)
        if d:
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
    all_domains = set()
    raw_hosts_all: List[str] = []
    mode = "html"

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
                # HTML fallback (rare for this page)
                domains, raw_hosts = _from_hrefs(
                    [a.get("href","") for a in BeautifulSoup(html, "html.parser").select("a[href]")],
                    directory_host
                )
                mode = "html"

            raw_hosts_all.extend(raw_hosts)
            all_domains.update(domains)
            time.sleep(0.4)
        except Exception as e:
            print(f"[scrape_directory] Error on {u}: {e}")
            continue

    top_hosts = [f"{h}:{c}" for h, c in Counter(raw_hosts_all).most_common(12)]
    return sorted(all_domains), mode, top_hosts
