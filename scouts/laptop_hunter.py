import asyncio
import json
import re
from playwright.async_api import async_playwright

GEBIZ_URL = "https://www.gebiz.gov.sg/ptn/opportunity/BOListing.xhtml"
SEARCH_TERM = "laptop"
MAX_RESULTS = 20
OUTPUT_FILE = "found_tenders.json"


def parse_ref_number(header_text: str) -> str:
    # Format: "<n>\n<Type> - <REF> / <ALT-REF>\n<STATUS>"
    match = re.search(r'-\s+([A-Z0-9]+)', header_text)
    return match.group(1) if match else ""


def parse_closing_date(content_text: str) -> str:
    match = re.search(r'Closed\s*\n([\d]+ \w+ \d{4})', content_text)
    return match.group(1) if match else "N/A"


def parse_title(content_text: str) -> str:
    # First non-empty line in the content block is the title
    for line in content_text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


async def hunt() -> list[dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"Opening GeBIZ opportunities page...")
        await page.goto(GEBIZ_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        print(f"Searching for '{SEARCH_TERM}'...")
        search_input = page.locator("#contentForm\\:j_idt183_searchBar_INPUT-SEARCH")
        await search_input.wait_for(state="visible", timeout=60000)
        await search_input.click()
        await search_input.fill(SEARCH_TERM)
        await page.locator("#contentForm\\:j_idt183_searchBar_BUTTON-GO").click()
        await page.wait_for_load_state("networkidle", timeout=30000)

        # Expand all result rows
        arrows = await page.query_selector_all(".formSectionHeader6_SERIAL-NUMBER-ARROW")
        print(f"Found {len(arrows)} result(s). Expanding...")
        for arrow in arrows:
            await arrow.click()
            await page.wait_for_timeout(400)
        await page.wait_for_load_state("networkidle", timeout=15000)

        # Scrape each result block
        mains = await page.query_selector_all(".formSectionHeader6_MAIN")
        tenders = []
        for main in mains[:MAX_RESULTS]:
            data = await main.evaluate("""el => ({
                header: el.innerText.trim(),
                content: el.nextElementSibling ? el.nextElementSibling.innerText.trim() : ''
            })""")

            header = data["header"]
            content = data["content"]

            tender = {
                "title": parse_title(content),
                "reference_number": parse_ref_number(header),
                "closing_date": parse_closing_date(content),
                "status": header.splitlines()[-1].strip() if header.splitlines() else "",
            }
            if "laptop" in tender["title"].lower():
                tenders.append(tender)
                print(f"  [{tender['reference_number']}] {tender['title']} — closes {tender['closing_date']}")
            else:
                print(f"  [skip] {tender['title'][:60]}...")

        await browser.close()
        return tenders


async def main():
    tenders = await hunt()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(tenders, f, indent=2)

    print(f"\nSaved {len(tenders)} tender(s) to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
