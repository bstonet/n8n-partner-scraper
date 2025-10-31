from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from .scrape_directory import scrape_directory
from .render import render_html_sync   # Playwright renderer (sync wrapper)

app = FastAPI(title="n8n Partner Scraper")

class ScrapeRequest(BaseModel):
    # Accept either a single URL or a list of URLs
    url: Optional[str] = None
    urls: Optional[List[str]] = None
    # JS-rendering controls
    use_js: bool = False
    wait_ms: int = 1500

@app.get("/")
def index():
    return {
        "service": "n8n-partner-scraper",
        "status": "ok",
        "endpoints": ["/healthz", "/scrape-directory", "/docs"]
    }

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/scrape-directory")
def scrape_directory_endpoint(payload: ScrapeRequest):
    # Normalize to a list of URLs
    urls: List[str] = []
    if payload.urls:
        urls.extend(payload.urls)
    if payload.url:
        urls.append(payload.url)

    if not urls:
        return {"count": 0, "domains": [], "note": "Provide 'url' or 'urls'."}

    # Switch renderer on when use_js=True
    renderer = render_html_sync if payload.use_js else None

    domains = scrape_directory(
        urls=urls,
        use_js=payload.use_js,
        renderer=renderer,
        wait_ms=payload.wait_ms,
    )
    return {"count": len(domains), "domains": domains}
