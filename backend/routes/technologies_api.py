"""
Technologies API - Full CRUD for LED Technologies
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter(prefix="/api/technologies", tags=["technologies"])

# Import database
from database import db, id_query

# Pydantic Models
class TechSpec(BaseModel):
    label: str
    value: str
    description: Optional[str] = None

class TechApplication(BaseModel):
    name: str
    description: str
    icon: Optional[str] = None

class TechnologyBase(BaseModel):
    name: str
    slug: str
    tagline: str
    description: str
    hero_image: str
    icon: str
    color: str  # Brand color for the technology
    overview: str
    specs: List[TechSpec] = []
    key_features: List[str] = []
    applications: List[TechApplication] = []
    advantages: List[str] = []
    considerations: List[str] = []
    faqs: List[dict] = []
    related_products: List[str] = []
    related_technologies: List[str] = []
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: bool = True
    order: int = 0

class TechnologyCreate(TechnologyBase):
    pass

class TechnologyUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    hero_image: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    overview: Optional[str] = None
    specs: Optional[List[TechSpec]] = None
    key_features: Optional[List[str]] = None
    applications: Optional[List[TechApplication]] = None
    advantages: Optional[List[str]] = None
    considerations: Optional[List[str]] = None
    faqs: Optional[List[dict]] = None
    related_products: Optional[List[str]] = None
    related_technologies: Optional[List[str]] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None

def serialize_technology(tech: dict) -> dict:
    if not tech:
        return None
    return {
        "id": str(tech.get("_id", "")),
        "name": tech.get("name", ""),
        "slug": tech.get("slug", ""),
        "tagline": tech.get("tagline", ""),
        "description": tech.get("description", ""),
        "hero_image": tech.get("hero_image", ""),
        "icon": tech.get("icon", ""),
        "color": tech.get("color", "cyan"),
        "overview": tech.get("overview", ""),
        "specs": tech.get("specs", []),
        "key_features": tech.get("key_features", []),
        "applications": tech.get("applications", []),
        "advantages": tech.get("advantages", []),
        "considerations": tech.get("considerations", []),
        "faqs": tech.get("faqs", []),
        "related_products": tech.get("related_products", []),
        "related_technologies": tech.get("related_technologies", []),
        "seo_title": tech.get("seo_title"),
        "seo_description": tech.get("seo_description"),
        "is_active": tech.get("is_active", True),
        "order": tech.get("order", 0),
        "created_at": tech.get("created_at", ""),
        "updated_at": tech.get("updated_at", ""),
    }

# ============ PUBLIC ENDPOINTS ============

@router.get("")
async def get_all_technologies(active_only: bool = True):
    """Get all technologies"""
    # Using imported db
    query = {"is_active": True} if active_only else {}
    technologies = await db.technologies_content.find(query).sort("order", 1).to_list(50)
    return [serialize_technology(t) for t in technologies]

@router.get("/{slug}")
async def get_technology_by_slug(slug: str):
    """Get a single technology by slug"""
    # Using imported db
    technology = await db.technologies_content.find_one({"slug": slug})
    if not technology:
        raise HTTPException(status_code=404, detail="Technology not found")
    return serialize_technology(technology)

# ============ ADMIN ENDPOINTS ============

@router.get("/admin/all")
async def admin_get_all_technologies():
    """Admin: Get all technologies including inactive"""
    # Using imported db
    technologies = await db.technologies_content.find({}).sort("order", 1).to_list(50)
    return [serialize_technology(t) for t in technologies]

@router.post("/admin/create")
async def create_technology(technology: TechnologyCreate):
    """Admin: Create a new technology"""
    # Using imported db
    
    existing = await db.technologies_content.find_one({"slug": technology.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Technology with this slug already exists")
    
    now = datetime.now(timezone.utc).isoformat()
    tech_dict = technology.model_dump()
    tech_dict["created_at"] = now
    tech_dict["updated_at"] = now
    
    result = await db.technologies_content.insert_one(tech_dict)
    created = await db.technologies_content.find_one({"_id": result.inserted_id})
    return serialize_technology(created)

@router.put("/admin/{technology_id}")
async def update_technology(technology_id: str, technology: TechnologyUpdate):
    """Admin: Update a technology"""
    # Using imported db
    
    flt = id_query(technology_id)
    existing = await db.technologies_content.find_one(flt)
    if not existing:
        raise HTTPException(status_code=404, detail="Technology not found")

    update_data = {k: v for k, v in technology.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.technologies_content.update_one(flt, {"$set": update_data})
    updated = await db.technologies_content.find_one(flt)
    return serialize_technology(updated)

@router.delete("/admin/{technology_id}")
async def delete_technology(technology_id: str):
    """Admin: Delete a technology"""
    # Using imported db
    
    result = await db.technologies_content.delete_one(id_query(technology_id))
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Technology not found")

    return {"message": "Technology deleted successfully"}

@router.post("/admin/{technology_id}/toggle-active")
async def toggle_technology_active(technology_id: str):
    """Admin: Toggle technology active status"""
    # Using imported db
    
    flt = id_query(technology_id)
    technology = await db.technologies_content.find_one(flt)
    if not technology:
        raise HTTPException(status_code=404, detail="Technology not found")

    new_status = not technology.get("is_active", True)
    await db.technologies_content.update_one(
        flt,
        {"$set": {"is_active": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"is_active": new_status}
