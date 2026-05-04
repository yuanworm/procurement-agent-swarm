import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

TENDERS_FILE = "found_tenders.json"
OUTPUT_FILE = "tender_summaries.md"
DETAIL_URL = "https://www.gebiz.gov.sg/ptn/opportunity/directlink.xhtml?docCode={ref}"

# Sections we want to extract from page text
SECTION_MARKERS = [
    "QUOTATION DOCUMENTS",
    "ITEMS TO RESPOND",
    "DELIVERY INFORMATION",
    "AWARDING AGENCY",
    "WHO TO CONTACT",
]

BOILERPLATE = [
    "A Singapore Government Agency Website",
    "GETTING STARTED", "ANNOUNCEMENTS", "ABOUT US",
    "Home\nOpportunities\nSupplier Directory",
    "Government Electronic Business\nProcurement Information",
    "Supported browsers are",
    "Report Vulnerability", "Privacy Statement", "Terms of Use", "Sitemap",
    "© 2026 GOVERNMENT OF SINGAPORE",
    "The information contained within the procurement notices",
    "Please log in to view the Documents",
    "SIGN UP", "WHICH TO USE?",
]


def clean_text(text: str) -> str:
    for bp in BOILERPLATE:
        text = text.replace(bp, "")
    # Collapse excess blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_field(text: str, label: str) -> str:
    match = re.search(rf'{re.escape(label)}\s*\n(.+)', text)
    return match.group(1).strip() if match else "N/A"


def extract_section(text: str, start_marker: str, end_markers: list[str]) -> str:
    pattern = rf'{re.escape(start_marker)}\n(.*?)(?=' + '|'.join(re.escape(m) for m in end_markers) + r'|$)'
    match = re.search(pattern, text, re.S)
    return match.group(1).strip() if match else ""


def extract_doc_names(text: str) -> list[str]:
    # Document names appear between "QUOTATION DOCUMENTS" and next section
    section = extract_section(text, "QUOTATION DOCUMENTS", SECTION_MARKERS[1:] + ["WHO TO CONTACT"])
    names = [ln.strip() for ln in section.splitlines() if ln.strip() and "." in ln]
    return names


def extract_items(text: str) -> list[str]:
    section = extract_section(text, "ITEMS TO RESPOND", ["DELIVERY INFORMATION", "AWARDING AGENCY", "Government Electronic Business"])
    if not section:
        return []
    items = []
    for block in re.split(r'\n(?=\d+\s*\nItem No\.)', section):
        block = block.strip()
        if not block:
            continue
        name_match = re.search(r'Item No\. \d+\nMandatory to Bid: \w+\n(.+)', block)
        qty_match = re.search(r'Required Quantity\n([\d.]+)', block)
        uom_match = re.search(r'Unit of Measurement\n(\w+)', block)
        remark_match = re.search(r'Remarks\n(.+)', block)
        item_name = name_match.group(1).strip() if name_match else block.splitlines()[0]
        qty = qty_match.group(1).rstrip('0').rstrip('.') if qty_match else "?"
        uom = uom_match.group(1) if uom_match else ""
        remark = remark_match.group(1).strip() if remark_match else ""
        items.append(f"{qty} × {uom} — {item_name}" + (f" *(Note: {remark})*" if remark else ""))
    return items


async def fetch_detail(page, ref: str) -> dict:
    url = DETAIL_URL.format(ref=ref)
    await page.goto(url, wait_until="networkidle", timeout=30000)
    raw = await page.evaluate("document.body.innerText")
    text = clean_text(raw)

    agency      = extract_field(text, "Agency")
    published   = extract_field(text, "Published")
    closed      = extract_field(text, "Closed")
    proc_type   = extract_field(text, "Procurement Type")
    proc_method = extract_field(text, "Procurement Method")
    category    = extract_field(text, "Procurement Category")
    remarks     = extract_field(text, "Remarks")
    docs        = extract_doc_names(text)
    items       = extract_items(text)

    return {
        "agency": agency,
        "published": published,
        "closed": closed,
        "procurement_type": proc_type,
        "procurement_method": proc_method,
        "category": category,
        "remarks": remarks,
        "spec_documents": docs,
        "items": items,
        "url": url,
    }


def render_markdown(tenders: list[dict], details: list[dict]) -> str:
    lines = ["# Laptop Tender Summaries", f"*Sourced from GeBIZ — {len(tenders)} tender(s) found*\n", "---\n"]

    for tender, detail in zip(tenders, details):
        lines.append(f"## {tender['title']}")
        lines.append(f"**Reference:** `{tender['reference_number']}` | "
                     f"**Status:** {tender['status']} | "
                     f"**Closing Date:** {tender['closing_date']}\n")

        lines.append("### Key Details")
        lines.append(f"| Field | Value |")
        lines.append(f"|-------|-------|")
        lines.append(f"| Agency | {detail['agency']} |")
        lines.append(f"| Published | {detail['published']} |")
        lines.append(f"| Closed | {detail['closed']} |")
        lines.append(f"| Procurement Type | {detail['procurement_type']} |")
        lines.append(f"| Procurement Method | {detail['procurement_method']} |")
        lines.append(f"| Category | {detail['category']} |")
        if detail['remarks'] not in ("N/A", ""):
            lines.append(f"| Remarks | {detail['remarks']} |")
        lines.append("")

        if detail['items']:
            lines.append("### Requirement Specifications (Items to Respond)")
            for item in detail['items']:
                lines.append(f"- {item}")
            lines.append("")

        if detail['spec_documents']:
            lines.append("### Specification Documents *(login required to download)*")
            for doc in detail['spec_documents']:
                lines.append(f"- `{doc}`")
            lines.append("")

        lines.append(f"[View on GeBIZ]({detail['url']})\n")
        lines.append("---\n")

    return "\n".join(lines)


async def main():
    tenders = json.loads(Path(TENDERS_FILE).read_text())
    print(f"Loaded {len(tenders)} tender(s) from {TENDERS_FILE}")

    details = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for tender in tenders:
            ref = tender["reference_number"]
            print(f"  Researching {ref} — {tender['title'][:50]}...")
            detail = await fetch_detail(page, ref)
            details.append(detail)

        await browser.close()

    md = render_markdown(tenders, details)
    Path(OUTPUT_FILE).write_text(md)
    print(f"\nSaved summaries to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
