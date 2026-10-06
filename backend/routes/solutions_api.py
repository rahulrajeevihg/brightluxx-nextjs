"""
Solutions API - Full CRUD for Solutions/Industries
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter(prefix="/api/solutions", tags=["solutions"])

# Import database
from database import db, id_query

# Pydantic Models
class Feature(BaseModel):
    title: str
    description: str
    icon: Optional[str] = None

class Benefit(BaseModel):
    title: str
    description: str

class SolutionBase(BaseModel):
    title: str
    slug: str
    tagline: str
    description: str
    icon: str
    hero_image: str
    features: List[Feature] = []
    benefits: List[Benefit] = []
    use_cases: List[str] = []
    related_products: List[str] = []
    related_technologies: List[str] = []
    stats: List[dict] = []
    faqs: List[dict] = []
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: bool = True
    order: int = 0

class SolutionCreate(SolutionBase):
    pass

class SolutionUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    hero_image: Optional[str] = None
    features: Optional[List[Feature]] = None
    benefits: Optional[List[Benefit]] = None
    use_cases: Optional[List[str]] = None
    related_products: Optional[List[str]] = None
    related_technologies: Optional[List[str]] = None
    stats: Optional[List[dict]] = None
    faqs: Optional[List[dict]] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None

def serialize_solution(solution: dict) -> dict:
    if not solution:
        return None
    return {
        "id": str(solution.get("_id", "")),
        "title": solution.get("title", ""),
        "slug": solution.get("slug", ""),
        "tagline": solution.get("tagline", ""),
        "description": solution.get("description", ""),
        "icon": solution.get("icon", ""),
        "hero_image": solution.get("hero_image", ""),
        "features": solution.get("features", []),
        "benefits": solution.get("benefits", []),
        "use_cases": solution.get("use_cases", []),
        "related_products": solution.get("related_products", []),
        "related_technologies": solution.get("related_technologies", []),
        "stats": solution.get("stats", []),
        "faqs": solution.get("faqs", []),
        "seo_title": solution.get("seo_title"),
        "seo_description": solution.get("seo_description"),
        "is_active": solution.get("is_active", True),
        "order": solution.get("order", 0),
        "created_at": solution.get("created_at", ""),
        "updated_at": solution.get("updated_at", ""),
    }

# ============ PUBLIC ENDPOINTS ============

@router.get("")
async def get_all_solutions(active_only: bool = True):
    """Get all solutions"""
    # Using imported db
    query = {"is_active": True} if active_only else {}
    solutions = await db.solutions.find(query).sort("order", 1).to_list(50)
    return [serialize_solution(s) for s in solutions]

@router.get("/{slug}")
async def get_solution_by_slug(slug: str):
    """Get a single solution by slug"""
    # Using imported db
    solution = await db.solutions.find_one({"slug": slug})
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")
    return serialize_solution(solution)

# ============ ADMIN ENDPOINTS ============

@router.get("/admin/all")
async def admin_get_all_solutions():
    """Admin: Get all solutions including inactive"""
    # Using imported db
    solutions = await db.solutions.find({}).sort("order", 1).to_list(50)
    return [serialize_solution(s) for s in solutions]

@router.post("/admin/create")
async def create_solution(solution: SolutionCreate):
    """Admin: Create a new solution"""
    # Using imported db
    
    existing = await db.solutions.find_one({"slug": solution.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Solution with this slug already exists")
    
    now = datetime.now(timezone.utc).isoformat()
    solution_dict = solution.model_dump()
    solution_dict["created_at"] = now
    solution_dict["updated_at"] = now
    
    result = await db.solutions.insert_one(solution_dict)
    created = await db.solutions.find_one({"_id": result.inserted_id})
    return serialize_solution(created)

@router.put("/admin/{solution_id}")
async def update_solution(solution_id: str, solution: SolutionUpdate):
    """Admin: Update a solution"""
    # Using imported db
    
    flt = id_query(solution_id)
    existing = await db.solutions.find_one(flt)
    if not existing:
        raise HTTPException(status_code=404, detail="Solution not found")

    update_data = {k: v for k, v in solution.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.solutions.update_one(flt, {"$set": update_data})
    updated = await db.solutions.find_one(flt)
    return serialize_solution(updated)

@router.delete("/admin/{solution_id}")
async def delete_solution(solution_id: str):
    """Admin: Delete a solution"""
    # Using imported db
    
    result = await db.solutions.delete_one(id_query(solution_id))
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Solution not found")

    return {"message": "Solution deleted successfully"}

@router.post("/admin/{solution_id}/toggle-active")
async def toggle_solution_active(solution_id: str):
    """Admin: Toggle solution active status"""
    # Using imported db
    
    flt = id_query(solution_id)
    solution = await db.solutions.find_one(flt)
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    new_status = not solution.get("is_active", True)
    await db.solutions.update_one(
        flt,
        {"$set": {"is_active": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"is_active": new_status}
