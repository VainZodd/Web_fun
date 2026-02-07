import asyncio
from playwright.async_api import async_playwright
import os

async def verify_live_streams():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        # Load the page
        file_path = "file://" + os.path.abspath("Nexus_News.html")
        await page.goto(file_path)

        # Wait for boot loader to disappear
        await page.wait_for_selector("#boot-loader", state="detached", timeout=10000)

        # Navigate to LIVE tab
        await page.click("#nav-live")
        await asyncio.sleep(2) # Wait for animation

        # Verify streams are rendered
        streams = await page.query_selector_all(".uplink-card")
        print(f"Found {len(streams)} live streams.")

        # Check first stream name
        first_stream_name = await page.inner_text(".uplink-card:first-child div[style*='font-size:0.55rem']")
        print(f"First stream: {first_stream_name}")

        # Take screenshot of Live view
        await page.screenshot(path="live_streams_verify.png")

        # Switch to second stream
        await page.click(".uplink-card:nth-child(2)")
        await asyncio.sleep(2) # Wait for transition

        current_name = await page.inner_text("#stream-name")
        print(f"Switched to: {current_name}")

        await page.screenshot(path="live_streams_switched.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_live_streams())
