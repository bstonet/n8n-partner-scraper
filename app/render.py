from __future__ import annotations
import asyncio
from typing import List
from playwright.async_api import async_playwright

async def _auto_scroll(page, max_steps: int = 20, pause_ms: int = 300) -> None:
    last_height = 0
    for _ in range(max_steps):
        height = await page.evaluate("() => document.body.scrollHeight")
        if height == last_height:
            break
        last_height = height
        await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(pause_ms)

async def render_html(url: str, wait_ms: int = 1500) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await _auto_scroll(page)
        if wait_ms: await page.wait_for_timeout(wait_ms)
        html = await page.content()
        await browser.close()
        return html

async def render_collect_hrefs(url: str, wait_ms: int = 1500) -> List[str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await _auto_scroll(page)
        if wait_ms: await page.wait_for_timeout(wait_ms)
        hrefs = await page.evaluate(
            "Array.from(document.querySelectorAll('a[href]')).map(a => a.href)"
        )
        await browser.close()
        return hrefs

def render_html_sync(url: str, wait_ms: int = 1500) -> str:
    return asyncio.run(render_html(url, wait_ms))

def render_collect_hrefs_sync(url: str, wait_ms: int = 1500):
    return asyncio.run(render_collect_hrefs(url, wait_ms))
