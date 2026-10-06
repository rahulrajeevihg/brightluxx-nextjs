"""
Site Content API - Full CRUD for Static Page Content (About, FAQ, CPD, etc.)
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, Any
from pydantic import BaseModel
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter(prefix="/api/site-content", tags=["site-content"])

# Import database
from database import db

# Pydantic Models
class SiteContentBase(BaseModel):
    page_slug: str  # about, faq, cpd, contact, services, etc.
    title: str
    content: dict  # Flexible JSON structure for page-specific content
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: bool = True

class SiteContentCreate(SiteContentBase):
    pass

class SiteContentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[dict] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: Optional[bool] = None

def serialize_content(content: dict) -> dict:
    if not content:
        return None
    return {
        "id": str(content.get("_id", "")),
        "page_slug": content.get("page_slug", ""),
        "title": content.get("title", ""),
        "content": content.get("content", {}),
        "seo_title": content.get("seo_title"),
        "seo_description": content.get("seo_description"),
        "is_active": content.get("is_active", True),
        "created_at": content.get("created_at", ""),
        "updated_at": content.get("updated_at", ""),
    }

# ============ PUBLIC ENDPOINTS ============

@router.get("/{page_slug}")
async def get_page_content(page_slug: str):
    """Get content for a specific page by slug"""
    # Using imported db
    content = await db.site_content.find_one({"page_slug": page_slug, "is_active": True})
    if not content:
        raise HTTPException(status_code=404, detail="Page content not found")
    return serialize_content(content)

@router.get("")
async def get_all_page_content(active_only: bool = True):
    """Get all page content"""
    # Using imported db
    query = {"is_active": True} if active_only else {}
    contents = await db.site_content.find(query).sort("page_slug", 1).to_list(100)
    return [serialize_content(c) for c in contents]

# ============ ADMIN ENDPOINTS ============

@router.get("/admin/all")
async def admin_get_all_content():
    """Admin: Get all page content including inactive"""
    # Using imported db
    contents = await db.site_content.find({}).sort("page_slug", 1).to_list(100)
    return [serialize_content(c) for c in contents]

@router.post("/admin/create")
async def create_page_content(content: SiteContentCreate):
    """Admin: Create new page content"""
    # Using imported db
    
    existing = await db.site_content.find_one({"page_slug": content.page_slug})
    if existing:
        raise HTTPException(status_code=400, detail="Page content with this slug already exists")
    
    now = datetime.now(timezone.utc).isoformat()
    content_dict = content.model_dump()
    content_dict["created_at"] = now
    content_dict["updated_at"] = now
    
    result = await db.site_content.insert_one(content_dict)
    created = await db.site_content.find_one({"_id": result.inserted_id})
    return serialize_content(created)

@router.put("/admin/{page_slug}")
async def update_page_content(page_slug: str, content: SiteContentUpdate):
    """Admin: Update page content by slug"""
    # Using imported db
    
    existing = await db.site_content.find_one({"page_slug": page_slug})
    if not existing:
        raise HTTPException(status_code=404, detail="Page content not found")
    
    update_data = {k: v for k, v in content.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.site_content.update_one({"page_slug": page_slug}, {"$set": update_data})
    updated = await db.site_content.find_one({"page_slug": page_slug})
    return serialize_content(updated)

@router.delete("/admin/{page_slug}")
async def delete_page_content(page_slug: str):
    """Admin: Delete page content"""
    # Using imported db
    
    result = await db.site_content.delete_one({"page_slug": page_slug})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Page content not found")
    
    return {"message": "Page content deleted successfully"}

@router.post("/admin/{page_slug}/toggle-active")
async def toggle_content_active(page_slug: str):
    """Admin: Toggle page content active status"""
    # Using imported db
    
    content = await db.site_content.find_one({"page_slug": page_slug})
    if not content:
        raise HTTPException(status_code=404, detail="Page content not found")
    
    new_status = not content.get("is_active", True)
    await db.site_content.update_one(
        {"page_slug": page_slug},
        {"$set": {"is_active": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"is_active": new_status}

# ============ UPSERT ENDPOINT (Create or Update) ============

@router.post("/admin/upsert")
async def upsert_page_content(content: SiteContentCreate):
    """Admin: Create or update page content"""
    # Using imported db
    
    now = datetime.now(timezone.utc).isoformat()
    existing = await db.site_content.find_one({"page_slug": content.page_slug})
    
    if existing:
        # Update
        update_data = content.model_dump()
        update_data["updated_at"] = now
        await db.site_content.update_one({"page_slug": content.page_slug}, {"$set": update_data})
        updated = await db.site_content.find_one({"page_slug": content.page_slug})
        return serialize_content(updated)
    else:
        # Create
        content_dict = content.model_dump()
        content_dict["created_at"] = now
        content_dict["updated_at"] = now
        result = await db.site_content.insert_one(content_dict)
        created = await db.site_content.find_one({"_id": result.inserted_id})
        return serialize_content(created)
