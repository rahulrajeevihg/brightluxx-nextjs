"""Design Assist request route."""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from database import leads_col
from email_service import send_email, NOTIFICATION_EMAIL
from email_templates import design_assist_email
from anti_spam import validate_submission_full, check_recaptcha
from utils import get_client_ip

router = APIRouter()


class DesignAssistRequest(BaseModel):
    name: str
    email: str
    company: str
    role: str
    phone: Optional[str] = ""
    project_type: Optional[str] = ""
    project_stage: Optional[str] = ""
    message: Optional[str] = ""
    fax: Optional[str] = None


@router.post("/api/design-assist/request")
async def submit_design_assist(data: DesignAssistRequest, request: Request):
    client_ip = get_client_ip(request)
    validation_data = {"name": data.name, "email": data.email, "phone": data.phone, "message": data.message or "", "fax": data.fax}
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(validation_data, client_ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"success": True, "message": "Thank you! Our design assist team will contact you within 24 hours."}
        raise HTTPException(status_code=422, detail=error_msg)

    await check_recaptcha(request)

    lead_dict = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "email": data.email,
        "company": data.company,
        "role": data.role,
        "phone": data.phone,
        "source": "design_assist",
        "application": f"Design Assist: {data.project_type or 'General'}",
        "status": "new",
        "notes": "",
        "design_assist_details": {
            "project_type": data.project_type,
            "project_stage": data.project_stage,
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
                "project_type": data.project_type,
                "requirements": data.message,
                "deadline": data.project_stage,
            }
            subject, html = design_assist_email(email_data)
            await send_email(NOTIFICATION_EMAIL, subject, html)
        except Exception:
            pass

    return {
        "success": True,
        "message": "Thank you! Our design assist team will contact you within 24 hours.",
    }
