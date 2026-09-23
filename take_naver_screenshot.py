import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.goto("https://finance.naver.com/sise/sise_market_sum.naver")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="C:/Users/User/.gemini/antigravity/brain/15b083a3-5bd8-4da9-bc44-163bca90bdb5/naver_finance.png")
        await browser.close()
        print("Saved screenshot of naver finance!")

asyncio.run(run())

