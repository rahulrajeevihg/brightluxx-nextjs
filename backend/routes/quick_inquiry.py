from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from database import leads_col
from email_service import notify_new_lead
from anti_spam import validate_submission_full, check_recaptcha
from utils import get_client_ip

router = APIRouter(prefix="/api")


class QuickInquiryRequest(BaseModel):
    name: str
    email: str
    phone: str = ""
    message: str = ""
    page_context: str = ""
    page_url: str = ""
    # Honeypot
    website: Optional[str] = None
    fax: Optional[str] = None


@router.post("/quick-inquiry")
async def quick_inquiry(req: QuickInquiryRequest, request: Request):
    ip = get_client_ip(request)

    # Anti-spam + geo
    data = req.dict()
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(data, ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"status": "ok"}
        raise HTTPException(status_code=422, detail=error_msg)

    await check_recaptcha(request)

    lead = {
        "name": req.name,
        "email": req.email,
        "phone": req.phone,
        "message": req.message,
        "source": "quick_inquiry",
        "page_context": req.page_context,
        "page_url": req.page_url,
        "spam_score": spam_score,
        "ip": ip,
        "geo": {"country": geo_data.get("country", ""), "country_name": geo_data.get("country_name", ""), "city": geo_data.get("city", "")},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await leads_col.insert_one(lead)
    lead.pop("_id", None)
    try:
        await notify_new_lead({**lead, "application": req.page_context})
    except Exception:
        pass
    return {"status": "ok"}
