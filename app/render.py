from __future__ import annotations
import asyncio
from typing import List
from playwright.async_api import async_playwright, Page, Frame

async def _auto_scroll(page: Page, max_steps: int = 25, pause_ms: int = 250) -> None:
    last_height = 0
    for _ in range(max_steps):
        height = await page.evaluate("() => document.body.scrollHeight")
        if height == last_height:
            break
        last_height = height
        await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(pause_ms)

async def _collect_hrefs_from_frame(frame: Frame) -> List[str]:
    # Collect all anchor hrefs present in this frame
    try:
        hrefs = await frame.evaluate("Array.from(document.querySelectorAll('a[href]')).map(a => a.href)")
        return hrefs or []
    except Exception:
        return []

async def render_collect_hrefs_allframes(url: str, wait_ms: int = 1800) -> List[str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await _auto_scroll(page)
        if wait_ms:
            await page.wait_for_timeout(wait_ms)

        # Collect from top page
        all_hrefs: List[str] = []
        top = await page.evaluate("Array.from(document.querySelectorAll('a[href]')).map(a => a.href)")
        if top:
            all_hrefs.extend(top)

        # Collect from every frame (including cross-origin if accessible)
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            try:
                # try to scroll inside the frame to trigger lazy content
                try:
                    await frame.evaluate("() => { window.scrollTo(0, document.body.scrollHeight) }")
                    await page.wait_for_timeout(200)
                except Exception:
                    pass
                links = await _collect_hrefs_from_frame(frame)
                if links:
                    all_hrefs.extend(links)
            except Exception:
                continue

        await browser.close()
        return all_hrefs

async def render_html(url: str, wait_ms: int = 1500) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await _auto_scroll(page)
        if wait_ms:
            await page.wait_for_timeout(wait_ms)
        html = await page.content()
        await browser.close()
        return html

def render_collect_hrefs_sync(url: str, wait_ms: int = 1800):
    return asyncio.run(render_collect_hrefs_allframes(url, wait_ms))

def render_html_sync(url: str, wait_ms: int = 1500) -> str:
    return asyncio.run(render_html(url, wait_ms))
