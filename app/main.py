from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from collections import Counter

from .scrape_directory import scrape_directory
import os
from fastapi import Depends, Header, HTTPException
from .scrape_directory_json import fetch_experts_json, extract_domains, scrape_directory_json
from .scrape_directory_crawl import crawl_directory
from .scrape_partner import scrape_partner as _scrape_partner
from .process import process_all
from .render import render_html_sync, render_collect_hrefs_sync

app = FastAPI(title="n8n Partner Scraper")

class ScrapeRequest(BaseModel):
    url: Optional[str] = None
    urls: Optional[List[str]] = None
    use_js: bool = True          # default ON for this portal
    wait_ms: int = 2500

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/")
def index():
    return {"status": "ok", "endpoints": [
        "/healthz",
        "/scrape-directory",
        "/scrape-directory/json",
        "/scrape-directory/crawl",
        "/debug-render",
        "/docs",
    ]}

@app.get("/debug-render")
def debug_render(url: str, wait_ms: int = 2500):
    # Call Playwright directly and show what it sees
    hrefs = render_collect_hrefs_sync(url, wait_ms)
    hosts = [h.split("//",1)[-1].split("/",1)[0].split(":")[0].lower().strip(".") for h in hrefs]
    top_hosts = [f"{h}:{c}" for h,c in Counter(hosts).most_common(12)]
    return {"href_count": len(hrefs), "top_hosts": top_hosts, "sample": hrefs[:10]}

@app.post("/scrape-directory")
def scrape_directory_endpoint(payload: ScrapeRequest):
    urls: List[str] = []
    if payload.urls: urls.extend(payload.urls)
    if payload.url: urls.append(payload.url)
    if not urls:
        return {"count": 0, "domains": [], "note": "Provide 'url' or 'urls'."}

    domains, mode, top_hosts = scrape_directory(
        urls=urls,
        use_js=True,  # force JS for reliability
        renderer=render_html_sync,
        renderer_hrefs=render_collect_hrefs_sync,
        wait_ms=payload.wait_ms,
    )
    return {"count": len(domains), "mode": mode, "top_raw_hosts": top_hosts, "domains": domains}


class JsonScrapeRequest(BaseModel):
    url: str


@app.post("/scrape-directory/json")
def scrape_directory_json_endpoint(payload: Optional[dict] = None):
    # New contract: optional body { feed_urls?: list[str] }, otherwise default feeds
    feed_urls = None
    if payload and isinstance(payload, dict):
        feed_urls = payload.get("feed_urls")
    try:
        return scrape_directory_json(feed_urls)
    except Exception as e:
        return {"count": 0, "domains": [], "error": str(e)}


class CrawlRequest(BaseModel):
    url: str
    limit_profiles: int = 100


@app.post("/scrape-directory/crawl")
def scrape_directory_crawl_endpoint(payload: CrawlRequest):
    try:
        domains = crawl_directory(payload.url, limit_profiles=payload.limit_profiles)
        return {"count": len(domains), "domains": domains}
    except Exception as e:
        return {"count": 0, "domains": [], "error": str(e)}


class PartnerReq(BaseModel):
    domain: str
    limit_pages: int = 6


@app.post("/scrape-partner")
def scrape_partner_endpoint(payload: PartnerReq):
    try:
        return _scrape_partner(payload.domain, limit_pages=payload.limit_pages)
    except Exception as e:
        return {"error": str(e)}


def require_bearer(Authorization: Optional[str] = Header(None)):
    token = os.getenv("BEARER_TOKEN")
    if not token:
        return
    if not Authorization or not Authorization.startswith("Bearer ") or Authorization.split(" ", 1)[1] != token:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/process")
def process_endpoint(_=Depends(require_bearer)):
    return process_all()
