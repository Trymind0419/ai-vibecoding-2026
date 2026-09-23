import asyncio
from playwright.async_api import async_playwright

async def scrape_krx():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        print("Navigating to KRX...")
        await page.goto("http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101", wait_until="networkidle")
        
        # Click search to populate the table (Default is KOSPI)
        try:
            await page.click('button#jsSearchButton')
            await page.wait_for_timeout(3000)
            text = await page.evaluate("document.body.innerText")
            print(text[:2000])
        except Exception as e:
            print("Error clicking:", e)
            
        await browser.close()

asyncio.run(scrape_krx())

