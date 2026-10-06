"""
Product Families API - Full CRUD for Product Family Landing Pages
(LumiMorph, NaturaTex, SignaTouch, GlassMorph, PixelVue)
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter(prefix="/api/product-families", tags=["product-families"])

# Import database
from database import db, id_query

# Pydantic Models
class Stat(BaseModel):
    value: str
    label: str

class ProductItem(BaseModel):
    name: str
    slug: str
    description: str
    image: str
    category: Optional[str] = None

class ProductFamilyBase(BaseModel):
    name: str
    slug: str  # lumimorph, naturatex, signatouch, glassmorph, pixelvue
    tagline: str
    description: str
    hero_image: str
    hero_video: Optional[str] = None
    brand_color: str  # Primary brand color (hex or tailwind class)
    accent_color: Optional[str] = None
    stats: List[Stat] = []
    overview: str
    key_features: List[str] = []
    products: List[ProductItem] = []  # Products within this family
    categories: List[dict] = []  # Product categories within family
    use_cases: List[str] = []
    gallery: List[str] = []
    faqs: List[dict] = []
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: bool = True
    order: int = 0

class ProductFamilyCreate(ProductFamilyBase):
    pass

class ProductFamilyUpdate(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    hero_image: Optional[str] = None
    hero_video: Optional[str] = None
    brand_color: Optional[str] = None
    accent_color: Optional[str] = None
    stats: Optional[List[Stat]] = None
    overview: Optional[str] = None
    key_features: Optional[List[str]] = None
    products: Optional[List[ProductItem]] = None
    categories: Optional[List[dict]] = None
    use_cases: Optional[List[str]] = None
    gallery: Optional[List[str]] = None
    faqs: Optional[List[dict]] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None

# Fallback hero images for when DB values are empty or broken
HERO_IMAGE_FALLBACKS = {
    'lumimorph': 'https://files.ihgbrands.com/homepage_grande-hero.webp',
    'naturatex': 'https://files.ihgbrands.com/emergent-images/ea77d4dd0e99bf17d39a28af7bcce5ed3db13b59241d32385de3a59cf9952a29.png',
    'signatouch': 'https://files.ihgbrands.com/emergent-images/f7ad6c93eff45321279f7b8912a259cd14afd89d426a4ecb8c8a049055ac5a98.png',
    'glassmorph': 'https://files.ihgbrands.com/emergent-images/64444ed7ca157e07ab9eeea06f1bb969e8744dbda982442ba235f506fd348b48.png',
    'pixelvue': 'https://files.ihgbrands.com/emergent-images/127b54193b9ab0ec636c8645560811771af1f58dde5daceea69f261828cf7c0a.png',
}

def serialize_family(family: dict) -> dict:
    if not family:
        return None
    slug = family.get("slug", "")
    hero_image = family.get("hero_image", "")
    if not hero_image:
        hero_image = HERO_IMAGE_FALLBACKS.get(slug, "")
    return {
        "id": str(family.get("_id", "")),
        "name": family.get("name", ""),
        "slug": slug,
        "tagline": family.get("tagline", ""),
        "description": family.get("description", ""),
        "hero_image": hero_image,
        "hero_video": family.get("hero_video"),
        "brand_color": family.get("brand_color", "rose"),
        "accent_color": family.get("accent_color"),
        "stats": family.get("stats", []),
        "overview": family.get("overview", ""),
        "key_features": family.get("key_features", []),
        "products": family.get("products", []),
        "categories": family.get("categories", []),
        "use_cases": family.get("use_cases", []),
        "gallery": family.get("gallery", []),
        "faqs": family.get("faqs", []),
        "seo_title": family.get("seo_title"),
        "seo_description": family.get("seo_description"),
        "is_active": family.get("is_active", True),
        "order": family.get("order", 0),
        "created_at": family.get("created_at", ""),
        "updated_at": family.get("updated_at", ""),
    }

# ============ PUBLIC ENDPOINTS ============

@router.get("")
async def get_all_families(active_only: bool = True):
    """Get all product families"""
    # Using imported db
    query = {"is_active": True} if active_only else {}
    families = await db.product_families.find(query).sort("order", 1).to_list(20)
    return [serialize_family(f) for f in families]

@router.get("/{slug}")
async def get_family_by_slug(slug: str):
    """Get a single product family by slug"""
    # Using imported db
    family = await db.product_families.find_one({"slug": slug})
    if not family:
        raise HTTPException(status_code=404, detail="Product family not found")
    return serialize_family(family)

# ============ ADMIN ENDPOINTS ============

@router.get("/admin/all")
async def admin_get_all_families():
    """Admin: Get all product families including inactive"""
    # Using imported db
    families = await db.product_families.find({}).sort("order", 1).to_list(20)
    return [serialize_family(f) for f in families]

@router.post("/admin/create")
async def create_family(family: ProductFamilyCreate):
    """Admin: Create a new product family"""
    # Using imported db
    
    existing = await db.product_families.find_one({"slug": family.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Product family with this slug already exists")
    
    now = datetime.now(timezone.utc).isoformat()
    family_dict = family.model_dump()
    family_dict["created_at"] = now
    family_dict["updated_at"] = now
    
    result = await db.product_families.insert_one(family_dict)
    created = await db.product_families.find_one({"_id": result.inserted_id})
    return serialize_family(created)

@router.put("/admin/{family_id}")
async def update_family(family_id: str, family: ProductFamilyUpdate):
    """Admin: Update a product family"""
    # Using imported db
    
    flt = id_query(family_id)
    existing = await db.product_families.find_one(flt)
    if not existing:
        raise HTTPException(status_code=404, detail="Product family not found")

    update_data = {k: v for k, v in family.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.product_families.update_one(flt, {"$set": update_data})
    updated = await db.product_families.find_one(flt)
    return serialize_family(updated)

@router.delete("/admin/{family_id}")
async def delete_family(family_id: str):
    """Admin: Delete a product family"""
    # Using imported db
    
    result = await db.product_families.delete_one(id_query(family_id))
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product family not found")

    return {"message": "Product family deleted successfully"}

@router.post("/admin/{family_id}/toggle-active")
async def toggle_family_active(family_id: str):
    """Admin: Toggle product family active status"""
    # Using imported db
    
    flt = id_query(family_id)
    family = await db.product_families.find_one(flt)
    if not family:
        raise HTTPException(status_code=404, detail="Product family not found")

    new_status = not family.get("is_active", True)
    await db.product_families.update_one(
        flt,
        {"$set": {"is_active": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"is_active": new_status}
