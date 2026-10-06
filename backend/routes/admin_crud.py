from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from database import products_col, inspirations_col, projects_col, leads_col
from models import AdminProductCreate, AdminProductUpdate, AdminInspirationCreate, AdminProjectCreate
from utils import serialize_doc, slugify
from auth import get_current_admin
from routes.ssr_meta import clear_ssr_cache

router = APIRouter()


# --- Products CRUD ---

@router.get("/api/admin/products")
async def admin_get_products(category: Optional[str] = None, search: Optional[str] = None, status: Optional[str] = None, page: int = 1, limit: int = 50, admin=Depends(get_current_admin)):
    query = {}
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"product_code": {"$regex": search, "$options": "i"}},
        ]
    total = await products_col.count_documents(query)
    skip = (page - 1) * limit
    cursor = products_col.find(query).sort("created_at", -1).skip(skip).limit(limit)
    products = [serialize_doc(doc) for doc in await cursor.to_list(length=limit)]
    return {"products": products, "total": total, "page": page, "pages": (total + limit - 1) // limit}


@router.post("/api/admin/products")
async def admin_create_product(data: AdminProductCreate, admin=Depends(get_current_admin)):
    product_dict = data.dict()
    product_dict["id"] = str(uuid.uuid4())
    product_dict["slug"] = data.slug or slugify(data.name)
    product_dict["created_at"] = datetime.now(timezone.utc)
    existing = await products_col.find_one({"product_code": data.product_code})
    if existing:
        raise HTTPException(status_code=400, detail=f"Product code {data.product_code} already exists")
    await products_col.insert_one(product_dict)
    clear_ssr_cache()
    return {"success": True, "product": serialize_doc(await products_col.find_one({"id": product_dict["id"]}))}


@router.put("/api/admin/products/{product_id}")
async def admin_update_product(product_id: str, data: AdminProductUpdate, admin=Depends(get_current_admin)):
    update_dict = data.dict(exclude_unset=True, exclude_none=True)
    if data.slug:
        update_dict["slug"] = data.slug
    elif data.name:
        update_dict["slug"] = slugify(data.name)
    update_dict["updated_at"] = datetime.now(timezone.utc)
    result = await products_col.update_one({"id": product_id}, {"$set": update_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    updated = await products_col.find_one({"id": product_id})
    clear_ssr_cache()
    return {"success": True, "product": serialize_doc(updated)}


@router.delete("/api/admin/products/{product_id}")
async def admin_delete_product(product_id: str, admin=Depends(get_current_admin)):
    result = await products_col.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    clear_ssr_cache()
    return {"success": True}


@router.post("/api/admin/products/bulk-delete")
async def admin_bulk_delete_products(ids: List[str], admin=Depends(get_current_admin)):
    result = await products_col.delete_many({"id": {"$in": ids}})
    clear_ssr_cache()
    return {"success": True, "deleted": result.deleted_count}


# --- Inspirations CRUD ---

@router.get("/api/admin/inspirations")
async def admin_get_inspirations(category: Optional[str] = None, search: Optional[str] = None, page: int = 1, limit: int = 50, admin=Depends(get_current_admin)):
    query = {}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [{"title": {"$regex": search, "$options": "i"}}]
    total = await inspirations_col.count_documents(query)
    skip = (page - 1) * limit
    cursor = inspirations_col.find(query).sort("created_at", -1).skip(skip).limit(limit)
    items = [serialize_doc(doc) for doc in await cursor.to_list(length=limit)]
    return {"inspirations": items, "total": total, "page": page, "pages": (total + limit - 1) // limit}


@router.post("/api/admin/inspirations")
async def admin_create_inspiration(data: AdminInspirationCreate, admin=Depends(get_current_admin)):
    item = data.dict()
    item["id"] = str(uuid.uuid4())
    item["slug"] = data.slug or slugify(data.title)
    item["created_at"] = datetime.now(timezone.utc)
    await inspirations_col.insert_one(item)
    return {"success": True, "inspiration": serialize_doc(await inspirations_col.find_one({"id": item["id"]}))}


@router.put("/api/admin/inspirations/{item_id}")
async def admin_update_inspiration(item_id: str, data: AdminInspirationCreate, admin=Depends(get_current_admin)):
    update = data.dict(exclude_unset=True)
    update["slug"] = data.slug or slugify(data.title)
    update["updated_at"] = datetime.now(timezone.utc)
    result = await inspirations_col.update_one({"id": item_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Inspiration not found")
    return {"success": True, "inspiration": serialize_doc(await inspirations_col.find_one({"id": item_id}))}


@router.delete("/api/admin/inspirations/{item_id}")
async def admin_delete_inspiration(item_id: str, admin=Depends(get_current_admin)):
    result = await inspirations_col.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Inspiration not found")
    return {"success": True}


# --- Projects CRUD ---

@router.get("/api/admin/projects")
async def admin_get_projects(sector: Optional[str] = None, search: Optional[str] = None, page: int = 1, limit: int = 50, admin=Depends(get_current_admin)):
    query = {}
    if sector:
        query["sector"] = sector
    if search:
        query["$or"] = [{"title": {"$regex": search, "$options": "i"}}, {"client_name": {"$regex": search, "$options": "i"}}]
    total = await projects_col.count_documents(query)
    skip = (page - 1) * limit
    cursor = projects_col.find(query).sort("created_at", -1).skip(skip).limit(limit)
    items = [serialize_doc(doc) for doc in await cursor.to_list(length=limit)]
    return {"projects": items, "total": total, "page": page, "pages": (total + limit - 1) // limit}


@router.post("/api/admin/projects")
async def admin_create_project(data: AdminProjectCreate, admin=Depends(get_current_admin)):
    item = data.dict()
    item["id"] = str(uuid.uuid4())
    item["slug"] = data.slug or slugify(data.title)
    item["created_at"] = datetime.now(timezone.utc)
    await projects_col.insert_one(item)
    return {"success": True, "project": serialize_doc(await projects_col.find_one({"id": item["id"]}))}


@router.put("/api/admin/projects/{item_id}")
async def admin_update_project(item_id: str, data: AdminProjectCreate, admin=Depends(get_current_admin)):
    update = data.dict(exclude_unset=True)
    update["slug"] = data.slug or slugify(data.title)
    update["updated_at"] = datetime.now(timezone.utc)
    result = await projects_col.update_one({"id": item_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True, "project": serialize_doc(await projects_col.find_one({"id": item_id}))}


@router.delete("/api/admin/projects/{item_id}")
async def admin_delete_project(item_id: str, admin=Depends(get_current_admin)):
    result = await projects_col.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True}


# --- Leads ---

@router.get("/api/admin/leads")
async def admin_get_leads(status: Optional[str] = None, search: Optional[str] = None, page: int = 1, limit: int = 50, admin=Depends(get_current_admin)):
    query = {}
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
        ]
    total = await leads_col.count_documents(query)
    skip = (page - 1) * limit
    cursor = leads_col.find(query).sort("created_at", -1).skip(skip).limit(limit)
    items = [serialize_doc(doc) for doc in await cursor.to_list(length=limit)]
    return {"leads": items, "total": total, "page": page, "pages": (total + limit - 1) // limit}


@router.put("/api/admin/leads/{lead_id}")
async def admin_update_lead(lead_id: str, data: dict, admin=Depends(get_current_admin)):
    allowed = {"status", "notes"}
    update = {k: v for k, v in data.items() if k in allowed}
    update["updated_at"] = datetime.now(timezone.utc)
    result = await leads_col.update_one({"id": lead_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"success": True, "lead": serialize_doc(await leads_col.find_one({"id": lead_id}))}


@router.delete("/api/admin/leads/{lead_id}")
async def admin_delete_lead(lead_id: str, admin=Depends(get_current_admin)):
    result = await leads_col.delete_one({"id": lead_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"success": True}


# --- Export / Import ---

@router.get("/api/admin/export/{collection}")
async def admin_export(collection: str, admin=Depends(get_current_admin)):
    col_map = {"products": products_col, "inspirations": inspirations_col, "projects": projects_col, "leads": leads_col}
    col = col_map.get(collection)
    if col is None:
        raise HTTPException(status_code=400, detail="Invalid collection")
    cursor = col.find().sort("created_at", -1)
    items = [serialize_doc(doc) for doc in await cursor.to_list(length=1000)]
    return {"data": items, "count": len(items)}


@router.post("/api/admin/import/{collection}")
async def admin_import(collection: str, data: List[dict], admin=Depends(get_current_admin)):
    col_map = {"products": products_col, "inspirations": inspirations_col, "projects": projects_col}
    col = col_map.get(collection)
    if col is None:
        raise HTTPException(status_code=400, detail="Invalid collection")
    imported = 0
    for item in data:
        if "id" not in item:
            item["id"] = str(uuid.uuid4())
        if "created_at" not in item:
            item["created_at"] = datetime.now(timezone.utc)
        try:
            await col.insert_one(item)
            imported += 1
        except Exception as e:
            print(f"Import error: {e}")
    return {"success": True, "imported": imported}
