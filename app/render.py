from __future__ import annotations
import asyncio
from typing import List
from playwright.async_api import async_playwright, Page, Frame

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

async def _auto_scroll(page: Page, max_steps: int = 25, pause_ms: int = 250) -> None:
    last = 0
    for _ in range(max_steps):
        h = await page.evaluate("() => document.body.scrollHeight")
        if h == last: break
        last = h
        await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(pause_ms)

async def _frame_hrefs(frame: Frame) -> List[str]:
    try:
        return await frame.evaluate("Array.from(document.querySelectorAll('a[href]')).map(a => a.href)") or []
    except Exception:
        return []

async def render_collect_hrefs_allframes(url: str, wait_ms: int = 1800) -> List[str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        context = await browser.new_context(user_agent=UA, locale="en-US")
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await _auto_scroll(page)
        if wait_ms: await page.wait_for_timeout(wait_ms)

        hrefs = await _frame_hrefs(page.main_frame)
        for fr in page.frames:
            if fr is page.main_frame: continue
            try:
                try:
                    await fr.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(200)
                except Exception:
                    pass
                hrefs.extend(await _frame_hrefs(fr))
            except Exception:
                continue

        await browser.close()
        return hrefs

async def render_html(url: str, wait_ms: int = 1500) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        context = await browser.new_context(user_agent=UA, locale="en-US")
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await _auto_scroll(page)
        if wait_ms: await page.wait_for_timeout(wait_ms)
        html = await page.content()
        await browser.close()
        return html

def render_collect_hrefs_sync(url: str, wait_ms: int = 1800):
    return asyncio.run(render_collect_hrefs_allframes(url, wait_ms))

def render_html_sync(url: str, wait_ms: int = 1500) -> str:
    return asyncio.run(render_html(url, wait_ms))
