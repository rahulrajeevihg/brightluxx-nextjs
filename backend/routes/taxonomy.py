"""
Taxonomy management - Categories and Sectors for Products, Inspirations, Projects.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
import uuid

from database import db
from auth import get_current_admin

router = APIRouter()

taxonomy_col = db["taxonomy"]


class TaxonomyCreate(BaseModel):
    type: str  # product_category, inspiration_category, project_sector
    value: str  # slug value
    label: str  # display label
    description: Optional[str] = None
    order: int = 0
    is_active: bool = True


class TaxonomyUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


# Public endpoints
@router.get("/api/taxonomy/{type}")
async def get_taxonomy(type: str):
    """Get all active taxonomy items of a type."""
    cursor = taxonomy_col.find(
        {"type": type, "is_active": True},
        {"_id": 0}
    ).sort("order", 1)
    items = await cursor.to_list(length=500)
    return {"items": items, "count": len(items)}


# Admin endpoints
@router.get("/api/admin/taxonomy")
async def admin_get_all_taxonomy(admin=Depends(get_current_admin)):
    """Get all taxonomy items grouped by type."""
    cursor = taxonomy_col.find({}, {"_id": 0}).sort([("type", 1), ("order", 1)])
    items = await cursor.to_list(length=1000)
    
    # Group by type
    grouped = {
        "product_category": [],
        "inspiration_category": [],
        "project_sector": [],
    }
    for item in items:
        if item["type"] in grouped:
            grouped[item["type"]].append(item)
    
    # Get counts from actual data
    products_col = db["products"]
    inspirations_col = db["inspirations"]
    projects_col = db["projects"]
    
    # Count products by category
    product_cats = await products_col.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]).to_list(length=500)
    product_cat_counts = {c["_id"]: c["count"] for c in product_cats if c["_id"]}
    
    # Count inspirations by category
    insp_cats = await inspirations_col.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]).to_list(length=500)
    insp_cat_counts = {c["_id"]: c["count"] for c in insp_cats if c["_id"]}
    
    # Count projects by sector
    proj_sectors = await projects_col.aggregate([
        {"$group": {"_id": "$sector", "count": {"$sum": 1}}}
    ]).to_list(length=500)
    proj_sector_counts = {s["_id"]: s["count"] for s in proj_sectors if s["_id"]}
    
    # Add counts to items
    for item in grouped["product_category"]:
        item["count"] = product_cat_counts.get(item["value"], 0)
    for item in grouped["inspiration_category"]:
        item["count"] = insp_cat_counts.get(item["value"], 0)
    for item in grouped["project_sector"]:
        item["count"] = proj_sector_counts.get(item["value"], 0)
    
    return {
        "taxonomy": grouped,
        "totals": {
            "product_category": len(grouped["product_category"]),
            "inspiration_category": len(grouped["inspiration_category"]),
            "project_sector": len(grouped["project_sector"]),
        }
    }


@router.post("/api/admin/taxonomy")
async def create_taxonomy(data: TaxonomyCreate, admin=Depends(get_current_admin)):
    """Create a new taxonomy item."""
    # Check if already exists
    existing = await taxonomy_col.find_one({"type": data.type, "value": data.value})
    if existing:
        raise HTTPException(status_code=400, detail="This item already exists")
    
    item_id = str(uuid.uuid4())[:12]
    item = {
        "id": item_id,
        "type": data.type,
        "value": data.value,
        "label": data.label,
        "description": data.description,
        "order": data.order,
        "is_active": data.is_active,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    
    await taxonomy_col.insert_one(item)
    return {"success": True, "item": {k: v for k, v in item.items() if k != "_id"}}


@router.put("/api/admin/taxonomy/{item_id}")
async def update_taxonomy(item_id: str, data: TaxonomyUpdate, admin=Depends(get_current_admin)):
    """Update a taxonomy item."""
    existing = await taxonomy_col.find_one({"id": item_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await taxonomy_col.update_one({"id": item_id}, {"$set": update_data})
    
    updated = await taxonomy_col.find_one({"id": item_id}, {"_id": 0})
    return {"success": True, "item": updated}


@router.delete("/api/admin/taxonomy/{item_id}")
async def delete_taxonomy(item_id: str, admin=Depends(get_current_admin)):
    """Delete a taxonomy item."""
    result = await taxonomy_col.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"success": True}


@router.post("/api/admin/taxonomy/sync")
async def sync_taxonomy(admin=Depends(get_current_admin)):
    """Sync taxonomy from existing data in products, inspirations, projects."""
    products_col = db["products"]
    inspirations_col = db["inspirations"]
    projects_col = db["projects"]
    
    synced = {"product_category": 0, "inspiration_category": 0, "project_sector": 0}
    now = datetime.now(timezone.utc)
    
    # Sync product categories
    product_cats = await products_col.distinct("category")
    for cat in product_cats:
        if cat and isinstance(cat, str):
            exists = await taxonomy_col.find_one({"type": "product_category", "value": cat})
            if not exists:
                await taxonomy_col.insert_one({
                    "id": str(uuid.uuid4())[:12],
                    "type": "product_category",
                    "value": cat,
                    "label": cat.replace("-", " ").title(),
                    "description": None,
                    "order": 0,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                })
                synced["product_category"] += 1
    
    # Sync inspiration categories
    insp_cats = await inspirations_col.distinct("category")
    for cat in insp_cats:
        if cat and isinstance(cat, str):
            exists = await taxonomy_col.find_one({"type": "inspiration_category", "value": cat})
            if not exists:
                await taxonomy_col.insert_one({
                    "id": str(uuid.uuid4())[:12],
                    "type": "inspiration_category",
                    "value": cat,
                    "label": cat.replace("-", " ").title(),
                    "description": None,
                    "order": 0,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                })
                synced["inspiration_category"] += 1
    
    # Sync project sectors
    proj_sectors = await projects_col.distinct("sector")
    for sector in proj_sectors:
        if sector and isinstance(sector, str):
            exists = await taxonomy_col.find_one({"type": "project_sector", "value": sector})
            if not exists:
                await taxonomy_col.insert_one({
                    "id": str(uuid.uuid4())[:12],
                    "type": "project_sector",
                    "value": sector,
                    "label": sector.replace("-", " ").title(),
                    "description": None,
                    "order": 0,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                })
                synced["project_sector"] += 1
    
    return {"success": True, "synced": synced}
