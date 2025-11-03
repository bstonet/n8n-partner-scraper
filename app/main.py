from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from .scrape_directory import scrape_directory
from .render import render_html_sync, render_collect_hrefs_sync

app = FastAPI(title="n8n Partner Scraper")

class ScrapeRequest(BaseModel):
    url: Optional[str] = None
    urls: Optional[List[str]] = None
    use_js: bool = False
    wait_ms: int = 2000

@app.get("/")
def index():
    return {"status": "ok", "endpoints": ["/healthz", "/scrape-directory", "/docs"]}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/scrape-directory")
def scrape_directory_endpoint(payload: ScrapeRequest):
    urls: List[str] = []
    if payload.urls: urls.extend(payload.urls)
    if payload.url: urls.append(payload.url)
    if not urls:
        return {"count": 0, "domains": [], "note": "Provide 'url' or 'urls'."}

    domains, mode, top_hosts = scrape_directory(
        urls=urls,
        use_js=payload.use_js,
        renderer=render_html_sync if payload.use_js else None,
        renderer_hrefs=render_collect_hrefs_sync if payload.use_js else None,
        wait_ms=payload.wait_ms,
    )
    return {
        "count": len(domains),
        "mode": mode,
        "top_raw_hosts": top_hosts,
        "domains": domains
    }
