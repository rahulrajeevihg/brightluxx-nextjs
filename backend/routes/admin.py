from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from jose import jwt, JWTError

from database import admins_col, products_col, inspirations_col, projects_col, leads_col
from models import AdminLogin, AdminPasswordChange
from utils import serialize_doc, login_limiter, get_client_ip
from auth import (
    pwd_context, create_token, get_current_admin, set_auth_cookies, clear_auth_cookies,
    ACCESS_TOKEN_EXPIRY, REFRESH_SECRET, ALGORITHM,
)

router = APIRouter()


@router.post("/api/admin/login")
async def admin_login(creds: AdminLogin, request: Request):
    client_ip = get_client_ip(request)
    if not login_limiter.check(client_ip):
        remaining_wait = 60
        raise HTTPException(status_code=429, detail=f"Too many login attempts. Try again in {remaining_wait}s.", headers={"Retry-After": str(remaining_wait)})
    admin = await admins_col.find_one({"email": creds.email})
    if not admin or not pwd_context.verify(creds.password, admin["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    login_limiter.reset(client_ip)
    access_token = create_token({"email": admin["email"], "role": admin.get("role", "admin")}, "access")
    refresh_token = create_token({"email": admin["email"], "role": admin.get("role", "admin")}, "refresh")
    body = {
        "token": access_token,
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRY,
        "admin": {"email": admin["email"], "name": admin.get("name", "Admin"), "role": admin.get("role", "admin")}
    }
    response = JSONResponse(content=body)
    set_auth_cookies(response, access_token, refresh_token)
    return response


@router.post("/api/admin/refresh")
async def admin_refresh_token(request: Request):
    # Read refresh token from cookie first, then from body
    token = request.cookies.get("blx_refresh")
    if not token:
        try:
            data = await request.json()
            token = data.get("refresh_token", "")
        except Exception:
            token = ""
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token provided")
    try:
        payload = jwt.decode(token, REFRESH_SECRET, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        admin = await admins_col.find_one({"email": payload.get("email")})
        if not admin:
            raise HTTPException(status_code=401, detail="Admin not found")
        new_access = create_token({"email": admin["email"], "role": admin.get("role", "admin")}, "access")
        body = {"token": new_access, "expires_in": ACCESS_TOKEN_EXPIRY}
        response = JSONResponse(content=body)
        set_auth_cookies(response, new_access)
        return response
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


@router.get("/api/admin/me")
async def admin_me(admin=Depends(get_current_admin)):
    return {"email": admin["email"], "name": admin.get("name", "Admin"), "role": admin.get("role", "super_admin")}


@router.post("/api/admin/logout")
async def admin_logout():
    response = JSONResponse(content={"success": True})
    clear_auth_cookies(response)
    return response


@router.post("/api/admin/change-password")
async def admin_change_password(data: AdminPasswordChange, admin=Depends(get_current_admin)):
    admin_doc = await admins_col.find_one({"email": admin["email"]})
    if not admin_doc:
        raise HTTPException(status_code=404, detail="Admin not found")
    if not pwd_context.verify(data.current_password, admin_doc["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    hashed = pwd_context.hash(data.new_password)
    await admins_col.update_one({"email": admin["email"]}, {"$set": {"password": hashed, "password_changed_at": datetime.now(timezone.utc)}})
    return {"success": True, "message": "Password changed successfully"}


@router.get("/api/admin/stats")
async def admin_stats(admin=Depends(get_current_admin)):
    product_count = await products_col.count_documents({})
    inspiration_count = await inspirations_col.count_documents({})
    project_count = await projects_col.count_documents({})
    lead_count = await leads_col.count_documents({})
    new_leads = await leads_col.count_documents({"status": "new"})

    cat_pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    categories = []
    async for doc in products_col.aggregate(cat_pipeline):
        categories.append({"category": doc["_id"], "count": doc["count"]})

    recent_leads_cursor = leads_col.find().sort("created_at", -1).limit(5)
    recent_leads = [serialize_doc(doc) for doc in await recent_leads_cursor.to_list(length=5)]

    recent_products_cursor = products_col.find().sort("created_at", -1).limit(5)
    recent_products = [serialize_doc(doc) for doc in await recent_products_cursor.to_list(length=5)]

    lead_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    lead_status_map = {}
    async for doc in leads_col.aggregate(lead_pipeline):
        status_key = doc["_id"] or "new"
        lead_status_map[status_key] = lead_status_map.get(status_key, 0) + doc["count"]
    lead_statuses = [{"status": k, "count": v} for k, v in lead_status_map.items()]

    return {
        "products": product_count,
        "inspirations": inspiration_count,
        "projects": project_count,
        "leads": lead_count,
        "new_leads": new_leads,
        "categories": categories,
        "lead_statuses": lead_statuses,
        "recent_leads": recent_leads,
        "recent_products": recent_products
    }
