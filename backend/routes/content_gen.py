"""
Batch SEO + Product Content Generation.
Generates SEO metadata for all uncovered pages and enriches products
with FAQ, application details, and expanded descriptions.
"""
import asyncio
import json
import os
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, BackgroundTasks
from database import db
from auth import get_current_admin

router = APIRouter()
logger = logging.getLogger("content_gen")

# Job tracking
_job = {"status": "idle", "phase": "", "progress": 0, "total": 0, "errors": [], "completed": 0}

PRODUCTION_URL = "https://brightluxx.com"
API_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

# All known routes that need SEO coverage
ALL_ROUTES = {
    "/": "Homepage — Premium LED Display Solutions",
    "/products": "LED Display Products Catalog",
    "/product-families": "LED Display Product Families Overview",
    "/solutions": "LED Display Solutions by Industry",
    "/contact": "Contact & Enquiries",
    "/about": "About Brightluxx",
    "/blog": "Blog & Industry Insights",
    "/faq": "Frequently Asked Questions",
    "/case-studies": "Project Case Studies",
    "/projects": "Project Portfolio",
    "/resources": "Resources & Downloads",
    "/knowledge": "Knowledge Hub",
    "/calculator": "LED Screen Size Calculator Tool",
    "/budget-estimator": "LED Display Budget Estimator Tool",
    "/viewing-distance": "Viewing Distance Calculator",
    "/power-estimator": "Power Consumption Estimator",
    "/project-planner": "LED Project Planner",
    "/technology-selector": "LED Technology Selector Quiz",
    "/spec-substitution": "Spec Substitution Service",
    "/value-engineering": "Value Engineering Service",
    "/installation-guide": "LED Display Installation Guide",
    "/cpd-programme": "CPD Lunch & Learn Programme",
    "/for-architects": "Resources for Architects",
    "/for-contractors": "Resources for Contractors",
    "/distribution": "Distribution & Franchise Partnerships",
    "/factory-tour": "Virtual Factory Tour",
    "/compare-brands": "LED Brand Comparison",
    "/led-screen-suppliers-dubai": "LED Screen Suppliers in Dubai",
    "/abu-dhabi": "LED Displays Abu Dhabi",
    "/saudi-arabia": "LED Displays Saudi Arabia",
    "/qatar": "LED Screens Qatar",
    "/kuwait": "LED Displays Kuwait",
    "/government-solutions": "Government LED Solutions",
    "/indoor-led": "Indoor LED Display Range",
    "/outdoor-led": "Outdoor LED Display Range",
    "/luxury-home-cinema": "Luxury Home Cinema LED",
    "/art-immersive": "Art & Immersive LED Installations",
    "/signage-solutions": "Digital Signage Solutions",
    "/lumimorph": "LumiMorph LED Product Family",
    "/naturatex": "NaturaTex Texture Screen Family",
    "/signatouch": "SignaTouch Interactive Signage Family",
    "/glassmorph": "GlassMorph Smart Glass Family",
    "/pixelvue": "PixelVue LED Display Family",
    "/lumimorph/elite": "LumiMorph Elite Fine-Pitch LED",
    "/lumimorph/grande": "LumiMorph Grande Large-Scale LED",
    "/lumimorph/mini": "LumiMorph Mini Compact LED",
    "/naturatex/holoveil": "NaturaTex HoloVeil Transparent Display",
    "/signatouch/touch-kiosk": "SignaTouch Touch Kiosk",
    "/signatouch/smart-signage": "SignaTouch Smart Signage",
    "/signatouch/self-service": "SignaTouch Self-Service Terminal",
    "/glassmorph/smart-film": "GlassMorph Smart Film PDLC",
    "/glassmorph/led-film": "GlassMorph LED Film",
    "/glassmorph/media-glass": "GlassMorph Media Glass",
    "/glassmorph/switchable-glass": "GlassMorph Switchable Glass",
    "/glassmorph/flying-display": "GlassMorph Flying Display",
    "/glassmorph/hanging-led": "GlassMorph Hanging LED",
    "/pixelvue/iposter": "PixelVue iPoster Digital Poster",
    "/pixelvue/iflip": "PixelVue iFlip Double-Sided LED",
    "/pixelvue/ultra-flip": "PixelVue UltraFlip Premium Poster",
    "/pixelvue/digi-standee": "PixelVue DigiStandee",
    "/pixelvue/ooh-poster": "PixelVue OOH Poster Outdoor Display",
    "/pixelvue/unity": "PixelVue Unity Modular LED",
    "/pixelvue/tetris": "PixelVue Tetris Stackable LED",
    "/pixelvue/videobrick": "PixelVue VideoBrick",
    "/pixelvue/iconference": "PixelVue iConference Meeting Display",
    "/pixelvue/ezeesign": "PixelVue EzeeSign",
    "/pixelvue/ishelf": "PixelVue iShelf Retail Display",
    "/pixelvue/tablevision": "PixelVue TableVision",
    "/technology": "LED Display Technologies Overview",
    "/technology/cob-led": "COB Chip-on-Board LED Technology",
    "/technology/cob": "COB LED Technology",
    "/technology/microled": "MicroLED & MiP Technology",
    "/technology/mip-led": "MiP LED Technology",
    "/technology/gob": "GOB Protection Technology",
    "/technology/hdr": "HDR & Color Technology",
    "/technology/driving-ic": "Driving IC Technology",
    "/technology/fine-pitch-led": "Fine Pitch LED Technology",
    "/technology/media-facade": "Media Facade LED Technology",
    "/technology/all-in-one-dvled": "All-in-One dvLED Technology",
    "/technology/transparent-led": "Transparent LED Technology",
    "/technology/creative-led": "Creative LED Technology",
    "/technology/3d-anamorphic-led": "3D Anamorphic LED Technology",
    "/solutions/retail": "LED for Retail & Hospitality",
    "/solutions/corporate": "LED for Corporate & Offices",
    "/solutions/entertainment": "LED for Entertainment & Events",
    "/solutions/transportation": "LED for Transportation",
    "/solutions/worship": "LED for Houses of Worship",
    "/solutions/control-rooms": "LED for Control Rooms",
    "/solutions/virtual-production": "LED for Virtual Production",
    "/solutions/architecture": "Architectural LED Displays",
    "/tools/roi-calculator": "ROI Calculator Tool",
    "/compare-products": "Product Comparison Tool",
}


async def _generate_with_llm(prompt: str, session_id: str) -> dict:
    """Call LLM and parse JSON response."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    chat = LlmChat(
        api_key=API_KEY,
        session_id=session_id,
        system_message=(
            "You are an expert SEO content specialist for Brightluxx, a premium LED display solutions "
            "company in Dubai, UAE serving the GCC/Middle East. You generate highly optimized, accurate, "
            "and compelling content. Always respond with valid JSON only. No markdown, no code blocks."
        ),
    ).with_model("openai", "gpt-4.1-mini")

    response = await chat.send_message(UserMessage(text=prompt))
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(cleaned)


async def _generate_seo_batch():
    """Generate SEO metadata for all pages missing from DB."""
    seo_col = db["page_seo"]

    existing = set()
    async for doc in seo_col.find({}, {"path": 1}):
        existing.add(doc["path"])

    # Also add product pages
    products = []
    async for p in db["products"].find({}, {"slug": 1, "name": 1, "category": 1, "tagline": 1, "pixel_pitch": 1, "description": 1}):
        path = f"/products/{p['slug']}"
        if path not in existing:
            products.append(p)
            ALL_ROUTES[path] = f"Product: {p['name']}"

    missing = {p: desc for p, desc in ALL_ROUTES.items() if p not in existing}
    _job["total"] = len(missing)
    _job["phase"] = "seo_pages"
    logger.info(f"Generating SEO for {len(missing)} missing pages")

    batch_size = 5
    paths_list = list(missing.items())

    for i in range(0, len(paths_list), batch_size):
        batch = paths_list[i:i + batch_size]
        batch_desc = "\n".join(f"- {path}: {desc}" for path, desc in batch)

        prompt = f"""Generate SEO metadata for these {len(batch)} pages on brightluxx.com:

{batch_desc}

For EACH page, generate:
- "meta_title": 50-60 chars, include primary keyword, compelling
- "meta_description": 150-160 chars, include call-to-action and UAE/Dubai location
- "keywords": Array of 6-8 relevant keywords (mix short+long tail)
- "og_title": Social-optimized title, 55-60 chars
- "og_description": Social description, 100-120 chars, engaging
- "image_alt": Descriptive alt text for hero image, 10-20 words

Return JSON object where keys are the URL paths. Example:
{{
  "/products": {{
    "meta_title": "...",
    "meta_description": "...",
    "keywords": ["...", "..."],
    "og_title": "...",
    "og_description": "...",
    "image_alt": "..."
  }}
}}"""

        try:
            result = await _generate_with_llm(prompt, f"seo-batch-{i}")

            for path, data in result.items():
                if not isinstance(data, dict):
                    continue
                path = path.strip()
                if not path.startswith("/"):
                    continue

                doc = {
                    "path": path,
                    "name": missing.get(path, path),
                    "category": "auto-generated",
                    "meta_title": data.get("meta_title", ""),
                    "meta_description": data.get("meta_description", ""),
                    "keywords": data.get("keywords", []),
                    "og_title": data.get("og_title", ""),
                    "og_description": data.get("og_description", ""),
                    "image_alt": data.get("image_alt", ""),
                    "canonical_url": f"{PRODUCTION_URL}{path}",
                    "schema_type": "WebPage",
                    "noindex": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                await seo_col.update_one({"path": path}, {"$set": doc}, upsert=True)
                _job["completed"] += 1
                _job["progress"] = _job["completed"]

        except Exception as e:
            logger.error(f"SEO batch error: {e}")
            _job["errors"].append(f"SEO batch {i}: {str(e)[:100]}")

        await asyncio.sleep(1)  # Rate limit

    logger.info(f"SEO generation complete: {_job['completed']}/{_job['total']}")


async def _enrich_products():
    """Add FAQ, application details, and expand thin descriptions for all products."""
    products_col = db["products"]
    _job["phase"] = "product_enrichment"

    products = []
    async for p in products_col.find({}):
        products.append(p)

    _job["total"] += len(products)
    logger.info(f"Enriching {len(products)} products with FAQ + applications")

    batch_size = 3
    for i in range(0, len(products), batch_size):
        batch = products[i:i + batch_size]

        for product in batch:
            pid = product["_id"]
            name = product.get("name", "")
            slug = product.get("slug", "")
            category = product.get("category", "")
            tagline = product.get("tagline", "")
            description = product.get("description", "")
            pixel_pitch = product.get("pixel_pitch", "")
            brightness = product.get("brightness", "")
            key_specs = product.get("key_specs", {})
            application = product.get("application", "")

            specs_str = ", ".join(f"{k}: {v}" for k, v in key_specs.items()) if isinstance(key_specs, dict) else str(key_specs)

            prompt = f"""Generate FAQ and application details for this LED display product:

Product: {name}
Category: {category}
Tagline: {tagline}
Pixel Pitch: {pixel_pitch}
Brightness: {brightness}
Key Specs: {specs_str}
Application: {application}
Current Description: {description}

Generate a JSON object with:
1. "faq": Array of 6-8 objects, each with "q" (question) and "a" (answer). Questions should be what a buyer/specifier would ask. Include technical specs, installation, pricing context, warranty, comparison with alternatives, and use-case questions. Answers should be 2-3 sentences, accurate and helpful.

2. "applications": Array of 4-6 objects, each with "title" (application name), "description" (2-3 sentences on why this product fits), and "icon" (one of: ShoppingBag, Building2, Theater, TrafficCone, Globe, Grid3X3, Box, Cuboid, GraduationCap, Tv, Monitor, Sparkles).

3. "expanded_description": If the current description is less than 150 characters, provide an expanded 200-300 character description that highlights key selling points, technology, and ideal use cases. If the current description is already sufficient, return null.

Return valid JSON only."""

            try:
                result = await _generate_with_llm(prompt, f"product-{slug}")

                update = {"updated_at": datetime.now(timezone.utc).isoformat()}

                if "faq" in result and isinstance(result["faq"], list):
                    update["faq"] = result["faq"]

                if "applications" in result and isinstance(result["applications"], list):
                    update["applications"] = result["applications"]

                if result.get("expanded_description") and len(description) < 150:
                    update["description"] = result["expanded_description"]

                if update:
                    await products_col.update_one({"_id": pid}, {"$set": update})

                _job["completed"] += 1
                _job["progress"] = _job["completed"]

            except Exception as e:
                logger.error(f"Product enrich error for {slug}: {e}")
                _job["errors"].append(f"Product {slug}: {str(e)[:100]}")

            await asyncio.sleep(0.5)

        await asyncio.sleep(1)  # Rate limit between batches

    logger.info(f"Product enrichment complete: {_job['completed']}/{_job['total']}")


async def _enrich_blogs():
    """Generate FAQ sections for all blog posts."""
    blogs_col = db["blogs"]
    _job["phase"] = "blog_faq"

    blogs = []
    async for b in blogs_col.find({}):
        blogs.append(b)

    _job["total"] += len(blogs)
    logger.info(f"Generating FAQ for {len(blogs)} blog posts")

    for blog in blogs:
        bid = blog["_id"]
        title = blog.get("title", "")
        slug = blog.get("slug", "")
        content = blog.get("content", "")
        excerpt = blog.get("excerpt", "")
        tags = blog.get("tags", [])
        category = blog.get("category", "")

        # Use excerpt + first 800 chars of content as context
        content_preview = content[:800] if content else excerpt

        prompt = f"""Generate FAQ for this LED display industry blog post:

Title: {title}
Category: {category}
Tags: {', '.join(tags) if isinstance(tags, list) else str(tags)}
Excerpt: {excerpt}
Content preview: {content_preview}

Generate 5-7 FAQ items that:
1. Cover the key questions a reader would have after seeing this topic
2. Include at least one "how" question, one "why" question, and one comparison/cost question
3. Include UAE/GCC context where relevant
4. Answers should be 2-4 sentences, authoritative and helpful
5. Questions should target long-tail search keywords related to this topic

Return JSON: {{"faq": [{{"q": "...", "a": "..."}}]}}"""

        try:
            result = await _generate_with_llm(prompt, f"blog-{slug}")

            if "faq" in result and isinstance(result["faq"], list) and len(result["faq"]) > 0:
                await blogs_col.update_one(
                    {"_id": bid},
                    {"$set": {"faq": result["faq"], "updated_at": datetime.now(timezone.utc).isoformat()}}
                )

            _job["completed"] += 1
            _job["progress"] = _job["completed"]

        except Exception as e:
            logger.error(f"Blog FAQ error for {slug}: {e}")
            _job["errors"].append(f"Blog {slug}: {str(e)[:100]}")

        await asyncio.sleep(1)

    logger.info(f"Blog FAQ generation complete")


async def _add_product_schema_fields():
    """Add schema-ready fields (brand, availability, priceRange, warranty) to products."""
    products_col = db["products"]
    _job["phase"] = "product_schema"

    # Category-based price ranges (USD, approximate for B2B LED industry)
    PRICE_RANGES = {
        "cob-microled": {"low": 2500, "high": 15000, "currency": "USD"},
        "mip": {"low": 1800, "high": 12000, "currency": "USD"},
        "indoor": {"low": 800, "high": 8000, "currency": "USD"},
        "all-in-one": {"low": 3000, "high": 25000, "currency": "USD"},
        "cinema-led": {"low": 5000, "high": 50000, "currency": "USD"},
        "dvled": {"low": 4000, "high": 40000, "currency": "USD"},
        "outdoor": {"low": 600, "high": 5000, "currency": "USD"},
        "outdoor-hb": {"low": 800, "high": 6000, "currency": "USD"},
        "outdoor-gob": {"low": 700, "high": 5500, "currency": "USD"},
        "outdoor-fp": {"low": 1200, "high": 8000, "currency": "USD"},
        "mesh": {"low": 400, "high": 3000, "currency": "USD"},
        "road-signal": {"low": 500, "high": 4000, "currency": "USD"},
        "transparent": {"low": 1500, "high": 10000, "currency": "USD"},
        "flexible": {"low": 1200, "high": 8000, "currency": "USD"},
        "custom-shapes": {"low": 2000, "high": 15000, "currency": "USD"},
        "sphere": {"low": 5000, "high": 30000, "currency": "USD"},
        "naked-eye-3d": {"low": 3000, "high": 20000, "currency": "USD"},
        "ceiling-led": {"low": 1500, "high": 10000, "currency": "USD"},
        "digital-signage": {"low": 500, "high": 8000, "currency": "USD"},
        "smart-tv": {"low": 300, "high": 5000, "currency": "USD"},
        "ready-made": {"low": 2000, "high": 15000, "currency": "USD"},
        "interactive": {"low": 2000, "high": 12000, "currency": "USD"},
        "virtual-production": {"low": 3000, "high": 25000, "currency": "USD"},
        "poster-totem": {"low": 800, "high": 5000, "currency": "USD"},
        "shelf-edge": {"low": 200, "high": 1500, "currency": "USD"},
        "accessories": {"low": 50, "high": 2000, "currency": "USD"},
        "signage-solutions": {"low": 500, "high": 15000, "currency": "USD"},
        "home-cinema": {"low": 8000, "high": 80000, "currency": "USD"},
    }
    DEFAULT_PRICE = {"low": 500, "high": 10000, "currency": "USD"}

    count = 0
    async for product in products_col.find({}):
        cat = product.get("category", "")
        price = PRICE_RANGES.get(cat, DEFAULT_PRICE)

        schema_fields = {
            "brand": "Brightluxx",
            "manufacturer": "Brightluxx",
            "availability": "InStock",
            "price_range": price,
            "warranty": "3 Years Standard | 5 Years Extended Available",
            "condition": "NewCondition",
            "schema_updated": datetime.now(timezone.utc).isoformat(),
        }

        await products_col.update_one({"_id": product["_id"]}, {"$set": schema_fields})
        count += 1
        _job["completed"] += 1
        _job["progress"] = _job["completed"]

    _job["total"] += count
    logger.info(f"Product schema fields added to {count} products")


async def _run_full_generation():
    """Run SEO generation, product enrichment, blog FAQ, and product schema."""
    _job.update({"status": "running", "phase": "seo_pages", "progress": 0, "total": 0, "errors": [], "completed": 0})
    try:
        await _generate_seo_batch()
        await _enrich_products()
        await _enrich_blogs()
        await _add_product_schema_fields()

        # Clear SSR meta cache so new data is served
        from routes.ssr_meta import _meta_cache
        _meta_cache.clear()

        _job["status"] = "complete"
        _job["phase"] = "done"
    except Exception as e:
        _job["status"] = "error"
        _job["errors"].append(str(e))
        logger.error(f"Full generation error: {e}")


async def _run_blog_and_schema():
    """Run only blog FAQ + product schema (skipping already-done SEO + product enrichment)."""
    _job.update({"status": "running", "phase": "blog_faq", "progress": 0, "total": 0, "errors": [], "completed": 0})
    try:
        await _enrich_blogs()
        await _add_product_schema_fields()

        from routes.ssr_meta import _meta_cache
        _meta_cache.clear()

        _job["status"] = "complete"
        _job["phase"] = "done"
    except Exception as e:
        _job["status"] = "error"
        _job["errors"].append(str(e))
        logger.error(f"Blog/schema generation error: {e}")


@router.post("/api/admin/content/generate-all")
async def start_full_generation(background_tasks: BackgroundTasks, admin=Depends(get_current_admin)):
    """Start background generation of SEO metadata + product enrichment + blog FAQ + schema."""
    if _job["status"] == "running":
        return {"error": "Generation already in progress", "job": _job}
    background_tasks.add_task(_run_full_generation)
    return {"status": "started", "message": "Full background generation started"}


@router.post("/api/admin/content/generate-blog-schema")
async def start_blog_schema_generation(background_tasks: BackgroundTasks, admin=Depends(get_current_admin)):
    """Start background generation of blog FAQ + product schema only."""
    if _job["status"] == "running":
        return {"error": "Generation already in progress", "job": _job}
    background_tasks.add_task(_run_blog_and_schema)
    return {"status": "started", "message": "Blog FAQ + Product Schema generation started"}


@router.get("/api/admin/content/generate-status")
async def get_generation_status(admin=Depends(get_current_admin)):
    """Check the status of the background generation job."""
    return _job
