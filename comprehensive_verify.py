
import asyncio
from playwright.async_api import async_playwright
import time
import os

async def verify_nexus():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})

        # Start server if not running - assuming it's already running on 3000
        url = "http://localhost:3000/Nexus_News.html"

        try:
            await page.goto(url)
            print("Page loaded. Waiting for boot sequence...")

            # Wait for boot loader to disappear (should happen when data is fetched)
            await page.wait_for_selector("#boot-loader", state="hidden", timeout=10000)
            print("Boot sequence complete.")

            # Take screenshot of Dashboard
            await page.screenshot(path="verify_dashboard.png")
            print("Dashboard screenshot saved.")

            # Click Archive (DATA)
            await page.click("button:has-text('DATA')")
            await asyncio.sleep(1)
            await page.screenshot(path="verify_archive.png")
            print("Archive screenshot saved.")

            # Click LIVE
            await page.click("button:has-text('LIVE')")
            await asyncio.sleep(2) # Give video time to maybe show something
            await page.screenshot(path="verify_live.png")
            print("Live screenshot saved.")

            # Click ID
            await page.click("button:has-text('ID')")
            await asyncio.sleep(1)
            await page.screenshot(path="verify_id.png")
            print("ID screenshot saved.")

        except Exception as e:
            print(f"Error during verification: {e}")
            await page.screenshot(path="verify_error.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_nexus())
