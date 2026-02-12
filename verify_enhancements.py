import asyncio
from playwright.async_api import async_playwright
import os

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        abs_path = os.path.abspath("Nexus_News.html")
        await page.goto(f"file://{abs_path}")
        await page.wait_for_selector("#boot-loader", state="detached")

        # 1. Capture Dashboard with News Cards and Badges
        await page.wait_for_selector(".news-card")
        await page.screenshot(path="verify_v3_dashboard_badges.png")

        # 2. Open Detail View
        await page.click('.news-card:first-child')
        await page.wait_for_selector("#detail:not(.hidden)")
        await asyncio.sleep(0.5) # Wait for GSAP
        await page.screenshot(path="verify_v3_detail_analysis.png")

        # 3. Verify English/German switch for badges
        await page.click('button:has(.material-symbols-outlined:text("settings"))')
        await page.wait_for_selector("#filter-modal:not(.hidden)")
        await page.click('#btn-lang-de')
        await page.click('#txt-apply')
        await page.wait_for_selector("#filter-modal.hidden")

        # Re-open detail to see German badges
        await page.click('.news-card:first-child')
        await page.wait_for_selector("#detail:not(.hidden)")
        await asyncio.sleep(0.5)
        await page.screenshot(path="verify_v3_detail_de.png")

        print("Verification images generated.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
