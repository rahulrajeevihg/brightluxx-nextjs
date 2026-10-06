"""Specification substitution service endpoints."""
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from starlette.concurrency import run_in_threadpool
from typing import List, Optional
from datetime import datetime, timezone
import os
import uuid

from database import leads_col
from email_service import send_email, NOTIFICATION_EMAIL
from email_templates import spec_substitution_email
from anti_spam import validate_submission_full, check_recaptcha
from object_storage import APP_NAME, put_object
from utils import get_client_ip

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/api/spec-substitution")
async def submit_spec_substitution(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    company: str = Form(...),
    phone: str = Form(""),
    projectName: str = Form(""),
    description: str = Form(""),
    fax: str = Form(""),
    files: List[UploadFile] = File(default=[]),
):
    """Handle spec substitution form with file uploads."""
    ip = get_client_ip(request)
    validation_data = {"name": name, "email": email, "phone": phone, "message": description, "fax": fax}
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(validation_data, ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"success": True, "submission_id": "ok"}
        raise HTTPException(status_code=422, detail=error_msg)

    await check_recaptcha(request)

    submission_id = str(uuid.uuid4())[:8]

    saved_files = []
    for f in files[:5]:
        if f.filename:
            content = await f.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail=f"{f.filename} exceeds the 10 MB upload limit")
            extension = os.path.splitext(f.filename)[1].lower().lstrip(".") or "bin"
            object_path = f"{APP_NAME}/uploads/spec-submissions/{submission_id}/{uuid.uuid4()}.{extension}"
            try:
                stored = await run_in_threadpool(
                    put_object,
                    object_path,
                    content,
                    f.content_type or "application/octet-stream",
                )
            except Exception as exc:
                raise HTTPException(status_code=503, detail="File upload is temporarily unavailable") from exc
            saved_files.append({
                "name": f.filename,
                "storage_path": stored["path"],
                "content_type": f.content_type or "application/octet-stream",
                "size": stored["size"],
                "is_deleted": False,
            })

    # Save to database
    lead_data = {
        "name": name,
        "email": email,
        "company": company,
        "phone": phone,
        "project_name": projectName,
        "description": description,
        "files": saved_files,
        "submission_id": submission_id,
        "source": "spec_substitution",
        "ip": ip[:50],
        "spam_score": spam_score,
        "geo": {"country": geo_data.get("country", ""), "city": geo_data.get("city", "")},
        "status": "new",
        "created_at": datetime.now(timezone.utc),
    }
    await leads_col.insert_one(lead_data)

    # Send enhanced email notification
    if NOTIFICATION_EMAIL:
        file_list = ", ".join([f["name"] for f in saved_files]) if saved_files else "No files attached"
        try:
            email_data = {
                "name": name,
                "email": email,
                "company": company,
                "phone": phone,
                "current_spec": f"Files: {file_list}" if saved_files else "No files",
                "project_name": projectName,
                "reason": description,
            }
            subject, html = spec_substitution_email(email_data)
            await send_email(NOTIFICATION_EMAIL, subject, html)
        except Exception:
            pass

    return {"success": True, "submission_id": submission_id}
