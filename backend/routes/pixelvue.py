"""
PixelVue Products API - Full CRUD for PixelVue LED Display Products
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from bson import ObjectId
import os

router = APIRouter(prefix="/api/pixelvue", tags=["pixelvue"])

# Import database
from database import db, id_query

# Pydantic Models
class QuickSpec(BaseModel):
    label: str
    value: str

class Feature(BaseModel):
    icon: str
    title: str
    desc: str

class Application(BaseModel):
    name: str
    desc: str

class Specification(BaseModel):
    label: str
    value: str

class FAQ(BaseModel):
    question: str
    answer: str

class PixelVueProductBase(BaseModel):
    name: str
    slug: str
    category: str  # poster, commercial, creative
    tagline: str
    description: str
    hero_image: str
    quick_specs: List[QuickSpec] = []
    features: List[Feature] = []
    applications: List[Application] = []
    specifications: List[Specification] = []
    faqs: List[FAQ] = []
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: bool = True
    order: int = 0

class PixelVueProductCreate(PixelVueProductBase):
    pass

class PixelVueProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    hero_image: Optional[str] = None
    quick_specs: Optional[List[QuickSpec]] = None
    features: Optional[List[Feature]] = None
    applications: Optional[List[Application]] = None
    specifications: Optional[List[Specification]] = None
    faqs: Optional[List[FAQ]] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None

class PixelVueProductResponse(PixelVueProductBase):
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

def serialize_product(product: dict) -> dict:
    """Convert MongoDB document to response format"""
    if not product:
        return None
    return {
        "id": str(product.get("_id", "")),
        "name": product.get("name", ""),
        "slug": product.get("slug", ""),
        "category": product.get("category", ""),
        "tagline": product.get("tagline", ""),
        "description": product.get("description", ""),
        "hero_image": product.get("hero_image", ""),
        "quick_specs": product.get("quick_specs", []),
        "features": product.get("features", []),
        "applications": product.get("applications", []),
        "specifications": product.get("specifications", []),
        "faqs": product.get("faqs", []),
        "seo_title": product.get("seo_title"),
        "seo_description": product.get("seo_description"),
        "is_active": product.get("is_active", True),
        "order": product.get("order", 0),
        "created_at": product.get("created_at", ""),
        "updated_at": product.get("updated_at", ""),
    }

# ============ PUBLIC ENDPOINTS ============

@router.get("/products", response_model=List[PixelVueProductResponse])
async def get_all_products(category: Optional[str] = None, active_only: bool = True):
    """Get all PixelVue products, optionally filtered by category"""
    # Using imported db
    query = {}
    if active_only:
        query["is_active"] = True
    if category:
        query["category"] = category
    
    products = await db.pixelvue_products.find(query).sort("order", 1).to_list(100)
    return [serialize_product(p) for p in products]

@router.get("/products/{slug}", response_model=PixelVueProductResponse)
async def get_product_by_slug(slug: str):
    """Get a single product by slug"""
    # Using imported db
    product = await db.pixelvue_products.find_one({"slug": slug})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_product(product)

@router.get("/categories")
async def get_categories():
    """Get all product categories with counts"""
    # Using imported db
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    results = await db.pixelvue_products.aggregate(pipeline).to_list(10)
    return [{"category": r["_id"], "count": r["count"]} for r in results]

# ============ ADMIN ENDPOINTS ============

@router.get("/admin/products", response_model=List[PixelVueProductResponse])
async def admin_get_all_products(category: Optional[str] = None):
    """Admin: Get all products including inactive"""
    # Using imported db
    query = {}
    if category:
        query["category"] = category
    products = await db.pixelvue_products.find(query).sort([("category", 1), ("order", 1)]).to_list(100)
    return [serialize_product(p) for p in products]

@router.post("/admin/products", response_model=PixelVueProductResponse)
async def create_product(product: PixelVueProductCreate):
    """Admin: Create a new product"""
    # Using imported db
    
    # Check for duplicate slug
    existing = await db.pixelvue_products.find_one({"slug": product.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Product with this slug already exists")
    
    now = datetime.now(timezone.utc).isoformat()
    product_dict = product.model_dump()
    product_dict["created_at"] = now
    product_dict["updated_at"] = now
    
    result = await db.pixelvue_products.insert_one(product_dict)
    created = await db.pixelvue_products.find_one({"_id": result.inserted_id})
    return serialize_product(created)

@router.put("/admin/products/{product_id}", response_model=PixelVueProductResponse)
async def update_product(product_id: str, product: PixelVueProductUpdate):
    """Admin: Update a product"""
    # Using imported db
    
    flt = id_query(product_id)
    existing = await db.pixelvue_products.find_one(flt)
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check for duplicate slug if slug is being changed
    update_data = {k: v for k, v in product.model_dump().items() if v is not None}
    if "slug" in update_data and update_data["slug"] != existing.get("slug"):
        slug_exists = await db.pixelvue_products.find_one({"slug": update_data["slug"], "_id": {"$nin": flt["_id"]["$in"]}})
        if slug_exists:
            raise HTTPException(status_code=400, detail="Product with this slug already exists")

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.pixelvue_products.update_one(flt, {"$set": update_data})
    updated = await db.pixelvue_products.find_one(flt)
    return serialize_product(updated)

@router.delete("/admin/products/{product_id}")
async def delete_product(product_id: str):
    """Admin: Delete a product"""
    # Using imported db
    
    result = await db.pixelvue_products.delete_one(id_query(product_id))
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Product deleted successfully"}

@router.post("/admin/products/{product_id}/toggle-active")
async def toggle_product_active(product_id: str):
    """Admin: Toggle product active status"""
    # Using imported db
    
    flt = id_query(product_id)
    product = await db.pixelvue_products.find_one(flt)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_status = not product.get("is_active", True)
    await db.pixelvue_products.update_one(
        flt,
        {"$set": {"is_active": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"is_active": new_status}

@router.post("/admin/products/reorder")
async def reorder_products(product_orders: List[dict]):
    """Admin: Reorder products (expects list of {id, order})"""
    # Using imported db
    
    for item in product_orders:
        try:
            await db.pixelvue_products.update_one(
                id_query(item["id"]),
                {"$set": {"order": item["order"]}}
            )
        except Exception:
            continue
    
    return {"message": "Products reordered successfully"}
