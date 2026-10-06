"""Cheat sheet and BIM reference download endpoints (lead-gated)."""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import os

from database import leads_col
from email_service import send_email, NOTIFICATION_EMAIL
from email_templates import download_request_email
from anti_spam import validate_submission_full, check_recaptcha
from utils import get_client_ip

router = APIRouter()

DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), '..', 'downloads')
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

CHEATSHEETS = {
    "pixel-pitch-cheatsheet": "Pixel Pitch Cheat Sheet",
    "brightness-cheatsheet": "Brightness & Nits Cheat Sheet",
    "cob-mip-smd-cheatsheet": "COB vs MiP vs SMD Cheat Sheet",
    "outdoor-checklist": "Outdoor LED Durability Checklist",
}

BIM_REFS = {
    "all-in-one-dvled": "All-in-One dvLED Technical Reference",
    "fine-pitch-wall": "Fine-Pitch LED Wall Technical Reference",
    "outdoor-cabinet": "Outdoor LED Cabinet Technical Reference",
    "transparent-film": "Transparent LED Film Technical Reference",
}


class DownloadRequest(BaseModel):
    email: str
    name: str = ""
    company: str = ""
    role: str = ""
    fax: Optional[str] = None


@router.post("/api/downloads/{doc_type}/{doc_id}/request")
async def request_download(doc_type: str, doc_id: str, data: DownloadRequest, request: Request):
    """Lead-gated download for cheat sheets and BIM references."""
    if doc_type == "cheatsheet":
        catalog = CHEATSHEETS
    elif doc_type == "bim":
        catalog = BIM_REFS
    else:
        return {"error": "Invalid document type"}

    if doc_id not in catalog:
        return {"error": "Document not found"}

    ip = get_client_ip(request)
    validation_data = {"name": data.name, "email": data.email, "fax": data.fax}
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(validation_data, ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"download_url": f"/api/downloads/{doc_type}/{doc_id}/file"}
        raise HTTPException(status_code=422, detail=error_msg)

    await check_recaptcha(request)

    lead_data = {
        "name": data.name,
        "email": data.email,
        "company": data.company,
        "role": data.role,
        "source": f"{doc_type}_download",
        "document": doc_id,
        "document_title": catalog[doc_id],
        "ip": ip[:50],
        "spam_score": spam_score,
        "geo": {"country": geo_data.get("country", ""), "city": geo_data.get("city", "")},
        "status": "new",
        "created_at": datetime.now(timezone.utc),
    }
    await leads_col.insert_one(lead_data)

    # Send enhanced email notification
    if NOTIFICATION_EMAIL:
        try:
            email_data = {
                "name": data.name or "Unknown",
                "email": data.email,
                "company": data.company,
                "role": data.role,
                "document_title": catalog[doc_id],
                "document_type": doc_type.replace("_", " ").title(),
            }
            subject, html = download_request_email(email_data)
            await send_email(NOTIFICATION_EMAIL, subject, html)
        except Exception:
            pass

    return {"download_url": f"/api/downloads/{doc_type}/{doc_id}/file"}


@router.get("/api/downloads/{doc_type}/{doc_id}/file")
async def serve_download(doc_type: str, doc_id: str):
    """Serve the actual PDF file."""
    pdf_path = os.path.join(DOWNLOADS_DIR, f"{doc_type}-{doc_id}.pdf")

    if not os.path.exists(pdf_path):
        from cheatsheet_generator import CHEATSHEET_GENERATORS, BIM_TYPES, generate_bim_reference
        if doc_type == "cheatsheet" and doc_id in CHEATSHEET_GENERATORS:
            CHEATSHEET_GENERATORS[doc_id](pdf_path)
        elif doc_type == "bim" and doc_id in BIM_TYPES:
            generate_bim_reference(doc_id, pdf_path)
        else:
            return {"error": "Document not found"}

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"Brightluxx-{doc_id}.pdf",
    )


@router.get("/api/downloads/catalog")
async def list_downloads():
    """List all available downloads."""
    return {
        "cheatsheets": [{"id": k, "title": v} for k, v in CHEATSHEETS.items()],
        "bim_references": [{"id": k, "title": v} for k, v in BIM_REFS.items()],
    }
