"""
WordPress legacy URL redirects and proper 404 handling.
Also serves /api/llms.txt as plain text for AI crawlers.
"""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse
from database import db
import os

router = APIRouter(tags=["Redirects"])

EXTERNAL_CDN = "https://files.ihgbrands.com"


@router.get("/api/cdn/{filename:path}")
async def legacy_cdn_redirect(filename: str):
    """Legacy /api/cdn/* image paths → permanent redirect to external CDN."""
    flat = filename.replace("/", "_")
    return RedirectResponse(
        url=f"{EXTERNAL_CDN}/uploads_{flat}",
        status_code=301,
        headers={"Cache-Control": "public, max-age=86400"},
    )

# WordPress legacy URL → current equivalent
WP_REDIRECTS = {
    "/our-works/": "/projects",
    "/our-works": "/projects",
    "/digital-solutions/": "/solutions",
    "/digital-solutions": "/solutions",
    "/products/led-display": "/products",
    "/products/led-display/": "/products",
    "/products/indoor-led-display": "/indoor-led",
    "/products/indoor-led-display/": "/indoor-led",
    "/products/outdoor-led-display": "/outdoor-led",
    "/products/outdoor-led-display/": "/outdoor-led",
    "/products/spherical-led-display": "/products",
    "/products/spherical-led-display/": "/products",
    "/products/cube-led-display-p3": "/products",
    "/products/cube-led-display-p3/": "/products",
    "/products/transparent-led-display": "/glassmorph",
    "/products/transparent-led-display/": "/glassmorph",
    "/products/rental-led-display": "/products",
    "/products/flexible-led-display": "/products",
    "/download-catalog/": "/products",
    "/download-catalog": "/products",
    "/about-us/": "/about",
    "/about-us": "/about",
    "/contact-us/": "/contact",
    "/contact-us": "/contact",
    "/services/": "/solutions",
    "/services": "/solutions",
    "/portfolio/": "/projects",
    "/portfolio": "/projects",
    "/gallery/": "/projects",
    "/gallery": "/projects",
}


@router.get("/api/wp-redirect")
async def check_redirect(path: str = "/"):
    """Check if a path has a WordPress redirect."""
    target = WP_REDIRECTS.get(path)
    if target:
        return {"redirect": True, "target": target}
    if path.startswith("/wp-content/") or path.startswith("/wp-admin/"):
        return {"redirect": True, "target": "/products"}
    return {"redirect": False}


@router.get("/api/llms.txt")
async def llms_txt():
    """Serve llms.txt as plain text for AI crawlers."""
    llms_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "llms.txt")
    if os.path.exists(llms_path):
        with open(llms_path, "r") as f:
            return PlainTextResponse(f.read(), media_type="text/plain")
    # Fallback
    return PlainTextResponse(
        "# Brightluxx — Premium LED Display Solutions\n"
        "Website: https://brightluxx.com\n"
        "Location: Dubai, UAE\n"
        "Products: MicroLED, Video Walls, Transparent LED, Interactive Kiosks, Smart Glass\n"
        "Serving: UAE, Saudi Arabia, Qatar, Kuwait, GCC\n",
        media_type="text/plain",
    )
