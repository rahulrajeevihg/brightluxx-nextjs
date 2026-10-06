"""Admin file upload routes - uploads to external CDN server with auto-optimization."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List
from pathlib import Path
import uuid
import os

from auth import get_current_admin
from cdn_upload import upload_image_to_cdn
from image_optimizer import optimize_image, get_image_info

router = APIRouter()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".avif"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/api/admin/upload")
async def admin_upload_file(file: UploadFile = File(...), admin=Depends(get_current_admin)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB")

    original_size = len(content)
    safe_name = file.filename.replace(" ", "-")
    unique_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"

    # Upload with auto-optimization (resize + WebP + compress)
    cdn_url = upload_image_to_cdn(unique_name, content, "uploads")

    return {
        "success": True,
        "url": cdn_url,
        "filename": os.path.basename(cdn_url),
        "original_size": original_size,
        "optimized": cdn_url.endswith(".webp"),
        "content_type": file.content_type or "application/octet-stream",
    }


@router.post("/api/admin/upload/multiple")
async def admin_upload_multiple(files: List[UploadFile] = File(...), admin=Depends(get_current_admin)):
    uploaded = []
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            continue

        safe_name = file.filename.replace(" ", "-")
        unique_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"

        try:
            cdn_url = upload_image_to_cdn(unique_name, content, "uploads")
            uploaded.append({
                "url": cdn_url,
                "filename": os.path.basename(cdn_url),
                "original_size": len(content),
                "original_name": file.filename,
            })
        except Exception:
            continue

    return {"success": True, "uploaded": uploaded, "count": len(uploaded)}
