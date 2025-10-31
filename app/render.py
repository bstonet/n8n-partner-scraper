from __future__ import annotations
import asyncio
from playwright.async_api import async_playwright

async def render_html(url: str, wait_ms: int = 1500) -> str:
    """Return fully-rendered HTML using headless Chromium."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)
        if wait_ms:
            await page.wait_for_timeout(wait_ms)
        html = await page.content()
        await browser.close()
        return html

def render_html_sync(url: str, wait_ms: int = 1500) -> str:
    """Synchronous wrapper for render_html (safe for FastAPI endpoints)."""
    return asyncio.run(render_html(url, wait_ms))
