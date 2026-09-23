import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        print("Navigating to http://127.0.0.1:8008/ ...")
        await page.goto("http://127.0.0.1:8008/")
        
        await page.wait_for_timeout(2000)
        
        print("Searching for 035420 (NAVER)...")
        await page.fill("#search-symbol", "035420")
        await page.click("button:has-text('검색')")
        
        await page.wait_for_timeout(2000)
        
        print("Taking screenshot...")
        await page.screenshot(path="C:/Users/User/.gemini/antigravity/brain/15b083a3-5bd8-4da9-bc44-163bca90bdb5/naver_proof.png")
        await browser.close()
        print("Screenshot saved to naver_proof.png!")

asyncio.run(run())
