"""
Extract heading hierarchy (h1-h4) from all site pages using Playwright.
Stores results in MongoDB page_seo collection and outputs heading-data.json.
"""
import asyncio
import json
from playwright.async_api import async_playwright
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")
BASE_URL = "http://localhost:3000"

# All site routes
ROUTES = [
    "/", "/products", "/product-families", "/solutions", "/contact", "/about",
    "/lumimorph", "/lumimorph/elite", "/lumimorph/grande", "/lumimorph/mini",
    "/naturatex", "/naturatex/holoveil",
    "/signatouch", "/signatouch/touch-kiosk", "/signatouch/smart-signage", "/signatouch/self-service",
    "/glassmorph", "/glassmorph/smart-film", "/glassmorph/led-film", "/glassmorph/media-glass", "/glassmorph/flying-display",
    "/pixelvue",
    "/art-immersive", "/luxury-home-cinema",
    "/applications", "/knowledge",
    "/knowledge/cob-vs-mip-vs-smd", "/knowledge/pixel-pitch-guide", "/knowledge/brightness-nits-guide",
    "/knowledge/ip-rating-guide", "/knowledge/refresh-rate-guide", "/knowledge/processing-calibration",
    "/knowledge/cms-multi-site",
    "/blog", "/case-studies", "/projects", "/inspirations",
    "/faq", "/factory-tour", "/for-architects", "/design-assist", "/cpd-programme",
    "/tech-guide", "/budget-estimator", "/signage-solutions",
    "/indoor-led", "/outdoor-led",
    "/led-screen-dubai", "/led-display-abu-dhabi", "/led-screen-saudi-arabia",
    "/led-screen-qatar", "/led-screen-kuwait",
    "/digital-experience", "/latest-tech", "/resource-library",
]


async def extract_headings_from_page(page, url):
    """Visit a page and extract all heading elements."""
    try:
        await page.goto(url, wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(1500)

        headings = await page.evaluate("""
            () => {
                const results = [];
                const seen = new Set();
                document.querySelectorAll('h1, h2, h3, h4').forEach(el => {
                    const text = el.textContent.trim().replace(/\\s+/g, ' ');
                    if (text && text.length > 1 && !seen.has(text)) {
                        seen.add(text);
                        results.push({
                            tag: el.tagName.toLowerCase(),
                            text: text
                        });
                    }
                });
                return results;
            }
        """)
        return headings
    except Exception as e:
        print(f"  Error: {e}")
        return []


async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    col = db["page_seo"]

    all_data = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page()

        for i, route in enumerate(ROUTES):
            url = f"{BASE_URL}{route}"
            print(f"[{i+1}/{len(ROUTES)}] {route}...")
            headings = await extract_headings_from_page(page, url)

            if headings:
                all_data[route] = headings
                # Update MongoDB
                await col.update_one(
                    {"path": route},
                    {"$set": {"headings": headings}},
                    upsert=False,
                )
                h_summary = ", ".join(f"{h['tag']}:{h['text'][:30]}" for h in headings[:3])
                print(f"  Found {len(headings)} headings: {h_summary}")
            else:
                print(f"  No headings found")

        await browser.close()

    # Save to JSON file
    output_path = "/app/frontend/heading-data.json"
    with open(output_path, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"\nSaved heading data for {len(all_data)} pages to {output_path}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
