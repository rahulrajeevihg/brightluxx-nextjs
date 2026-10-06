"""
Extract heading hierarchy from React JSX files by parsing the source code.
Stores results in MongoDB and heading-data.json.
"""
import re
import os
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")
PAGES_DIR = "/app/frontend/src/pages"

# Map routes to their JSX source files
ROUTE_FILE_MAP = {
    "/": "Home.js",
    "/products": "Products.js",
    "/product-families": "ProductFamilies.js",
    "/solutions": "Solutions.js",
    "/contact": "Contact.js",
    "/about": "About.js",
    "/lumimorph": "lumimorph/LumiMorphLanding.js",
    "/lumimorph/elite": "lumimorph/LumiMorphElitePage.js",
    "/lumimorph/grande": "lumimorph/LumiMorphGrandePage.js",
    "/lumimorph/mini": "lumimorph/LumiMorphMiniPage.js",
    "/naturatex": "naturatex/NaturaTexPage.js",
    "/naturatex/holoveil": "naturatex/HoloVeilPage.js",
    "/signatouch": "signatouch/SignaTouchLanding.js",
    "/signatouch/touch-kiosk": "signatouch/TouchKioskPage.js",
    "/signatouch/smart-signage": "signatouch/SmartSignagePage.js",
    "/signatouch/self-service": "signatouch/SelfServicePage.js",
    "/glassmorph": "glassmorph/GlassMorphLanding.js",
    "/glassmorph/smart-film": "glassmorph/SmartFilmPage.js",
    "/glassmorph/led-film": "glassmorph/LedFilmPage.js",
    "/glassmorph/media-glass": "glassmorph/MediaGlassPage.js",
    "/glassmorph/flying-display": "glassmorph/FlyingDisplayPage.js",
    "/pixelvue": "pixelvue/PixelVueLanding.js",
    "/art-immersive": "ArtImmersive.js",
    "/luxury-home-cinema": "LuxuryHomeCinema.js",
    "/applications": "ApplicationsIndex.js",
    "/knowledge": "KnowledgeHub.js",
    "/knowledge/cob-vs-mip-vs-smd": "knowledge/CobVsMipVsSmd.js",
    "/knowledge/pixel-pitch-guide": "knowledge/PixelPitchGuide.js",
    "/knowledge/brightness-nits-guide": "knowledge/BrightnessGuide.js",
    "/knowledge/ip-rating-guide": "knowledge/IpRatingGuide.js",
    "/knowledge/refresh-rate-guide": "knowledge/RefreshRateGuide.js",
    "/knowledge/processing-calibration": "knowledge/ProcessingCalibration.js",
    "/knowledge/cms-multi-site": "knowledge/CmsMultiSite.js",
    "/blog": "Blog.js",
    "/case-studies": "CaseStudiesIndex.js",
    "/projects": "ProjectsIndex.js",
    "/inspirations": "InspirationsIndex.js",
    "/faq": "FAQ.js",
    "/factory-tour": "FactoryTour.js",
    "/for-architects": "ForArchitects.js",
    "/design-assist": "DesignAssist.js",
    "/cpd-programme": "CpdProgramme.js",
    "/tech-guide": "TechGuide.js",
    "/budget-estimator": "BudgetEstimator.js",
    "/signage-solutions": "SignageSolutions.js",
    "/indoor-led": "IndoorLed.js",
    "/outdoor-led": "OutdoorLed.js",
    "/led-screen-dubai": "DubaiPage.js",
    "/led-display-abu-dhabi": "AbuDhabiPage.js",
    "/led-screen-saudi-arabia": "SaudiPage.js",
    "/led-screen-qatar": "QatarPage.js",
    "/led-screen-kuwait": "KuwaitPage.js",
    "/digital-experience": "DigitalExperience.js",
    "/latest-tech": "LatestTechIndex.js",
    "/resource-library": "ResourceLibrary.js",
}


def extract_headings_from_jsx(filepath):
    """Extract heading text from JSX file using regex."""
    if not os.path.exists(filepath):
        return []

    with open(filepath, "r") as f:
        content = f.read()

    headings = []
    seen = set()

    # Pattern 1: <h1 ... >Text</h1>  (static text)
    for match in re.finditer(r'<(h[1-4])\b[^>]*>\s*([^<{]+?)\s*<\/\1>', content):
        tag, text = match.group(1), match.group(2).strip()
        text = re.sub(r'\s+', ' ', text)
        if text and len(text) > 1 and text not in seen:
            seen.add(text)
            headings.append({"tag": tag, "text": text})

    # Pattern 2: <h1 ... >{variable}</h1> — skip (dynamic)
    # Pattern 3: <h1 ... >Static {dynamic} static</h1> — extract static parts
    for match in re.finditer(r'<(h[1-4])\b[^>]*>((?:[^<]|<(?!/\1))+?)<\/\1>', content, re.DOTALL):
        tag = match.group(1)
        inner = match.group(2).strip()
        # Remove JSX expressions
        text = re.sub(r'\{[^}]*\}', '', inner)
        # Remove nested JSX tags
        text = re.sub(r'<[^>]*>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if text and len(text) > 1 and text not in seen:
            seen.add(text)
            headings.append({"tag": tag, "text": text})

    return headings


async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    col = db["page_seo"]

    all_data = {}
    found_count = 0
    missing_files = []

    for route, rel_path in ROUTE_FILE_MAP.items():
        filepath = os.path.join(PAGES_DIR, rel_path)
        if not os.path.exists(filepath):
            # Try alternate locations
            for alt_dir in ["", "dea/"]:
                alt = os.path.join(PAGES_DIR, alt_dir, rel_path)
                if os.path.exists(alt):
                    filepath = alt
                    break

        headings = extract_headings_from_jsx(filepath)

        if headings:
            all_data[route] = headings
            await col.update_one(
                {"path": route},
                {"$set": {"headings": headings}},
                upsert=False,
            )
            found_count += 1
            h_str = ", ".join(f"{h['tag']}:{h['text'][:35]}" for h in headings[:3])
            print(f"  {route} → {len(headings)} headings: {h_str}")
        else:
            if os.path.exists(filepath):
                # File exists but no headings found, try to get name from DB
                doc = await col.find_one({"path": route}, {"_id": 0, "name": 1, "meta_title": 1})
                if doc:
                    name = doc.get("name") or doc.get("meta_title") or route.strip("/").replace("-", " ").title()
                    fallback = [{"tag": "h1", "text": name}]
                    all_data[route] = fallback
                    await col.update_one({"path": route}, {"$set": {"headings": fallback}})
                    found_count += 1
                    print(f"  {route} → fallback H1: {name}")
                else:
                    print(f"  {route} → no headings, no DB entry")
            else:
                missing_files.append(f"{route} ({rel_path})")

    # Save to JSON
    output_path = "/app/frontend/heading-data.json"
    with open(output_path, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\nDone: {found_count}/{len(ROUTE_FILE_MAP)} pages with headings")
    if missing_files:
        print(f"Missing files: {len(missing_files)}")
        for mf in missing_files[:10]:
            print(f"  - {mf}")
    print(f"Saved to {output_path}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
