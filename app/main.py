from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from collections import Counter

from .scrape_directory import scrape_directory
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
    return {"status": "ok", "endpoints": ["/healthz", "/scrape-directory", "/debug-render", "/docs"]}

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
