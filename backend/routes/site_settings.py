"""Site Settings API — CRUD for site-wide configuration."""
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from database import db

router = APIRouter()
col = db["site_settings"]

DEFAULTS = {
    "key": "main",
    "branding": {
        "logo_url": "/assets/brightluxx-logo-dark.png",
        "favicon_url": "/favicon.ico",
        "company_name": "Brightluxx",
        "tagline": "Premium LED Display Solutions",
        "established_year": "2005",
    },
    "contact": {
        "phone": "+971 4 258 5754",
        "email": "sales@brightluxx.com",
        "whatsapp": "+971559954274",
        "address": "Jebel Ali Industrial Area 1, Dubai, UAE",
    },
    "social": {
        "instagram": "https://www.instagram.com/brightluxx/",
        "facebook": "https://www.facebook.com/brightluxx/",
        "linkedin": "https://www.linkedin.com/company/brightluxx/",
        "youtube": "https://www.youtube.com/@brightluxx",
        "twitter": "",
        "tiktok": "",
    },
    "embeds": {
        "google_map": "",
    },
    "seo": {
        "meta_title": "Brightluxx — Premium LED Display Solutions",
        "meta_description": "Leading LED display manufacturer & supplier in the GCC. Indoor, outdoor, creative, and transparent LED solutions for architects & contractors.",
        "og_image": "",
    },
}


class SiteSettings(BaseModel):
    branding: Optional[dict] = None
    contact: Optional[dict] = None
    social: Optional[dict] = None
    embeds: Optional[dict] = None
    seo: Optional[dict] = None


@router.get("/api/site-settings")
async def get_site_settings():
    doc = await col.find_one({"key": "main"}, {"_id": 0})
    if not doc:
        await col.insert_one(DEFAULTS.copy())
        doc = {k: v for k, v in DEFAULTS.items() if k != "_id"}
    doc.pop("_id", None)
    doc.pop("key", None)
    return doc


@router.put("/api/site-settings")
async def update_site_settings(settings: SiteSettings):
    update = {}
    for field in ["branding", "contact", "social", "embeds", "seo"]:
        val = getattr(settings, field, None)
        if val is not None:
            update[field] = val

    if not update:
        return {"success": True}

    existing = await col.find_one({"key": "main"})
    if not existing:
        full = DEFAULTS.copy()
        full.update(update)
        await col.insert_one(full)
    else:
        await col.update_one({"key": "main"}, {"$set": update})

    doc = await col.find_one({"key": "main"}, {"_id": 0, "key": 0})
    return {"success": True, "settings": doc}



DEFAULT_OG_IMAGE = "https://files.ihgbrands.com/assets_brightluxx-logo-nav.png"

@router.get("/api/og-image")
async def get_og_image():
    """Redirect to the current OG image. Used by social crawlers."""
    doc = await col.find_one({"key": "main"}, {"_id": 0})
    og_url = (doc or {}).get("seo", {}).get("og_image", "") or DEFAULT_OG_IMAGE
    return RedirectResponse(url=og_url, status_code=302)
