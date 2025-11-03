from typing import List, Tuple, Dict
import re
import requests
from bs4 import BeautifulSoup

from .scrape_directory import HEADERS
from .score import score_signals


def _session_with_retries() -> requests.Session:
    s = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=3)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


def fetch(url: str, session: requests.Session) -> str:
    r = session.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    text = r.text
    if len(text) > 500_000:
        text = text[:500_000]
    return text


def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _candidate_paths() -> List[List[str]]:
    return [
        ["/"],
        ["/about"],
        ["/services", "/solutions"],
        ["/case-studies", "/customers", "/clients"],
        ["/industries", "/verticals"],
        ["/security", "/compliance"],
    ]


def scrape_partner(domain: str, limit_pages: int = 6) -> Dict:
    session = _session_with_retries()
    sources: List[str] = []
    text_blobs: List[str] = []

    for group in _candidate_paths():
        if len(sources) >= limit_pages:
            break
        for p in group:
            if len(sources) >= limit_pages:
                break
            url = f"https://{domain}{p}"
            try:
                html = fetch(url, session)
                txt = extract_visible_text(html)
            except Exception:
                continue
            if not txt:
                continue
            text_blobs.append(txt[:800])
            sources.append(url)

    combined = "\n\n".join(text_blobs)
    score = score_signals(combined)

    return {
        "domain": domain,
        "pages_scanned": len(sources),
        "tier": score["tier"],
        "score_total": score["total"],
        "score_components": score["components"],
        "sources": sources,
    }


