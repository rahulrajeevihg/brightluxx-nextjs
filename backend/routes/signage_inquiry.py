from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from database import leads_col
from email_service import send_email, NOTIFICATION_EMAIL
from email_templates import signage_inquiry_email
from anti_spam import validate_submission_full, check_recaptcha
from utils import get_client_ip

router = APIRouter(prefix="/api")


class SignageInquiryRequest(BaseModel):
    name: str
    company: str = ""
    email: str
    phone: str = ""
    signage_type: str
    quantity: str = ""
    letter_height: str = ""
    illumination: str = ""
    material: str = ""
    display_size: str = ""
    location: str = ""
    installation_address: str = ""
    timeline: str = ""
    budget_range: str = ""
    project_brief: str = ""
    # Honeypot
    fax: Optional[str] = None


@router.post("/signage-inquiry")
async def signage_inquiry(req: SignageInquiryRequest, request: Request):
    ip = get_client_ip(request)
    validation_data = {"name": req.name, "email": req.email, "phone": req.phone, "message": req.project_brief, "fax": req.fax}
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(validation_data, ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"status": "ok", "message": "Inquiry submitted successfully"}
        raise HTTPException(status_code=422, detail=error_msg)

    await check_recaptcha(request)

    lead = {
        "name": req.name,
        "company": req.company,
        "email": req.email,
        "phone": req.phone,
        "source": "signage_inquiry",
        "signage_type": req.signage_type,
        "quantity": req.quantity,
        "letter_height": req.letter_height,
        "illumination": req.illumination,
        "material": req.material,
        "display_size": req.display_size,
        "location": req.location,
        "installation_address": req.installation_address,
        "timeline": req.timeline,
        "budget_range": req.budget_range,
        "project_brief": req.project_brief,
        "spam_score": spam_score,
        "ip": ip,
        "geo": {"country": geo_data.get("country", ""), "country_name": geo_data.get("country_name", ""), "city": geo_data.get("city", "")},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    await leads_col.insert_one(lead)
    lead.pop("_id", None)
    
    if NOTIFICATION_EMAIL:
        subject, html = signage_inquiry_email(lead)
        await send_email(NOTIFICATION_EMAIL, subject, html)
    
    return {"status": "ok", "message": "Inquiry submitted successfully"}
