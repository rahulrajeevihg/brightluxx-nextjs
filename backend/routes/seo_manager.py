"""
SEO Manager API — Per-page SEO data management with AI auto-generation.
"""
from fastapi import APIRouter, Depends, Body, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from database import db
from routes.admin import get_current_admin
from bson import ObjectId
from bson.errors import InvalidId
import os
import asyncio

from routes.ssr_meta import clear_ssr_cache


def parse_oid(page_id: str) -> ObjectId:
    """Parse and validate a page_id as ObjectId, or raise 400."""
    try:
        return ObjectId(page_id)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail="Invalid page ID")

router = APIRouter(tags=["SEO Manager"])
col = db["page_seo"]

# All site pages with default descriptions for AI context
SITE_PAGES = [
    {"path": "/", "name": "Homepage", "category": "Main"},
    {"path": "/products", "name": "All Products", "category": "Main"},
    {"path": "/product-families", "name": "Product Families", "category": "Main"},
    {"path": "/solutions", "name": "Solutions", "category": "Main"},
    {"path": "/contact", "name": "Contact Us", "category": "Main"},
    {"path": "/about", "name": "About Brightluxx", "category": "Main"},
    {"path": "/lumimorph", "name": "LumiMorph", "category": "Product Family"},
    {"path": "/lumimorph/elite", "name": "LumiMorph Elite", "category": "Product Family"},
    {"path": "/lumimorph/grande", "name": "LumiMorph Grande", "category": "Product Family"},
    {"path": "/lumimorph/mini", "name": "LumiMorph Mini", "category": "Product Family"},
    {"path": "/naturatex", "name": "NaturaTex", "category": "Product Family"},
    {"path": "/naturatex/holoveil", "name": "NaturaTex HoloVeil", "category": "Product Family"},
    {"path": "/signatouch", "name": "SignaTouch", "category": "Product Family"},
    {"path": "/signatouch/touch-kiosk", "name": "Touch Kiosk", "category": "Product Family"},
    {"path": "/signatouch/smart-signage", "name": "Smart Signage", "category": "Product Family"},
    {"path": "/signatouch/self-service", "name": "Self Service", "category": "Product Family"},
    {"path": "/glassmorph", "name": "GlassMorph", "category": "Product Family"},
    {"path": "/glassmorph/smart-film", "name": "Smart Film", "category": "Product Family"},
    {"path": "/glassmorph/led-film", "name": "LED Film", "category": "Product Family"},
    {"path": "/glassmorph/media-glass", "name": "Media Glass", "category": "Product Family"},
    {"path": "/glassmorph/flying-display", "name": "Flying Display", "category": "Product Family"},
    {"path": "/pixelvue", "name": "PixelVue", "category": "Product Family"},
    {"path": "/art-immersive", "name": "Art & Immersive", "category": "Lifestyle"},
    {"path": "/luxury-home-cinema", "name": "Luxury Home Cinema", "category": "Lifestyle"},
    {"path": "/applications", "name": "Applications", "category": "Content"},
    {"path": "/knowledge", "name": "Knowledge Hub", "category": "Content"},
    {"path": "/knowledge/cob-vs-mip-vs-smd", "name": "COB vs MIP vs SMD", "category": "Content"},
    {"path": "/knowledge/pixel-pitch-guide", "name": "Pixel Pitch Guide", "category": "Content"},
    {"path": "/knowledge/brightness-nits-guide", "name": "Brightness Guide", "category": "Content"},
    {"path": "/knowledge/ip-rating-guide", "name": "IP Rating Guide", "category": "Content"},
    {"path": "/knowledge/refresh-rate-guide", "name": "Refresh Rate Guide", "category": "Content"},
    {"path": "/knowledge/processing-calibration", "name": "Processing & Calibration", "category": "Content"},
    {"path": "/knowledge/cms-multi-site", "name": "CMS Multi-Site", "category": "Content"},
    {"path": "/blog", "name": "Blog", "category": "Content"},
    {"path": "/case-studies", "name": "Case Studies", "category": "Content"},
    {"path": "/projects", "name": "Projects", "category": "Content"},
    {"path": "/inspirations", "name": "Inspirations", "category": "Content"},
    {"path": "/faq", "name": "FAQ", "category": "Other"},
    {"path": "/factory-tour", "name": "Factory Tour", "category": "Other"},
    {"path": "/for-architects", "name": "For Architects", "category": "Other"},
    {"path": "/design-assist", "name": "Design Assist", "category": "Other"},
    {"path": "/cpd-programme", "name": "CPD Programme", "category": "Other"},
    {"path": "/tech-guide", "name": "Tech Guide", "category": "Other"},
    {"path": "/budget-estimator", "name": "Budget Estimator", "category": "Other"},
    {"path": "/signage-solutions", "name": "Signage Solutions", "category": "Other"},
    {"path": "/indoor-led", "name": "Indoor LED", "category": "SEO Landing"},
    {"path": "/outdoor-led", "name": "Outdoor LED", "category": "SEO Landing"},
    {"path": "/led-screen-dubai", "name": "LED Screen Dubai", "category": "SEO Landing"},
    {"path": "/led-display-abu-dhabi", "name": "LED Display Abu Dhabi", "category": "SEO Landing"},
    {"path": "/led-screen-saudi-arabia", "name": "LED Screen Saudi Arabia", "category": "SEO Landing"},
    {"path": "/led-screen-qatar", "name": "LED Screen Qatar", "category": "SEO Landing"},
    {"path": "/led-screen-kuwait", "name": "LED Screen Kuwait", "category": "SEO Landing"},
    {"path": "/digital-experience", "name": "Digital Experience", "category": "Other"},
    {"path": "/latest-tech", "name": "Latest Technology", "category": "Content"},
    {"path": "/resource-library", "name": "Resource Library", "category": "Content"},
]


def compute_seo_score(data: dict) -> dict:
    """Compute SEO score (0-100) with per-field breakdown."""
    breakdown = {}
    title = data.get("meta_title", "") or ""
    desc = data.get("meta_description", "") or ""
    keywords = data.get("keywords", []) or []
    slug = data.get("path", "") or ""
    alt_text = data.get("image_alt", "") or ""

    # Title score (0-25): 50-60 chars is ideal
    tl = len(title)
    if tl == 0:
        breakdown["title"] = {"score": 0, "max": 25, "tip": "Missing meta title"}
    elif 50 <= tl <= 60:
        breakdown["title"] = {"score": 25, "max": 25, "tip": "Perfect length"}
    elif 40 <= tl <= 70:
        breakdown["title"] = {"score": 20, "max": 25, "tip": f"{tl} chars — aim for 50-60"}
    elif 20 <= tl < 40:
        breakdown["title"] = {"score": 12, "max": 25, "tip": "Too short — expand to 50-60 chars"}
    else:
        breakdown["title"] = {"score": 8, "max": 25, "tip": f"{tl} chars — too {'long' if tl > 70 else 'short'}"}

    # Description score (0-25): 150-160 chars is ideal
    dl = len(desc)
    if dl == 0:
        breakdown["description"] = {"score": 0, "max": 25, "tip": "Missing meta description"}
    elif 140 <= dl <= 160:
        breakdown["description"] = {"score": 25, "max": 25, "tip": "Perfect length"}
    elif 120 <= dl <= 170:
        breakdown["description"] = {"score": 20, "max": 25, "tip": f"{dl} chars — aim for 150-160"}
    elif 80 <= dl < 120:
        breakdown["description"] = {"score": 12, "max": 25, "tip": "Too short — expand to 150-160 chars"}
    else:
        breakdown["description"] = {"score": 8, "max": 25, "tip": f"{dl} chars — too {'long' if dl > 170 else 'short'}"}

    # Keywords score (0-20): 3-8 keywords is ideal
    kl = len(keywords)
    if kl == 0:
        breakdown["keywords"] = {"score": 0, "max": 20, "tip": "No keywords set"}
    elif 3 <= kl <= 8:
        breakdown["keywords"] = {"score": 20, "max": 20, "tip": f"{kl} keywords — good"}
    elif 1 <= kl < 3:
        breakdown["keywords"] = {"score": 10, "max": 20, "tip": "Add more keywords (3-8 recommended)"}
    else:
        breakdown["keywords"] = {"score": 14, "max": 20, "tip": f"{kl} keywords — consider trimming to top 8"}

    # URL slug score (0-15)
    if slug and "/" in slug:
        parts = slug.strip("/").split("/")
        last = parts[-1] if parts else ""
        if last and len(last) < 60 and "-" in last:
            breakdown["slug"] = {"score": 15, "max": 15, "tip": "Clean URL"}
        elif last and len(last) < 60:
            breakdown["slug"] = {"score": 12, "max": 15, "tip": "OK — consider adding hyphens"}
        else:
            breakdown["slug"] = {"score": 8, "max": 15, "tip": "Slug may be too long"}
    else:
        breakdown["slug"] = {"score": 10, "max": 15, "tip": "Root path"}

    # Image alt text (0-15)
    if alt_text and len(alt_text) > 10:
        breakdown["image_alt"] = {"score": 15, "max": 15, "tip": "Good alt text"}
    elif alt_text:
        breakdown["image_alt"] = {"score": 8, "max": 15, "tip": "Alt text too short — be descriptive"}
    else:
        breakdown["image_alt"] = {"score": 0, "max": 15, "tip": "Missing image alt text"}

    total = sum(v["score"] for v in breakdown.values())
    return {"score": total, "max": 100, "breakdown": breakdown}


def serialize(doc: dict) -> dict:
    if not doc:
        return None
    score_data = compute_seo_score(doc)
    return {
        "id": str(doc["_id"]),
        "path": doc.get("path", ""),
        "name": doc.get("name", ""),
        "category": doc.get("category", ""),
        "meta_title": doc.get("meta_title", ""),
        "meta_description": doc.get("meta_description", ""),
        "keywords": doc.get("keywords", []),
        "image_alt": doc.get("image_alt", ""),
        "og_title": doc.get("og_title", ""),
        "og_description": doc.get("og_description", ""),
        "canonical_url": doc.get("canonical_url", ""),
        "schema_type": doc.get("schema_type", "WebPage"),
        "noindex": doc.get("noindex", False),
        "score": score_data["score"],
        "score_breakdown": score_data["breakdown"],
        "updated_at": doc.get("updated_at", ""),
    }


# ─── PUBLIC ────────────────────────────────────────────────────────
@router.get("/api/seo/page-meta")
async def get_page_meta(path: str = "/"):
    """Public endpoint: get SEO meta for a page path."""
    doc = await col.find_one({"path": path})
    if not doc:
        return {"meta_title": "", "meta_description": "", "keywords": [], "image_alt": "", "og_title": "", "og_description": ""}
    return {
        "meta_title": doc.get("meta_title", ""),
        "meta_description": doc.get("meta_description", ""),
        "keywords": doc.get("keywords", []),
        "image_alt": doc.get("image_alt", ""),
        "og_title": doc.get("og_title", ""),
        "og_description": doc.get("og_description", ""),
        "canonical_url": doc.get("canonical_url", ""),
        "schema_type": doc.get("schema_type", "WebPage"),
        "noindex": doc.get("noindex", False),
    }


# ─── ADMIN ─────────────────────────────────────────────────────────
@router.post("/api/admin/seo/seed")
async def seed_pages(admin=Depends(get_current_admin)):
    """Initialize page_seo collection with all site pages."""
    count = 0
    for page in SITE_PAGES:
        existing = await col.find_one({"path": page["path"]})
        if not existing:
            await col.insert_one({
                "path": page["path"],
                "name": page["name"],
                "category": page.get("category", "Other"),
                "meta_title": "",
                "meta_description": "",
                "keywords": [],
                "image_alt": "",
                "og_title": "",
                "og_description": "",
                "canonical_url": "",
                "schema_type": "WebPage",
                "noindex": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            count += 1
    return {"seeded": count, "total_pages": len(SITE_PAGES)}


@router.get("/api/admin/seo/pages")
async def list_pages(admin=Depends(get_current_admin)):
    """List all pages with their SEO data and scores."""
    # Seed if empty
    total = await col.count_documents({})
    if total == 0:
        for page in SITE_PAGES:
            await col.insert_one({
                "path": page["path"],
                "name": page["name"],
                "category": page.get("category", "Other"),
                "meta_title": "", "meta_description": "", "keywords": [],
                "image_alt": "", "og_title": "", "og_description": "",
                "canonical_url": "", "schema_type": "WebPage", "noindex": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
    docs = await col.find({}, {"_id": 1, "path": 1, "name": 1, "category": 1, "meta_title": 1, "meta_description": 1, "keywords": 1, "image_alt": 1, "og_title": 1, "og_description": 1, "canonical_url": 1, "schema_type": 1, "noindex": 1, "updated_at": 1}).to_list(500)
    return [serialize(d) for d in docs if d]


@router.get("/api/admin/seo/pages/{page_id}")
async def get_page(page_id: str, admin=Depends(get_current_admin)):
    oid = parse_oid(page_id)
    doc = await col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Page not found")
    return serialize(doc)


class SEOUpdate(BaseModel):
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: Optional[List[str]] = None
    image_alt: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    canonical_url: Optional[str] = None
    schema_type: Optional[str] = None
    noindex: Optional[bool] = None


@router.put("/api/admin/seo/pages/{page_id}")
async def update_page(page_id: str, data: SEOUpdate, admin=Depends(get_current_admin)):
    from bson import ObjectId
    update = {k: v for k, v in data.dict().items() if v is not None}
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    await col.update_one({"_id": parse_oid(page_id)}, {"$set": update})
    clear_ssr_cache()
    doc = await col.find_one({"_id": parse_oid(page_id)})
    return serialize(doc)


class AIGenerateRequest(BaseModel):
    page_id: str
    fields: List[str] = ["meta_title", "meta_description", "keywords", "image_alt", "og_title", "og_description"]


@router.post("/api/admin/seo/ai-generate")
async def ai_generate_seo(req: AIGenerateRequest, admin=Depends(get_current_admin)):
    """AI-generate SEO content for a page using GPT-5.2."""
    from bson import ObjectId
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json as json_mod

    doc = await col.find_one({"_id": parse_oid(req.page_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Page not found")

    api_key = os.environ.get("EMERGENT_LLM_KEY", "")
    chat = LlmChat(
        api_key=api_key,
        session_id=f"seo-gen-{req.page_id}",
        system_message=(
            "You are an expert SEO specialist for Brightluxx, a premium LED display solutions company "
            "based in UAE serving the GCC region. Generate optimized SEO content that targets architects, "
            "contractors, and project managers. Focus on LED displays, digital signage, MicroLED, and "
            "related technology keywords relevant to the Middle East market. "
            "Always respond with valid JSON only, no markdown."
        ),
    ).with_model("openai", "gpt-5.2")

    page_name = doc.get("name", "")
    page_path = doc.get("path", "")
    page_category = doc.get("category", "")

    field_instructions = {
        "meta_title": "meta_title: 50-60 characters, include 'Brightluxx' brand and primary keyword",
        "meta_description": "meta_description: 150-160 characters, compelling with call-to-action, include location (UAE/Dubai)",
        "keywords": "keywords: Array of 5-7 relevant keyword strings, mix of short-tail and long-tail",
        "image_alt": "image_alt: Descriptive alt text (10-20 words) for the page hero image",
        "og_title": "og_title: Social-optimized title (55-60 chars), slightly different from meta_title",
        "og_description": "og_description: Social-optimized description (100-120 chars), engaging and shareable",
    }
    requested_instructions = "\n".join(f"- {field_instructions[f]}" for f in req.fields if f in field_instructions)

    prompt = (
        f"Generate SEO content for this page:\n"
        f"Page: {page_name}\nURL path: {page_path}\nCategory: {page_category}\n\n"
        f"Generate ONLY these fields (nothing else):\n{requested_instructions}\n\n"
        f"Return a JSON object with ONLY the requested field(s). No extra fields. No markdown, no code blocks."
    )

    response = await chat.send_message(UserMessage(text=prompt))

    # Parse the AI response
    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        generated = json_mod.loads(cleaned)
    except Exception:
        return {"error": "AI response parsing failed", "raw": response[:500]}

    # Update the DB with generated fields
    update = {}
    for field in req.fields:
        if field in generated:
            update[field] = generated[field]
    update["updated_at"] = datetime.now(timezone.utc).isoformat()

    await col.update_one({"_id": parse_oid(req.page_id)}, {"$set": update})
    updated_doc = await col.find_one({"_id": parse_oid(req.page_id)})
    return {"generated": generated, "page": serialize(updated_doc)}


class BulkAIRequest(BaseModel):
    page_ids: List[str]


@router.post("/api/admin/seo/ai-generate-bulk")
async def ai_generate_bulk(req: BulkAIRequest, admin=Depends(get_current_admin)):
    """AI-generate SEO for multiple pages."""
    results = []
    for pid in req.page_ids[:10]:  # Limit to 10 at a time
        try:
            single = AIGenerateRequest(page_id=pid)
            result = await ai_generate_seo(single, admin)
            results.append({"page_id": pid, "status": "ok" if "page" in result else "error"})
        except Exception as e:
            results.append({"page_id": pid, "status": "error", "message": str(e)})
    return {"results": results}


# ─── BULK GENERATE ALL MISSING ─────────────────────────────────────
bulk_job_col = db["seo_bulk_jobs"]


async def _run_bulk_generation(job_id: str):
    """Background coroutine: generate SEO for all pages missing meta_description or keywords."""
    import asyncio
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json as json_mod
    from bson import ObjectId

    api_key = os.environ.get("EMERGENT_LLM_KEY", "")

    # Find pages needing generation
    pages = await col.find({
        "$or": [
            {"meta_description": {"$in": ["", None]}},
            {"keywords": {"$in": [[], None]}},
            {"meta_title": {"$in": ["", None]}},
        ]
    }).to_list(500)

    total = len(pages)
    await bulk_job_col.update_one(
        {"job_id": job_id},
        {"$set": {"total": total, "status": "running"}},
    )

    succeeded = 0
    failed = 0

    for i, doc in enumerate(pages):
        try:
            page_id = str(doc["_id"])
            page_name = doc.get("name", "")
            page_path = doc.get("path", "")
            page_category = doc.get("category", "")

            # Determine which fields are missing
            fields_needed = []
            if not doc.get("meta_title"):
                fields_needed.append("meta_title")
            if not doc.get("meta_description"):
                fields_needed.append("meta_description")
            if not doc.get("keywords") or len(doc.get("keywords", [])) == 0:
                fields_needed.append("keywords")
            if not doc.get("image_alt"):
                fields_needed.append("image_alt")
            if not doc.get("og_title"):
                fields_needed.append("og_title")
            if not doc.get("og_description"):
                fields_needed.append("og_description")

            if not fields_needed:
                succeeded += 1
                continue

            chat = LlmChat(
                api_key=api_key,
                session_id=f"seo-bulk-{page_id}-{job_id[:8]}",
                system_message=(
                    "You are an expert SEO specialist for Brightluxx, a premium LED display solutions company "
                    "based in UAE serving the GCC region. Generate optimized SEO content that targets architects, "
                    "contractors, and project managers. Focus on LED displays, digital signage, MicroLED, and "
                    "related technology keywords relevant to the Middle East market. "
                    "Always respond with valid JSON only, no markdown."
                ),
            ).with_model("openai", "gpt-5.2")

            field_instructions = {
                "meta_title": "meta_title: 50-60 characters, include 'Brightluxx' brand and primary keyword",
                "meta_description": "meta_description: 150-160 characters, compelling with call-to-action, include location (UAE/Dubai)",
                "keywords": "keywords: Array of 5-7 relevant keyword strings, mix of short-tail and long-tail",
                "image_alt": "image_alt: Descriptive alt text (10-20 words) for the page hero image",
                "og_title": "og_title: Social-optimized title (55-60 chars), slightly different from meta_title",
                "og_description": "og_description: Social-optimized description (100-120 chars), engaging and shareable",
            }
            requested_instructions = "\n".join(f"- {field_instructions[f]}" for f in fields_needed if f in field_instructions)

            prompt = (
                f"Generate SEO content for this page:\n"
                f"Page: {page_name}\nURL path: {page_path}\nCategory: {page_category}\n\n"
                f"Generate ONLY these fields (nothing else):\n{requested_instructions}\n\n"
                f"Return a JSON object with ONLY the requested field(s). No extra fields. No markdown, no code blocks."
            )

            response = await chat.send_message(UserMessage(text=prompt))

            # Parse the AI response
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            generated = json_mod.loads(cleaned)

            # Update the DB
            update = {}
            for field in fields_needed:
                if field in generated:
                    update[field] = generated[field]
            if update:
                update["updated_at"] = datetime.now(timezone.utc).isoformat()
                await col.update_one({"_id": doc["_id"]}, {"$set": update})

            succeeded += 1
        except Exception as e:
            failed += 1

        # Update progress
        await bulk_job_col.update_one(
            {"job_id": job_id},
            {"$set": {"processed": i + 1, "succeeded": succeeded, "failed": failed}},
        )

        # Small delay to avoid rate limiting
        await asyncio.sleep(1)

    # Mark complete
    await bulk_job_col.update_one(
        {"job_id": job_id},
        {"$set": {"status": "completed", "processed": total, "succeeded": succeeded, "failed": failed, "completed_at": datetime.now(timezone.utc).isoformat()}},
    )


@router.post("/api/admin/seo/ai-generate-all-missing")
async def ai_generate_all_missing(admin=Depends(get_current_admin)):
    """Trigger bulk AI generation for all pages missing SEO content. Runs as background task."""
    from fastapi import BackgroundTasks
    import uuid as uuid_mod

    # Check if a job is already running (with 30-min timeout for stale jobs)
    running = await bulk_job_col.find_one({"status": "running"})
    if running:
        # Check if the job is stale (>30 minutes old)
        started = running.get("started_at", "")
        if started:
            from datetime import datetime as dt
            try:
                start_time = dt.fromisoformat(started.replace("Z", "+00:00"))
                if (datetime.now(timezone.utc) - start_time).total_seconds() > 1800:
                    await bulk_job_col.update_one(
                        {"job_id": running["job_id"]},
                        {"$set": {"status": "timed_out"}},
                    )
                else:
                    return {
                        "status": "already_running",
                        "job_id": running["job_id"],
                        "processed": running.get("processed", 0),
                        "total": running.get("total", 0),
                    }
            except Exception:
                pass
        else:
            return {
                "status": "already_running",
                "job_id": running["job_id"],
                "processed": running.get("processed", 0),
                "total": running.get("total", 0),
            }

    # Count pages needing work
    missing_count = await col.count_documents({
        "$or": [
            {"meta_description": {"$in": ["", None]}},
            {"keywords": {"$in": [[], None]}},
            {"meta_title": {"$in": ["", None]}},
        ]
    })

    if missing_count == 0:
        return {"status": "nothing_to_do", "message": "All pages already have SEO content"}

    job_id = str(uuid_mod.uuid4())[:12]
    await bulk_job_col.insert_one({
        "job_id": job_id,
        "status": "starting",
        "total": missing_count,
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
    })

    # Launch as asyncio task (runs in the event loop)
    asyncio.ensure_future(_run_bulk_generation(job_id))

    return {"status": "started", "job_id": job_id, "total_pages": missing_count}


@router.get("/api/admin/seo/bulk-job-status")
async def bulk_job_status(admin=Depends(get_current_admin)):
    """Check the status of the latest bulk generation job."""
    job = await bulk_job_col.find_one({}, sort=[("started_at", -1)])
    if not job:
        return {"status": "no_jobs"}
    return {
        "job_id": job.get("job_id"),
        "status": job.get("status"),
        "total": job.get("total", 0),
        "processed": job.get("processed", 0),
        "succeeded": job.get("succeeded", 0),
        "failed": job.get("failed", 0),
        "started_at": job.get("started_at", ""),
        "completed_at": job.get("completed_at", ""),
    }


@router.get("/api/admin/seo/stats")
async def seo_stats(admin=Depends(get_current_admin)):
    """Get overall SEO health stats."""
    docs = await col.find({}).to_list(500)
    total = len(docs)
    if total == 0:
        return {"total_pages": 0, "avg_score": 0, "optimized": 0, "needs_work": 0, "missing": 0}

    scores = []
    optimized = 0
    needs_work = 0
    missing = 0
    for d in docs:
        s = compute_seo_score(d)["score"]
        scores.append(s)
        if s >= 70:
            optimized += 1
        elif s >= 30:
            needs_work += 1
        else:
            missing += 1

    return {
        "total_pages": total,
        "avg_score": round(sum(scores) / total) if total else 0,
        "optimized": optimized,
        "needs_work": needs_work,
        "missing": missing,
    }
