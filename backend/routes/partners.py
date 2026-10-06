"""Routes for distribution, supplier registration, and technical support forms."""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from database import db, leads_col
from email_service import send_email, NOTIFICATION_EMAIL
from email_templates import franchise_email, supplier_email, support_email
from anti_spam import validate_submission_full, check_recaptcha
from utils import get_client_ip

router = APIRouter()


class FranchiseRequest(BaseModel):
    name: str
    company: str
    email: str
    phone: str
    country: str
    city: str
    business_type: str = ""
    experience: str = ""
    message: str = ""
    fax: Optional[str] = None


class SupplierRegistration(BaseModel):
    company_name: str
    contact_person: str
    email: str
    phone: str
    country: str
    product_category: str
    certifications: str = ""
    website: str = ""
    message: str = ""
    fax: Optional[str] = None


class TechnicalSupportRequest(BaseModel):
    name: str
    company: str
    email: str
    phone: str
    product: str = ""
    issue_type: str = ""
    description: str
    urgency: str = "normal"
    fax: Optional[str] = None


@router.post("/api/franchise-request")
async def franchise_request(data: FranchiseRequest, request: Request):
    ip = get_client_ip(request)
    validation_data = {"name": data.name, "email": data.email, "phone": data.phone, "message": data.message, "fax": data.fax}
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(validation_data, ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"success": True, "message": "Thank you! We will review your application and get back to you within 48 hours."}
        raise HTTPException(status_code=422, detail=error_msg)

    await check_recaptcha(request)

    lead = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "company": data.company,
        "email": data.email,
        "phone": data.phone,
        "source": "franchise_request",
        "application": f"Franchise/Distribution — {data.country}, {data.city}",
        "status": "new",
        "country": data.country,
        "city": data.city,
        "business_type": data.business_type,
        "experience": data.experience,
        "message": data.message,
        "spam_score": spam_score,
        "ip": ip,
        "geo": {"country": geo_data.get("country", ""), "country_name": geo_data.get("country_name", ""), "city": geo_data.get("city", "")},
        "created_at": datetime.now(timezone.utc),
    }
    await leads_col.insert_one(lead)

    if NOTIFICATION_EMAIL:
        try:
            subject, html = franchise_email(lead)
            await send_email(NOTIFICATION_EMAIL, subject, html)
        except Exception:
            pass

    return {"success": True, "message": "Thank you! We will review your application and get back to you within 48 hours."}


@router.post("/api/supplier-registration")
async def supplier_registration(data: SupplierRegistration, request: Request):
    ip = get_client_ip(request)
    # Note: website is a legitimate field for suppliers, so only check fax honeypot
    validation_data = {"name": data.contact_person, "email": data.email, "phone": data.phone, "message": data.message, "fax": data.fax}
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(validation_data, ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"success": True, "message": "Registration received! Our procurement team will review and contact you."}
        raise HTTPException(status_code=422, detail=error_msg)

    await check_recaptcha(request)

    doc = {
        "id": str(uuid.uuid4()),
        "company_name": data.company_name,
        "contact_person": data.contact_person,
        "email": data.email,
        "phone": data.phone,
        "country": data.country,
        "product_category": data.product_category,
        "certifications": data.certifications,
        "website": data.website,
        "message": data.message,
        "status": "pending",
        "spam_score": spam_score,
        "ip": ip,
        "geo": {"country": geo_data.get("country", ""), "country_name": geo_data.get("country_name", ""), "city": geo_data.get("city", "")},
        "created_at": datetime.now(timezone.utc),
    }
    await db["supplier_registrations"].insert_one(doc)

    lead = {
        "id": doc["id"],
        "name": data.contact_person,
        "company": data.company_name,
        "email": data.email,
        "phone": data.phone,
        "source": "supplier_registration",
        "application": f"Supplier — {data.product_category}",
        "status": "new",
        "spam_score": spam_score,
        "ip": ip,
        "geo": {"country": geo_data.get("country", ""), "country_name": geo_data.get("country_name", ""), "city": geo_data.get("city", "")},
        "created_at": datetime.now(timezone.utc),
    }
    await leads_col.insert_one(lead)

    if NOTIFICATION_EMAIL:
        try:
            subject, html = supplier_email(doc)
            await send_email(NOTIFICATION_EMAIL, subject, html)
        except Exception:
            pass

    return {"success": True, "message": "Registration received! Our procurement team will review and contact you."}


@router.post("/api/technical-support")
async def technical_support(data: TechnicalSupportRequest, request: Request):
    ip = get_client_ip(request)
    validation_data = {"name": data.name, "email": data.email, "phone": data.phone, "message": data.description, "fax": data.fax}
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(validation_data, ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"success": True, "message": "Support ticket created! Our technical team will respond within 4 hours for urgent requests."}
        raise HTTPException(status_code=422, detail=error_msg)

    await check_recaptcha(request)

    doc = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "company": data.company,
        "email": data.email,
        "phone": data.phone,
        "product": data.product,
        "issue_type": data.issue_type,
        "description": data.description,
        "urgency": data.urgency,
        "status": "open",
        "spam_score": spam_score,
        "ip": ip,
        "geo": {"country": geo_data.get("country", ""), "country_name": geo_data.get("country_name", ""), "city": geo_data.get("city", "")},
        "created_at": datetime.now(timezone.utc),
    }
    await db["support_tickets"].insert_one(doc)

    lead = {
        "id": doc["id"],
        "name": data.name,
        "company": data.company,
        "email": data.email,
        "phone": data.phone,
        "source": "technical_support",
        "application": f"Support — {data.issue_type} ({data.urgency})",
        "status": "new",
        "spam_score": spam_score,
        "ip": ip,
        "geo": {"country": geo_data.get("country", ""), "country_name": geo_data.get("country_name", ""), "city": geo_data.get("city", "")},
        "created_at": datetime.now(timezone.utc),
    }
    await leads_col.insert_one(lead)

    if NOTIFICATION_EMAIL:
        try:
            subject, html = support_email(doc)
            await send_email(NOTIFICATION_EMAIL, subject, html)
        except Exception:
            pass

    return {"success": True, "message": "Support ticket created! Our technical team will respond within 4 hours for urgent requests."}
