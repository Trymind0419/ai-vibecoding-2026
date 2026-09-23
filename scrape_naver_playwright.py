import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Loading Naver Finance Market Sum...")
        await page.goto("https://finance.naver.com/sise/sise_market_sum.naver")
        
        # Extract KOSPI top 20
        # Naver finance table usually has links with href='/item/main.naver?code=...'
        print("Evaluating page...")
        items = await page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[href^="/item/main.naver?code="]'));
            const results = [];
            // Many links are duplicated (img and text). We get the text ones.
            for (let a of links) {
                const name = a.innerText.trim();
                if (name && name !== '') {
                    const codeMatch = a.href.match(/code=(\\d{6})/);
                    if (codeMatch && codeMatch[1]) {
                        results.push({ name: name, symbol: codeMatch[1] });
                    }
                }
            }
            // Remove duplicates
            const unique = [];
            const symbols = new Set();
            for (let r of results) {
                if (!symbols.has(r.symbol)) {
                    symbols.add(r.symbol);
                    unique.push(r);
                }
            }
            return unique.slice(0, 20);
        }""")
        
        print("Scraped Top 20:", json.dumps(items, ensure_ascii=False))
        
        # Save to file so we can read it easily
        with open('live_kospi.json', 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False)
            
        await browser.close()

asyncio.run(run())

