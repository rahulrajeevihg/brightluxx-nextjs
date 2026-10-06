"""CPD / Lunch & Learn programme routes."""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from database import leads_col
from email_service import send_email, NOTIFICATION_EMAIL
from email_templates import cpd_request_email
from anti_spam import validate_submission_full, check_recaptcha
from utils import get_client_ip

router = APIRouter()


class CPDRequest(BaseModel):
    name: str
    email: str
    company: str
    role: str
    phone: Optional[str] = ""
    preferred_topic: str
    preferred_format: str = "in-office"
    group_size: Optional[str] = ""
    preferred_date: Optional[str] = ""
    message: Optional[str] = ""
    fax: Optional[str] = None


@router.post("/api/cpd/request")
async def submit_cpd_request(data: CPDRequest, request: Request):
    client_ip = get_client_ip(request)
    validation_data = {"name": data.name, "email": data.email, "phone": data.phone, "message": data.message or "", "fax": data.fax}
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(validation_data, client_ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"success": True, "message": "Thank you! Our team will contact you within 24 hours to schedule your session."}
        raise HTTPException(status_code=422, detail=error_msg)

    await check_recaptcha(request)

    lead_dict = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "email": data.email,
        "company": data.company,
        "role": data.role,
        "phone": data.phone,
        "source": "cpd_programme",
        "application": f"CPD: {data.preferred_topic}",
        "status": "new",
        "notes": "",
        "cpd_details": {
            "preferred_topic": data.preferred_topic,
            "preferred_format": data.preferred_format,
            "group_size": data.group_size,
            "preferred_date": data.preferred_date,
            "message": data.message,
        },
        "created_at": datetime.now(timezone.utc),
    }

    lead_dict["spam_score"] = spam_score
    lead_dict["ip"] = client_ip
    lead_dict["geo"] = {"country": geo_data.get("country", ""), "country_name": geo_data.get("country_name", ""), "city": geo_data.get("city", "")}
    await leads_col.insert_one(lead_dict)

    # Send enhanced email notification
    if NOTIFICATION_EMAIL:
        try:
            email_data = {
                "name": data.name,
                "email": data.email,
                "company": data.company,
                "phone": data.phone,
                "role": data.role,
                "attendees": data.group_size,
                "preferred_date": data.preferred_date,
                "preferred_topic": data.preferred_topic,
                "notes": data.message,
            }
            subject, html = cpd_request_email(email_data)
            await send_email(NOTIFICATION_EMAIL, subject, html)
        except Exception:
            pass

    return {
        "success": True,
        "message": "Thank you! Our team will contact you within 24 hours to schedule your session.",
    }
