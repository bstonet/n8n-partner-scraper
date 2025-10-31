# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from .scrape_directory import scrape_directory  # make sure this exists

app = FastAPI(title="n8n Partner Scraper")

class ScrapeRequest(BaseModel):
    # accept either a single URL or a list of URLs
    url: Optional[str] = None
    urls: Optional[List[str]] = None

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/scrape-directory")
def scrape_directory_endpoint(payload: ScrapeRequest):
    # normalize to a list
    urls: List[str] = []
    if payload.urls:
        urls.extend(payload.urls)
    if payload.url:
        urls.append(payload.url)

    if not urls:
        return {"count": 0, "domains": [], "note": "Provide url or urls"}

    domains = scrape_directory(urls)
    return {"count": len(domains), "domains": domains}
