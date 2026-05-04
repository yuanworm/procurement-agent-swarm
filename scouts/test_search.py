import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "https://www.gebiz.gov.sg"
SCREENSHOT_PATH = "screenshot_gebiz.png"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"Navigating to {TARGET_URL} ...")
        await page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)

        title = await page.title()
        print(f"Page title: {title}")

        await page.screenshot(path=SCREENSHOT_PATH, full_page=True)
        print(f"Screenshot saved to {SCREENSHOT_PATH}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
