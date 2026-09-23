import asyncio
from playwright.async_api import async_playwright

async def verify_rollback():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        await page.set_viewport_size({"width": 1600, "height": 1000})
        await page.goto("http://127.0.0.1:8008")
        await page.wait_for_timeout(2000)
        
        # Verify no tv chart or iframe
        chart_el = await page.query_selector("#tradingview_chart, #tv-chart-wrapper, iframe")
        print("Chart element exists:", bool(chart_el))
        
        # Test search
        s_input = await page.query_selector("#search-symbol")
        await s_input.fill("카카오")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(2000)
        
        q_name = await page.inner_text("#quote-name")
        q_price = await page.inner_text("#quote-price")
        print(f"Quote Board: Name={q_name}, Price={q_price}")
        
        await page.screenshot(path="C:/Users/User/.gemini/antigravity/brain/15b083a3-5bd8-4da9-bc44-163bca90bdb5/rollback_proof.png")
        print("Screenshot saved to rollback_proof.png")
        await b.close()

asyncio.run(verify_rollback())
