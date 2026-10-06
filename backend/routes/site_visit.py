from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from database import leads_col
from email_service import send_email, NOTIFICATION_EMAIL
from email_templates import site_visit_email
from anti_spam import validate_submission_full, check_recaptcha
from utils import get_client_ip

router = APIRouter(prefix="/api")


class SiteVisitRequest(BaseModel):
    name: str
    email: str
    phone: str = ""
    company: str = ""
    project_brief: str = ""
    page_url: str = ""
    fax: Optional[str] = None


@router.post("/site-visit-request")
async def site_visit_request(req: SiteVisitRequest, request: Request):
    ip = get_client_ip(request)
    validation_data = {"name": req.name, "email": req.email, "phone": req.phone, "message": req.project_brief, "fax": req.fax}
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(validation_data, ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"status": "ok"}
        raise HTTPException(status_code=422, detail=error_msg)

    await check_recaptcha(request)

    lead = {
        "name": req.name,
        "email": req.email,
        "phone": req.phone,
        "company": req.company,
        "message": req.project_brief,
        "source": "exit_intent_site_visit",
        "page_url": req.page_url,
        "spam_score": spam_score,
        "ip": ip,
        "geo": {"country": geo_data.get("country", ""), "country_name": geo_data.get("country_name", ""), "city": geo_data.get("city", "")},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await leads_col.insert_one(lead)
    lead.pop("_id", None)
    
    if NOTIFICATION_EMAIL:
        try:
            email_data = {
                "name": req.name,
                "email": req.email,
                "company": req.company,
                "phone": req.phone,
                "project_type": "Site Visit",
                "location": req.page_url,
                "notes": req.project_brief,
            }
            subject, html = site_visit_email(email_data)
            await send_email(NOTIFICATION_EMAIL, subject, html)
        except Exception:
            pass
    
    return {"status": "ok"}
