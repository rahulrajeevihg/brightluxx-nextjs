"""
Prerender API — Serves heading hierarchy data for crawler pre-rendering.
"""
from fastapi import APIRouter
from database import db

router = APIRouter(tags=["Prerender"])
seo_col = db["page_seo"]


@router.get("/api/prerender/headings")
async def get_headings(path: str = "/"):
    """Return the heading hierarchy for a given page path."""
    doc = await seo_col.find_one({"path": path}, {"_id": 0, "headings": 1, "name": 1})
    if doc and doc.get("headings"):
        return doc["headings"]
    # Fallback: return a basic H1 from the page name
    if doc and doc.get("name"):
        return [{"tag": "h1", "text": doc["name"]}]
    return []


@router.get("/api/prerender/page")
async def get_prerender_data(path: str = "/"):
    """Return full prerender data (headings + SEO meta) for a page."""
    doc = await seo_col.find_one({"path": path}, {"_id": 0})
    if not doc:
        return {"headings": [], "meta": {}}
    return {
        "headings": doc.get("headings", []),
        "meta": {
            "title": doc.get("meta_title", ""),
            "description": doc.get("meta_description", ""),
            "keywords": doc.get("keywords", []),
            "og_title": doc.get("og_title", ""),
            "og_description": doc.get("og_description", ""),
            "image_alt": doc.get("image_alt", ""),
            "canonical_url": doc.get("canonical_url", ""),
            "schema_type": doc.get("schema_type", "WebPage"),
            "noindex": doc.get("noindex", False),
        },
    }
