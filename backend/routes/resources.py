"""
Resources API routes for managing the Resource Library.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
import uuid
import os

from database import db
from auth import get_current_admin
from utils import serialize_doc
from cdn_upload import upload_to_cdn

router = APIRouter()

resources_col = db["resources"]

# External CDN base URL for uploaded files
EXTERNAL_CDN = ""


class ResourceCreate(BaseModel):
    title: str
    description: str
    category: str  # specpack, cheatsheet, bim, guide
    tags: List[str] = []
    # For downloadable resources
    pack_id: Optional[str] = None
    doc_id: Optional[str] = None
    bim_id: Optional[str] = None
    # For knowledge base links
    link: Optional[str] = None
    # Uploaded file URL
    file_url: Optional[str] = None
    # Status
    is_active: bool = True
    order: int = 0


class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    pack_id: Optional[str] = None
    doc_id: Optional[str] = None
    bim_id: Optional[str] = None
    link: Optional[str] = None
    file_url: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None


# Public endpoint - get all active resources
@router.get("/api/resources")
async def get_resources(category: Optional[str] = None):
    """Get all active resources, optionally filtered by category."""
    query = {"is_active": True}
    if category and category != "all":
        query["category"] = category
    
    cursor = resources_col.find(query, {"_id": 0}).sort("order", 1)
    resources = await cursor.to_list(length=500)
    
    # Get counts by category
    counts = {
        "all": await resources_col.count_documents({"is_active": True}),
        "specpack": await resources_col.count_documents({"is_active": True, "category": "specpack"}),
        "cheatsheet": await resources_col.count_documents({"is_active": True, "category": "cheatsheet"}),
        "bim": await resources_col.count_documents({"is_active": True, "category": "bim"}),
        "guide": await resources_col.count_documents({"is_active": True, "category": "guide"}),
    }
    
    return {"resources": resources, "counts": counts}


# Admin endpoints
@router.get("/api/admin/resources")
async def admin_get_resources(admin=Depends(get_current_admin)):
    """Get all resources for admin (including inactive)."""
    cursor = resources_col.find({}, {"_id": 0}).sort([("category", 1), ("order", 1)])
    resources = await cursor.to_list(length=500)
    
    counts = {
        "all": await resources_col.count_documents({}),
        "specpack": await resources_col.count_documents({"category": "specpack"}),
        "cheatsheet": await resources_col.count_documents({"category": "cheatsheet"}),
        "bim": await resources_col.count_documents({"category": "bim"}),
        "guide": await resources_col.count_documents({"category": "guide"}),
        "active": await resources_col.count_documents({"is_active": True}),
        "inactive": await resources_col.count_documents({"is_active": False}),
    }
    
    return {"resources": resources, "counts": counts}


@router.post("/api/admin/resources")
async def create_resource(data: ResourceCreate, admin=Depends(get_current_admin)):
    """Create a new resource."""
    resource_id = str(uuid.uuid4())[:12]
    
    resource = {
        "id": resource_id,
        "title": data.title,
        "description": data.description,
        "category": data.category,
        "tags": data.tags,
        "pack_id": data.pack_id,
        "doc_id": data.doc_id,
        "bim_id": data.bim_id,
        "link": data.link,
        "file_url": data.file_url,
        "is_active": data.is_active,
        "order": data.order,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    
    await resources_col.insert_one(resource)
    
    return {"success": True, "resource": {k: v for k, v in resource.items() if k != "_id"}}


@router.post("/api/admin/resources/upload")
async def upload_resource_file(
    file: UploadFile = File(...),
    admin=Depends(get_current_admin)
):
    """Upload a PDF or document file for a resource."""
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
        "application/x-zip-compressed",
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: PDF, DOC, DOCX, XLS, XLSX, ZIP"
        )
    
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1].lower()
    unique_name = f"resource_{uuid.uuid4().hex[:8]}{ext}"
    
    # Read file content
    content = await file.read()
    
    # Upload to external CDN via SFTP
    try:
        cdn_url = upload_to_cdn(unique_name, content, "resources")
        
        return {
            "success": True,
            "file_url": cdn_url,
            "filename": file.filename,
            "size": len(content),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.put("/api/admin/resources/{resource_id}")
async def update_resource(resource_id: str, data: ResourceUpdate, admin=Depends(get_current_admin)):
    """Update a resource."""
    existing = await resources_col.find_one({"id": resource_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await resources_col.update_one({"id": resource_id}, {"$set": update_data})
    
    updated = await resources_col.find_one({"id": resource_id}, {"_id": 0})
    return {"success": True, "resource": updated}


@router.delete("/api/admin/resources/{resource_id}")
async def delete_resource(resource_id: str, admin=Depends(get_current_admin)):
    """Delete a resource."""
    result = await resources_col.delete_one({"id": resource_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"success": True, "message": "Resource deleted"}


@router.post("/api/admin/resources/seed")
async def seed_resources(admin=Depends(get_current_admin)):
    """Seed the database with default resources (one-time migration)."""
    existing_count = await resources_col.count_documents({})
    if existing_count > 0:
        return {"success": False, "message": f"Resources already exist ({existing_count} found). Clear first if you want to re-seed."}
    
    default_resources = [
        # Spec Packs
        {"id": "sp-cob", "category": "specpack", "title": "COB vs MiP vs SMD", "description": "Technology comparison with specification tables", "tags": ["Technology", "Comparison"], "pack_id": "cob-mip-smd", "order": 1},
        {"id": "sp-pitch", "category": "specpack", "title": "Pixel Pitch Guide", "description": "Viewing distance formulas and cost analysis", "tags": ["Pixel Pitch", "Calculator"], "pack_id": "pixel-pitch", "order": 2},
        {"id": "sp-bright", "category": "specpack", "title": "Brightness & Nits", "description": "GCC-specific brightness specification", "tags": ["Brightness", "Outdoor"], "pack_id": "brightness-nits", "order": 3},
        {"id": "sp-ip", "category": "specpack", "title": "IP Rating Guide", "description": "Protection ratings and serviceability", "tags": ["IP Rating", "Outdoor"], "pack_id": "ip-rating", "order": 4},
        {"id": "sp-refresh", "category": "specpack", "title": "Refresh Rate Guide", "description": "Camera-friendly specification", "tags": ["Refresh Rate", "Broadcast"], "pack_id": "refresh-rate", "order": 5},
        {"id": "sp-retail", "category": "specpack", "title": "Retail & Hospitality", "description": "Application-specific spec pack", "tags": ["Retail", "Hospitality"], "pack_id": "retail-hospitality", "order": 6},
        {"id": "sp-outdoor", "category": "specpack", "title": "Outdoor & DOOH", "description": "Outdoor billboard specification", "tags": ["Outdoor", "DOOH"], "pack_id": "outdoor-dooh", "order": 7},
        {"id": "sp-corp", "category": "specpack", "title": "Corporate & Control Room", "description": "Fine-pitch specification", "tags": ["Corporate", "Control Room"], "pack_id": "corporate-control", "order": 8},
        {"id": "sp-health", "category": "specpack", "title": "Healthcare", "description": "Hospital signage specification", "tags": ["Healthcare", "Wayfinding"], "pack_id": "healthcare-wayfinding", "order": 9},
        {"id": "sp-edu", "category": "specpack", "title": "Education", "description": "Campus signage specification", "tags": ["Education", "Campus"], "pack_id": "education-campus", "order": 10},
        {"id": "sp-super", "category": "specpack", "title": "Supermarket", "description": "Promotions network specification", "tags": ["Supermarket", "Retail"], "pack_id": "supermarket-promotions", "order": 11},
        {"id": "sp-resi", "category": "specpack", "title": "Residential Cinema", "description": "Home cinema wall specification", "tags": ["Residential", "Premium"], "pack_id": "residential-cinema", "order": 12},
        # Cheat Sheets
        {"id": "cs-pitch", "category": "cheatsheet", "title": "Pixel Pitch Cheat Sheet", "description": "One-page quick reference: viewing distance, resolution, cost per sqm", "tags": ["Pixel Pitch", "Quick Ref"], "doc_id": "pixel-pitch-cheatsheet", "order": 1},
        {"id": "cs-bright", "category": "cheatsheet", "title": "Brightness & Nits Cheat Sheet", "description": "UAE/GCC environment brightness guide on one page", "tags": ["Brightness", "UAE"], "doc_id": "brightness-cheatsheet", "order": 2},
        {"id": "cs-tech", "category": "cheatsheet", "title": "COB vs MiP vs SMD Cheat Sheet", "description": "Technology comparison quick reference", "tags": ["Technology", "Comparison"], "doc_id": "cob-mip-smd-cheatsheet", "order": 3},
        {"id": "cs-outdoor", "category": "cheatsheet", "title": "Outdoor Durability Checklist", "description": "Heat, dust, IP, service access checklist for UAE", "tags": ["Outdoor", "UAE", "Checklist"], "doc_id": "outdoor-checklist", "order": 4},
        # BIM / CAD
        {"id": "bim-aio", "category": "bim", "title": "All-in-One dvLED Reference", "description": "Dimensions, mounting, electrical for 110\"-216\" displays", "tags": ["dvLED", "Indoor"], "bim_id": "all-in-one-dvled", "order": 1},
        {"id": "bim-fp", "category": "bim", "title": "Fine-Pitch Wall Reference", "description": "Cabinet-based video wall. P0.9 to P1.9 configurations", "tags": ["Fine Pitch", "Video Wall"], "bim_id": "fine-pitch-wall", "order": 2},
        {"id": "bim-od", "category": "bim", "title": "Outdoor Cabinet Reference", "description": "IP65 outdoor cabinets. P3.9 to P10 with structural specs", "tags": ["Outdoor", "Billboard"], "bim_id": "outdoor-cabinet", "order": 3},
        {"id": "bim-tf", "category": "bim", "title": "Transparent LED Film Reference", "description": "Window-mount display. Adhesive mounting and controller details", "tags": ["Transparent", "Retail"], "bim_id": "transparent-film", "order": 4},
        # Knowledge Base (links)
        {"id": "kb-cob", "category": "guide", "title": "COB vs MiP vs SMD — Full Guide", "description": "Deep-dive technology comparison with real-install insights", "tags": ["Technology"], "link": "/knowledge/cob-vs-mip-vs-smd", "order": 1},
        {"id": "kb-pitch", "category": "guide", "title": "Pixel Pitch Explained", "description": "Resolution, viewing distance, cost analysis, and calculator", "tags": ["Pixel Pitch"], "link": "/knowledge/pixel-pitch-guide", "order": 2},
        {"id": "kb-bright", "category": "guide", "title": "Brightness & Nits Guide", "description": "Indoor vs outdoor GCC brightness specification", "tags": ["Brightness", "Outdoor"], "link": "/knowledge/brightness-nits-guide", "order": 3},
        {"id": "kb-ip", "category": "guide", "title": "IP Rating & Serviceability", "description": "Protection ratings, front vs rear service, UAE requirements", "tags": ["IP Rating"], "link": "/knowledge/ip-rating-guide", "order": 4},
        {"id": "kb-rr", "category": "guide", "title": "Refresh Rate & Camera Guide", "description": "Flicker-free, camera-friendly specification", "tags": ["Refresh Rate", "Broadcast"], "link": "/knowledge/refresh-rate-guide", "order": 5},
        {"id": "kb-proc", "category": "guide", "title": "Processing & Calibration", "description": "Video processing, calibration workflows, colour management", "tags": ["Processing", "Calibration"], "link": "/knowledge/processing-calibration", "order": 6},
        {"id": "kb-cms", "category": "guide", "title": "CMS for Multi-Site Signage", "description": "Content management for multi-location networks", "tags": ["CMS", "Multi-Site"], "link": "/knowledge/cms-multi-site", "order": 7},
        {"id": "kb-sla", "category": "guide", "title": "SLA Gap Analysis", "description": "Common SLA gaps, tier comparison, and audit checklist for LED display contracts", "tags": ["SLA", "Contracts", "Maintenance"], "link": "/sla-guide", "order": 8},
    ]
    
    now = datetime.now(timezone.utc)
    for r in default_resources:
        r["is_active"] = True
        r["created_at"] = now
        r["updated_at"] = now
        r.setdefault("pack_id", None)
        r.setdefault("doc_id", None)
        r.setdefault("bim_id", None)
        r.setdefault("link", None)
    
    await resources_col.insert_many(default_resources)
    
    return {"success": True, "message": f"Seeded {len(default_resources)} resources"}
