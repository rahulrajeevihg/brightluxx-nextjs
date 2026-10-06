"""Spec Pack PDF generation and gated download endpoints."""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import os

from database import leads_col
from email_service import send_email, NOTIFICATION_EMAIL
from email_templates import specpack_download_email
from anti_spam import validate_submission_full, check_recaptcha
from utils import get_client_ip

router = APIRouter()

PDF_DIR = os.path.join(os.path.dirname(__file__), '..', 'specpacks')
os.makedirs(PDF_DIR, exist_ok=True)


class SpecPackRequest(BaseModel):
    email: str
    name: str = ""
    company: str = ""
    role: str = ""
    pack_id: str = ""
    fax: Optional[str] = None


SPEC_PACKS = {
    "retail-hospitality": "Retail & Hospitality LED Spec Pack",
    "outdoor-dooh": "Outdoor & DOOH LED Spec Pack",
    "corporate-control": "Corporate & Control Room LED Spec Pack",
    "healthcare-wayfinding": "Healthcare Digital Signage Spec Pack",
    "education-campus": "Education Campus Signage Spec Pack",
    "cob-mip-smd": "COB vs MiP vs SMD Technology Guide",
    "pixel-pitch": "Pixel Pitch Specification Guide",
    "brightness-nits": "Brightness & Nits Guide for GCC",
    "ip-rating": "IP Rating & Serviceability Guide",
    "refresh-rate": "Refresh Rate & Camera Guide",
    "supermarket-promotions": "Supermarket Digital Signage Spec Pack",
    "residential-cinema": "Residential Cinema Wall Spec Pack",
}


@router.post("/api/specpacks/{pack_id}/download")
async def download_specpack(pack_id: str, data: SpecPackRequest, request: Request):
    """Gated spec pack download - captures lead then returns download URL."""
    if pack_id not in SPEC_PACKS:
        return {"error": "Spec pack not found"}

    ip = get_client_ip(request)
    validation_data = {"name": data.name, "email": data.email, "fax": data.fax}
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(validation_data, ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"download_url": f"/api/specpacks/{pack_id}/file"}
        raise HTTPException(status_code=422, detail=error_msg)

    await check_recaptcha(request)

    # Capture the lead
    lead_data = {
        "name": data.name,
        "email": data.email,
        "company": data.company,
        "role": data.role,
        "source": "spec_pack_download",
        "spec_pack": pack_id,
        "spec_pack_title": SPEC_PACKS[pack_id],
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
                "spec_pack_title": SPEC_PACKS[pack_id],
            }
            subject, html = specpack_download_email(email_data)
            await send_email(NOTIFICATION_EMAIL, subject, html)
        except Exception:
            pass

    # Check if PDF exists, if not generate it
    pdf_path = os.path.join(PDF_DIR, f"{pack_id}.pdf")
    if not os.path.exists(pdf_path):
        from specpack_generator import generate_spec_pack
        generate_spec_pack(pack_id, pdf_path)

    return {"download_url": f"/api/specpacks/{pack_id}/file"}


@router.get("/api/specpacks/{pack_id}/file")
async def serve_specpack_file(pack_id: str):
    """Serve the actual PDF file."""
    pdf_path = os.path.join(PDF_DIR, f"{pack_id}.pdf")
    if not os.path.exists(pdf_path):
        from specpack_generator import generate_spec_pack
        generate_spec_pack(pack_id, pdf_path)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"Brightluxx-{pack_id}-spec-pack.pdf",
    )


@router.get("/api/specpacks")
async def list_specpacks():
    """List available spec packs."""
    return {"packs": [{"id": k, "title": v} for k, v in SPEC_PACKS.items()]}
