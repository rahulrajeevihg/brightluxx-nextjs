"""
Applications/Industries API - Full CRUD for Industry Applications
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter(prefix="/api/applications", tags=["applications"])

# Import database
from database import db, id_query

# Pydantic Models
class UseCase(BaseModel):
    title: str
    description: str
    image: Optional[str] = None

class Benefit(BaseModel):
    title: str
    description: str
    icon: Optional[str] = None

class ApplicationBase(BaseModel):
    name: str
    slug: str
    tagline: str
    description: str
    hero_image: str
    icon: str
    color: str
    overview: str
    use_cases: List[UseCase] = []
    benefits: List[Benefit] = []
    key_features: List[str] = []
    recommended_products: List[dict] = []  # {name, slug, family}
    case_study_ids: List[str] = []  # Reference to case studies
    gallery: List[str] = []  # Image URLs
    faqs: List[dict] = []
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: bool = True
    order: int = 0

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    hero_image: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    overview: Optional[str] = None
    use_cases: Optional[List[UseCase]] = None
    benefits: Optional[List[Benefit]] = None
    key_features: Optional[List[str]] = None
    recommended_products: Optional[List[dict]] = None
    case_study_ids: Optional[List[str]] = None
    gallery: Optional[List[str]] = None
    faqs: Optional[List[dict]] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None

def serialize_application(app: dict) -> dict:
    if not app:
        return None
    return {
        "id": str(app.get("_id", "")),
        "name": app.get("name", ""),
        "slug": app.get("slug", ""),
        "tagline": app.get("tagline", ""),
        "description": app.get("description", ""),
        "hero_image": app.get("hero_image", ""),
        "icon": app.get("icon", ""),
        "color": app.get("color", "blue"),
        "overview": app.get("overview", ""),
        "use_cases": app.get("use_cases", []),
        "benefits": app.get("benefits", []),
        "key_features": app.get("key_features", []),
        "recommended_products": app.get("recommended_products", []),
        "case_study_ids": app.get("case_study_ids", []),
        "gallery": app.get("gallery", []),
        "faqs": app.get("faqs", []),
        "seo_title": app.get("seo_title"),
        "seo_description": app.get("seo_description"),
        "is_active": app.get("is_active", True),
        "order": app.get("order", 0),
        "created_at": app.get("created_at", ""),
        "updated_at": app.get("updated_at", ""),
    }

# ============ PUBLIC ENDPOINTS ============

@router.get("")
async def get_all_applications(active_only: bool = True):
    """Get all industry applications"""
    # Using imported db
    query = {"is_active": True} if active_only else {}
    applications = await db.applications_content.find(query).sort("order", 1).to_list(50)
    return [serialize_application(a) for a in applications]

@router.get("/{slug}")
async def get_application_by_slug(slug: str):
    """Get a single application by slug"""
    # Using imported db
    application = await db.applications_content.find_one({"slug": slug})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return serialize_application(application)

# ============ ADMIN ENDPOINTS ============

@router.get("/admin/all")
async def admin_get_all_applications():
    """Admin: Get all applications including inactive"""
    # Using imported db
    applications = await db.applications_content.find({}).sort("order", 1).to_list(50)
    return [serialize_application(a) for a in applications]

@router.post("/admin/create")
async def create_application(application: ApplicationCreate):
    """Admin: Create a new application"""
    # Using imported db
    
    existing = await db.applications_content.find_one({"slug": application.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Application with this slug already exists")
    
    now = datetime.now(timezone.utc).isoformat()
    app_dict = application.model_dump()
    app_dict["created_at"] = now
    app_dict["updated_at"] = now
    
    result = await db.applications_content.insert_one(app_dict)
    created = await db.applications_content.find_one({"_id": result.inserted_id})
    return serialize_application(created)

@router.put("/admin/{application_id}")
async def update_application(application_id: str, application: ApplicationUpdate):
    """Admin: Update an application"""
    # Using imported db
    
    flt = id_query(application_id)
    existing = await db.applications_content.find_one(flt)
    if not existing:
        raise HTTPException(status_code=404, detail="Application not found")

    update_data = {k: v for k, v in application.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.applications_content.update_one(flt, {"$set": update_data})
    updated = await db.applications_content.find_one(flt)
    return serialize_application(updated)

@router.delete("/admin/{application_id}")
async def delete_application(application_id: str):
    """Admin: Delete an application"""
    # Using imported db
    
    result = await db.applications_content.delete_one(id_query(application_id))
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")

    return {"message": "Application deleted successfully"}

@router.post("/admin/{application_id}/toggle-active")
async def toggle_application_active(application_id: str):
    """Admin: Toggle application active status"""
    # Using imported db
    
    flt = id_query(application_id)
    application = await db.applications_content.find_one(flt)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    new_status = not application.get("is_active", True)
    await db.applications_content.update_one(
        flt,
        {"$set": {"is_active": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"is_active": new_status}
