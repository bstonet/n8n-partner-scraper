# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="n8n Partner Scraper")  # <- must be named `app`

class ScrapeRequest(BaseModel):
    url: str

class PartnerRequest(BaseModel):
    domain: str

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/scrape-directory")
def scrape_directory(payload: ScrapeRequest):
    return {"message": f"Pretending to scrape directory at {payload.url}"}

@app.post("/scrape-partner")
def scrape_partner(payload: PartnerRequest):
    return {
        "domain": payload.domain,
        "tier": "SMB",
        "score_total": 42,
        "notes": "Placeholder response"
    }
