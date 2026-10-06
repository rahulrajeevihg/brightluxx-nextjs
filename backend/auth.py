from fastapi import HTTPException, Header, Request
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from typing import Optional
import os

from database import admins_col
from utils import serialize_doc

SECRET_KEY = os.environ.get("JWT_SECRET")
REFRESH_SECRET = os.environ.get("JWT_REFRESH_SECRET")
if not SECRET_KEY or not REFRESH_SECRET:
    raise RuntimeError("JWT_SECRET and JWT_REFRESH_SECRET must be set in environment")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRY = 4 * 3600
REFRESH_TOKEN_EXPIRY = 7 * 24 * 3600

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(data: dict, token_type: str = "access"):
    if token_type == "refresh":
        exp = datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TOKEN_EXPIRY)
        secret = REFRESH_SECRET
    else:
        exp = datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_EXPIRY)
        secret = SECRET_KEY
    return jwt.encode({**data, "exp": exp.timestamp(), "type": token_type}, secret, algorithm=ALGORITHM)


def set_auth_cookies(response, access_token: str, refresh_token: str = None):
    """Set httpOnly secure cookies for auth tokens."""
    response.set_cookie(
        key="blx_access", value=access_token, httponly=True,
        secure=True, samesite="none", max_age=ACCESS_TOKEN_EXPIRY, path="/",
    )
    if refresh_token:
        response.set_cookie(
            key="blx_refresh", value=refresh_token, httponly=True,
            secure=True, samesite="none", max_age=REFRESH_TOKEN_EXPIRY, path="/",
        )


def clear_auth_cookies(response):
    """Clear auth cookies on logout."""
    response.delete_cookie("blx_access", path="/")
    response.delete_cookie("blx_refresh", path="/")


async def get_current_admin(request: Request):
    """Extract and verify admin from httpOnly cookie or Authorization header."""
    # Try cookie first, then header
    token = request.cookies.get("blx_access")
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") not in (None, "access"):
            raise HTTPException(status_code=401, detail="Invalid token type")
        admin = await admins_col.find_one({"email": payload.get("email")})
        if not admin:
            raise HTTPException(status_code=401, detail="Admin not found")
        return serialize_doc(admin)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
