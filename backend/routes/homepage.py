"""
Homepage content management - Dynamic sections for the homepage.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import uuid
import os

from database import db
from auth import get_current_admin
from fastapi.responses import StreamingResponse
import requests as http_requests
router = APIRouter()

homepage_col = db["homepage_content"]

# Object storage config
_STORAGE_BASE = "https://integrations.emergentagent.com/objstore/api/v1/storage"
_storage_key_cache = {"key": None}


def _get_storage_key():
    """Get or cache the object storage key."""
    if _storage_key_cache["key"]:
        return _storage_key_cache["key"]
    emergent_key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not emergent_key:
        return None
    resp = http_requests.post(f"{_STORAGE_BASE}/init", json={"emergent_key": emergent_key}, timeout=15)
    if resp.status_code == 200:
        _storage_key_cache["key"] = resp.json()["storage_key"]
        return _storage_key_cache["key"]
    return None


@router.get("/api/media/{path:path}")
@router.head("/api/media/{path:path}")
async def serve_media(path: str, request: Request):
    """Proxy media files from Emergent object storage with Range support."""
    storage_key = _get_storage_key()
    if not storage_key:
        raise HTTPException(503, "Storage not available")

    obj_path = f"brightluxx/{path}"
    upstream_url = f"{_STORAGE_BASE}/objects/{obj_path}"
    upstream_headers = {"X-Storage-Key": storage_key}

    # Forward Range header if present
    range_header = request.headers.get("range")
    if range_header:
        upstream_headers["Range"] = range_header

    resp = http_requests.get(
        upstream_url,
        headers=upstream_headers,
        stream=True,
        timeout=30,
    )
    if resp.status_code not in (200, 206):
        raise HTTPException(404, "Media not found")

    content_type = resp.headers.get("Content-Type", "application/octet-stream")
    content_length = resp.headers.get("Content-Length")
    content_range = resp.headers.get("Content-Range")

    headers = {
        "Cache-Control": "public, max-age=86400, immutable",
        "Accept-Ranges": "bytes",
    }
    if content_length:
        headers["Content-Length"] = content_length
    if content_range:
        headers["Content-Range"] = content_range

    status_code = resp.status_code  # 200 or 206

    if request.method == "HEAD":
        resp.close()
        return StreamingResponse(
            iter([]),
            status_code=status_code,
            media_type=content_type,
            headers=headers,
        )

    return StreamingResponse(
        resp.iter_content(chunk_size=256 * 1024),
        status_code=status_code,
        media_type=content_type,
        headers=headers,
    )


class HeroSection(BaseModel):
    headline: str = "Premium LED Display Solutions"
    subheadline: str = "Specification Engine for Architects & Contractors"
    cta_text: str = "Explore Products"
    cta_link: str = "/products"
    video_urls: List[str] = []
    poster_image: str = ""


class StatItem(BaseModel):
    value: str
    label: str
    suffix: str = ""


class EntryDoor(BaseModel):
    title: str
    description: str
    image: str
    link: str
    cta_text: str = "Explore"


class ClientItem(BaseModel):
    name: str
    logo_url: Optional[str] = None


class ShowcaseReel(BaseModel):
    enabled: bool = False
    video_url: str = ""
    title: str = "See It In Action"
    subtitle: str = "Real installations across UAE and beyond"


class HomepageContent(BaseModel):
    hero: Optional[HeroSection] = None
    stats: Optional[List[StatItem]] = None
    entry_doors: Optional[List[EntryDoor]] = None
    clients: Optional[List[ClientItem]] = None
    showcase_reel: Optional[ShowcaseReel] = None
    featured_products_title: str = "Featured Products"
    featured_products_subtitle: str = "Premium LED displays engineered for the Gulf region"
    projects_title: str = "Case Studies"
    projects_subtitle: str = "Real installations across UAE and MENA"
    why_brightluxx_title: str = "Why Brightluxx?"
    why_brightluxx_items: Optional[List[Dict[str, str]]] = None


# Default content
DEFAULT_HERO = {
    "headline": "Premium LED Display Solutions",
    "subheadline": "Specification Engine for Architects & Contractors",
    "cta_text": "Explore Products",
    "cta_link": "/products",
    "video_urls": [
        "https://files.ihgbrands.com/videos_hero-video-1.mp4",
        "/videos/hero-video-2.mp4"
    ],
    "poster_image": "https://files.ihgbrands.com/uploads_hero_banner.webp"
}

DEFAULT_STATS = [
    {"value": "500", "label": "Projects Delivered", "suffix": "+"},
    {"value": "15", "label": "Years Experience", "suffix": "+"},
    {"value": "50", "label": "Expert Team", "suffix": "+"},
    {"value": "24", "label": "Service Support", "suffix": "/7"},
]

DEFAULT_ENTRY_DOORS = [
    {
        "title": "Products",
        "description": "MicroLED, outdoor, rental, transparent. Full range.",
        "image": "/uploads/cob_microled_1.webp",
        "link": "/products",
        "cta_text": "Browse"
    },
    {
        "title": "Inspirations",
        "description": "See how LED transforms spaces across industries.",
        "image": "/uploads/insp_retail.webp",
        "link": "/inspirations",
        "cta_text": "Discover"
    },
    {
        "title": "Projects",
        "description": "Real installations. Proven results across UAE and MENA.",
        "image": "/uploads/proj_indian_pavilion___expo_2020_dubai.webp",
        "link": "/projects",
        "cta_text": "View"
    }
]

DEFAULT_WHY_ITEMS = [
    {"icon": "Factory", "title": "Direct Factory", "description": "No middlemen. Factory-direct pricing with full QC control."},
    {"icon": "Package", "title": "Gulf-Grade Stock", "description": "High-brightness, heat-resistant panels ready in Dubai."},
    {"icon": "Truck", "title": "Fast Delivery", "description": "48-hour dispatch from our UAE warehouse."},
    {"icon": "GraduationCap", "title": "CPD Training", "description": "Accredited LED specification training for your team."},
    {"icon": "Wrench", "title": "Full Installation", "description": "Turnkey installation with certified technicians."},
    {"icon": "HeartHandshake", "title": "5-Year Warranty", "description": "Industry-leading warranty with local support."},
]

DEFAULT_CLIENTS = [
    {"name": "RTA Dubai", "logo_url": None},
    {"name": "Dubai Police", "logo_url": None},
    {"name": "DEWA", "logo_url": None},
    {"name": "Emirates NBD", "logo_url": None},
    {"name": "Dubai Islamic Bank", "logo_url": None},
    {"name": "Etihad Airways", "logo_url": None},
    {"name": "Sharjah Airport", "logo_url": None},
    {"name": "ADNOC", "logo_url": None},
    {"name": "Emaar", "logo_url": None},
    {"name": "Carrefour", "logo_url": None},
    {"name": "Mashreq Bank", "logo_url": None},
    {"name": "RAKBANK", "logo_url": None},
    {"name": "Al Naboodah", "logo_url": None},
    {"name": "Jumeirah Group", "logo_url": None},
    {"name": "BEEAH", "logo_url": None},
    {"name": "City Centre", "logo_url": None},
    {"name": "Abu Dhabi Islamic Bank", "logo_url": None},
    {"name": "Ministry of Finance UAE", "logo_url": None},
]


@router.get("/api/homepage-content")
async def get_homepage_content():
    """Get homepage content for public display."""
    content = await homepage_col.find_one({"type": "main"}, {"_id": 0})
    
    if not content:
        # Return defaults
        return {"content": {
            "hero": DEFAULT_HERO,
            "stats": DEFAULT_STATS,
            "entry_doors": DEFAULT_ENTRY_DOORS,
            "clients": DEFAULT_CLIENTS,
            "featured_products_title": "Featured Products",
            "featured_products_subtitle": "Premium LED displays engineered for the Gulf region",
            "projects_title": "Case Studies",
            "projects_subtitle": "Real installations across UAE and MENA",
            "why_brightluxx_title": "Why Brightluxx?",
            "why_brightluxx_items": DEFAULT_WHY_ITEMS,
        }}
    
    # Add defaults for missing fields
    if "clients" not in content or not content.get("clients"):
        content["clients"] = DEFAULT_CLIENTS
    
    return {"content": content}


@router.get("/api/admin/homepage-content")
async def admin_get_homepage_content(admin=Depends(get_current_admin)):
    """Get homepage content for admin editing."""
    content = await homepage_col.find_one({"type": "main"}, {"_id": 0})
    
    if not content:
        # Return defaults for editing
        return {
            "type": "main",
            "hero": DEFAULT_HERO,
            "stats": DEFAULT_STATS,
            "entry_doors": DEFAULT_ENTRY_DOORS,
            "clients": DEFAULT_CLIENTS,
            "featured_products_title": "Featured Products",
            "featured_products_subtitle": "Premium LED displays engineered for the Gulf region",
            "projects_title": "Case Studies",
            "projects_subtitle": "Real installations across UAE and MENA",
            "why_brightluxx_title": "Why Brightluxx?",
            "why_brightluxx_items": DEFAULT_WHY_ITEMS,
            "is_default": True,
        }
    
    # Add defaults for missing fields
    if "clients" not in content or not content.get("clients"):
        content["clients"] = DEFAULT_CLIENTS
    
    content["is_default"] = False
    return content


@router.put("/api/admin/homepage-content")
async def update_homepage_content(data: dict, admin=Depends(get_current_admin)):
    """Update homepage content."""
    data["type"] = "main"
    data["updated_at"] = datetime.now(timezone.utc)
    
    # Remove is_default flag if present
    data.pop("is_default", None)
    
    existing = await homepage_col.find_one({"type": "main"})
    
    if existing:
        await homepage_col.update_one({"type": "main"}, {"$set": data})
    else:
        data["created_at"] = datetime.now(timezone.utc)
        await homepage_col.insert_one(data)
    
    updated = await homepage_col.find_one({"type": "main"}, {"_id": 0})
    return {"success": True, "content": updated}


@router.post("/api/admin/homepage-content/reset")
async def reset_homepage_content(admin=Depends(get_current_admin)):
    """Reset homepage content to defaults."""
    await homepage_col.delete_one({"type": "main"})
    return {"success": True, "message": "Homepage content reset to defaults"}


@router.post("/api/admin/homepage/upload-image")
async def upload_homepage_image(
    file: UploadFile = File(...),
    admin=Depends(get_current_admin)
):
    """Upload an image for homepage sections."""
    from cdn_upload import upload_image_to_cdn
    
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: JPEG, PNG, WebP, GIF"
        )
    
    ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    unique_name = f"homepage_{uuid.uuid4().hex[:8]}{ext}"
    
    content = await file.read()
    
    try:
        image_url = upload_image_to_cdn(unique_name, content, "homepage")
        
        return {
            "success": True,
            "url": image_url,
            "filename": file.filename,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


import base64

uploads_col = db["upload_sessions"]
chunks_col = db["upload_chunks"]


@router.post("/api/admin/homepage/upload-video/init")
async def init_chunked_upload(request: Request, admin=Depends(get_current_admin)):
    """Initialize a chunked video upload session."""
    body = await request.json()
    filename = body.get("filename", "video.mp4")
    total_size = body.get("totalSize", 0)
    content_type = body.get("contentType", "video/mp4")

    allowed_types = ["video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"]
    if content_type not in allowed_types:
        raise HTTPException(400, "Invalid file type. Allowed: MP4, WebM, MOV, AVI")
    if total_size > 100 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum 100MB.")

    upload_id = uuid.uuid4().hex[:12]
    await uploads_col.insert_one({
        "upload_id": upload_id,
        "filename": filename,
        "total_size": total_size,
        "content_type": content_type,
        "chunk_count": 0,
        "created_at": datetime.now(timezone.utc),
    })

    return {"uploadId": upload_id}


@router.post("/api/admin/homepage/upload-video/chunk/{upload_id}")
async def upload_chunk(upload_id: str, file: UploadFile = File(...), admin=Depends(get_current_admin)):
    """Upload a single chunk (stored as separate MongoDB document)."""
    session = await uploads_col.find_one({"upload_id": upload_id})
    if not session:
        raise HTTPException(404, "Upload session not found")

    content = await file.read()
    chunk_idx = session["chunk_count"]

    # Store each chunk as a separate document (avoids 16MB document limit)
    await chunks_col.insert_one({
        "upload_id": upload_id,
        "index": chunk_idx,
        "data": base64.b64encode(content).decode("ascii"),
    })

    await uploads_col.update_one(
        {"upload_id": upload_id},
        {"$inc": {"chunk_count": 1}},
    )

    return {"chunkIndex": chunk_idx, "received": len(content)}


@router.post("/api/admin/homepage/upload-video/complete/{upload_id}")
async def complete_chunked_upload(upload_id: str, admin=Depends(get_current_admin)):
    """Reassemble chunks from MongoDB and upload to CDN."""
    from cdn_upload import upload_video_to_cdn

    session = await uploads_col.find_one({"upload_id": upload_id})
    if not session:
        raise HTTPException(404, "Upload session not found")

    # Reassemble chunks in order
    video_bytes = bytearray()
    for i in range(session["chunk_count"]):
        chunk_doc = await chunks_col.find_one({"upload_id": upload_id, "index": i})
        if not chunk_doc:
            await chunks_col.delete_many({"upload_id": upload_id})
            await uploads_col.delete_one({"upload_id": upload_id})
            raise HTTPException(400, f"Missing chunk {i}")
        video_bytes.extend(base64.b64decode(chunk_doc["data"]))

    if len(video_bytes) > 100 * 1024 * 1024:
        await chunks_col.delete_many({"upload_id": upload_id})
        await uploads_col.delete_one({"upload_id": upload_id})
        raise HTTPException(400, "Reassembled file exceeds 100MB limit")

    ext = os.path.splitext(session["filename"])[1].lower() or ".mp4"
    unique_name = f"hero_video_{uuid.uuid4().hex[:8]}{ext}"

    try:
        video_url = upload_video_to_cdn(unique_name, bytes(video_bytes))
    except Exception as e:
        raise HTTPException(500, f"CDN upload failed: {str(e)}")
    finally:
        await chunks_col.delete_many({"upload_id": upload_id})
        await uploads_col.delete_one({"upload_id": upload_id})

    return {"success": True, "url": video_url, "filename": session["filename"]}


@router.post("/api/admin/homepage/upload-video")
async def upload_homepage_video(
    file: UploadFile = File(...),
    admin=Depends(get_current_admin)
):
    """Upload a video for homepage hero section."""
    from cdn_upload import upload_video_to_cdn
    
    allowed_types = ["video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: MP4, WebM, MOV, AVI"
        )
    
    # Check file size (max 100MB)
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 100MB.")
    
    ext = os.path.splitext(file.filename)[1].lower() or ".mp4"
    unique_name = f"hero_video_{uuid.uuid4().hex[:8]}{ext}"
    
    try:
        video_url = upload_video_to_cdn(unique_name, content)
        
        return {
            "success": True,
            "url": video_url,
            "filename": file.filename,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
